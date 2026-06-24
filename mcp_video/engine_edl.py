"""EDL (Edit Decision List) export engine — generates CMX3600 files for NLEs like Premiere Pro.

Added by cocothinks-labs: https://github.com/cocothinks-labs/mcp-video
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from .errors import MCPVideoError
from .models import Timeline, TimelineClip


@dataclass
class EDLClip:
    """One edit decision: a source clip trimmed to [src_in, src_out)."""
    source_path: str
    src_in: float   # seconds in source file
    src_out: float  # seconds in source file


@dataclass
class EDLResult:
    output_path: str
    event_count: int
    title: str
    fps: float


def _seconds_to_timecode(seconds: float, fps: float) -> str:
    """Convert seconds to HH:MM:SS:FF timecode string."""
    total_frames = round(seconds * fps)
    ifps = round(fps)
    ff = total_frames % ifps
    total_secs = total_frames // ifps
    ss = total_secs % 60
    mm = (total_secs // 60) % 60
    hh = total_secs // 3600
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


def _reel_name(index: int, source_path: str) -> str:
    """Return an 8-char reel identifier. CMX3600 limit is 8 chars."""
    stem = os.path.splitext(os.path.basename(source_path))[0]
    # Use stem truncated to 8 chars so Premiere shows a meaningful name
    return stem[:8].ljust(8)


def export_edl_from_clips(
    clips: list[EDLClip],
    output_path: str,
    title: str = "mcp-video export",
    fps: float = 25.0,
) -> EDLResult:
    """Write a CMX3600 EDL file from a list of EDLClip decisions.

    Premiere Pro imports CMX3600 via File > Import. Each clip becomes one
    V-track cut event. Audio is not included (A tracks require a separate pass).
    """
    if not clips:
        raise MCPVideoError(
            "No clips provided for EDL export",
            error_type="validation_error",
            code="empty_clip_list",
        )

    lines: list[str] = [
        f"TITLE: {title}",
        "FCM: NON-DROP FRAME",
        "",
    ]

    rec_pos = 0.0
    for idx, clip in enumerate(clips, start=1):
        duration = clip.src_out - clip.src_in
        if duration <= 0:
            raise MCPVideoError(
                f"Clip {idx} has zero or negative duration (src_in={clip.src_in}, src_out={clip.src_out})",
                error_type="validation_error",
                code="invalid_clip_duration",
            )

        src_in_tc  = _seconds_to_timecode(clip.src_in,  fps)
        src_out_tc = _seconds_to_timecode(clip.src_out, fps)
        rec_in_tc  = _seconds_to_timecode(rec_pos,            fps)
        rec_out_tc = _seconds_to_timecode(rec_pos + duration,  fps)
        reel       = _reel_name(idx, clip.source_path)
        clip_name  = os.path.basename(clip.source_path)

        lines.append(f"{idx:03d}  {reel} V     C        {src_in_tc} {src_out_tc} {rec_in_tc} {rec_out_tc}")
        lines.append(f"* FROM CLIP NAME: {clip_name}")
        lines.append(f"* SOURCE FILE: {clip.source_path}")
        lines.append("")

        rec_pos += duration

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("\n".join(lines))

    return EDLResult(
        output_path=output_path,
        event_count=len(clips),
        title=title,
        fps=fps,
    )


def export_edl_from_timeline(
    timeline: Timeline | dict,
    output_path: str,
    title: str = "mcp-video export",
    fps: float | None = None,
) -> EDLResult:
    """Convert a mcp-video Timeline JSON to a CMX3600 EDL.

    Reads the same Timeline structure accepted by video_edit / edit_timeline.
    Only video tracks are included; audio tracks are ignored (EDL audio
    requires separate A-track events, out of scope here).
    """
    if isinstance(timeline, dict):
        timeline = Timeline.model_validate(timeline)

    clips: list[EDLClip] = []
    detected_fps: float | None = None

    for track in timeline.tracks:
        if track.type != "video":
            continue
        for clip in track.clips:
            src_in = clip.trim_start or 0.0

            if clip.trim_end is not None:
                src_out = clip.trim_end
            elif clip.duration is not None:
                src_out = src_in + clip.duration
            else:
                # probe the file to get its full duration
                try:
                    from .engine_probe import probe
                    info = probe(clip.source)
                    src_out = float(info.duration)
                    if detected_fps is None and info.fps:
                        detected_fps = float(info.fps)
                except Exception:
                    raise MCPVideoError(
                        f"Cannot determine duration for clip '{clip.source}'. "
                        "Provide trim_end or duration in the timeline.",
                        error_type="validation_error",
                        code="missing_clip_duration",
                    )

            clips.append(EDLClip(source_path=clip.source, src_in=src_in, src_out=src_out))

    if not clips:
        raise MCPVideoError(
            "Timeline contains no video clips to export as EDL",
            error_type="validation_error",
            code="empty_timeline",
        )

    resolved_fps = fps or detected_fps or 25.0
    return export_edl_from_clips(clips, output_path, title=title, fps=resolved_fps)
