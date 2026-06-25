# mcp-video_EDL_AAF

> **Fork of [mcp-video](https://github.com/KyaniteLabs/mcp-video) by KyaniteLabs** — adds CMX3600 EDL and After Effects JSX export so AI-assembled edits land directly in Premiere Pro or After Effects for professional retouching.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

## What this fork adds

The original mcp-video gives AI agents a full video editing surface (119 tools, FFmpeg-powered). What it lacks is a **handoff to professional NLEs**: once the AI assembles a cut, there is no standard way to bring that edit into Premiere Pro or After Effects for retouching.

This fork adds that bridge via two industry-standard formats:

| Format | Used by | Import path |
|--------|---------|-------------|
| **CMX3600 EDL** | Premiere Pro, Avid, DaVinci Resolve | `File > Import` |
| **ExtendScript JSX** | After Effects | `File > Scripts > Run Script File` |

### New MCP tools (5)

| Tool | Output | Description |
|------|--------|-------------|
| `video_export_edl` | `.edl` | Export CMX3600 EDL from a clip list |
| `video_export_edl_from_timeline` | `.edl` | Export CMX3600 EDL from a mcp-video Timeline JSON |
| `video_export_aescript` | `.jsx` | Export After Effects script from a clip list |
| `video_export_aescript_from_timeline` | `.jsx` | Export After Effects script from a Timeline JSON |
| `video_export_edit_package` | `.edl` + `.jsx` | Export both formats in one call |

---

## Installation

```bash
git clone https://github.com/cocothinks-labs/mcp-video_EDL_AAF.git
cd mcp-video_EDL_AAF
pip install -e ".[all]"
```

### Configure in Claude Code

Add to your `.claude/settings.json` under `mcpServers`:

```json
"mcp-video-edl": {
  "command": "python",
  "args": ["-m", "mcp_video", "--mcp"],
  "cwd": "/path/to/mcp-video_EDL_AAF",
  "env": {
    "MCP_VIDEO_OUTPUT_BASE": "/path/to/your/projects/folder"
  }
}
```

`MCP_VIDEO_OUTPUT_BASE` sets the default root for output files. When set, `video_export_edit_package` only needs a project `title` — it creates `{base}/{title}/` automatically.

---

## Usage

### Export both EDL and JSX in one call

```python
# Claude calls this tool with your clip decisions
video_export_edit_package(
    clips=[
        {"source": "/media/interview.mp4", "src_in": 10.0, "src_out": 45.5},
        {"source": "/media/broll.mp4",     "src_in":  0.0, "src_out": 12.0},
        {"source": "/media/interview.mp4", "src_in": 60.0, "src_out": 90.0},
    ],
    title="ClientProject_v1",
    fps=25.0,
)
# → saves ClientProject_v1.edl and ClientProject_v1.jsx
#   to {MCP_VIDEO_OUTPUT_BASE}/ClientProject_v1/
```

### Import into Premiere Pro

```
File > Import → select ClientProject_v1.edl
```

Premiere reconstructs the sequence with source clips linked by path.

### Import into After Effects

```
File > Scripts > Run Script File → select ClientProject_v1.jsx
```

A new composition is created with all clips trimmed and placed at the correct timecodes.

### Export from a Timeline JSON

If you already have a mcp-video Timeline (used by `video_edit`), export both formats without re-specifying clips:

```python
video_export_edl_from_timeline(timeline=my_timeline_json, output_path="/output/edit.edl")
video_export_aescript_from_timeline(timeline=my_timeline_json, output_path="/output/edit.jsx")
```

---

## Workflow

```
Claude assembles rough cut (mcp-video tools)
        │
        ▼
video_export_edit_package(clips, title="ProjectName")
        │
        ├── ProjectName.edl ──► Premiere Pro  ──► retouch, color, audio
        │
        └── ProjectName.jsx ──► After Effects ──► motion, compositing
```

---

## Project structure

```
mcp_video/
├── engine_edl.py          # CMX3600 EDL generation
├── engine_aescript.py     # After Effects JSX generation
├── server_tools_edl.py    # MCP tool registrations (5 tools)
└── server.py              # updated imports

docs/
└── mcp-video_EDL_AAF_overview.pdf   # Bilingual overview (EN + ES)
```

---

## Attribution & License

This project is a fork of **[mcp-video](https://github.com/KyaniteLabs/mcp-video)** by [KyaniteLabs](https://github.com/KyaniteLabs), released under the [Apache 2.0 License](LICENSE).

All original code, tools, and copyright notices are preserved. The additions in this fork (`engine_edl.py`, `engine_aescript.py`, `server_tools_edl.py`) are authored by **[cocothinks-labs](https://github.com/cocothinks-labs)** and are also released under Apache 2.0.

Apache 2.0 summary: free to use, modify, and redistribute — commercially or not — as long as you keep the original copyright notices and indicate what you changed.

---

## Maintained by

**cocothinks-labs** · [cocothinks.com](https://cocothinks.com)

Senior motion, VFX & AI production professional. Open source tools where broadcast craft meets generative AI.
