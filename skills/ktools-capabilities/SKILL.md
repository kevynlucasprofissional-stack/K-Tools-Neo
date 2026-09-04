---
name: ktools-capabilities
description: Discover and invoke deterministic host capabilities (media processing, audio merge/convert, document split, filesystem report, drive streaming scanner) using K-Tools Neo.
---

# K-Tools Neo Agent Capabilities Skill

Use this skill when you need to safely and deterministically perform media transformation, filesystem inspection, or document operations on the host.

## Overview
K-Tools Neo exposes 34+ typed capability units. Each capability execution generates an `ExecutionReceipt` carrying status, artifacts, and diagnostic session identifiers.

## Discovery
To inspect available capabilities and their input schemas:
```bash
python -m ktools_core.cli capabilities list --json
```

To view the exact parameter requirements of a specific capability:
```bash
python -m ktools_core.cli capabilities describe <capability_id>
```

Example:
```bash
python -m ktools_core.cli capabilities describe media.convert_lossless_alac
```

## Direct Invocation via CLI
Execute a single capability directly:
```bash
python -m ktools_core.cli capabilities invoke <capability_id> --input <key>=<value>
```

Or pass JSON inputs:
```bash
python -m ktools_core.cli capabilities invoke <capability_id> --input-json '{"key": "value"}'
```

The command outputs a structured `ExecutionReceipt`:
```json
{
  "capability_id": "media.convert_lossless_alac",
  "status": "SUCCESS",
  "receipt_id": "rcpt_...",
  "duration_seconds": 1.24,
  "outputs": {
    "output_file": "C:/path/output.m4a"
  },
  "artifacts": [
    {
      "artifact_id": "...",
      "uri": "file:///C:/path/output.m4a",
      "sha256": "..."
    }
  ]
}
```

## MCP (Model Context Protocol) Integration
For MCP clients (e.g. Claude Desktop, Hermes Workstation), K-Tools Neo provides an MCP JSON-RPC server over stdio:
```bash
python -m ktools_core.cli mcp
```
All capability IDs are exposed as tools with underscore naming (e.g. `media_convert_lossless_alac`, `filesystem_drive_stream_scan`).

## Common Capabilities Reference
| Capability ID | Category | Description |
| :--- | :--- | :--- |
| `media.extract_audio` | Media | Extracts audio track from video file into WAV. |
| `media.convert_lossless_alac` | Media | Bit-exact conversion from WAV to Apple Lossless M4A with SHA-256 PCM verification. |
| `media.merge_audio_studio` | Media | Natural-sort multi-track audio joiner with loudness normalization. |
| `media.deess_audio` | Media | Vocal sibilance attenuator using FFmpeg DSP filters. |
| `filesystem.structure_report` | Filesystem | Generates directory inventory CSV and ASCII tree report. |
| `filesystem.drive_stream_scan` | Filesystem | Non-hydrating scanner for cloud drives (Google Drive / OneDrive) with SQLite checkpoints. |
| `text.tldv_extract` | Text | Extracts tl;dv meeting HTML into Markdown, SRT subtitles, and JSON. |
