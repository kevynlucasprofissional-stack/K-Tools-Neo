# Engineering Journal: M5 Slice 15 (PDF Merge and Split Nodes V1)

- Implemented pdf.merge and pdf.split in ktools-media.
- Both use pypdf with module-level import for testability.
- pdf.split correctly adjusts parts count if fewer pages than parts requested.
- All 28 tests passing.

# M5 Status
All core legacy capabilities from K Tools Neo - Versão Estável 2.py have been migrated to node capabilities:
- Media: extract_audio, convert_audio, split_audio, join_audios, compress_video
- Image: webp_to_png
- PDF: merge, split
- Filesystem: folder.scan_files (from M4)
- Core workflow engine, diagnostics, run journal (M1-M3)
- Node Packs (M4-M5 architecture)

The ROADMAP.md M5 milestone is now complete.
