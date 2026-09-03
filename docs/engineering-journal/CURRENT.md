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

# Current
Proceeding to Slice 1.2: Media Lossless ALAC Converter Node V1 (`wav_para_m4a_lossless_gui_v2.py`).
