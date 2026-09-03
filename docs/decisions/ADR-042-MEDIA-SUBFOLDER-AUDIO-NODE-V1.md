# ADR 042: Media Extract and Join by Subfolder Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The workspace contains `Extrair e unir audios - varredura subpastas.py` and `JA_de_Vários_videos.py`. In video course ingestion, lectures are organized into modular directories. Manually wiring separate extraction and concatenation nodes for dozens of subfolders is tedious and error-prone. A batch orchestrator node solves this naturally.

## Decision
- Implement `media.extract_and_join_by_subfolder` node in `ktools-media`.
- Takes a `FOLDER` artifact, scans recursively for supported video files, and groups them by parent folder.
- For each subfolder with videos:
  - Sorts videos naturally with `natural_sort_key`.
  - Extracts and concatenates the audio into a single output audio track (m4a, mp3, etc.).
  - Writes atomically via `.tmp`.
- Outputs:
  - `audios`: `FILE_SET` of all generated audio artifacts.
  - `report`: `JSON` summary detailing processed folders, video counts, and paths.

## Consequences
- Complex multi-folder video-to-audio extraction pipelines can now execute in a single workflow step.
