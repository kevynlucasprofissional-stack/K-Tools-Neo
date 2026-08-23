import importlib
import importlib.metadata
import inspect
import os
import re
import shutil
import subprocess
import time
import unicodedata
from urllib.parse import parse_qs, urlparse

import yt_dlp

from .auth_cache import active_cookie_file, inspect_cookie_file
from .errors import CaptureLogger, ClassifiedFailureError, ErrorKind, classify_failure, technical_summary
from .retry_policy import (
    exhausted_message,
    is_network_retryable,
    retry_decision,
    yt_dlp_retry_options,
)
from .control import (
    CONTROL_FILENAME,
    SCHEMA_VERSION,
    CorruptControlError,
    backup_control,
    cleanup_stage,
    control_path,
    load_control,
    make_playlist_state,
    merge_playlist_items,
    migrate_control_state,
    now_iso,
    preserve_corrupt_control,
    save_control,
    stage_dir,
)


MEDIA_EXTENSIONS = {
    ".mp4", ".mkv", ".webm", ".mov", ".m4v",
    ".m4a", ".mp3", ".aac", ".opus", ".ogg", ".wav", ".flac",
}


class AuthCacheExpired(RuntimeError):
    pass


class DownloadInterrupted(RuntimeError):
    pass


class EmptyPlaylistExtractionError(RuntimeError):
    """yt-dlp returned playlist metadata but no playlist entries."""

    def __init__(self, playlist_id=None, title=None, expected_count=None):
        self.playlist_id = playlist_id
        self.title = title
        self.expected_count = expected_count
        detail = "nenhum item foi retornado para uma playlist"
        if expected_count:
            detail += f" que informa {expected_count} item(ns)"
        super().__init__(detail)


# A newly selected cookie export can still belong to the wrong account or be
# rejected server-side. Bound repeated server-auth refreshes so a persistent
# AUTH_EXPIRED response cannot create an infinite interaction loop.
MAX_AUTH_REFRESHES_PER_OPERATION = 2

# yt-dlp can intermittently return valid playlist metadata with zero entries.
# Keep this recovery bounded and independent from network retry budgets.
MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS = 3
EMPTY_PLAYLIST_RETRY_DELAY_SECONDS = 1


def _youtube_opts(logger=None):
    opts = {
        "js_runtimes": {"deno": {}},
        **yt_dlp_retry_options(),
    }
    cookie_path = active_cookie_file()
    if cookie_path:
        opts["cookiefile"] = cookie_path
    if logger is not None:
        opts["logger"] = logger
    return opts


def _ffmpeg_exe():
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.isfile(exe):
            return exe
    except Exception:
        pass
    return None


def _invoke_auth_refresh(callback, reason=None, *, initial=False):
    """Invoke the auth callback without swallowing TypeError raised inside it.

    Older custom callbacks may accept only ``reason``.  Determine compatibility
    from the callable signature before execution instead of treating any runtime
    TypeError as a signature mismatch and accidentally calling the callback twice.
    """
    if not callback:
        return False

    try:
        signature = inspect.signature(callback)
    except (TypeError, ValueError):
        # Builtins/opaque callables: use the current contract and let real errors
        # surface rather than guessing and invoking the callback twice.
        return bool(callback(reason, initial=initial))

    try:
        signature.bind(reason, initial=initial)
    except TypeError:
        signature.bind(reason)
        return bool(callback(reason))
    return bool(callback(reason, initial=initial))


def _version_tuple(value):
    numbers = re.findall(r"\d+", str(value or ""))
    return tuple(int(part) for part in numbers[:3]) if numbers else ()


def _required_ejs_version():
    """Read yt-dlp's exact yt-dlp-ejs pin from installed package metadata."""
    try:
        requirements = importlib.metadata.requires("yt-dlp") or []
    except Exception:
        return None
    for requirement in requirements:
        if not requirement.lower().lstrip().startswith("yt-dlp-ejs"):
            continue
        match = re.search(r"==\s*([^;\s]+)", requirement)
        if match:
            return match.group(1)
    return None


def _js_preflight_failure(detail):
    failure = classify_failure(RuntimeError(f"EJS JavaScript runtime: {detail}"))
    # The central classifier should own this category.  Keep the guard explicit
    # so a future taxonomy regression cannot accidentally trigger auth refresh.
    if failure.kind is not ErrorKind.JS_RUNTIME:
        raise RuntimeError(f"classificador não reconheceu falha JS_RUNTIME: {detail}")
    return failure


def _check_js_runtime():
    """Validate Deno + local yt-dlp-ejs without fetching remote components."""
    deno = shutil.which("deno")
    if not deno:
        return _js_preflight_failure("Deno não foi encontrado no PATH")

    try:
        proc = subprocess.run(
            [deno, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=5,
            check=False,
        )
    except Exception as e:
        return _js_preflight_failure(f"não foi possível executar Deno: {e}")

    version_match = re.search(r"(?im)^deno\s+([0-9]+(?:\.[0-9]+){1,2})", proc.stdout or "")
    deno_version = version_match.group(1) if version_match else None
    if proc.returncode != 0 or not deno_version:
        return _js_preflight_failure("não foi possível identificar a versão do Deno")
    if _version_tuple(deno_version) < (2, 3, 0):
        return _js_preflight_failure(f"Deno {deno_version} é antigo; é necessário Deno >= 2.3")

    try:
        importlib.import_module("yt_dlp_ejs")
    except Exception as e:
        return _js_preflight_failure(f"yt-dlp-ejs não está disponível: {e}")

    try:
        installed_ejs = importlib.metadata.version("yt-dlp-ejs")
    except Exception:
        installed_ejs = None
    required_ejs = _required_ejs_version()

    if not installed_ejs:
        return _js_preflight_failure("não foi possível identificar a versão instalada de yt-dlp-ejs")
    if not required_ejs:
        return _js_preflight_failure("não foi possível validar a versão de yt-dlp-ejs exigida pelo yt-dlp")
    if installed_ejs != required_ejs:
        return _js_preflight_failure(
            f"yt-dlp-ejs {installed_ejs} é incompatível; yt-dlp requer {required_ejs}"
        )
    return None


def _present_js_runtime_failure(failure):
    print(f"  ✗ {failure.user_message}")
    print('  reparo  » execute REINSTALAR_YT-DLP-TUI.bat e confirme que o Deno está atualizado')


def _preflight(file_format="audio", auth_refresh_callback=None):
    js_failure = _check_js_runtime()
    if js_failure:
        _present_js_runtime_failure(js_failure)
        return False

    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        print("  ✗ FFmpeg não está disponível")
        print("  reparo  » execute REINSTALAR_YT-DLP-TUI.bat")
        return False

    cookie_path = active_cookie_file()

    if not cookie_path:
        if _invoke_auth_refresh(auth_refresh_callback, initial=True):
            cookie_path = active_cookie_file()
        if not cookie_path:
            print("  ✗ nenhuma sessão do YouTube foi configurada")
            return False

    inspection = inspect_cookie_file(cookie_path)
    if not inspection.get("valid"):
        reason = inspection.get("reason") or "cache de autenticação inválido"
        if _invoke_auth_refresh(auth_refresh_callback, reason):
            cookie_path = active_cookie_file()
            inspection = inspect_cookie_file(cookie_path) if cookie_path else {"valid": False}
        if not inspection.get("valid"):
            print("  ✗ não foi possível validar a sessão do YouTube")
            return False

    return True


def _classify_failure(error=None, logger=None):
    return classify_failure(error, logger.messages if logger else None)


def _retry_wait(failure, attempt, *, label="operação"):
    """Wait before a bounded application-level network retry."""
    decision = retry_decision(failure, attempt)
    if not decision.retry:
        return False
    next_attempt = attempt + 1
    if failure.kind is ErrorKind.RATE_LIMIT:
        reason = "limite temporário do YouTube"
    else:
        reason = "instabilidade de rede/CDN"
    print(
        f"  ↻ {reason} » nova tentativa {next_attempt}/{decision.max_attempts} "
        f"em {decision.delay_seconds:g}s ({label})"
    )
    time.sleep(decision.delay_seconds)
    return True


def _call_with_recovery(operation, auth_refresh_callback=None, *, label="operação"):
    """Run metadata/search work with bounded auth refresh and network retries."""
    network_attempt = 1
    auth_refreshes = 0
    while True:
        try:
            return operation()
        except AuthCacheExpired as e:
            if auth_refreshes >= MAX_AUTH_REFRESHES_PER_OPERATION:
                raise DownloadInterrupted("a sessão do YouTube continuou sendo recusada após a renovação") from e
            if _invoke_auth_refresh(auth_refresh_callback, str(e)):
                auth_refreshes += 1
                continue
            raise DownloadInterrupted("autenticação do YouTube não foi renovada") from e
        except ClassifiedFailureError as e:
            failure = e.classification
            if is_network_retryable(failure) and _retry_wait(failure, network_attempt, label=label):
                network_attempt += 1
                continue
            raise


def _playlist_id_from_url(url):
    try:
        query = parse_qs(urlparse(url).query)
        values = query.get("list")
        if values:
            return values[0]
    except Exception:
        pass
    return None


def _video_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def _sanitize_folder_name(value):
    try:
        from yt_dlp.utils import sanitize_filename

        clean = sanitize_filename(value or "playlist", restricted=True)
    except Exception:
        clean = "".join(c if c.isalnum() or c in " ._-()[]" else "_" for c in (value or "playlist"))
    return clean.strip(" .") or "playlist"


def _find_existing_playlist_dir(output_root, playlist_id, title=None):
    """Find an existing task directory without hiding a corrupt control file."""
    if not playlist_id or not os.path.isdir(output_root):
        return None

    expected_name = _sanitize_folder_name(title) if title else None

    try:
        root_state = load_control(output_root)
    except CorruptControlError:
        root_state = None
        if expected_name and os.path.basename(os.path.abspath(output_root)) == expected_name:
            return output_root
    if root_state and root_state.get("playlist", {}).get("id") == playlist_id:
        return output_root

    if expected_name:
        expected = os.path.join(output_root, expected_name)
        if os.path.isdir(expected):
            # A corrupt control in the expected playlist directory still belongs
            # to this task and must be reconstructed there rather than abandoned.
            if os.path.isfile(control_path(expected)):
                return expected

    try:
        names = os.listdir(output_root)
    except OSError:
        return None
    for name in names:
        candidate = os.path.join(output_root, name)
        if not os.path.isdir(candidate):
            continue
        try:
            state = load_control(candidate)
        except CorruptControlError:
            continue
        if state and state.get("playlist", {}).get("id") == playlist_id:
            return candidate
    return None


def _canonical_playlist_url(url):
    """Use the dedicated YouTube playlist endpoint when a playlist id is present."""
    playlist_id = _playlist_id_from_url(url)
    if not playlist_id:
        return url
    try:
        host = (urlparse(url).hostname or "").lower().rstrip(".")
    except Exception:
        return url
    if host == "youtu.be" or host == "youtube.com" or host.endswith(".youtube.com"):
        return f"https://www.youtube.com/playlist?list={playlist_id}"
    return url


def _extract_playlist(url):
    canonical_url = _canonical_playlist_url(url)
    last_info = None
    playlist_id = _playlist_id_from_url(url) or "playlist"
    title = f"playlist-{playlist_id}"
    expected_count = None

    for attempt in range(1, MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS + 1):
        logger = CaptureLogger()
        # The first two attempts use the cheap flat playlist extractor. If the
        # YouTube tab extractor keeps returning an impossible empty entry list,
        # the final bounded attempt asks yt-dlp for full metadata without
        # downloading media. This is slower, so it is fallback-only.
        extract_flat = attempt < MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": extract_flat,
            "noplaylist": False,
            "ignoreerrors": True,
            **_youtube_opts(logger),
        }
        if not extract_flat:
            ydl_opts["skip_download"] = True

        # Preserve the existing behavior on the first attempt. Only after an
        # impossible empty result do we strip watch/index context and target the
        # playlist endpoint directly. This reduces regression risk for special
        # YouTube playlist-like URLs while still recovering the observed bug.
        extraction_url = url if attempt == 1 else canonical_url

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(extraction_url, download=False)
        except Exception as e:
            failure = _classify_failure(e, logger)
            if failure.kind is ErrorKind.AUTH_EXPIRED:
                raise AuthCacheExpired(failure.technical_message) from e
            raise ClassifiedFailureError(failure) from e

        if info:
            last_info = info
            playlist_id = info.get("id") or playlist_id
            title = info.get("title") or title
            expected_count = info.get("playlist_count") or info.get("n_entries") or expected_count
            entries = info.get("entries") or []
            if entries:
                break
        else:
            failure = _classify_failure(None, logger)
            if failure.kind is ErrorKind.AUTH_EXPIRED:
                raise AuthCacheExpired(failure.technical_message)
            if failure.kind is not ErrorKind.UNKNOWN:
                raise ClassifiedFailureError(failure)
            entries = []

        if attempt < MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS:
            print(
                f"  ↻ a lista de vídeos veio vazia; tentando extrair novamente "
                f"({attempt + 1}/{MAX_EMPTY_PLAYLIST_EXTRACTION_ATTEMPTS})"
            )
            time.sleep(EMPTY_PLAYLIST_RETRY_DELAY_SECONDS)
    else:
        raise EmptyPlaylistExtractionError(playlist_id, title, expected_count)

    if not last_info or not entries:
        raise EmptyPlaylistExtractionError(playlist_id, title, expected_count)

    fresh_items = []
    for index, entry in enumerate(entries, 1):
        if not entry:
            # ``ignoreerrors=True`` can yield ``None`` for several reasons,
            # including temporary extractor/network failures. A missing flat
            # entry is therefore NOT sufficient evidence that the video was
            # permanently removed/private.
            fresh_items.append({
                "index": index,
                "video_id": f"unresolved-{index}",
                "title": "Vídeo não resolvido",
                "url": None,
                "available": True,
                "status": "unresolved",
                "attempts": 0,
                "retry_count": 0,
                "last_retry_at": None,
                "started_at": None,
                "completed_at": None,
                "final_file": None,
                "last_error": "não foi possível resolver esta entrada da playlist; tente novamente mais tarde",
                "last_error_kind": ErrorKind.UNKNOWN.value,
                "audit_status": "not_run",
                "audit_at": None,
                "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
            })
            continue

        video_id = entry.get("id")
        entry_url = entry.get("url") or entry.get("webpage_url")
        if video_id and (not entry_url or not str(entry_url).startswith("http")):
            entry_url = _video_url(video_id)

        resolved = bool(video_id and entry_url)
        fresh_items.append({
            "index": index,
            "video_id": video_id or f"unresolved-{index}",
            "title": entry.get("title") or "Sem título",
            "url": entry_url if resolved else None,
            "available": True,
            "status": "pending" if resolved else "unresolved",
            "attempts": 0,
            "retry_count": 0,
            "last_retry_at": None,
            "started_at": None,
            "completed_at": None,
            "final_file": None,
            "last_error": None if resolved else "metadados insuficientes para resolver esta entrada da playlist",
            "last_error_kind": None if resolved else ErrorKind.UNKNOWN.value,
            "audit_status": "not_run",
            "audit_at": None,
            "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
        })

    return {"id": playlist_id, "title": title, "entries": fresh_items}


def _media_candidates(folder):
    candidates = []
    if not os.path.isdir(folder):
        return candidates
    for root, _, files in os.walk(folder):
        for name in files:
            lower = name.lower()
            if lower.endswith((".part", ".ytdl", ".temp", ".tmp")):
                continue
            path = os.path.join(root, name)
            ext = os.path.splitext(lower)[1]
            if ext in MEDIA_EXTENSIONS:
                candidates.append(path)
    return candidates


def _find_existing_final_by_id(task_dir, video_id):
    token = f"[{video_id}]"
    try:
        for name in os.listdir(task_dir):
            path = os.path.join(task_dir, name)
            if not os.path.isfile(path):
                continue
            if token in name and os.path.splitext(name.lower())[1] in MEDIA_EXTENSIONS:
                # A media-looking symlink/junction must not make recovery trust
                # content outside the playlist directory.
                safe = _safe_final_path(task_dir, name)
                if safe:
                    return safe
    except OSError:
        pass
    return None




def _title_match_key(value):
    """Conservative title key used only for crash/control recovery.

    Final filenames are produced by yt-dlp from ``%(title)s`` with normal
    (non-restricted) sanitization.  Filesystems may force substitutions for a
    handful of illegal characters, so recovery compares Unicode-normalized
    alphanumeric content and only accepts a unique match.
    """
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(ch for ch in normalized if ch.isalnum())


def _find_existing_final_for_item(task_dir, item):
    """Recover either legacy ``[video_id]`` files or new title-only files."""
    legacy = _find_existing_final_by_id(task_dir, item.get("video_id"))
    if legacy:
        return legacy

    wanted = _title_match_key(item.get("title"))
    if not wanted:
        return None
    matches = []
    try:
        for name in os.listdir(task_dir):
            if os.path.splitext(name.lower())[1] not in MEDIA_EXTENSIONS:
                continue
            path = _safe_final_path(task_dir, name)
            if not path or not os.path.isfile(path):
                continue
            stem = os.path.splitext(name)[0]
            if _title_match_key(stem) == wanted:
                matches.append(path)
    except OSError:
        return None
    return matches[0] if len(matches) == 1 else None


def _final_destination(task_dir, staged_file, state, item):
    """Keep the YouTube title as filename and only disambiguate real collisions."""
    name = os.path.basename(staged_file)
    other_names = {
        str(other.get("final_file") or "").casefold()
        for other in state.get("items", [])
        if other is not item and other.get("final_file")
    }
    if name.casefold() not in other_names:
        return os.path.join(task_dir, name)

    stem, ext = os.path.splitext(name)
    index = 2
    while True:
        candidate = f"{stem} ({index}){ext}"
        if candidate.casefold() not in other_names and not os.path.exists(os.path.join(task_dir, candidate)):
            return os.path.join(task_dir, candidate)
        index += 1


def _safe_final_path(task_dir, final_name):
    """Resolve a control-recorded final filename only if it stays in task_dir."""
    if not final_name or not isinstance(final_name, str):
        return None
    if os.path.isabs(final_name) or os.path.basename(final_name) != final_name:
        return None
    try:
        root = os.path.realpath(task_dir)
        target = os.path.realpath(os.path.join(task_dir, final_name))
        if os.path.commonpath([root, target]) != root:
            return None
    except (OSError, ValueError):
        return None
    return os.path.join(task_dir, final_name)

def _quick_file_check(path):
    try:
        return os.path.isfile(path) and os.path.getsize(path) > 1024
    except OSError:
        return False


def _integrity_check(path, ffmpeg_exe=None):
    """Decode the complete media stream and fail on corruption/truncation."""
    if not _quick_file_check(path):
        return False, "arquivo ausente ou vazio"

    ffmpeg_exe = ffmpeg_exe or _ffmpeg_exe()
    if not ffmpeg_exe:
        # Defensive fallback for internal recovery calls. Normal downloads are
        # blocked by preflight when FFmpeg is unavailable, and the mandatory
        # final playlist audit refuses to claim success without FFmpeg.
        return True, "verificação básica (FFmpeg indisponível)"

    cmd = [
        ffmpeg_exe,
        "-hide_banner",
        "-nostdin",
        "-v", "error",
        "-xerror",
        "-i", path,
        "-map", "0:v?",
        "-map", "0:a?",
        "-f", "null",
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            timeout=None,
        )
    except Exception as e:
        return False, str(e)

    if proc.returncode == 0:
        return True, None
    message = (proc.stderr or "arquivo reprovado pelo FFmpeg").strip()
    if len(message) > 300:
        message = message[-300:]
    return False, message


def _is_link_like(path):
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    try:
        return bool(isjunction and isjunction(path))
    except OSError:
        return False


def _safe_delete(path, allowed_root):
    """Delete only a path lexically and physically contained by ``allowed_root``.

    Link-like paths are removed as links/junctions and are never traversed. This
    prevents a pre-existing staging symlink/junction from redirecting cleanup
    outside the user-selected task directory.
    """
    if not path:
        return False
    try:
        root = os.path.abspath(allowed_root)
        target = os.path.abspath(path)
        if os.path.commonpath([root, target]) != root:
            return False

        if _is_link_like(target):
            if os.path.islink(target):
                os.unlink(target)
            else:
                os.rmdir(target)
            return True

        root_real = os.path.realpath(root)
        target_real = os.path.realpath(target)
        if os.path.commonpath([root_real, target_real]) != root_real:
            return False

        if os.path.isdir(target):
            shutil.rmtree(target)
            return True
        if os.path.isfile(target):
            os.remove(target)
            return True
    except (OSError, ValueError):
        return False
    return False


_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

def _progress_percent(data):
    """Return a robust numeric progress percentage from a yt-dlp hook payload.

    Prefer numeric byte counters because ``_percent_str`` may contain ANSI
    control sequences depending on terminal/color settings.  Fall back to
    fragment counters, then to a sanitized textual percentage.
    """
    downloaded = data.get("downloaded_bytes")
    total = data.get("total_bytes") or data.get("total_bytes_estimate")
    try:
        if downloaded is not None and total is not None and float(total) > 0:
            value = (float(downloaded) / float(total)) * 100.0
            return round(max(0.0, min(value, 100.0)), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    fragment_index = data.get("fragment_index")
    fragment_count = data.get("fragment_count")
    try:
        if fragment_index is not None and fragment_count is not None and float(fragment_count) > 0:
            value = (float(fragment_index) / float(fragment_count)) * 100.0
            return round(max(0.0, min(value, 100.0)), 2)
    except (TypeError, ValueError, ZeroDivisionError):
        pass

    raw = _ANSI_ESCAPE_RE.sub("", str(data.get("_percent_str", ""))).strip().replace(",", ".")
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*%?", raw)
    if match:
        try:
            return max(0.0, min(float(match.group(1)), 100.0))
        except (TypeError, ValueError):
            pass
    return 0.0


class SimpleProgressTracker:
    def __init__(self):
        self.last_title = None

    def __call__(self, d):
        status = d.get("status")
        info = d.get("info_dict", {})
        title = info.get("title", "Sem título")
        if status == "downloading":
            percent = _progress_percent(d)
            if title != self.last_title:
                display = title[:52] + ".." if len(title) > 52 else title
                print(f"\n  {display}")
                self.last_title = title
            width = 20
            filled = int(width * max(0.0, min(percent, 100.0)) / 100)
            bar = "█" * filled + "░" * (width - filled)
            print(f"\r  {bar} {percent:.1f}%", end="", flush=True)
        elif status == "finished":
            print("\r  " + "█" * 20 + " 100% ✓", flush=True)


class ItemProgressTracker:
    def __init__(self, task_dir, state, item):
        self.task_dir = task_dir
        self.state = state
        self.item = item
        self.last_save = 0.0

    def __call__(self, d):
        status = d.get("status")
        if status == "downloading":
            percent = _progress_percent(d)

            self.item["status"] = "downloading"
            self.item["progress"] = {
                "percent": round(percent, 2),
                "downloaded_bytes": d.get("downloaded_bytes") or 0,
                "total_bytes": d.get("total_bytes") or d.get("total_bytes_estimate"),
            }

            width = 20
            filled = int(width * max(0.0, min(percent, 100.0)) / 100)
            bar = "█" * filled + "░" * (width - filled)
            title = self.item.get("title", "Sem título")
            display_title = title[:40] + ".." if len(title) > 40 else title
            print(f"\r  [{self.item.get('index')}] {display_title}  {bar} {percent:.1f}%", end="", flush=True)

            now = time.monotonic()
            if now - self.last_save >= 1.0:
                save_control(self.task_dir, self.state)
                self.last_save = now

        elif status == "finished":
            self.item["status"] = "processing"
            self.item["progress"]["percent"] = 100.0
            save_control(self.task_dir, self.state)
            print("", flush=True)


def _build_download_opts(stage, file_format, quality, tracker, logger):
    ydl_opts = {
        "outtmpl": os.path.join(stage, "%(title)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [tracker] if tracker else [],
        "continuedl": False,
        "nopart": False,
        "overwrites": True,
        "restrictfilenames": False,
        "fixup": "never",
        **_youtube_opts(logger),
    }

    ffmpeg_exe = _ffmpeg_exe()
    if ffmpeg_exe:
        ydl_opts["ffmpeg_location"] = ffmpeg_exe

    if file_format == "audio":
        ydl_opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
    else:
        if quality == "best":
            f_str = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b"
        else:
            f_str = (
                f"bv*[height<={quality}][ext=mp4]+ba[ext=m4a]/"
                f"bv*[height<={quality}]+ba/"
                f"b[height<={quality}]/b"
            )
        ydl_opts.update({"format": f_str, "merge_output_format": "mp4"})
    return ydl_opts


def _download_item_to_stage(item, task_dir, state, file_format, quality):
    """Download one playlist item with bounded full-item network retries."""
    video_id = item["video_id"]
    network_attempt = 1

    while True:
        stage = stage_dir(task_dir, video_id)
        cleanup_stage(task_dir, video_id)
        os.makedirs(stage, exist_ok=True)

        item["status"] = "downloading"
        item["attempts"] = int(item.get("attempts") or 0) + 1
        item["started_at"] = now_iso()
        item["completed_at"] = None
        item["last_error"] = None
        item["last_error_kind"] = None
        item.setdefault("retry_count", 0)
        item.setdefault("last_retry_at", None)
        item["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
        save_control(task_dir, state)

        logger = CaptureLogger()
        tracker = ItemProgressTracker(task_dir, state, item)
        ydl_opts = _build_download_opts(stage, file_format, quality, tracker, logger)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([item["url"]])
        except KeyboardInterrupt:
            cleanup_stage(task_dir, video_id)
            item["status"] = "pending"
            item["last_error"] = "download interrompido pelo usuário"
            item["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
            save_control(task_dir, state)
            raise
        except Exception as e:
            cleanup_stage(task_dir, video_id)
            failure = _classify_failure(e, logger)
            item["last_error_kind"] = failure.kind.value
            item["last_error"] = failure.technical_message
            item["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}

            if failure.kind is ErrorKind.AUTH_EXPIRED:
                item["status"] = "waiting_auth"
                save_control(task_dir, state)
                raise AuthCacheExpired(failure.technical_message) from e

            decision = retry_decision(failure, network_attempt)
            if decision.retry:
                item["status"] = "retry_wait"
                item["retry_count"] = int(item.get("retry_count") or 0) + 1
                item["last_retry_at"] = now_iso()
                save_control(task_dir, state)
                try:
                    _retry_wait(failure, network_attempt, label=f"item {item.get('index', '?')}")
                except KeyboardInterrupt:
                    cleanup_stage(task_dir, video_id)
                    item["status"] = "pending"
                    save_control(task_dir, state)
                    raise
                network_attempt += 1
                continue

            if failure.kind is ErrorKind.PERMANENT_UNAVAILABLE:
                item["available"] = False
                item["status"] = "unavailable"
                item["final_file"] = None
                item["last_error_kind"] = ErrorKind.PERMANENT_UNAVAILABLE.value
                item["last_error"] = technical_summary(failure, limit=500)
                save_control(task_dir, state)
                print(f"\n  aviso » {failure.user_message}")
                return None

            item["status"] = "failed"
            save_control(task_dir, state)
            if is_network_retryable(failure):
                print(f"\n  ✗ {exhausted_message(failure)}")
            else:
                print(f"\n  ✗ {failure.user_message}")
            if failure.kind is ErrorKind.UNKNOWN:
                print(f"  detalhe » {technical_summary(failure)}")
            return None

        candidates = _media_candidates(stage)
        if not candidates:
            cleanup_stage(task_dir, video_id)
            item["status"] = "failed"
            item["last_error"] = "yt-dlp terminou sem gerar um arquivo de mídia final"
            item["last_error_kind"] = ErrorKind.UNKNOWN.value
            save_control(task_dir, state)
            return None

        # After yt-dlp post-processing there should be a single final media file.
        # If more than one remains, the largest one is the safest final artifact.
        staged_file = max(candidates, key=lambda p: os.path.getsize(p))
        final_path = _final_destination(task_dir, staged_file, state, item)

        # This item is explicitly pending/retrying, so a same-named old file must
        # not silently satisfy a different requested quality/mode. Crash recovery
        # already reconciles valid completed files before we reach this point.
        if os.path.isfile(final_path):
            _safe_delete(final_path, task_dir)

        os.replace(staged_file, final_path)
        cleanup_stage(task_dir, video_id)

        item["status"] = "completed"
        item["completed_at"] = now_iso()
        item["final_file"] = os.path.basename(final_path)
        item["last_error"] = None
        item["last_error_kind"] = None
        size = os.path.getsize(final_path) if os.path.isfile(final_path) else 0
        item["progress"] = {"percent": 100.0, "downloaded_bytes": size, "total_bytes": size}
        save_control(task_dir, state)
        return final_path

def _recover_incomplete_state(task_dir, state):
    """Clean stale partials from a previous crash and restore resumable statuses."""
    changed = False
    for item in state.get("items", []):
        if not item.get("available", True):
            item["status"] = "unavailable"
            continue

        final_name = item.get("final_file")
        final_path = _safe_final_path(task_dir, final_name)
        if final_name and not final_path:
            item["final_file"] = None
            item["status"] = "pending"
            item["last_error"] = "caminho de arquivo final inválido no controle"
            item["last_error_kind"] = ErrorKind.LOCAL_IO.value
            changed = True
        if not final_path:
            recovered = _find_existing_final_for_item(task_dir, item)
            if recovered:
                item["final_file"] = os.path.basename(recovered)
                final_path = recovered
                changed = True

        if item.get("status") == "completed":
            cleanup_stage(task_dir, item.get("video_id"))
            if not final_path or not _quick_file_check(final_path):
                item["status"] = "pending"
                item["final_file"] = None
                item["last_error"] = "arquivo final não encontrado ao retomar"
                changed = True
            continue

        # Any item that was downloading/processing/waiting when the process died
        # is restarted from zero. Its isolated staging directory is deleted first.
        cleanup_stage(task_dir, item.get("video_id"))
        if final_path and os.path.isfile(final_path):
            ok, _ = _integrity_check(final_path)
            if ok:
                item["status"] = "completed"
                item["completed_at"] = item.get("completed_at") or now_iso()
                item["last_error"] = None
                item["last_error_kind"] = None
                changed = True
                continue
            _safe_delete(final_path, task_dir)
            item["final_file"] = None

        if item.get("status") in {"downloading", "processing", "waiting_auth", "retry_wait", "retrying", "failed", "interrupted"}:
            item["status"] = "pending"
            item["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
            changed = True

    if changed:
        save_control(task_dir, state)


def _audit_playlist(task_dir, state):
    items = state.get("items", [])
    if not items:
        state["status"] = "invalid_empty_playlist"
        state["audit"] = {
            "status": "blocked_empty_playlist",
            "last_run_at": now_iso(),
            "checked": 0,
            "ok": 0,
            "failed": 0,
            "unavailable": 0,
        }
        save_control(task_dir, state)
        raise EmptyPlaylistExtractionError(
            state.get("playlist", {}).get("id"),
            state.get("playlist", {}).get("title"),
            None,
        )

    available_items = [i for i in items if i.get("available", True)]
    unavailable_items = [i for i in state.get("items", []) if not i.get("available", True)]
    ffmpeg = _ffmpeg_exe()
    if not ffmpeg:
        # Never claim a full integrity audit when the decoder is unavailable,
        # and never delete media merely because the audit tool disappeared.
        state["audit"] = {
            "status": "blocked",
            "last_run_at": now_iso(),
            "checked": 0,
            "ok": 0,
            "failed": 0,
            "unavailable": len(unavailable_items),
        }
        save_control(task_dir, state)
        raise RuntimeError("FFmpeg indisponível para auditoria; arquivos preservados")
    bad = []
    ok_count = 0

    for item in unavailable_items:
        item["audit_status"] = "skipped_unavailable"
        item["audit_at"] = now_iso()

    state["audit"] = {
        "status": "running",
        "last_run_at": now_iso(),
        "checked": 0,
        "ok": 0,
        "failed": 0,
        "unavailable": len(unavailable_items),
    }
    save_control(task_dir, state)

    print("\n  auditoria final » verificando integridade de todos os arquivos disponíveis")
    for n, item in enumerate(available_items, 1):
        final_name = item.get("final_file")
        path = _safe_final_path(task_dir, final_name)
        if final_name and not path:
            item["last_error_kind"] = ErrorKind.LOCAL_IO.value
        title = item.get("title", "Sem título")
        display = title[:52] + ".." if len(title) > 52 else title
        print(f"  [{n}/{len(available_items)}] {display} ... ", end="", flush=True)

        if item.get("status") != "completed" or not path:
            valid, reason = False, "item não está marcado como concluído"
        else:
            valid, reason = _integrity_check(path, ffmpeg)

        state["audit"]["checked"] += 1
        if valid:
            ok_count += 1
            state["audit"]["ok"] += 1
            item["audit_status"] = "ok"
            item["audit_at"] = now_iso()
            print("OK")
        else:
            state["audit"]["failed"] += 1
            item["audit_status"] = "failed"
            item["audit_at"] = now_iso()
            item["last_error"] = f"auditoria: {reason}"
            if path and os.path.isfile(path):
                _safe_delete(path, task_dir)
            item["final_file"] = None
            if item.get("url"):
                item["status"] = "pending"
            else:
                # No URL means the playlist entry was not resolved.  This is
                # not evidence of permanent unavailability and cannot be
                # repaired by calling yt-dlp with a null URL.
                item["status"] = "unresolved"
                item["last_error_kind"] = ErrorKind.UNKNOWN.value
            item["progress"] = {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None}
            cleanup_stage(task_dir, item.get("video_id"))
            bad.append(item)
            print("FALHOU")
        save_control(task_dir, state)

    if bad:
        state["audit"]["status"] = "failed"
    elif unavailable_items:
        state["audit"]["status"] = "passed_with_unavailable"
    else:
        state["audit"]["status"] = "passed"
    save_control(task_dir, state)
    return bad, ok_count


def _prepare_playlist_state(output_root, metadata, source_url, file_format, quality):
    playlist_id = metadata["id"]
    existing_dir = _find_existing_playlist_dir(output_root, playlist_id, metadata.get("title"))
    task_dir = existing_dir or os.path.join(output_root, _sanitize_folder_name(metadata["title"]))
    os.makedirs(task_dir, exist_ok=True)

    rebuilt_from_corrupt = False
    try:
        state = load_control(task_dir)
    except CorruptControlError as e:
        preserved = preserve_corrupt_control(task_dir)
        print("  aviso    » o arquivo de controle estava corrompido; reconstruindo o progresso")
        if preserved:
            print(f"  backup   » {preserved}")
        state = None
        rebuilt_from_corrupt = True

    mode = {"format": file_format, "quality": quality}
    if state and (
        state.get("playlist", {}).get("id") != playlist_id
        or state.get("mode") != mode
    ):
        backup_control(task_dir)
        state = None

    if state:
        if state.get("schema_version") != SCHEMA_VERSION:
            # Preserve the exact v2 file before migrating its in-memory state.
            backup_control(task_dir)
            try:
                state, migrated = migrate_control_state(state)
            except ValueError as e:
                print(f"  aviso    » controle incompatível ({e}); reconstruindo o progresso")
                state = None
            else:
                if migrated:
                    print(f"  controle » migrado para schema {SCHEMA_VERSION} sem perder o progresso")

    if not state:
        state = make_playlist_state(
            playlist_id,
            metadata["title"],
            source_url,
            file_format,
            quality,
            metadata["entries"],
        )
    else:
        state["playlist"]["title"] = metadata["title"]
        state["playlist"]["source_url"] = source_url
        merge_playlist_items(state, metadata["entries"])
        state["status"] = "in_progress"

    save_control(task_dir, state)
    # This also reconciles a reconstructed control with media already present:
    # files are found by video ID and integrity-checked before becoming completed.
    _recover_incomplete_state(task_dir, state)
    if rebuilt_from_corrupt:
        save_control(task_dir, state)
    return task_dir, state


def _download_playlist(url, output_root, file_format, quality, auth_refresh_callback):
    metadata = _call_with_recovery(lambda: _extract_playlist(url), auth_refresh_callback, label="playlist")
    task_dir, state = _prepare_playlist_state(output_root, metadata, url, file_format, quality)

    print(f"\n  playlist » {metadata['title']}")
    print(f"  pasta    » {task_dir}")
    print(f"  controle » {os.path.join(task_dir, CONTROL_FILENAME)}")

    total = len([i for i in state.get("items", []) if i.get("available", True)])
    already = len([i for i in state.get("items", []) if i.get("status") == "completed"])
    if already:
        print(f"  retomada » {already}/{total} já concluídos; continuando do primeiro pendente")

    downloaded_files = []
    for item in state.get("items", []):
        if not item.get("available", True) or item.get("status") == "completed":
            continue
        if not item.get("url"):
            item["status"] = "unresolved"
            item["last_error_kind"] = ErrorKind.UNKNOWN.value
            item["last_error"] = item.get("last_error") or "entrada da playlist sem URL resolvida"
            save_control(task_dir, state)
            continue

        auth_refreshes = 0
        while True:
            try:
                result = _download_item_to_stage(item, task_dir, state, file_format, quality)
            except AuthCacheExpired as e:
                # The current item's staging directory was already deleted. After
                # the new cache is imported, the same item restarts from zero.
                if auth_refreshes < MAX_AUTH_REFRESHES_PER_OPERATION and _invoke_auth_refresh(auth_refresh_callback, str(e)):
                    auth_refreshes += 1
                    item["status"] = "pending"
                    item["last_error"] = None
                    item["last_error_kind"] = None
                    save_control(task_dir, state)
                    continue
                state["status"] = "interrupted_auth"
                save_control(task_dir, state)
                if auth_refreshes >= MAX_AUTH_REFRESHES_PER_OPERATION:
                    print("  ✗ a sessão do YouTube continuou sendo recusada após a renovação")
                return downloaded_files
            except KeyboardInterrupt:
                state["status"] = "interrupted"
                save_control(task_dir, state)
                raise

            if result:
                downloaded_files.append(result)
            # A non-auth failure is recorded but does not sacrifice the rest of
            # the playlist. The final repair pass will retry it once.
            break

    # First complete integrity audit. Any missing/corrupt file is deleted and
    # returned to pending, then automatically redownloaded once.
    bad, _ = _audit_playlist(task_dir, state)
    if bad:
        print(f"\n  reparo automático » {len(bad)} item(ns) serão baixados novamente")
        for item in list(bad):
            if not item.get("url"):
                item["status"] = "unresolved"
                item["last_error_kind"] = ErrorKind.UNKNOWN.value
                item["last_error"] = item.get("last_error") or "entrada da playlist sem URL resolvida"
                save_control(task_dir, state)
                continue
            auth_refreshes = 0
            while True:
                try:
                    result = _download_item_to_stage(item, task_dir, state, file_format, quality)
                except AuthCacheExpired as e:
                    if auth_refreshes < MAX_AUTH_REFRESHES_PER_OPERATION and _invoke_auth_refresh(auth_refresh_callback, str(e)):
                        auth_refreshes += 1
                        item["status"] = "pending"
                        item["last_error"] = None
                        item["last_error_kind"] = None
                        save_control(task_dir, state)
                        continue
                    state["status"] = "interrupted_auth"
                    save_control(task_dir, state)
                    if auth_refreshes >= MAX_AUTH_REFRESHES_PER_OPERATION:
                        print("  ✗ a sessão do YouTube continuou sendo recusada após a renovação")
                    return downloaded_files
                if result:
                    downloaded_files.append(result)
                break

        bad, _ = _audit_playlist(task_dir, state)

    # Recalculate after repair: an item can become permanently unavailable while
    # the task is running, so the initial playlist count is no longer authoritative.
    available_total = len([i for i in state.get("items", []) if i.get("available", True)])
    unavailable = len([i for i in state.get("items", []) if not i.get("available", True)])
    failed = len(bad)
    if failed:
        state["status"] = "incomplete"
        print(f"\n  ✗ auditoria final » {failed} arquivo(s) ainda faltando/corrompido(s)")
        print("  execute a mesma playlist novamente para tentar somente os pendentes")
    elif unavailable:
        state["status"] = "completed_with_unavailable"
        print(f"\n  ✓ auditoria final » {available_total}/{available_total} vídeos disponíveis íntegros")
        print(f"  aviso    » {unavailable} vídeo(s) da playlist estavam indisponíveis")
    else:
        state["status"] = "completed"
        print(f"\n  ✓ auditoria final » {available_total}/{available_total} vídeos presentes e íntegros")

    save_control(task_dir, state)
    return downloaded_files


def _download_single(url, output_root, file_format, quality, auth_refresh_callback):
    # Single videos use the same isolated staging strategy, so auth/network
    # interruptions never leave a corrupt final file in the user's folder.
    stage_root = os.path.join(output_root, ".yt-dlp-tui-single")
    _safe_delete(stage_root, output_root)
    os.makedirs(stage_root, exist_ok=True)
    network_attempt = 1
    auth_refreshes = 0

    while True:
        logger = CaptureLogger()
        ydl_opts = _build_download_opts(stage_root, file_format, quality, SimpleProgressTracker(), logger)
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except KeyboardInterrupt:
            _safe_delete(stage_root, output_root)
            raise
        except Exception as e:
            _safe_delete(stage_root, output_root)
            failure = _classify_failure(e, logger)

            if failure.kind is ErrorKind.AUTH_EXPIRED:
                if (
                    auth_refresh_callback
                    and auth_refreshes < MAX_AUTH_REFRESHES_PER_OPERATION
                    and _invoke_auth_refresh(auth_refresh_callback, failure.technical_message)
                ):
                    auth_refreshes += 1
                    os.makedirs(stage_root, exist_ok=True)
                    continue
                if auth_refreshes >= MAX_AUTH_REFRESHES_PER_OPERATION:
                    print("  ✗ a sessão do YouTube continuou sendo recusada após a renovação")
                elif not auth_refresh_callback:
                    print(f"  ✗ {failure.user_message}")
                return []

            decision = retry_decision(failure, network_attempt)
            if decision.retry:
                try:
                    _retry_wait(failure, network_attempt, label="vídeo")
                except KeyboardInterrupt:
                    _safe_delete(stage_root, output_root)
                    raise
                network_attempt += 1
                os.makedirs(stage_root, exist_ok=True)
                continue

            if is_network_retryable(failure):
                print(f"  ✗ {exhausted_message(failure)}")
            else:
                print(f"  ✗ {failure.user_message}")
            if failure.kind is ErrorKind.UNKNOWN:
                print(f"  detalhe » {technical_summary(failure)}")
            return []

        candidates = _media_candidates(stage_root)
        if not candidates:
            _safe_delete(stage_root, output_root)
            print("  ✗ erro » o download terminou sem arquivo final")
            return []

        final_files = []
        for staged in candidates:
            final_path = os.path.join(output_root, os.path.basename(staged))
            if os.path.exists(final_path):
                ok, _ = _integrity_check(final_path)
                if ok:
                    final_files.append(final_path)
                    continue
                _safe_delete(final_path, output_root)
            os.replace(staged, final_path)
            final_files.append(final_path)
        _safe_delete(stage_root, output_root)
        return final_files

def download_media(
    url,
    output_path,
    is_playlist=False,
    file_format="audio",
    quality="best",
    auth_refresh_callback=None,
):
    if not output_path:
        print("  ✗ erro » nenhuma pasta de download foi selecionada nesta execução")
        return []
    if not _preflight(file_format, auth_refresh_callback):
        return []

    output_path = os.path.abspath(output_path)
    os.makedirs(output_path, exist_ok=True)

    try:
        if is_playlist:
            return _download_playlist(url, output_path, file_format, quality, auth_refresh_callback)
        return _download_single(url, output_path, file_format, quality, auth_refresh_callback)
    except DownloadInterrupted as e:
        print(f"  ✗ interrompido » {e}")
        return []
    except KeyboardInterrupt:
        print("\n  download interrompido; progresso salvo para retomada")
        raise
    except EmptyPlaylistExtractionError as e:
        print("  ✗ não consegui obter os vídeos da playlist")
        print("  nenhum download foi iniciado; tente novamente em alguns instantes")
        if e.expected_count:
            print(f"  detalhe » o YouTube informou {e.expected_count} item(ns), mas a extração retornou 0")
        return []
    except Exception as e:
        # Authentication recovery is owned by the metadata/item layers above.
        # Do not recursively re-enter download_media here: that could create an
        # unbounded call stack if a future auth error escaped those layers.
        failure = _classify_failure(e)
        print(f"  ✗ {failure.user_message}")
        if failure.kind is ErrorKind.UNKNOWN:
            print(f"  detalhe » {technical_summary(failure)}")
        return []


def smart_download(
    url,
    output_path,
    file_format="audio",
    quality="best",
    auth_refresh_callback=None,
):
    is_playlist = "list=" in url
    return download_media(
        url,
        is_playlist=is_playlist,
        file_format=file_format,
        quality=quality,
        output_path=output_path,
        auth_refresh_callback=auth_refresh_callback,
    )


def fetch_search_results(query, n=3, auth_refresh_callback=None):
    if not _preflight("audio", auth_refresh_callback):
        return []

    def operation():
        logger = CaptureLogger()
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "noplaylist": False,
            **_youtube_opts(logger),
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
        except Exception as e:
            failure = _classify_failure(e, logger)
            if failure.kind is ErrorKind.AUTH_EXPIRED:
                raise AuthCacheExpired(failure.technical_message) from e
            raise ClassifiedFailureError(failure) from e
        return [
            {
                "id": e.get("id"),
                "title": e.get("title", "Sem título"),
                "duration": e.get("duration"),
                "uploader": e.get("uploader") or e.get("channel") or "?",
            }
            for e in info.get("entries", [])
            if e
        ]

    try:
        return _call_with_recovery(operation, auth_refresh_callback, label="busca")
    except DownloadInterrupted as e:
        print(f"  ✗ busca interrompida » {e}")
        return []
    except Exception as e:
        failure = _classify_failure(e)
        print(f"  ✗ {failure.user_message}")
        if failure.kind is ErrorKind.UNKNOWN:
            print(f"  detalhe » {technical_summary(failure)}")
        return []
