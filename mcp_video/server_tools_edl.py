"""MCP tool registrations for EDL export (cocothinks-labs addition)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field

from .engine_edl import EDLClip, export_edl_from_clips, export_edl_from_timeline
from .server_app import _result, _safe_tool, mcp


@mcp.tool()
@_safe_tool
def video_export_edl(
    clips: Annotated[
        list[dict],
        Field(
            description=(
                "List of edit decisions. Each dict must have: "
                "'source' (absolute path to the clip), "
                "'src_in' (start time in seconds in the source file), "
                "'src_out' (end time in seconds in the source file). "
                "Clips are assembled in order on the record timeline."
            )
        ),
    ],
    output_path: Annotated[
        str,
        Field(description="Absolute path for the output .edl file (CMX3600 format, importable by Premiere Pro via File > Import)."),
    ],
    title: Annotated[
        str,
        Field(description="Title embedded in the EDL header. Appears in Premiere Pro's sequence name on import."),
    ] = "mcp-video export",
    fps: Annotated[
        float,
        Field(description="Frame rate of the footage (e.g. 25.0, 29.97, 24.0). Must match the source footage.", gt=0),
    ] = 25.0,
) -> dict:
    """Export an Edit Decision List (EDL / CMX3600) from a list of clip in/out decisions.

    The resulting .edl file can be imported directly into Adobe Premiere Pro
    (File > Import) to reconstruct the edit on a timeline for retouching.

    Each clip entry requires:
    - source: absolute path to the video file on disk
    - src_in: start time in seconds within that file
    - src_out: end time in seconds within that file

    Example clips list:
        [
          {"source": "/videos/interview.mp4", "src_in": 10.0, "src_out": 45.0},
          {"source": "/videos/broll.mp4",     "src_in":  0.0, "src_out": 12.5}
        ]
    """
    edl_clips = [
        EDLClip(
            source_path=c["source"],
            src_in=float(c["src_in"]),
            src_out=float(c["src_out"]),
        )
        for c in clips
    ]
    result = export_edl_from_clips(edl_clips, output_path, title=title, fps=fps)
    return _result(
        {
            "output_path": result.output_path,
            "event_count": result.event_count,
            "title": result.title,
            "fps": result.fps,
            "import_instructions": (
                "Open Premiere Pro → File > Import → select this .edl file. "
                "Make sure the media paths on disk match those recorded in the EDL."
            ),
        }
    )


@mcp.tool()
@_safe_tool
def video_export_edl_from_timeline(
    timeline: Annotated[
        dict,
        Field(
            description=(
                "A mcp-video Timeline JSON object — the same structure accepted by video_edit. "
                "Only video tracks are exported; audio tracks are ignored."
            )
        ),
    ],
    output_path: Annotated[
        str,
        Field(description="Absolute path for the output .edl file (CMX3600 format)."),
    ],
    title: Annotated[
        str,
        Field(description="Title embedded in the EDL header."),
    ] = "mcp-video export",
    fps: Annotated[
        float | None,
        Field(description="Override frame rate. If omitted, detected automatically from the first clip."),
    ] = None,
) -> dict:
    """Export a CMX3600 EDL directly from a mcp-video Timeline JSON.

    Useful when you've already defined your edit as a Timeline (for video_edit)
    and want to also get an EDL for importing into Premiere Pro without
    re-specifying every clip manually.

    Premiere Pro import: File > Import → select the .edl file.
    """
    result = export_edl_from_timeline(timeline, output_path, title=title, fps=fps)
    return _result(
        {
            "output_path": result.output_path,
            "event_count": result.event_count,
            "title": result.title,
            "fps": result.fps,
            "import_instructions": (
                "Open Premiere Pro → File > Import → select this .edl file. "
                "Make sure the media paths on disk match those recorded in the EDL."
            ),
        }
    )
