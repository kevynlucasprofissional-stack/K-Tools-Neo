import json
import os
import shutil
import tempfile
from datetime import datetime, timezone


CONTROL_FILENAME = "YT-DLP-TUI-controle.json"
TEMP_DIRNAME = ".yt-dlp-tui-tmp"
SCHEMA_VERSION = 3


class CorruptControlError(RuntimeError):
    """The task control exists but cannot be safely interpreted."""

    def __init__(self, path, reason):
        self.path = path
        self.reason = str(reason)
        super().__init__(f"controle inválido em {path}: {self.reason}")


def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def control_path(task_dir):
    return os.path.join(task_dir, CONTROL_FILENAME)


def _validate_control(data):
    if not isinstance(data, dict):
        raise ValueError("raiz do controle não é um objeto JSON")
    if not isinstance(data.get("schema_version"), int):
        raise ValueError("schema_version ausente ou inválido")
    if data.get("task_type") != "playlist":
        raise ValueError("task_type inválido")
    playlist = data.get("playlist")
    if not isinstance(playlist, dict):
        raise ValueError("bloco playlist ausente ou inválido")
    if not playlist.get("id"):
        raise ValueError("playlist.id ausente")
    if not isinstance(data.get("mode"), dict):
        raise ValueError("bloco mode ausente ou inválido")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("lista items ausente ou inválida")
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"item {index} de playlist inválido")
        video_id = item.get("video_id")
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError(f"item {index}: video_id ausente ou inválido")
        status = item.get("status")
        if not isinstance(status, str) or not status.strip():
            raise ValueError(f"item {index}: status ausente ou inválido")
        if "available" in item and not isinstance(item.get("available"), bool):
            raise ValueError(f"item {index}: available inválido")
        if "final_file" in item and item.get("final_file") is not None and not isinstance(item.get("final_file"), str):
            raise ValueError(f"item {index}: final_file inválido")
        for counter in ("attempts", "retry_count"):
            if counter in item and not isinstance(item.get(counter), int):
                raise ValueError(f"item {index}: {counter} inválido")
        if "progress" in item and not isinstance(item.get("progress"), dict):
            raise ValueError(f"item {index}: progress inválido")
    return data


def load_control(task_dir):
    """Load a valid control file or raise CorruptControlError.

    An invalid JSON/control is deliberately not treated as if it never existed.
    The caller decides how to preserve and reconstruct it because only the
    playlist layer has enough metadata to rebuild progress safely.
    """
    path = control_path(task_dir)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return _validate_control(data)
    except CorruptControlError:
        raise
    except Exception as e:
        raise CorruptControlError(path, e) from e


def save_control(task_dir, state):
    """Atomically persist task state beside the downloaded media."""
    os.makedirs(task_dir, exist_ok=True)
    state["updated_at"] = now_iso()
    path = control_path(task_dir)
    fd, tmp = tempfile.mkstemp(prefix=".controle-", suffix=".tmp", dir=task_dir, text=True)
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
    return path


def backup_control(task_dir):
    path = control_path(task_dir)
    if not os.path.isfile(path):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(task_dir, f"YT-DLP-TUI-controle-{stamp}.bak.json")
    counter = 1
    while os.path.exists(backup):
        backup = os.path.join(task_dir, f"YT-DLP-TUI-controle-{stamp}-{counter}.bak.json")
        counter += 1
    shutil.copy2(path, backup)
    return backup


def preserve_corrupt_control(task_dir):
    """Move an unreadable control aside so a reconstructed state can be saved."""
    path = control_path(task_dir)
    if not os.path.isfile(path):
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    preserved = os.path.join(task_dir, f"YT-DLP-TUI-controle-{stamp}.corrupt.json")
    counter = 1
    while os.path.exists(preserved):
        preserved = os.path.join(task_dir, f"YT-DLP-TUI-controle-{stamp}-{counter}.corrupt.json")
        counter += 1
    os.replace(path, preserved)
    return preserved


def migrate_control_state(state):
    """Migrate the immediately previous schema without discarding progress."""
    _validate_control(state)
    version = state.get("schema_version")
    if version == SCHEMA_VERSION:
        return state, False
    if version != 2:
        raise ValueError(f"schema de controle não suportado: {version}")

    state["schema_version"] = SCHEMA_VERSION
    for item in state.get("items", []):
        if not isinstance(item, dict):
            continue
        item.setdefault("retry_count", 0)
        item.setdefault("last_retry_at", None)
        item.setdefault("last_error_kind", None)
        item.setdefault("audit_status", "not_run")
        item.setdefault("audit_at", None)
        item.setdefault("attempts", 0)
        item.setdefault("started_at", None)
        item.setdefault("completed_at", None)
        item.setdefault("final_file", None)
        item.setdefault("progress", {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None})
        if not item.get("available", True) or item.get("status") == "unavailable":
            item["available"] = False
            item["status"] = "unavailable"
            item["last_error_kind"] = item.get("last_error_kind") or "permanent_unavailable"

    audit = state.setdefault("audit", {})
    audit.setdefault("status", "not_run")
    audit.setdefault("last_run_at", None)
    audit.setdefault("checked", 0)
    audit.setdefault("ok", 0)
    audit.setdefault("failed", 0)
    audit.setdefault("unavailable", 0)
    return state, True


def stage_dir(task_dir, video_id):
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(video_id))
    return os.path.join(task_dir, TEMP_DIRNAME, safe_id)


def _is_link_like(path):
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    try:
        return bool(isjunction and isjunction(path))
    except OSError:
        return False


def _lexically_within(root, target):
    try:
        root_abs = os.path.abspath(root)
        target_abs = os.path.abspath(target)
        return os.path.commonpath([root_abs, target_abs]) == root_abs
    except (OSError, ValueError):
        return False


def _remove_link_like(path):
    # Symlinked directories must be unlinked, never traversed. Windows junctions
    # are removed with rmdir and likewise must never be followed recursively.
    if os.path.islink(path):
        os.unlink(path)
        return
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction and isjunction(path):
        os.rmdir(path)


def cleanup_stage(task_dir, video_id):
    """Remove only YT-DLP TUI staging paths without following links outside the task."""
    parent = os.path.join(task_dir, TEMP_DIRNAME)
    if not _lexically_within(task_dir, parent):
        return

    try:
        if _is_link_like(parent):
            _remove_link_like(parent)
            return
    except OSError:
        return

    path = stage_dir(task_dir, video_id)
    if not _lexically_within(task_dir, path):
        return
    try:
        if _is_link_like(path):
            _remove_link_like(path)
        elif os.path.isdir(path):
            task_real = os.path.realpath(task_dir)
            path_real = os.path.realpath(path)
            if os.path.commonpath([task_real, path_real]) == task_real:
                shutil.rmtree(path)
    except (OSError, ValueError):
        return

    try:
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
    except OSError:
        pass


def make_playlist_state(playlist_id, title, source_url, file_format, quality, items):
    now = now_iso()
    return {
        "schema_version": SCHEMA_VERSION,
        "task_type": "playlist",
        "playlist": {
            "id": playlist_id,
            "title": title,
            "source_url": source_url,
        },
        "mode": {"format": file_format, "quality": quality},
        "status": "in_progress",
        "created_at": now,
        "updated_at": now,
        "items": items,
        "audit": {
            "status": "not_run",
            "last_run_at": None,
            "checked": 0,
            "ok": 0,
            "failed": 0,
            "unavailable": 0,
        },
    }


def merge_playlist_items(state, fresh_items):
    """Refresh playlist metadata while preserving valid progress by video ID."""
    existing = state.get("items") or []
    pools = {}
    for item in existing:
        pools.setdefault(item.get("video_id"), []).append(item)

    merged = []
    for fresh in fresh_items:
        pool = pools.get(fresh.get("video_id")) or []
        old = pool.pop(0) if pool else None
        if not old:
            merged.append(fresh)
            continue

        preserved = dict(old)
        preserved.update({
            "index": fresh.get("index"),
            "video_id": fresh.get("video_id"),
            "title": fresh.get("title"),
            "url": fresh.get("url"),
        })

        fresh_available = fresh.get("available", True)
        if not fresh_available:
            preserved["available"] = False
            preserved["status"] = "unavailable"
            preserved["final_file"] = None
            preserved["last_error"] = fresh.get("last_error") or preserved.get("last_error") or "entrada indisponível na playlist"
            preserved["last_error_kind"] = "permanent_unavailable"
        elif old.get("status") == "unavailable" and not old.get("available", True):
            # The playlist metadata can later reveal a previously inaccessible
            # entry. Re-evaluate it rather than keeping stale unavailability.
            preserved["available"] = True
            preserved["status"] = "pending"
            preserved["last_error"] = None
            preserved["last_error_kind"] = None
            preserved["final_file"] = None
            preserved["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
        elif old.get("status") == "unresolved" and fresh.get("url"):
            preserved["available"] = True
            preserved["status"] = "pending"
            preserved["last_error"] = None
            preserved["last_error_kind"] = None
            preserved["final_file"] = None
            preserved["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
        else:
            preserved["available"] = True

        preserved.setdefault("retry_count", 0)
        preserved.setdefault("last_retry_at", None)
        preserved.setdefault("last_error_kind", None)
        merged.append(preserved)

    state["items"] = merged
    return state
