# M5 Extension: Media Extract and Join by Subfolder Node V1

## What was done
- Implemented `media.extract_and_join_by_subfolder` orchestrator migrating `Extrair e unir audios - varredura subpastas.py` and `JA_de_Vários_videos.py`.
- Automated recursive video discovery, per-folder grouping, and audio extraction/merging.
- Returns `FILE_SET` of audio tracks alongside a structured JSON execution report.
- Unit behavior tests and engine integration tests passing.
- Total 49/49 tests passing in `ktools-media`.
