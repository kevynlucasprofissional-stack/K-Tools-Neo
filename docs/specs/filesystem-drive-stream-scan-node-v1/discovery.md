# Discovery: Filesystem Drive Streaming Scanner Node V1

## Context and Problem
The workspace contains `K_Tools_Drive_Streaming_Scanner.py` (v1.4), a high-resilience streaming scanner built specifically for Google Drive for Desktop (and OneDrive) in "Stream files" mode on Windows.

Standard directory traversal tools (`os.walk`, `Path.stat()`, `Path.resolve()`) trigger cloud hydration, causing gigabytes or terabytes of remote files to download locally, filling the user's hard drive and stalling the machine.
Furthermore, streaming cloud filesystems frequently exhibit temporary I/O instability and sync latency.

## Key Capabilities Migrated
1. Non-hydrating enumeration:
   - On Windows: Uses native `FindFirstFileExW` / `FindNextFileW` via `ctypes` with `FindExInfoBasic` and `FIND_FIRST_EX_LARGE_FETCH`.
   - Checks `FILE_ATTRIBUTE_RECALL_ON_OPEN`, `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`, `FILE_ATTRIBUTE_OFFLINE` without touching file payloads.
   - Cross-platform fallback: Clean `os.scandir` on Linux/macOS.
2. Resilient SQLite Checkpoint Database:
   - Records visited directories, files, sizes, attributes, and errors in SQLite tables (`directories`, `files`, `errors`, `meta`).
   - Allows resuming interrupted multi-hour scans seamlessly.
3. Export Artifacts:
   - SQLite database artifact (`.sqlite3`).
   - Full CSV export artifact.
   - JSON report with counts of local vs offline/virtual files.

## Candidate Node Definition
- Node Type: `filesystem.drive_stream_scan`
- Inputs: `folder: PortDefinition(DataType.FOLDER)`
- Outputs:
  - `database: PortDefinition(DataType.FILE)`
  - `csv: PortDefinition(DataType.FILE)`
  - `report: PortDefinition(DataType.JSON)`
- Config:
  - `include_files` (bool, default True)
  - `include_hidden` (bool, default False)
  - `verify_stability` (bool, default False)
  - `output_dir` (optional str)
  - `base_name` (optional str, default "drive_scan")
