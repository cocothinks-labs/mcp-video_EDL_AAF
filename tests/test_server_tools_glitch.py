"""Tests for mcp_video/server_tools_glitch.py — MCP tool layer for glitch effects."""

from __future__ import annotations

import os

import pytest

from mcp_video.server_tools_glitch import (
    glitch_cmyk_split,
    glitch_datamoshing,
    glitch_macroblocking,
    glitch_rgb_shift,
    glitch_scanline_jitter,
    glitch_screen_tearing,
    glitch_turbulent_displacement,
    glitch_vhs_tracking,
)


# ---------------------------------------------------------------------------
# glitch_rgb_shift
# ---------------------------------------------------------------------------


class TestGlitchRgbShiftTool:
    def test_rejects_missing_file(self):
        result = glitch_rgb_shift("/nonexistent/video.mp4")
        assert result["success"] is False
        assert "error" in result

    def test_rejects_negative_amount(self, sample_video):
        result = glitch_rgb_shift(sample_video, amount=-1.0)
        assert result["success"] is False
        assert "error" in result

    def test_rejects_noise_above_one(self, sample_video):
        result = glitch_rgb_shift(sample_video, noise=1.5)
        assert result["success"] is False

    def test_rejects_noise_below_zero(self, sample_video):
        result = glitch_rgb_shift(sample_video, noise=-0.1)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "rgb_shift.mp4")
        result = glitch_rgb_shift(sample_video, output_path=out, amount=5.0, angle=0.0, noise=0.0)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "rgb_shift_rich.mp4")
        result = glitch_rgb_shift(sample_video, output_path=out, amount=5.0)
        assert result["success"] is True
        assert "duration" in result
        assert "resolution" in result
        assert "size_mb" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0

    @pytest.mark.slow
    def test_auto_output_path(self, sample_video):
        result = glitch_rgb_shift(sample_video, amount=3.0)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])


# ---------------------------------------------------------------------------
# glitch_scanline_jitter
# ---------------------------------------------------------------------------


class TestGlitchScanlineJitterTool:
    def test_rejects_missing_file(self):
        result = glitch_scanline_jitter("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_negative_jitter_amount(self, sample_video):
        result = glitch_scanline_jitter(sample_video, jitter_amount=-5.0)
        assert result["success"] is False

    def test_rejects_frequency_above_one(self, sample_video):
        result = glitch_scanline_jitter(sample_video, frequency=1.5)
        assert result["success"] is False

    def test_rejects_frequency_below_zero(self, sample_video):
        result = glitch_scanline_jitter(sample_video, frequency=-0.1)
        assert result["success"] is False

    def test_rejects_row_height_zero(self, sample_video):
        result = glitch_scanline_jitter(sample_video, row_height=0)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "scanline.mp4")
        result = glitch_scanline_jitter(sample_video, output_path=out, jitter_amount=10.0, frequency=0.2)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "scanline_rich.mp4")
        result = glitch_scanline_jitter(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_screen_tearing
# ---------------------------------------------------------------------------


class TestGlitchScreenTearingTool:
    def test_rejects_missing_file(self):
        result = glitch_screen_tearing("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_tear_count_zero(self, sample_video):
        result = glitch_screen_tearing(sample_video, tear_count=0)
        assert result["success"] is False

    def test_rejects_negative_offset_range(self, sample_video):
        result = glitch_screen_tearing(sample_video, offset_range=-10.0)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "tearing.mp4")
        result = glitch_screen_tearing(sample_video, output_path=out, tear_count=2, offset_range=30.0)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "tearing_rich.mp4")
        result = glitch_screen_tearing(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_vhs_tracking
# ---------------------------------------------------------------------------


class TestGlitchVhsTrackingTool:
    def test_rejects_missing_file(self):
        result = glitch_vhs_tracking("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_tracking_above_one(self, sample_video):
        result = glitch_vhs_tracking(sample_video, tracking=1.5)
        assert result["success"] is False

    def test_rejects_tracking_below_zero(self, sample_video):
        result = glitch_vhs_tracking(sample_video, tracking=-0.1)
        assert result["success"] is False

    def test_rejects_noise_amount_above_one(self, sample_video):
        result = glitch_vhs_tracking(sample_video, noise_amount=1.1)
        assert result["success"] is False

    def test_rejects_noise_amount_below_zero(self, sample_video):
        result = glitch_vhs_tracking(sample_video, noise_amount=-0.5)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "vhs.mp4")
        result = glitch_vhs_tracking(sample_video, output_path=out, tracking=0.3, noise_amount=0.01)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "vhs_rich.mp4")
        result = glitch_vhs_tracking(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_macroblocking
# ---------------------------------------------------------------------------


class TestGlitchMacroblockingTool:
    def test_rejects_missing_file(self):
        result = glitch_macroblocking("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_block_size_one(self, sample_video):
        result = glitch_macroblocking(sample_video, block_size=1)
        assert result["success"] is False

    def test_rejects_intensity_above_one(self, sample_video):
        result = glitch_macroblocking(sample_video, intensity=1.5)
        assert result["success"] is False

    def test_rejects_intensity_below_zero(self, sample_video):
        result = glitch_macroblocking(sample_video, intensity=-0.1)
        assert result["success"] is False

    def test_rejects_color_reduction_above_one(self, sample_video):
        result = glitch_macroblocking(sample_video, color_reduction=1.5)
        assert result["success"] is False

    def test_rejects_color_reduction_below_zero(self, sample_video):
        result = glitch_macroblocking(sample_video, color_reduction=-0.1)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "macro.mp4")
        result = glitch_macroblocking(sample_video, output_path=out, block_size=8)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "macro_rich.mp4")
        result = glitch_macroblocking(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "resolution" in result
        assert "size_mb" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_datamoshing
# ---------------------------------------------------------------------------


class TestGlitchDatamoshingTool:
    def test_rejects_missing_file(self):
        result = glitch_datamoshing("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_negative_drift(self, sample_video):
        result = glitch_datamoshing(sample_video, drift=-5.0)
        assert result["success"] is False

    def test_rejects_iframe_interval_zero(self, sample_video):
        result = glitch_datamoshing(sample_video, iframe_interval=0)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "datamosh.mp4")
        result = glitch_datamoshing(sample_video, output_path=out, drift=10.0, iframe_interval=15)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "datamosh_rich.mp4")
        result = glitch_datamoshing(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_cmyk_split
# ---------------------------------------------------------------------------


class TestGlitchCmykSplitTool:
    def test_rejects_missing_file(self):
        result = glitch_cmyk_split("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_negative_amount(self, sample_video):
        result = glitch_cmyk_split(sample_video, amount=-1.0)
        assert result["success"] is False

    def test_rejects_noise_above_one(self, sample_video):
        result = glitch_cmyk_split(sample_video, noise=1.5)
        assert result["success"] is False

    def test_rejects_noise_below_zero(self, sample_video):
        result = glitch_cmyk_split(sample_video, noise=-0.1)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "cmyk.mp4")
        result = glitch_cmyk_split(sample_video, output_path=out, amount=4.0)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "cmyk_rich.mp4")
        result = glitch_cmyk_split(sample_video, output_path=out)
        assert result["success"] is True
        assert "duration" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0


# ---------------------------------------------------------------------------
# glitch_turbulent_displacement
# ---------------------------------------------------------------------------


class TestGlitchTurbulentDisplacementTool:
    def test_rejects_missing_file(self):
        result = glitch_turbulent_displacement("/nonexistent/video.mp4")
        assert result["success"] is False

    def test_rejects_negative_amount(self, sample_video):
        result = glitch_turbulent_displacement(sample_video, amount=-1.0)
        assert result["success"] is False

    def test_rejects_octaves_zero(self, sample_video):
        result = glitch_turbulent_displacement(sample_video, octaves=0)
        assert result["success"] is False

    def test_rejects_octaves_above_five(self, sample_video):
        result = glitch_turbulent_displacement(sample_video, octaves=6)
        assert result["success"] is False

    @pytest.mark.slow
    def test_success(self, sample_video, tmp_path):
        out = str(tmp_path / "turbulent.mp4")
        result = glitch_turbulent_displacement(sample_video, output_path=out, amount=10.0, octaves=2)
        assert result["success"] is True
        assert os.path.isfile(result["output_path"])

    @pytest.mark.slow
    def test_rich_metadata_fields(self, sample_video, tmp_path):
        out = str(tmp_path / "turbulent_rich.mp4")
        result = glitch_turbulent_displacement(sample_video, output_path=out, octaves=1)
        assert result["success"] is True
        assert "duration" in result
        assert "resolution" in result
        assert "size_mb" in result
        assert "elapsed_ms" in result
        assert result["elapsed_ms"] is not None
        assert result["elapsed_ms"] > 0
