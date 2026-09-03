# ADR 045: Filesystem Drive Streaming Scanner Node V1

## Date
2026-09-03

## Status
Accepted

## Context
The repository had `K_Tools_Drive_Streaming_Scanner.py` (v1.4) specifically designed to scan cloud streaming filesystems like Google Drive for Desktop and OneDrive without triggering file hydration (mass downloading remote files to disk) and without crashing when temporary cloud I/O latency occurs.

## Decision
- Implement `filesystem.drive_stream_scan` in `ktools-filesystem`.
- Non-hydrating Windows directory enumeration via Win32 `FindFirstFileExW` / `FindNextFileW` with `FIND_FIRST_EX_LARGE_FETCH` and `FIND_EX_INFO_BASIC`.
- Directly checks reparse points and offline flags (`FILE_ATTRIBUTE_OFFLINE`, `FILE_ATTRIBUTE_RECALL_ON_OPEN`, `FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`).
- Safe cross-platform fallback with `os.scandir` on Linux/macOS.
- Persistent checkpointing using SQLite database (`directories`, `files`, `errors`, `meta`).
- Emits three outputs:
  - `database`: SQLite `.sqlite3` checkpoint file.
  - `csv`: full inventory CSV.
  - `report`: JSON summary with total files, total directories, offline cloud counts, and database location.

## Consequences
- Workflows can safely inspect and index massive cloud drives without consuming local storage or network bandwidth.
