from __future__ import annotations

import csv
import ctypes
import os
import sqlite3
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

# Windows attributes
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
FILE_ATTRIBUTE_OFFLINE = 0x00001000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


if sys.platform == "win32":
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class WIN32_FIND_DATAW(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", FILETIME),
            ("ftLastAccessTime", FILETIME),
            ("ftLastWriteTime", FILETIME),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("dwReserved0", wintypes.DWORD),
            ("dwReserved1", wintypes.DWORD),
            ("cFileName", wintypes.WCHAR * 260),
            ("cAlternateFileName", wintypes.WCHAR * 14),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    _FindFirstFileExW = _kernel32.FindFirstFileExW
    _FindFirstFileExW.argtypes = [
        wintypes.LPCWSTR,
        ctypes.c_int,
        ctypes.POINTER(WIN32_FIND_DATAW),
        ctypes.c_int,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    _FindFirstFileExW.restype = wintypes.HANDLE

    _FindNextFileW = _kernel32.FindNextFileW
    _FindNextFileW.argtypes = [wintypes.HANDLE, ctypes.POINTER(WIN32_FIND_DATAW)]
    _FindNextFileW.restype = wintypes.BOOL

    _FindClose = _kernel32.FindClose
    _FindClose.argtypes = [wintypes.HANDLE]
    _FindClose.restype = wintypes.BOOL

    FIND_EX_INFO_BASIC = 1
    FIND_EX_SEARCH_NAME_MATCH = 0
    FIND_FIRST_EX_LARGE_FETCH = 0x00000002


@dataclass(frozen=True)
class ScannedItem:
    name: str
    is_dir: bool
    size: int
    is_hidden: bool
    is_offline: bool


def _iter_dir_native(dir_path: Path) -> Iterator[ScannedItem]:
    if sys.platform == "win32":
        search_path = str(dir_path.resolve())
        if not search_path.startswith("\\\\?\\") and len(search_path) > 240:
            search_path = "\\\\?\\" + search_path
        search_pattern = os.path.join(search_path, "*")

        data = WIN32_FIND_DATAW()
        handle = _FindFirstFileExW(
            search_pattern,
            FIND_EX_INFO_BASIC,
            ctypes.byref(data),
            FIND_EX_SEARCH_NAME_MATCH,
            None,
            FIND_FIRST_EX_LARGE_FETCH,
        )
        if handle == INVALID_HANDLE_VALUE or handle == 0:
            return

        try:
            while True:
                name = data.cFileName
                if name not in (".", ".."):
                    attrs = data.dwFileAttributes
                    is_dir = bool(attrs & FILE_ATTRIBUTE_DIRECTORY)
                    is_hidden = bool(attrs & FILE_ATTRIBUTE_HIDDEN) or name.startswith(".")
                    is_offline = bool(
                        attrs
                        & (
                            FILE_ATTRIBUTE_OFFLINE
                            | FILE_ATTRIBUTE_RECALL_ON_OPEN
                            | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
                        )
                    )
                    size = (data.nFileSizeHigh << 32) | data.nFileSizeLow if not is_dir else 0
                    yield ScannedItem(
                        name=name,
                        is_dir=is_dir,
                        size=size,
                        is_hidden=is_hidden,
                        is_offline=is_offline,
                    )
                if not _FindNextFileW(handle, ctypes.byref(data)):
                    break
        finally:
            _FindClose(handle)
    else:
        try:
            with os.scandir(dir_path) as it:
                for entry in it:
                    is_dir = entry.is_dir(follow_symlinks=False)
                    stat_res = entry.stat(follow_symlinks=False) if not is_dir else None
                    size = stat_res.st_size if stat_res else 0
                    is_hidden = entry.name.startswith(".")
                    yield ScannedItem(
                        name=entry.name,
                        is_dir=is_dir,
                        size=size,
                        is_hidden=is_hidden,
                        is_offline=False,
                    )
        except OSError:
            return


def _init_checkpoint_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS directories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            parent_path TEXT,
            status TEXT DEFAULT 'pending'
        );
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            dir_path TEXT,
            name TEXT,
            size INTEGER,
            is_offline INTEGER
        );
        CREATE TABLE IF NOT EXISTS errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            error_message TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_files_dir ON files (dir_path);
        CREATE INDEX IF NOT EXISTS idx_dirs_status ON directories (status);
    """)
    conn.commit()


def stream_scan_directory(
    root_dir: Path,
    output_dir: Path,
    base_name: str = "drive_scan",
    include_files: bool = True,
    include_hidden: bool = False,
    verify_stability: bool = False,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Performs resilient non-hydrating scanning tailored for cloud filesystems (Google Drive, OneDrive).
    Persists progress in a checkpoint SQLite database and exports an inventory CSV.
    """
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    db_path = out_dir / f"{base_name}.sqlite3"
    csv_path = out_dir / f"{base_name}.csv"

    conn = sqlite3.connect(db_path)
    _init_checkpoint_db(conn)

    # Seed root
    root_str = str(root.resolve())
    with conn:
        conn.execute(
            "INSERT OR IGNORE INTO directories (path, parent_path, status) VALUES (?, NULL, 'pending')",
            (root_str,),
        )

    total_files = 0
    total_dirs = 0
    total_offline = 0
    total_bytes = 0

    cur = conn.cursor()
    while True:
        cur.execute("SELECT id, path FROM directories WHERE status = 'pending' LIMIT 50")
        batch = cur.fetchall()
        if not batch:
            break

        for dir_id, dir_path_str in batch:
            dir_p = Path(dir_path_str)
            try:
                subdirs = []
                file_rows = []
                for item in _iter_dir_native(dir_p):
                    if item.is_hidden and not include_hidden:
                        continue

                    item_path = dir_p / item.name
                    if item_path.resolve() in (db_path.resolve(), csv_path.resolve()):
                        continue
                    if item.name.endswith(".tmp") or item.name.endswith("-journal"):
                        continue

                    item_path_str = str(item_path.resolve())
                    if item.is_dir:
                        subdirs.append((item_path_str, dir_path_str))
                    elif include_files:
                        file_rows.append((
                            item_path_str,
                            dir_path_str,
                            item.name,
                            item.size,
                            1 if item.is_offline else 0,
                        ))
                        total_files += 1
                        total_bytes += item.size
                        if item.is_offline:
                            total_offline += 1

                with conn:
                    if subdirs:
                        conn.executemany(
                            "INSERT OR IGNORE INTO directories (path, parent_path, status) VALUES (?, ?, 'pending')",
                            subdirs,
                        )
                        total_dirs += len(subdirs)
                    if file_rows:
                        conn.executemany(
                            "INSERT OR IGNORE INTO files (path, dir_path, name, size, is_offline) VALUES (?, ?, ?, ?, ?)",
                            file_rows,
                        )
                    conn.execute(
                        "UPDATE directories SET status = 'completed' WHERE id = ?",
                        (dir_id,),
                    )
            except Exception as e:
                with conn:
                    conn.execute(
                        "INSERT INTO errors (path, error_message) VALUES (?, ?)",
                        (dir_path_str, str(e)),
                    )
                    conn.execute(
                        "UPDATE directories SET status = 'error' WHERE id = ?",
                        (dir_id,),
                    )

    # Export CSV
    tmp_csv = csv_path.with_name(f"{csv_path.name}.{uuid4().hex}.tmp")
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f_csv:
        csv_w = csv.writer(f_csv)
        csv_w.writerow(["type", "path", "name", "size_bytes", "is_offline"])

        cur.execute("SELECT path, 'directory', '', 0, 0 FROM directories WHERE status = 'completed'")
        for r in cur.fetchall():
            csv_w.writerow([r[1], r[0], r[2], r[3], r[4]])

        cur.execute("SELECT path, 'file', name, size, is_offline FROM files")
        for r in cur.fetchall():
            csv_w.writerow([r[1], r[0], r[2], r[3], r[4]])

    conn.close()

    try:
        os.replace(tmp_csv, csv_path)
    finally:
        if tmp_csv.exists():
            try:
                tmp_csv.unlink()
            except OSError:
                pass

    report: dict[str, Any] = {
        "root_directory": root_str,
        "total_directories": total_dirs,
        "total_files": total_files,
        "total_offline_files": total_offline,
        "total_bytes": total_bytes,
        "database_checkpoint": str(db_path),
    }

    return db_path, csv_path, report
