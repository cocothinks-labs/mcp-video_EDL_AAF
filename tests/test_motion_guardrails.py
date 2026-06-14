"""Tests for the low-motion / slideshow temporal-motion guardrail (issue #10).

A video can be technically clean (good brightness/contrast/audio/encoding) yet
visually behave like a low-motion slideshow / Ken Burns sequence with
insufficient temporal motion. For image-to-video and social creative this is a
defect, but the legacy quality checks pass it silently with no recommendations.

These tests pin the behaviour that a near-static / slideshow-like clip is
flagged (as a non-fatal recommendation / warning) while a genuinely-moving clip
is NOT flagged (no false positive).
"""

from __future__ import annotations

import shutil
import subprocess

import pytest


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


pytestmark = pytest.mark.skipif(not _has_ffmpeg(), reason="FFmpeg/ffprobe not installed")


def _run_ffmpeg(args: list[str]) -> None:
    result = subprocess.run(["ffmpeg", "-y", *args], capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr[-500:]}")


def create_slideshow_video(output_path: str) -> str:
    """Create a slideshow-like clip: a sequence of static color cards, hard cuts.

    Each "slide" is held perfectly still; motion only exists at the cut between
    slides. This mimics an unintended slideshow exported as a 30fps video.
    """
    _run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=320x240:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:s=320x240:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x240:d=1",
            "-f",
            "lavfi",
            "-i",
            "color=c=yellow:s=320x240:d=1",
            "-filter_complex",
            "[0][1][2][3]concat=n=4:v=1:a=0[v]",
            "-map",
            "[v]",
            "-r",
            "30",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
    )
    return output_path


def create_static_video(output_path: str) -> str:
    """Create a perfectly frozen single-color clip (zero temporal motion)."""
    _run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "color=c=gray:s=320x240:d=4:r=30",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
    )
    return output_path


def create_moving_video(output_path: str) -> str:
    """Create a genuinely-moving clip with continuous temporal motion."""
    _run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=320x240:r=30:d=4",
            "-pix_fmt",
            "yuv420p",
            output_path,
        ]
    )
    return output_path


def create_calm_pan_video(output_path: str) -> str:
    """Create a calm-but-real shot: gentle camera drift over textured content.

    This is the deliberate false-positive bait: a quiet, slow shot that a human
    would NOT call a slideshow. It must remain unflagged.
    """
    _run_ffmpeg(
        [
            "-f",
            "lavfi",
            "-i",
            "testsrc2=s=320x240:r=30:d=4",
            "-vf",
            "crop=240:180:'40+20*sin(t)':'30+15*cos(t)',scale=320:240,format=yuv420p",
            output_path,
        ]
    )
    return output_path


# --------------------------------------------------------------------------- #
# quality_guardrails (video_quality_check) surface
# --------------------------------------------------------------------------- #


class TestMotionCheckQualityGuardrails:
    """VisualQualityGuardrails.check_motion temporal-motion guardrail."""

    @pytest.fixture
    def guardrails(self):
        from mcp_video import VisualQualityGuardrails

        return VisualQualityGuardrails()

    def test_slideshow_is_flagged_as_low_motion(self, guardrails, tmp_path):
        """A slideshow-like clip should be flagged for insufficient temporal motion."""
        video_path = str(tmp_path / "slideshow.mp4")
        create_slideshow_video(video_path)

        report = guardrails.check_motion(video_path)

        assert report.check_name == "temporal_motion"
        assert report.passed is False, "Slideshow-like clip must be flagged as low-motion"
        assert "motion" in report.message.lower()
        assert 0.0 <= report.details["static_fraction"] <= 1.0
        assert report.details["static_fraction"] >= guardrails.MOTION_STATIC_FRACTION_MAX

    def test_static_clip_is_flagged_as_low_motion(self, guardrails, tmp_path):
        """A perfectly frozen clip is the extreme slideshow case and must be flagged."""
        video_path = str(tmp_path / "static.mp4")
        create_static_video(video_path)

        report = guardrails.check_motion(video_path)

        assert report.passed is False
        assert report.details["static_fraction"] >= guardrails.MOTION_STATIC_FRACTION_MAX

    def test_moving_clip_is_not_flagged(self, guardrails, tmp_path):
        """A genuinely-moving clip must NOT be flagged (no false positive)."""
        video_path = str(tmp_path / "moving.mp4")
        create_moving_video(video_path)

        report = guardrails.check_motion(video_path)

        assert report.check_name == "temporal_motion"
        assert report.passed is True, "Moving clip must not be flagged as low-motion"
        assert report.details["static_fraction"] < guardrails.MOTION_STATIC_FRACTION_MAX

    def test_calm_pan_is_not_flagged(self, guardrails, tmp_path):
        """A calm-but-real shot (gentle drift) must not be flagged as a slideshow."""
        video_path = str(tmp_path / "calm.mp4")
        create_calm_pan_video(video_path)

        report = guardrails.check_motion(video_path)

        assert report.passed is True, "Calm real motion must not be a false positive"

    def test_motion_check_included_in_run_all_checks(self, guardrails, tmp_path):
        """The motion check must be part of the standard battery."""
        video_path = str(tmp_path / "moving.mp4")
        create_moving_video(video_path)

        checks = guardrails.run_all_checks(video_path)
        names = [c.check_name for c in checks]
        assert "temporal_motion" in names

    def test_slideshow_surfaces_recommendation_without_hard_fail(self, tmp_path):
        """generate_report must surface a low-motion recommendation for a slideshow.

        Per issue #10 the motion finding is advisory: it should appear in
        ``recommendations`` (so an agent/human sees it) but must NOT silently
        flip an otherwise-clean technical gate. We assert the recommendation is
        present and mentions motion/slideshow.
        """
        from mcp_video import quality_check

        video_path = str(tmp_path / "slideshow.mp4")
        create_slideshow_video(video_path)

        report = quality_check(video_path)

        assert "temporal_motion" in [c["name"] for c in report["checks"]]
        joined = " ".join(report["recommendations"]).lower()
        assert "motion" in joined or "slideshow" in joined, (
            f"Expected a low-motion recommendation, got: {report['recommendations']}"
        )

    def test_moving_video_has_no_low_motion_recommendation(self, tmp_path):
        """A moving video must not produce a spurious low-motion recommendation."""
        from mcp_video import quality_check

        video_path = str(tmp_path / "moving.mp4")
        create_moving_video(video_path)

        report = quality_check(video_path)
        joined = " ".join(report["recommendations"]).lower()
        assert "temporal motion" not in joined and "slideshow" not in joined


# --------------------------------------------------------------------------- #
# design_quality (video_design_quality_check) surface
# --------------------------------------------------------------------------- #


class TestMotionCheckDesignQuality:
    """DesignQualityGuardrails motion guardrail integration."""

    def _issues(self, video_path: str):
        from mcp_video.design_quality.guardrails import DesignQualityGuardrails

        g = DesignQualityGuardrails()
        report = g.analyze(video_path)
        return report

    def test_slideshow_emits_low_motion_warning(self, tmp_path):
        video_path = str(tmp_path / "slideshow.mp4")
        create_slideshow_video(video_path)

        report = self._issues(video_path)
        motion_warnings = [
            i
            for i in report.issues
            if i.category == "motion" and ("slideshow" in i.message.lower() or "temporal motion" in i.message.lower())
        ]
        assert motion_warnings, "Slideshow must emit a low-motion design warning"
        assert all(w.severity == "warning" for w in motion_warnings)

    def test_moving_video_has_no_low_motion_warning(self, tmp_path):
        video_path = str(tmp_path / "moving.mp4")
        create_moving_video(video_path)

        report = self._issues(video_path)
        motion_warnings = [
            i
            for i in report.issues
            if i.category == "motion" and ("slideshow" in i.message.lower() or "temporal motion" in i.message.lower())
        ]
        assert not motion_warnings, "Moving video must not emit a low-motion design warning"
