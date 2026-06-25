"""MCP tool registrations for EDL and After Effects script export (cocothinks-labs)."""

from __future__ import annotations

import os
from typing import Annotated

from pydantic import Field

from .engine_edl import EDLClip, export_edl_from_clips, export_edl_from_timeline
from .engine_aescript import export_aescript_from_clips, export_aescript_from_timeline
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


# ---------------------------------------------------------------------------
# After Effects JSX script export
# ---------------------------------------------------------------------------

@mcp.tool()
@_safe_tool
def video_export_aescript(
    clips: Annotated[
        list[dict],
        Field(
            description=(
                "List of edit decisions. Each dict must have: "
                "'source' (absolute path to the clip), "
                "'src_in' (start time in seconds), "
                "'src_out' (end time in seconds)."
            )
        ),
    ],
    output_path: Annotated[
        str,
        Field(description="Absolute path for the output .jsx file."),
    ],
    comp_name: Annotated[
        str,
        Field(description="Name for the new After Effects composition."),
    ] = "mcp-video export",
    fps: Annotated[
        float,
        Field(description="Frame rate of the composition (e.g. 25.0, 29.97, 24.0).", gt=0),
    ] = 25.0,
    width: Annotated[
        int,
        Field(description="Composition width in pixels.", gt=0),
    ] = 1920,
    height: Annotated[
        int,
        Field(description="Composition height in pixels.", gt=0),
    ] = 1080,
) -> dict:
    """Export an After Effects ExtendScript (.jsx) from a list of clip in/out decisions.

    Running the script in After Effects (File > Scripts > Run Script File) creates
    a new composition with every clip trimmed and placed at the correct timecode —
    equivalent to importing an EDL into Premiere, but directly in AE with no
    intermediary step.

    Example clips list:
        [
          {"source": "/videos/interview.mp4", "src_in": 10.0, "src_out": 45.0},
          {"source": "/videos/broll.mp4",     "src_in":  0.0, "src_out": 12.5}
        ]
    """
    edl_clips = [
        EDLClip(source_path=c["source"], src_in=float(c["src_in"]), src_out=float(c["src_out"]))
        for c in clips
    ]
    result = export_aescript_from_clips(
        edl_clips, output_path, comp_name=comp_name, fps=fps, width=width, height=height
    )
    return _result(
        {
            "output_path": result.output_path,
            "event_count": result.event_count,
            "comp_name": result.comp_name,
            "fps": result.fps,
            "width": result.width,
            "height": result.height,
            "run_instructions": (
                "In After Effects: File > Scripts > Run Script File → select this .jsx file. "
                "A new composition will be created with all clips placed and trimmed."
            ),
        }
    )


@mcp.tool()
@_safe_tool
def video_export_aescript_from_timeline(
    timeline: Annotated[
        dict,
        Field(description="A mcp-video Timeline JSON object (same structure as video_edit)."),
    ],
    output_path: Annotated[
        str,
        Field(description="Absolute path for the output .jsx file."),
    ],
    comp_name: Annotated[
        str,
        Field(description="Name for the new After Effects composition."),
    ] = "mcp-video export",
    fps: Annotated[
        float | None,
        Field(description="Override frame rate. Auto-detected from clips if omitted."),
    ] = None,
    width: Annotated[
        int | None,
        Field(description="Override composition width. Auto-detected if omitted."),
    ] = None,
    height: Annotated[
        int | None,
        Field(description="Override composition height. Auto-detected if omitted."),
    ] = None,
) -> dict:
    """Export an After Effects JSX script from a mcp-video Timeline JSON.

    After Effects import: File > Scripts > Run Script File → select the .jsx.
    """
    result = export_aescript_from_timeline(
        timeline, output_path, comp_name=comp_name, fps=fps, width=width, height=height
    )
    return _result(
        {
            "output_path": result.output_path,
            "event_count": result.event_count,
            "comp_name": result.comp_name,
            "fps": result.fps,
            "width": result.width,
            "height": result.height,
            "run_instructions": (
                "In After Effects: File > Scripts > Run Script File → select this .jsx file. "
                "A new composition will be created with all clips placed and trimmed."
            ),
        }
    )


def _default_output_base() -> str | None:
    """Return MCP_VIDEO_OUTPUT_BASE env var if set, else None."""
    return os.environ.get("MCP_VIDEO_OUTPUT_BASE")


@mcp.tool()
@_safe_tool
def video_export_edit_package(
    clips: Annotated[
        list[dict],
        Field(
            description=(
                "List of edit decisions: 'source' (path), 'src_in' (seconds), 'src_out' (seconds)."
            )
        ),
    ],
    title: Annotated[
        str,
        Field(description="Project title. Used as subfolder name and as EDL/AE composition name."),
    ] = "mcp-video export",
    output_dir: Annotated[
        str | None,
        Field(
            description=(
                "Override output directory. If omitted, files are saved to "
                "{MCP_VIDEO_OUTPUT_BASE}/{title}/. "
                "MCP_VIDEO_OUTPUT_BASE must be set as an environment variable when omitted."
            )
        ),
    ] = None,
    fps: Annotated[
        float,
        Field(description="Frame rate of the footage.", gt=0),
    ] = 25.0,
    width: Annotated[
        int,
        Field(description="Composition width in pixels (for the AE script).", gt=0),
    ] = 1920,
    height: Annotated[
        int,
        Field(description="Composition height in pixels (for the AE script).", gt=0),
    ] = 1080,
) -> dict:
    """Export both a CMX3600 EDL and an After Effects JSX script in one operation.

    Produces two files inside a project subfolder:
    - <title>.edl  → import into Premiere Pro via File > Import
    - <title>.jsx  → run in After Effects via File > Scripts > Run Script File

    Output location (in priority order):
    1. output_dir parameter (if provided)
    2. {MCP_VIDEO_OUTPUT_BASE}/{title}/ (if MCP_VIDEO_OUTPUT_BASE env var is set)

    Set MCP_VIDEO_OUTPUT_BASE to your default projects folder so you never have
    to type the full path — just provide the project title.
    """
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)

    if output_dir is None:
        base = _default_output_base()
        if not base:
            from .errors import MCPVideoError
            raise MCPVideoError(
                "output_dir not provided and MCP_VIDEO_OUTPUT_BASE env var is not set. "
                "Either pass output_dir or set MCP_VIDEO_OUTPUT_BASE to your default projects folder.",
                error_type="validation_error",
                code="missing_output_dir",
            )
        output_dir = os.path.join(base, safe_title)

    edl_path = os.path.join(output_dir, f"{safe_title}.edl")
    jsx_path = os.path.join(output_dir, f"{safe_title}.jsx")

    edl_clips = [
        EDLClip(source_path=c["source"], src_in=float(c["src_in"]), src_out=float(c["src_out"]))
        for c in clips
    ]

    edl_result = export_edl_from_clips(edl_clips, edl_path, title=title, fps=fps)
    jsx_result = export_aescript_from_clips(
        edl_clips, jsx_path, comp_name=title, fps=fps, width=width, height=height
    )

    return _result(
        {
            "edl_path": edl_result.output_path,
            "jsx_path": jsx_result.output_path,
            "event_count": edl_result.event_count,
            "title": title,
            "fps": fps,
            "premiere_instructions": "File > Import → select the .edl file.",
            "aftereffects_instructions": "File > Scripts > Run Script File → select the .jsx file.",
        }
    )
