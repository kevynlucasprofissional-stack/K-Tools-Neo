from __future__ import annotations

"""
K-Tools Drive Streaming Scanner
===============================
Scanner de estrutura de pastas pensado para Google Drive for desktop em modo
"Stream files" no Windows.

Objetivo principal:
- reconstruir a árvore de diretórios com o mínimo possível de acesso ao conteúdo;
- evitar Path.resolve(), Path.stat() e abertura de arquivos durante a descoberta;
- usar enumeração nativa do Windows (FindFirstFileExW/FindNextFileW);
- repetir listagens para detectar instabilidade temporária;
- persistir progresso em SQLite para permitir retomada após interrupção;
- enumerar múltiplos diretórios em paralelo, mantendo a verificação individual de estabilidade;
- permitir nome-base personalizado para todos os arquivos de saída;
- registrar claramente diretórios não verificados/erros, sem fingir completude.

O script também possui fallback com os.scandir em outros sistemas para testes.
Nenhum pacote externo é necessário.
"""

import csv
import ctypes
import re
import json
import os
import sqlite3
import sys
import threading
import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Iterable, Optional

APP_TITLE = "K-Tools | Drive Streaming Scanner"
APP_VERSION = "1.1.0"
DEFAULT_OUTPUT_BASENAME = "estrutura_drive"

# Windows file attributes
FILE_ATTRIBUTE_HIDDEN = 0x00000002
FILE_ATTRIBUTE_DIRECTORY = 0x00000010
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
FILE_ATTRIBUTE_OFFLINE = 0x00001000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000

# Reparse tags that can create directory loops and are therefore not followed.
IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
IO_REPARSE_TAG_SYMLINK = 0xA000000C

ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_NO_MORE_FILES = 18
ERROR_INVALID_PARAMETER = 87


@dataclass
class ScanOptions:
    include_hidden: bool = False
    include_files: bool = False
    verify_stability: bool = True
    stability_passes: int = 3
    stability_delay: float = 0.20
    retries_per_directory: int = 4
    retry_base_delay: float = 0.40
    retry_rounds: int = 2
    follow_symlink_or_junction: bool = False
    max_workers: int = 4
    scan_batch_size: int = 32
    checkpoint_commit_every: int = 12


@dataclass(frozen=True)
class NativeEntry:
    name: str
    is_dir: bool
    attributes: int = 0
    size: int = 0
    reparse_tag: int = 0

    @property
    def is_hidden(self) -> bool:
        return bool(self.attributes & FILE_ATTRIBUTE_HIDDEN) or self.name.startswith(".")

    @property
    def is_reparse(self) -> bool:
        return bool(self.attributes & FILE_ATTRIBUTE_REPARSE_POINT)

    @property
    def is_offline_like(self) -> bool:
        return bool(
            self.attributes
            & (FILE_ATTRIBUTE_OFFLINE | FILE_ATTRIBUTE_RECALL_ON_OPEN | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)
        )


class ScanCancelled(Exception):
    pass


# -----------------------------------------------------------------------------
# Enumeração nativa Windows
# -----------------------------------------------------------------------------

if os.name == "nt":
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

    _GetFileAttributesW = _kernel32.GetFileAttributesW
    _GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
    _GetFileAttributesW.restype = wintypes.DWORD

    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
    FIND_EX_INFO_BASIC = 1
    FIND_EX_SEARCH_NAME_MATCH = 0
    FIND_FIRST_EX_LARGE_FETCH = 0x00000002


def _extended_windows_path(path: Path) -> str:
    """Converte caminho Windows para sintaxe long-path sem resolver links/providers."""
    raw = os.path.abspath(os.fspath(path))
    if raw.startswith("\\\\?\\"):
        return raw
    if raw.startswith("\\\\"):
        return "\\\\?\\UNC\\" + raw[2:]
    return "\\\\?\\" + raw


def _native_root_is_directory(path: Path) -> bool:
    if os.name != "nt":
        return path.is_dir()
    raw = _extended_windows_path(path)
    attrs = _GetFileAttributesW(raw)
    if attrs == INVALID_FILE_ATTRIBUTES:
        err = ctypes.get_last_error()
        raise OSError(err, ctypes.FormatError(err), str(path))
    return bool(attrs & FILE_ATTRIBUTE_DIRECTORY)


def _entry_from_find_data(data: "WIN32_FIND_DATAW") -> NativeEntry:
    attrs = int(data.dwFileAttributes)
    size = (int(data.nFileSizeHigh) << 32) | int(data.nFileSizeLow)
    return NativeEntry(
        name=str(data.cFileName),
        is_dir=bool(attrs & FILE_ATTRIBUTE_DIRECTORY),
        attributes=attrs,
        size=size,
        reparse_tag=int(data.dwReserved0) if attrs & FILE_ATTRIBUTE_REPARSE_POINT else 0,
    )


def _enumerate_windows_once(path: Path) -> list[NativeEntry]:
    """Enumera um diretório sem abrir arquivos ou pedir conteúdo dos placeholders."""
    base = _extended_windows_path(path).rstrip("\\/")
    pattern = base + "\\*"
    data = WIN32_FIND_DATAW()

    handle = _FindFirstFileExW(
        pattern,
        FIND_EX_INFO_BASIC,
        ctypes.byref(data),
        FIND_EX_SEARCH_NAME_MATCH,
        None,
        FIND_FIRST_EX_LARGE_FETCH,
    )
    if handle == INVALID_HANDLE_VALUE:
        err = ctypes.get_last_error()
        # Alguns filesystems/providers não aceitam LARGE_FETCH.
        if err == ERROR_INVALID_PARAMETER:
            handle = _FindFirstFileExW(
                pattern,
                FIND_EX_INFO_BASIC,
                ctypes.byref(data),
                FIND_EX_SEARCH_NAME_MATCH,
                None,
                0,
            )
            if handle == INVALID_HANDLE_VALUE:
                err = ctypes.get_last_error()
        if handle == INVALID_HANDLE_VALUE:
            if err == ERROR_FILE_NOT_FOUND:
                return []
            raise OSError(err, ctypes.FormatError(err), str(path))

    items: list[NativeEntry] = []
    try:
        while True:
            item = _entry_from_find_data(data)
            if item.name not in (".", ".."):
                items.append(item)

            if not _FindNextFileW(handle, ctypes.byref(data)):
                err = ctypes.get_last_error()
                if err == ERROR_NO_MORE_FILES:
                    break
                raise OSError(err, ctypes.FormatError(err), str(path))
    finally:
        _FindClose(handle)

    return items


def _enumerate_scandir_once(path: Path) -> list[NativeEntry]:
    """Fallback portável. No Windows o scanner prefere a API nativa acima."""
    items: list[NativeEntry] = []
    with os.scandir(path) as it:
        for entry in it:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                is_dir = False
            attrs = FILE_ATTRIBUTE_DIRECTORY if is_dir else 0
            if entry.name.startswith("."):
                attrs |= FILE_ATTRIBUTE_HIDDEN
            size = 0
            # Só consulta tamanho se o usuário realmente pediu inventário de arquivos.
            items.append(NativeEntry(entry.name, is_dir, attrs, size, 0))
    return items


def enumerate_once(path: Path) -> list[NativeEntry]:
    if os.name == "nt":
        return _enumerate_windows_once(path)
    return _enumerate_scandir_once(path)


def _snapshot_key(items: Iterable[NativeEntry], include_files: bool) -> tuple[tuple[str, bool], ...]:
    visible = ((item.name.casefold(), item.is_dir) for item in items if include_files or item.is_dir)
    return tuple(sorted(visible))


def _natural_key(text: str):
    import re
    return [int(p) if p.isdigit() else p.casefold() for p in re.split(r"(\d+)", text)]


def enumerate_stable(
    path: Path,
    options: ScanOptions,
    cancel_event: threading.Event,
) -> tuple[list[NativeEntry], bool, int]:
    """Enumera com retry e, opcionalmente, confirma que duas leituras consecutivas concordam."""
    last_error: Optional[BaseException] = None

    for attempt in range(1, options.retries_per_directory + 1):
        if cancel_event.is_set():
            raise ScanCancelled()
        try:
            first = enumerate_once(path)
            if not options.verify_stability:
                return first, True, attempt

            previous = first
            previous_key = _snapshot_key(previous, options.include_files)
            max_passes = max(2, options.stability_passes)

            for _ in range(2, max_passes + 1):
                if cancel_event.wait(options.stability_delay):
                    raise ScanCancelled()
                current = enumerate_once(path)
                current_key = _snapshot_key(current, options.include_files)
                if current_key == previous_key:
                    return current, True, attempt
                previous = current
                previous_key = current_key

            # O diretório respondeu, mas mudou entre leituras. Usa o snapshot mais recente
            # e marca como não confirmado em vez de inventar união de estados diferentes.
            return previous, False, attempt
        except ScanCancelled:
            raise
        except (OSError, PermissionError) as exc:
            last_error = exc
            if attempt >= options.retries_per_directory:
                break
            delay = options.retry_base_delay * (2 ** (attempt - 1))
            if cancel_event.wait(delay):
                raise ScanCancelled()

    if last_error:
        raise last_error
    raise OSError(f"Falha desconhecida ao enumerar {path}")


# -----------------------------------------------------------------------------
# Persistência / retomada
# -----------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_rel TEXT NOT NULL,
    depth INTEGER NOT NULL,
    attributes INTEGER NOT NULL DEFAULT 0,
    reparse_tag INTEGER NOT NULL DEFAULT 0,
    offline_like INTEGER NOT NULL DEFAULT 0,
    scan_state TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    stable INTEGER,
    last_error TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    parent_rel TEXT NOT NULL,
    depth INTEGER NOT NULL,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    attributes INTEGER NOT NULL DEFAULT 0,
    offline_like INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    level TEXT NOT NULL,
    rel_path TEXT NOT NULL,
    message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_state ON nodes(scan_state, id);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_rel);
CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_rel);
"""


def utc_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def open_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def set_meta(conn: sqlite3.Connection, key: str, value: object) -> None:
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, json.dumps(value, ensure_ascii=False)),
    )


def get_meta(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return json.loads(row[0])
    except Exception:
        return row[0]


def add_event(conn: sqlite3.Connection, level: str, rel_path: str, message: str) -> None:
    conn.execute(
        "INSERT INTO events(created_at,level,rel_path,message) VALUES(?,?,?,?)",
        (utc_now_iso(), level, rel_path, message),
    )


def rel_to_path(root: Path, rel_path: str) -> Path:
    if not rel_path:
        return root
    return root.joinpath(*rel_path.split("/"))


def child_rel(parent_rel: str, name: str) -> str:
    return f"{parent_rel}/{name}" if parent_rel else name


def display_rel(rel_path: str) -> str:
    return rel_path.replace("/", os.sep)


def sanitize_output_basename(value: str) -> str:
    """Normaliza um nome-base seguro para arquivos no Windows sem mexer no caminho de saída."""
    value = (value or "").strip()
    value = re.sub(r'[<>:"/\\|?*]+', "_", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    if not value:
        value = DEFAULT_OUTPUT_BASENAME
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
    if value.upper() in reserved:
        value = "_" + value
    return value[:120].rstrip(" .") or DEFAULT_OUTPUT_BASENAME


def output_paths(output_dir: Path, base_name: str, include_files: bool = False) -> dict[str, Path]:
    base = sanitize_output_basename(base_name)
    paths = {
        "tree_txt": output_dir / f"{base}.txt",
        "folders_csv": output_dir / f"{base}_pastas.csv",
        "structure_json": output_dir / f"{base}.json",
        "diagnostics_csv": output_dir / f"{base}_diagnostico.csv",
        "summary_json": output_dir / f"{base}_resumo.json",
        "checkpoint": output_dir / f"{base}_checkpoint.sqlite3",
    }
    if include_files:
        paths["files_csv"] = output_dir / f"{base}_arquivos.csv"
    return paths


def path_is_inside(child: Path, parent: Path) -> bool:
    try:
        child_abs = os.path.normcase(os.path.abspath(os.fspath(child)))
        parent_abs = os.path.normcase(os.path.abspath(os.fspath(parent)))
        return os.path.commonpath([child_abs, parent_abs]) == parent_abs
    except Exception:
        return False


class DriveTreeScanner:
    def __init__(
        self,
        root: Path,
        output_dir: Path,
        options: Optional[ScanOptions] = None,
        progress_callback: Optional[Callable[[dict], None]] = None,
        output_basename: str = DEFAULT_OUTPUT_BASENAME,
    ) -> None:
        self.root = Path(root)
        self.output_dir = Path(output_dir)
        self.options = options or ScanOptions()
        self.progress_callback = progress_callback
        self.cancel_event = threading.Event()
        self.output_basename = sanitize_output_basename(output_basename)
        self.db_path = output_paths(self.output_dir, self.output_basename)["checkpoint"]

    def cancel(self) -> None:
        self.cancel_event.set()

    def _emit(self, **payload) -> None:
        if self.progress_callback:
            try:
                self.progress_callback(payload)
            except Exception:
                pass

    def _validate(self) -> None:
        if not _native_root_is_directory(self.root):
            raise ValueError("A pasta raiz selecionada não é um diretório válido.")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if path_is_inside(self.output_dir, self.root):
            raise ValueError(
                "Escolha uma pasta de saída FORA da pasta/Drive que será varrido. "
                "Isso evita alterar a própria árvore durante a análise."
            )

    def _prepare_db(self, resume: bool) -> sqlite3.Connection:
        if self.db_path.exists() and not resume:
            self.db_path.unlink()
            for suffix in ("-wal", "-shm"):
                sidecar = Path(str(self.db_path) + suffix)
                if sidecar.exists():
                    sidecar.unlink()

        conn = open_db(self.db_path)
        stored_root = get_meta(conn, "root")
        current_root = os.path.abspath(os.fspath(self.root))
        if stored_root and os.path.normcase(stored_root) != os.path.normcase(current_root):
            conn.close()
            raise ValueError(
                "O checkpoint existente pertence a outra pasta raiz. "
                "Desmarque 'Retomar checkpoint' ou escolha outra pasta de saída."
            )

        if not stored_root:
            set_meta(conn, "root", current_root)
            set_meta(conn, "started_at", utc_now_iso())
            set_meta(conn, "app_version", APP_VERSION)
            set_meta(conn, "output_basename", self.output_basename)
            set_meta(conn, "options", self.options.__dict__)
            conn.execute(
                "INSERT OR IGNORE INTO nodes(rel_path,name,parent_rel,depth,scan_state) VALUES('','[RAIZ]','',0,'pending')"
            )
            conn.commit()
        elif resume:
            stored_options = get_meta(conn, "options", {}) or {}
            # Opções que alteram o universo descoberto não podem mudar no meio de um checkpoint.
            structural_keys = ("include_hidden", "include_files", "follow_symlink_or_junction")
            changed = [
                key for key in structural_keys
                if bool(stored_options.get(key, False)) != bool(getattr(self.options, key))
            ]
            if changed:
                conn.close()
                raise ValueError(
                    "O checkpoint foi criado com opções diferentes (" + ", ".join(changed) + "). "
                    "Desmarque 'Retomar checkpoint' para iniciar uma varredura nova com as opções atuais."
                )
        return conn

    def _insert_entries(
        self,
        conn: sqlite3.Connection,
        parent_rel: str,
        parent_depth: int,
        entries: list[NativeEntry],
    ) -> tuple[int, int, int]:
        dirs_added = 0
        files_added = 0
        links_skipped = 0

        for item in sorted(entries, key=lambda e: _natural_key(e.name)):
            if not self.options.include_hidden and item.is_hidden:
                continue
            rel = child_rel(parent_rel, item.name)

            if item.is_dir:
                is_link_loop_risk = item.is_reparse and item.reparse_tag in {
                    IO_REPARSE_TAG_MOUNT_POINT,
                    IO_REPARSE_TAG_SYMLINK,
                }
                state = "skipped_link" if (is_link_loop_risk and not self.options.follow_symlink_or_junction) else "pending"
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO nodes(
                        rel_path,name,parent_rel,depth,attributes,reparse_tag,offline_like,scan_state
                    ) VALUES(?,?,?,?,?,?,?,?)
                    """,
                    (
                        rel,
                        item.name,
                        parent_rel,
                        parent_depth + 1,
                        item.attributes,
                        item.reparse_tag,
                        int(item.is_offline_like),
                        state,
                    ),
                )
                if cur.rowcount:
                    dirs_added += 1
                    if state == "skipped_link":
                        links_skipped += 1
                        add_event(conn, "warning", rel, "Junction/symlink não seguido para evitar loop de recursão.")
            elif self.options.include_files:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO files(
                        rel_path,name,parent_rel,depth,size_bytes,attributes,offline_like
                    ) VALUES(?,?,?,?,?,?,?)
                    """,
                    (
                        rel,
                        item.name,
                        parent_rel,
                        parent_depth + 1,
                        item.size,
                        item.attributes,
                        int(item.is_offline_like),
                    ),
                )
                if cur.rowcount:
                    files_added += 1

        return dirs_added, files_added, links_skipped

    def _stats(self, conn: sqlite3.Connection) -> dict:
        total_dirs = conn.execute("SELECT COUNT(*) FROM nodes WHERE rel_path<>''").fetchone()[0]
        scanned = conn.execute("SELECT COUNT(*) FROM nodes WHERE rel_path<>'' AND scan_state IN ('scanned','scanned_unstable')").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM nodes WHERE scan_state='pending'").fetchone()[0]
        failed = conn.execute("SELECT COUNT(*) FROM nodes WHERE scan_state='error'").fetchone()[0]
        unstable = conn.execute("SELECT COUNT(*) FROM nodes WHERE scan_state='scanned_unstable'").fetchone()[0]
        skipped = conn.execute("SELECT COUNT(*) FROM nodes WHERE scan_state='skipped_link'").fetchone()[0]
        files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        return {
            "folders_found": total_dirs,
            "folders_scanned": scanned,
            "folders_pending": pending,
            "folders_error": failed,
            "folders_unstable": unstable,
            "links_skipped": skipped,
            "files_found": files,
        }

    def run(self, resume: bool = True) -> dict:
        self._validate()
        conn = self._prepare_db(resume=resume)
        retry_round = 0
        workers = max(1, min(int(self.options.max_workers or 1), 12))
        batch_size = max(workers, int(self.options.scan_batch_size or workers))
        commit_every = max(1, int(self.options.checkpoint_commit_every or 1))
        executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="DriveEnum")

        try:
            set_meta(conn, "last_run_started_at", utc_now_iso())
            set_meta(conn, "last_run_workers", workers)
            conn.commit()

            while True:
                if self.cancel_event.is_set():
                    raise ScanCancelled()

                rows = conn.execute(
                    "SELECT id,rel_path,depth,attempts FROM nodes WHERE scan_state='pending' ORDER BY id LIMIT ?",
                    (batch_size,),
                ).fetchall()

                if not rows:
                    error_count = conn.execute("SELECT COUNT(*) FROM nodes WHERE scan_state='error'").fetchone()[0]
                    if error_count and retry_round < self.options.retry_rounds:
                        retry_round += 1
                        conn.execute("UPDATE nodes SET scan_state='pending' WHERE scan_state='error'")
                        add_event(conn, "info", "", f"Iniciando rodada extra de retry {retry_round}/{self.options.retry_rounds}.")
                        conn.commit()
                        self._emit(
                            message=f"Revisitando {error_count} pasta(s) com erro — rodada {retry_round}...",
                            **self._stats(conn),
                        )
                        if self.cancel_event.wait(self.options.retry_base_delay):
                            raise ScanCancelled()
                        continue
                    break

                future_map = {}
                for row in rows:
                    node_id, rel_path, depth, previous_attempts = row
                    path = rel_to_path(self.root, rel_path)
                    future = executor.submit(enumerate_stable, path, self.options, self.cancel_event)
                    future_map[future] = (node_id, rel_path, depth, previous_attempts)

                changed_since_commit = 0

                for future in as_completed(future_map):
                    node_id, rel_path, depth, previous_attempts = future_map[future]
                    pretty = display_rel(rel_path) or str(self.root)

                    if self.cancel_event.is_set():
                        conn.commit()
                        raise ScanCancelled()

                    try:
                        entries, stable, attempts_used = future.result()
                        dirs_added, files_added, _ = self._insert_entries(conn, rel_path, depth, entries)
                        state = "scanned" if stable else "scanned_unstable"
                        conn.execute(
                            "UPDATE nodes SET scan_state=?, attempts=?, stable=?, last_error='' WHERE id=?",
                            (state, previous_attempts + attempts_used, int(stable), node_id),
                        )
                        if not stable:
                            add_event(
                                conn,
                                "warning",
                                rel_path,
                                "A listagem mudou entre as passagens de verificação; foi preservado o snapshot mais recente.",
                            )

                        changed_since_commit += 1
                        if changed_since_commit >= commit_every:
                            conn.commit()
                            changed_since_commit = 0

                        stats = self._stats(conn)
                        self._emit(
                            message=(
                                f"Lida: {pretty} | +{dirs_added} pasta(s)"
                                + (f" | +{files_added} arquivo(s)" if self.options.include_files else "")
                                + (f" | {workers} workers" if workers > 1 else "")
                            ),
                            current_path=pretty,
                            **stats,
                        )
                    except ScanCancelled:
                        conn.commit()
                        raise
                    except Exception as exc:
                        conn.execute(
                            "UPDATE nodes SET scan_state='error', attempts=attempts+1, last_error=? WHERE id=?",
                            (str(exc), node_id),
                        )
                        add_event(conn, "error", rel_path, str(exc))
                        changed_since_commit += 1
                        if changed_since_commit >= commit_every:
                            conn.commit()
                            changed_since_commit = 0
                        self._emit(
                            message=f"Falha temporária/permanente: {pretty} — {exc}",
                            current_path=pretty,
                            **self._stats(conn),
                        )

                conn.commit()

            set_meta(conn, "finished_at", utc_now_iso())
            final_stats = self._stats(conn)
            complete = final_stats["folders_error"] == 0 and final_stats["folders_unstable"] == 0
            set_meta(conn, "complete_verified", complete)
            conn.commit()

            outputs = export_reports(
                conn, self.root, self.output_dir, self.options, output_basename=self.output_basename
            )
            final_stats["complete_verified"] = complete
            final_stats["outputs"] = {k: str(v) for k, v in outputs.items()}
            final_stats["checkpoint"] = str(self.db_path)
            final_stats["workers"] = workers
            return final_stats
        except ScanCancelled:
            set_meta(conn, "cancelled_at", utc_now_iso())
            conn.commit()
            raise
        finally:
            self.cancel_event.set() if self.cancel_event.is_set() else None
            executor.shutdown(wait=True, cancel_futures=True)
            conn.close()


# -----------------------------------------------------------------------------
# Exportações
# -----------------------------------------------------------------------------

def _atomic_text(path: Path, writer: Callable[[object], None], newline: str = "") -> None:
    temp = path.with_name(path.name + ".tmp")
    try:
        with temp.open("w", encoding="utf-8", newline=newline) as fh:
            writer(fh)
        os.replace(temp, path)
    finally:
        if temp.exists():
            try:
                temp.unlink()
            except Exception:
                pass


def _summary_payload(conn: sqlite3.Connection, root: Path, options: ScanOptions) -> dict:
    def count(sql: str) -> int:
        return int(conn.execute(sql).fetchone()[0])

    return {
        "root": os.path.abspath(os.fspath(root)),
        "generated_at": utc_now_iso(),
        "complete_verified": bool(get_meta(conn, "complete_verified", False)),
        "started_at": get_meta(conn, "started_at"),
        "finished_at": get_meta(conn, "finished_at"),
        "options": options.__dict__,
        "folders": {
            "total": count("SELECT COUNT(*) FROM nodes WHERE rel_path<>''"),
            "scanned": count("SELECT COUNT(*) FROM nodes WHERE rel_path<>'' AND scan_state IN ('scanned','scanned_unstable')"),
            "errors": count("SELECT COUNT(*) FROM nodes WHERE scan_state='error'"),
            "unstable": count("SELECT COUNT(*) FROM nodes WHERE scan_state='scanned_unstable'"),
            "links_skipped": count("SELECT COUNT(*) FROM nodes WHERE scan_state='skipped_link'"),
        },
        "files_total": count("SELECT COUNT(*) FROM files"),
    }


def export_reports(
    conn: sqlite3.Connection,
    root: Path,
    output_dir: Path,
    options: ScanOptions,
    output_basename: str = DEFAULT_OUTPUT_BASENAME,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = output_paths(output_dir, output_basename, include_files=options.include_files)
    txt_path = paths["tree_txt"]
    csv_path = paths["folders_csv"]
    json_path = paths["structure_json"]
    errors_path = paths["diagnostics_csv"]
    summary_path = paths["summary_json"]
    files_path = paths.get("files_csv")

    summary = _summary_payload(conn, root, options)

    def write_tree(fh):
        fh.write("ESTRUTURA DE PASTAS — GOOGLE DRIVE / DRIVE STREAMING\n")
        fh.write("=" * 62 + "\n")
        fh.write(f"Raiz: {summary['root']}\n")
        fh.write(f"Gerado em: {summary['generated_at']}\n")
        fh.write(f"Pastas encontradas: {summary['folders']['total']}\n")
        fh.write(f"Pastas com erro: {summary['folders']['errors']}\n")
        fh.write(f"Pastas com listagem instável: {summary['folders']['unstable']}\n")
        fh.write(f"Links/junctions ignorados: {summary['folders']['links_skipped']}\n")
        fh.write(f"Verificação completa: {'SIM' if summary['complete_verified'] else 'NÃO'}\n\n")
        fh.write("[RAIZ] " + str(root) + "\n")
        for rel_path, name, depth, state in conn.execute(
            "SELECT rel_path,name,depth,scan_state FROM nodes WHERE rel_path<>'' ORDER BY rel_path COLLATE NOCASE"
        ):
            marker = ""
            if state == "error":
                marker = "  [ERRO DE ACESSO]"
            elif state == "scanned_unstable":
                marker = "  [NÃO ESTÁVEL]"
            elif state == "skipped_link":
                marker = "  [LINK NÃO SEGUIDO]"
            fh.write("    " * max(depth - 1, 0) + "└── " + name + "/" + marker + "\n")

    _atomic_text(txt_path, write_tree)

    temp_csv = csv_path.with_name(csv_path.name + ".tmp")
    with temp_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["caminho_relativo", "nome", "pasta_pai", "profundidade", "estado", "tentativas", "estavel", "atributos", "reparse_tag", "offline_like", "ultimo_erro"])
        for row in conn.execute(
            "SELECT rel_path,name,parent_rel,depth,scan_state,attempts,stable,attributes,reparse_tag,offline_like,last_error FROM nodes WHERE rel_path<>'' ORDER BY rel_path COLLATE NOCASE"
        ):
            row = list(row)
            row[0] = display_rel(row[0])
            row[2] = display_rel(row[2])
            writer.writerow(row)
    os.replace(temp_csv, csv_path)

    # JSON plano por design: preserva todos os caminhos sem risco de recursão profunda.
    def write_json(fh):
        fh.write('{\n  "summary": ')
        json.dump(summary, fh, ensure_ascii=False, indent=2)
        fh.write(',\n  "folders": [\n')
        first = True
        for rel_path, name, parent_rel, depth, state, attempts, stable, attributes, reparse_tag, offline_like, last_error in conn.execute(
            "SELECT rel_path,name,parent_rel,depth,scan_state,attempts,stable,attributes,reparse_tag,offline_like,last_error FROM nodes WHERE rel_path<>'' ORDER BY rel_path COLLATE NOCASE"
        ):
            if not first:
                fh.write(",\n")
            first = False
            obj = {
                "relative_path": display_rel(rel_path),
                "name": name,
                "parent": display_rel(parent_rel),
                "depth": depth,
                "state": state,
                "attempts": attempts,
                "stable": None if stable is None else bool(stable),
                "attributes": attributes,
                "reparse_tag": reparse_tag,
                "offline_like": bool(offline_like),
            }
            if last_error:
                obj["last_error"] = last_error
            fh.write("    " + json.dumps(obj, ensure_ascii=False))
        fh.write("\n  ]\n}\n")

    _atomic_text(json_path, write_json)

    temp_err = errors_path.with_name(errors_path.name + ".tmp")
    with temp_err.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["data_hora", "nivel", "caminho_relativo", "mensagem"])
        for created_at, level, rel_path, message in conn.execute(
            "SELECT created_at,level,rel_path,message FROM events ORDER BY id"
        ):
            writer.writerow([created_at, level, display_rel(rel_path), message])
    os.replace(temp_err, errors_path)

    _atomic_text(summary_path, lambda fh: json.dump(summary, fh, ensure_ascii=False, indent=2))

    outputs = {
        "tree_txt": txt_path,
        "folders_csv": csv_path,
        "structure_json": json_path,
        "diagnostics_csv": errors_path,
        "summary_json": summary_path,
    }

    if options.include_files and files_path is not None:
        temp_files = files_path.with_name(files_path.name + ".tmp")
        with temp_files.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["caminho_relativo", "nome", "pasta_pai", "profundidade", "tamanho_bytes", "atributos", "offline_like"])
            for rel_path, name, parent_rel, depth, size_bytes, attributes, offline_like in conn.execute(
                "SELECT rel_path,name,parent_rel,depth,size_bytes,attributes,offline_like FROM files ORDER BY rel_path COLLATE NOCASE"
            ):
                writer.writerow([display_rel(rel_path), name, display_rel(parent_rel), depth, size_bytes, attributes, offline_like])
        os.replace(temp_files, files_path)
        outputs["files_csv"] = files_path

    return outputs


# -----------------------------------------------------------------------------
# GUI
# -----------------------------------------------------------------------------

class ScannerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("920x660")
        self.minsize(820, 600)
        self.scanner: Optional[DriveTreeScanner] = None
        self.worker: Optional[threading.Thread] = None

        self.root_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.home() / "K-Tools Drive Scan"))
        self.output_name_var = tk.StringVar(value=DEFAULT_OUTPUT_BASENAME)
        self.workers_var = tk.StringVar(value="4")
        self.include_hidden_var = tk.BooleanVar(value=False)
        self.include_files_var = tk.BooleanVar(value=False)
        self.verify_var = tk.BooleanVar(value=True)
        self.resume_var = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass

        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text="Drive Streaming Scanner", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(
            outer,
            text="Varredura robusta de árvores de pastas em Google Drive for desktop (modo streaming), sem abrir o conteúdo dos arquivos.",
            wraplength=830,
        ).grid(row=1, column=0, sticky="w", pady=(4, 18))

        paths = ttk.LabelFrame(outer, text="Pastas", padding=12)
        paths.grid(row=2, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)

        ttk.Label(paths, text="Pasta raiz / Drive:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(paths, textvariable=self.root_var).grid(row=0, column=1, sticky="ew", pady=5)
        ttk.Button(paths, text="Escolher…", command=self.choose_root).grid(row=0, column=2, padx=(8, 0), pady=5)

        ttk.Label(paths, text="Saída local:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(paths, textvariable=self.output_var).grid(row=1, column=1, sticky="ew", pady=5)
        ttk.Button(paths, text="Escolher…", command=self.choose_output).grid(row=1, column=2, padx=(8, 0), pady=5)

        ttk.Label(paths, text="Nome-base da saída:").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(paths, textvariable=self.output_name_var).grid(row=2, column=1, sticky="ew", pady=5)
        ttk.Label(paths, text="Ex.: Meu Drive 2026 → Meu Drive 2026.txt / .json / _pastas.csv", foreground="#666666").grid(
            row=3, column=1, columnspan=2, sticky="w", pady=(2, 0)
        )

        ttk.Label(
            paths,
            text="Recomendado: salve a saída em C:\\... ou outra pasta local, fora do próprio Drive analisado.",
            foreground="#666666",
        ).grid(row=4, column=1, columnspan=2, sticky="w", pady=(2, 0))

        opts = ttk.LabelFrame(outer, text="Modo de varredura", padding=12)
        opts.grid(row=3, column=0, sticky="ew", pady=(14, 0))
        ttk.Checkbutton(opts, text="Confirmar cada diretório com leituras repetidas (recomendado)", variable=self.verify_var).grid(row=0, column=0, sticky="w")
        speed_row = ttk.Frame(opts)
        speed_row.grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(speed_row, text="Varreduras simultâneas:").pack(side="left")
        ttk.Combobox(speed_row, textvariable=self.workers_var, values=("1", "2", "4", "6", "8"), state="readonly", width=5).pack(side="left", padx=(8, 8))
        ttk.Label(speed_row, text="4 = rápido e conservador para Drive streaming", foreground="#666666").pack(side="left")
        ttk.Checkbutton(opts, text="Incluir pastas/arquivos ocultos", variable=self.include_hidden_var).grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Checkbutton(opts, text="Inventariar também arquivos (mais lento; árvore de pastas não precisa disso)", variable=self.include_files_var).grid(row=3, column=0, sticky="w", pady=(6, 0))
        ttk.Checkbutton(opts, text="Retomar checkpoint existente quando possível", variable=self.resume_var).grid(row=4, column=0, sticky="w", pady=(6, 0))

        controls = ttk.Frame(outer)
        controls.grid(row=4, column=0, sticky="ew", pady=(16, 0))
        self.start_btn = ttk.Button(controls, text="Iniciar varredura", command=self.start_scan)
        self.start_btn.pack(side="left")
        self.cancel_btn = ttk.Button(controls, text="Cancelar", command=self.cancel_scan, state="disabled")
        self.cancel_btn.pack(side="left", padx=8)
        ttk.Button(controls, text="Abrir pasta de saída", command=self.open_output).pack(side="right")

        status_box = ttk.LabelFrame(outer, text="Status", padding=12)
        status_box.grid(row=5, column=0, sticky="nsew", pady=(14, 0))
        outer.rowconfigure(5, weight=1)
        status_box.columnconfigure(0, weight=1)
        status_box.rowconfigure(3, weight=1)

        self.progress = ttk.Progressbar(status_box, mode="indeterminate")
        self.progress.grid(row=0, column=0, sticky="ew")
        self.status_label = ttk.Label(status_box, text="Pronto para iniciar.", wraplength=820)
        self.status_label.grid(row=1, column=0, sticky="w", pady=(10, 4))
        self.count_label = ttk.Label(status_box, text="Pastas: 0 | Lidas: 0 | Erros: 0 | Instáveis: 0")
        self.count_label.grid(row=2, column=0, sticky="w")

        self.log = tk.Text(status_box, height=12, wrap="word", font=("Consolas", 9))
        self.log.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        self.log.configure(state="disabled")

    def choose_root(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta do Google Drive a mapear")
        if folder:
            self.root_var.set(folder)

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta LOCAL para os relatórios")
        if folder:
            self.output_var.set(folder)

    def open_output(self) -> None:
        path = Path(self.output_var.get().strip())
        if not path.exists():
            messagebox.showinfo(APP_TITLE, "A pasta de saída ainda não existe.")
            return
        try:
            if os.name == "nt":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _on_progress(self, data: dict) -> None:
        def apply():
            self.status_label.configure(text=data.get("message", "Analisando…"))
            self.count_label.configure(
                text=(
                    f"Pastas: {data.get('folders_found', 0)} | "
                    f"Lidas: {data.get('folders_scanned', 0)} | "
                    f"Pendentes: {data.get('folders_pending', 0)} | "
                    f"Erros: {data.get('folders_error', 0)} | "
                    f"Instáveis: {data.get('folders_unstable', 0)}"
                )
            )
            self._append_log(data.get("message", ""))
        self.after(0, apply)

    def start_scan(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        root = self.root_var.get().strip()
        out = self.output_var.get().strip()
        output_name = sanitize_output_basename(self.output_name_var.get())
        self.output_name_var.set(output_name)
        if not root or not out:
            messagebox.showwarning(APP_TITLE, "Selecione a pasta raiz e a pasta de saída.")
            return
        try:
            workers = max(1, min(int(self.workers_var.get()), 8))
        except ValueError:
            workers = 4
            self.workers_var.set("4")

        options = ScanOptions(
            include_hidden=self.include_hidden_var.get(),
            include_files=self.include_files_var.get(),
            verify_stability=self.verify_var.get(),
            max_workers=workers,
        )
        self.scanner = DriveTreeScanner(
            Path(root), Path(out), options, self._on_progress, output_basename=output_name
        )
        self.start_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress.start(12)
        self.status_label.configure(text="Preparando varredura…")
        self._append_log("--- Início da varredura ---")

        def work():
            try:
                result = self.scanner.run(resume=self.resume_var.get())
                self.after(0, lambda: self._finish_success(result))
            except ScanCancelled:
                self.after(0, self._finish_cancelled)
            except Exception as exc:
                self.after(0, lambda e=exc: self._finish_error(e))

        self.worker = threading.Thread(target=work, name="DriveStreamingScanner", daemon=True)
        self.worker.start()

    def cancel_scan(self) -> None:
        if self.scanner:
            self.scanner.cancel()
            self.status_label.configure(text="Cancelamento solicitado. O checkpoint será preservado.")
            self.cancel_btn.configure(state="disabled")

    def _reset_buttons(self) -> None:
        self.progress.stop()
        self.start_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")

    def _finish_success(self, result: dict) -> None:
        self._reset_buttons()
        verified = result.get("complete_verified", False)
        if verified:
            msg = f"Concluído e verificado: {result.get('folders_found', 0)} pasta(s)."
        else:
            msg = (
                "Varredura concluída, mas há trechos que não puderam ser confirmados. "
                f"Erros: {result.get('folders_error', 0)} | Instáveis: {result.get('folders_unstable', 0)}."
            )
        self.status_label.configure(text=msg)
        self._append_log(msg)
        messagebox.showinfo(APP_TITLE, msg + "\n\nOs relatórios foram salvos na pasta de saída.")

    def _finish_cancelled(self) -> None:
        self._reset_buttons()
        msg = "Varredura cancelada. O checkpoint foi preservado e pode ser retomado depois."
        self.status_label.configure(text=msg)
        self._append_log(msg)

    def _finish_error(self, exc: Exception) -> None:
        self._reset_buttons()
        msg = f"Erro: {exc}"
        self.status_label.configure(text=msg)
        self._append_log(msg)
        messagebox.showerror(APP_TITLE, msg)


if __name__ == "__main__":
    app = ScannerApp()
    app.mainloop()
