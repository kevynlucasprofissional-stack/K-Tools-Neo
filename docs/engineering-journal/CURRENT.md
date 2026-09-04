# Engineering Journal: M5 Slice 15 (PDF Merge and Split Nodes V1)

- Implemented pdf.merge and pdf.split in ktools-media.
- Both use pypdf with module-level import for testability.
- pdf.split correctly adjusts parts count if fewer pages than parts requested.
- All 28 tests passing.

# M5 Status
All core legacy capabilities from K Tools Neo - Versão Estável 2.py have been migrated to node capabilities:
- Media: extract_audio, convert_audio, split_audio, join_audios, compress_video, join_videos
- Image: webp_to_png
- PDF: merge, split
- Filesystem: folder.scan_files (from M4)
- Core workflow engine, diagnostics, run journal (M1-M3)
- Node Packs (M4-M5 architecture)

The ROADMAP.md M5 milestone is now complete.

# Engineering Journal: M5 Extension (Legacy Utility Migration)

## Slice 1.1: Media Join Videos Node V1 (`JV.py`)
- Implemented `media.join_videos` in `ktools-media`.
- Fast stream-copy concat with fallback normalization to H.264/AAC.
- Atomic file replacement via `.tmp`.
- All behavior and engine tests passing (33/33 in ktools-media).
- ADR-038 accepted.

## Slice 1.2: Media Lossless ALAC Converter Node V1 (`wav_para_m4a_lossless_gui_v2.py`)
- Implemented `media.convert_lossless_alac` in `ktools-media`.
- Transcodes to ALAC in `.m4a` with decoded PCM SHA-256 bit-exact verification.
- Output metadata captures hash proof and `verified_bit_exact: true`.
- All behavior and engine tests passing (37/37 in ktools-media).
- ADR-039 accepted.

## Slice 1.3: Media Merge Audio Studio Node V1 (`Audio Merge Studio V2.py`)
- Implemented `media.merge_audio_studio` in `ktools-media`.
- Natural alphanumeric sorting, mixed audio/video source support, optional loudness normalization, SHA-256 integrity hash.
- All behavior and engine tests passing (42/42 in ktools-media).
- ADR-040 accepted.

## Slice 1.4: Media De-ess Audio Node V1 (`removedor_sibilancia_gui_v2.py`)
- Implemented `media.deess_audio` in `ktools-media`.
- Dynamic sibilance reduction and spectral noise reduction via FFmpeg filter chain.
- All behavior and engine tests passing (46/46 in ktools-media).
- ADR-041 accepted.

## Slice 1.5: Media Extract and Join by Subfolder Node V1 (`JA_de_Vários_videos.py` / `varredura subpastas`)
- Implemented `media.extract_and_join_by_subfolder` orchestrator in `ktools-media`.
- Scans directory tree, groups videos by subfolder, and creates one consolidated audio file per module.
- Returns `FILE_SET` of audios + `JSON` summary report.
- All behavior and engine tests passing (49/49 in ktools-media).
- ADR-042 accepted.

## Slice 2.1: Text tl;dv Extract Node V1 (`Extrator TLDV.py`)
- Implemented `text.tldv_extract` in `ktools-text`.
- Zero-dependency standard library HTML parser for `#transcript-container`.
- Exports Markdown, SRT captions, and structured JSON.
- All behavior and engine tests passing (32/32 in ktools-text).
- ADR-043 accepted.

## Slice 3.1: Filesystem Structure Report Node V1 (`EC.py`)
- Implemented `filesystem.structure_report` in `ktools-filesystem`.
- Generates CSV inventory, ASCII tree TXT, and JSON metrics payload.
- All behavior and engine tests passing (11/11 in ktools-filesystem).
- ADR-044 accepted.

## Slice 3.2: Filesystem Drive Streaming Scanner Node V1 (`K_Tools_Drive_Streaming_Scanner.py` v1.4)
- Implemented `filesystem.drive_stream_scan` in `ktools-filesystem`.
- Non-hydrating Win32 native scanning with SQLite checkpoints and CSV export.
- All behavior and engine tests passing (14/14 in ktools-filesystem).
- ADR-045 accepted.

## Milestone M6: Agent Capability Interface V1
- Implemented `CapabilityManifest` with `SideEffectClass` projections in `ktools_core.manifest`.
- Implemented `ExecutionReceipt` schema and `ArtifactRecord` in `ktools_core.receipt`.
- Implemented unified `CapabilityInvoker` in `ktools_core.invoker`.
- Implemented native Model Context Protocol (MCP) server in `ktools_core.mcp_server`.
- Extended CLI with `capabilities list`, `describe`, `invoke`, and `mcp` in `ktools_core.cli`.
- Authored agent skill playbook in `skills/ktools-capabilities/SKILL.md`.
- Conformance test suite (`test_capability_conformance.py`) proves parity between WorkflowEngine, Direct API, CLI, and MCP across all 34 capabilities.
- ADR-046 accepted.

## Milestone M7: System Capabilities, Events + Scoped Safety
- Created `packages/ktools-system` implementing least-privilege `CapabilityScope` and `PolicyAction` classification (`models.py`).
- Implemented core system capabilities:
  - `system.process_launch`: safe bounded subprocess execution with timeout, output capture, and scope checks.
  - `system.clipboard_read` and `system.clipboard_write`: cross-platform clipboard access.
  - `system.host_health`: CPU, memory, platform, and disk metrics inspection.
  - `system.notify`: user attention notification emission.
- Implemented `SystemEventStream` pub/sub and history event bus (`events.py`).
- Registered system node pack in `ktools_core.registry.load_all_installed_node_packs`.
- Conformance and safety tests pass (8/8 in ktools-system, 85/85 in ktools-core).
- Total capability catalog expanded from 34 to 39 nodes.
- ADR-047 accepted.

# Current
Milestones M6 and M7 are RESOLVED / PROMOTED.
Proceeding to Milestone M8: Cross-Platform Host Provider Architecture.

