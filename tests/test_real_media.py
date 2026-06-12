"""Codec integration tests — validates features against synthesized media.

These tests use FFmpeg lavfi-generated files that exercise real-world codec
paths: HEVC/H.264 in MOV containers, variable-aspect-ratio inputs, alpha-channel
PNG overlay compositing, and composition of multiple features.

Cheap tests (1080p, fast to encode) run without a marker in the default suite.
Expensive tests (4K, slow to encode) carry @pytest.mark.slow.

Run all including slow: pytest tests/test_real_media.py -m "" -v
"""

from __future__ import annotations

import shutil
import subprocess
import os

import pytest

from mcp_video.engine import (
    apply_filter,
    normalize_audio,
    overlay_video,
    split_screen,
    probe,
)
from mcp_video.server import video_batch


# ---------------------------------------------------------------------------
# Encoder availability helpers
# ---------------------------------------------------------------------------


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _has_libx265() -> bool:
    """Return True if libx265 is compiled into the available ffmpeg."""
    if not _has_ffmpeg():
        return False
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    encoders_cmd = [ffmpeg_bin, "-encoders"]
    result = subprocess.run(encoders_cmd, capture_output=True, text=True, timeout=10)
    return "libx265" in result.stdout


def _ffmpeg_run(cmd: list[str], label: str) -> None:
    """Run an ffmpeg command; skip the test if the command fails."""
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        pytest.skip(f"FFmpeg synthesis failed ({label}): {stderr[-300:]}")


# ---------------------------------------------------------------------------
# Module-scoped synthetic fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def synth_landscape_hevc(tmp_path_factory) -> str:
    """1920x1080 HEVC-in-MOV, 2 s, no audio — exercises HEVC codec path."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    if not _has_libx265():
        pytest.skip("libx265 encoder not available")
    out = str(tmp_path_factory.mktemp("synth") / "landscape_1080_hevc.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30:duration=2",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            out,
        ],
        "landscape HEVC",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create landscape HEVC fixture")
    return out


@pytest.fixture(scope="module")
def synth_landscape_hevc_audio(tmp_path_factory) -> str:
    """1920x1080 HEVC-in-MOV, 2 s, with AAC audio — for normalize_audio tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    if not _has_libx265():
        pytest.skip("libx265 encoder not available")
    out = str(tmp_path_factory.mktemp("synth") / "landscape_1080_hevc_audio.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1920x1080:rate=30:duration=2",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            out,
        ],
        "landscape HEVC + audio",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create landscape HEVC+audio fixture")
    return out


@pytest.fixture(scope="module")
def synth_square_hevc(tmp_path_factory) -> str:
    """1080x1080 HEVC-in-MOV, 2 s — square aspect for PIP overlay tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    if not _has_libx265():
        pytest.skip("libx265 encoder not available")
    out = str(tmp_path_factory.mktemp("synth") / "square_1080_hevc.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1080x1080:rate=30:duration=2",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            out,
        ],
        "square HEVC",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create square HEVC fixture")
    return out


@pytest.fixture(scope="module")
def synth_portrait_hevc(tmp_path_factory) -> str:
    """1080x1920 HEVC-in-MOV, 2 s — portrait aspect for split-screen tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    if not _has_libx265():
        pytest.skip("libx265 encoder not available")
    out = str(tmp_path_factory.mktemp("synth") / "portrait_1080_hevc.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=1080x1920:rate=30:duration=2",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            out,
        ],
        "portrait HEVC",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create portrait HEVC fixture")
    return out


@pytest.fixture(scope="module")
def synth_crop_h264(tmp_path_factory) -> str:
    """640x480 H.264-in-MOV, 2 s — small crop resolution for batch tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    out = str(tmp_path_factory.mktemp("synth") / "crop_640x480.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=640x480:rate=30:duration=2",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            out,
        ],
        "640x480 H.264",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create 640x480 H.264 fixture")
    return out


@pytest.fixture(scope="module")
def synth_timeline_mp4(tmp_path_factory) -> str:
    """1920x1080 H.264 MP4, 2 s, with AAC audio — for filter-chain tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    out = str(tmp_path_factory.mktemp("synth") / "timeline.mp4")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "smptehdbars=size=1920x1080:duration=2:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            out,
        ],
        "timeline MP4",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create timeline MP4 fixture")
    return out


@pytest.fixture(scope="module")
def synth_alpha_png(tmp_path_factory) -> str:
    """320x240 RGBA PNG — semi-transparent overlay for alpha compositing tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    out = str(tmp_path_factory.mktemp("synth") / "alpha_overlay.png")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=red@0.5:size=320x240,format=rgba",
            "-frames:v",
            "1",
            "-update",
            "1",
            out,
        ],
        "alpha PNG",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create alpha PNG fixture")
    return out


@pytest.fixture(scope="module")
def synth_4k_hevc(tmp_path_factory) -> str:
    """3840x2160 HEVC-in-MOV, 2 s — 4K fixture for slow tests."""
    if not _has_ffmpeg():
        pytest.skip("FFmpeg not installed")
    if not _has_libx265():
        pytest.skip("libx265 encoder not available")
    out = str(tmp_path_factory.mktemp("synth") / "4k_hevc.mov")
    _ffmpeg_run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=3840x2160:rate=24:duration=2",
            "-c:v",
            "libx265",
            "-tag:v",
            "hvc1",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            out,
        ],
        "4K HEVC",
    )
    if not os.path.isfile(out):
        pytest.skip("Failed to create 4K HEVC fixture")
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFilterSynthMedia:
    """Validate video filters on synthesized HEVC footage."""

    @pytest.mark.parametrize(
        "filter_name,params",
        [
            ("blur", {"radius": 8}),
            ("grayscale", {}),
            ("sharpen", {"amount": 2.0}),
            ("sepia", {}),
            ("invert", {}),
            ("vignette", {}),
        ],
    )
    def test_filter_preserves_resolution(self, synth_landscape_hevc, tmp_path, filter_name, params):
        out = str(tmp_path / f"{filter_name}.mov")
        result = apply_filter(synth_landscape_hevc, filter_name, params or None, out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(synth_landscape_hevc)
        assert info.width == orig.width
        assert info.height == orig.height

    @pytest.mark.parametrize("preset", ["warm", "cool", "vintage", "cinematic", "noir"])
    def test_color_preset_preserves_resolution(self, synth_landscape_hevc, tmp_path, preset):
        out = str(tmp_path / f"preset_{preset}.mov")
        result = apply_filter(synth_landscape_hevc, "color_preset", {"preset": preset}, out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(synth_landscape_hevc)
        assert info.width == orig.width
        assert info.height == orig.height

    @pytest.mark.slow
    def test_filter_preserves_4k_resolution(self, synth_4k_hevc, tmp_path):
        """4K HEVC filter — verifies high-resolution path is preserved."""
        out = str(tmp_path / "4k_grayscale.mov")
        result = apply_filter(synth_4k_hevc, "grayscale", {}, out)
        assert result.success
        info = probe(result.output_path)
        orig = probe(synth_4k_hevc)
        assert info.width == orig.width
        assert info.height == orig.height


class TestNormalizeAudioSynthMedia:
    """Validate audio normalization on synthesized HEVC footage with audio."""

    def test_normalize_audio_preserves_codec(self, synth_landscape_hevc_audio, tmp_path):
        out = str(tmp_path / "norm_youtube.mov")
        result = normalize_audio(synth_landscape_hevc_audio, target_lufs=-16.0, output_path=out)
        assert result.success
        info = probe(result.output_path)
        assert info.audio_codec in ("aac", "mp4a")
        assert info.codec in ("h264", "hevc", "libx264")


class TestOverlaySynthMedia:
    """Validate picture-in-picture overlay with synthesized files."""

    def test_square_on_landscape_pip(self, synth_landscape_hevc, synth_square_hevc, tmp_path):
        out = str(tmp_path / "pip.mov")
        result = overlay_video(
            synth_landscape_hevc,
            synth_square_hevc,
            position="bottom-right",
            width=360,
            output_path=out,
        )
        assert result.success
        info = probe(result.output_path)
        orig = probe(synth_landscape_hevc)
        assert info.width == orig.width
        assert info.height == orig.height

    def test_png_alpha_overlay(self, synth_landscape_hevc, synth_alpha_png, tmp_path):
        """PNG with alpha channel composited onto HEVC video."""
        out = str(tmp_path / "png_overlay.mov")
        result = overlay_video(
            synth_landscape_hevc,
            synth_alpha_png,
            position="center",
            width=400,
            opacity=0.9,
            output_path=out,
        )
        assert result.success
        info = probe(result.output_path)
        orig = probe(synth_landscape_hevc)
        assert info.width == orig.width
        assert info.height == orig.height


class TestSplitScreenSynthMedia:
    """Validate split-screen compositing with synthesized files."""

    def test_portrait_square_side_by_side(self, synth_portrait_hevc, synth_square_hevc, tmp_path):
        out = str(tmp_path / "sbs.mov")
        result = split_screen(synth_portrait_hevc, synth_square_hevc, layout="side-by-side", output_path=out)
        assert result.success
        info = probe(result.output_path)
        assert info.height > 0
        assert info.width > 0


class TestBatchSynthMedia:
    """Validate batch_process with synthesized files at multiple resolutions."""

    def test_blur_across_resolutions(self, synth_landscape_hevc, synth_square_hevc, synth_crop_h264, tmp_path):
        files = [synth_landscape_hevc, synth_square_hevc, synth_crop_h264]
        result = video_batch(
            inputs=files,
            operation="blur",
            params={"filter_params": {"radius": 8, "strength": 2}},
        )
        assert result["success"]
        assert result["succeeded"] == 3
        for r in result["results"]:
            assert r["success"]
            assert os.path.isfile(r["output_path"])


class TestCrossFeatureSynthMedia:
    """Test composition of multiple features on synthesized media."""

    def test_filter_then_overlay(self, synth_landscape_hevc, synth_square_hevc, tmp_path):
        filtered = str(tmp_path / "filtered.mov")
        r1 = apply_filter(synth_landscape_hevc, "color_preset", {"preset": "warm"}, filtered)
        assert r1.success

        out = str(tmp_path / "filtered_pip.mov")
        r2 = overlay_video(
            r1.output_path,
            synth_square_hevc,
            position="bottom-right",
            width=320,
            output_path=out,
        )
        assert r2.success
        info = probe(r2.output_path)
        assert info.width == probe(synth_landscape_hevc).width

    def test_filter_chain_then_normalize(self, synth_timeline_mp4, tmp_path):
        step1 = str(tmp_path / "cinematic.mp4")
        r1 = apply_filter(synth_timeline_mp4, "color_preset", {"preset": "cinematic"}, step1)
        assert r1.success

        step2 = str(tmp_path / "cinematic_sharp.mp4")
        r2 = apply_filter(r1.output_path, "sharpen", {"amount": 1.5}, step2)
        assert r2.success

        out = str(tmp_path / "final.mp4")
        r3 = normalize_audio(r2.output_path, target_lufs=-14.0, output_path=out)
        assert r3.success
        assert os.path.isfile(r3.output_path)
