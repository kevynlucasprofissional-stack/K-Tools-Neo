# Discovery: Media Extract and Join by Subfolder Node V1

## Context and Problem
The workspace contains `Extrair e unir audios - varredura subpastas.py` and `JA_de_Vários_videos.py`. These scripts automate batch video course ingestion: given a folder tree containing multiple course modules/subfolders, each with several video lectures, the tool:
1. Groups video files by their parent subfolder.
2. Extracts and concatenates the audio of each subfolder into one consolidated audio track per module.
3. Produces a summary report of all generated tracks and counts.

While individual atomic nodes (`extract_audio`, `join_audios`) exist, users frequently require this high-level batch workflow executed automatically across entire directory trees without manually assembling complex sub-graphs.

## Candidate Node Definition
- Node Type: `media.extract_and_join_by_subfolder`
- Inputs: `folder: FOLDER` (or `files: FILE_SET`)
- Outputs:
  - `audios: PortDefinition(DataType.FILE_SET)`
  - `report: PortDefinition(DataType.JSON)`
- Config:
  - `format` (str, default "m4a")
  - `bitrate` (str, default "192k")
  - `output_dir` (optional str)

## Technical Architecture
- Module: `packages/ktools-media/src/ktools_media/orchestrators/subfolder_audio.py`
- Functions:
  - `extract_and_join_by_subfolder(root_dir: Path, output_dir: Optional[Path], ...) -> tuple[list[Path], dict[str, Any]]`
- Atomic writes per folder, isolated temporary workspace.
- M3 compliant subprocess monitoring.
