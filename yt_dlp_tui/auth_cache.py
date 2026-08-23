"""Private, user-managed YouTube authentication cache.

YT-DLP TUI never ships a cookies file.  The user selects a Netscape-format
export when needed; only Google/YouTube root-domain cookies are copied into a
private managed cache under the user's local application-data directory.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time


ALLOWED_COOKIE_DOMAINS = (
    "youtube.com",
    "youtube-nocookie.com",
    "google.com",
    "googlevideo.com",
)

AUTH_COOKIE_NAMES = {
    "SID",
    "HSID",
    "SSID",
    "APISID",
    "SAPISID",
    "LOGIN_INFO",
    "__Secure-1PSID",
    "__Secure-3PSID",
    "__Secure-1PAPISID",
    "__Secure-3PAPISID",
}


def cache_dir():
    """Return the private writable directory for the active auth cache."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "YT-DLP-TUI")
    return os.path.join(os.path.expanduser("~"), ".yt-dlp-tui")


def managed_cookie_file():
    return os.path.join(cache_dir(), "cookies.txt")


def _harden_cache_permissions(path, *, directory=False):
    """Best-effort restriction for the managed authentication cache.

    POSIX permissions are deterministic.  On Windows, ``os.chmod`` does not
    provide real ACL isolation, so use the built-in ``icacls`` utility when it
    is available.  Failure to harden is non-fatal because Windows environments
    can have custom ACL/domain policies, but the source cookies are never made
    more permissive by this function.
    """
    try:
        os.chmod(path, 0o700 if directory else 0o600)
    except OSError:
        pass

    if os.name != "nt":
        return

    icacls = shutil.which("icacls")
    username = os.environ.get("USERNAME")
    domain = os.environ.get("USERDOMAIN")
    if not icacls or not username:
        return
    principal = f"{domain}\\{username}" if domain else username
    grant = f"{principal}:(OI)(CI)F" if directory else f"{principal}:F"
    try:
        subprocess.run(
            [icacls, path, "/inheritance:r", "/grant:r", grant],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass




def active_cookie_file():
    """Resolve the only persistent cookie cache used by YT-DLP TUI.

    User-selected exports are imported into the private managed location first;
    yt-dlp never reads a project-bundled file or an arbitrary persistent source.
    The environment variable is set by the app to the managed path for process
    integration, but it is not accepted as an alternate persistence location.
    """
    managed = managed_cookie_file()
    if os.path.isfile(managed):
        os.environ["YT_DLP_TUI_COOKIES"] = managed
        return managed
    os.environ.pop("YT_DLP_TUI_COOKIES", None)
    return None


def _normalized_domain(raw_domain):
    prefix = "#HttpOnly_"
    if raw_domain.startswith(prefix):
        raw_domain = raw_domain[len(prefix):]
    return raw_domain.lstrip(".").lower()


def _domain_allowed(domain):
    # Keep only root-domain cookies relevant to YouTube authentication.  This
    # intentionally excludes Gmail/Drive/Calendar/etc. subdomain sessions.
    return domain in ALLOWED_COOKIE_DOMAINS


def inspect_cookie_file(path):
    """Validate a Netscape cookie export without exposing cookie values."""
    if not path or not os.path.isfile(path):
        return {"valid": False, "reason": "arquivo não encontrado", "kept": 0, "auth": 0}

    kept = 0
    auth = 0
    live_auth = 0
    now = int(time.time())
    saw_netscape_header = False

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                line = raw.rstrip("\r\n")
                if line.startswith("# Netscape HTTP Cookie File") or line.startswith("# HTTP Cookie File"):
                    saw_netscape_header = True
                    continue
                if not line or (line.startswith("#") and not line.startswith("#HttpOnly_")):
                    continue
                parts = line.split("\t")
                if len(parts) < 7:
                    continue
                domain = _normalized_domain(parts[0])
                if not _domain_allowed(domain):
                    continue
                kept += 1
                name = parts[5]
                if name in AUTH_COOKIE_NAMES:
                    auth += 1
                    try:
                        expires = int(parts[4] or "0")
                    except ValueError:
                        expires = 0
                    if expires == 0 or expires > now:
                        live_auth += 1
    except OSError as e:
        return {"valid": False, "reason": str(e), "kept": 0, "auth": 0}

    if not saw_netscape_header:
        return {
            "valid": False,
            "reason": "formato inválido: cabeçalho Netscape não encontrado",
            "kept": kept,
            "auth": auth,
        }

    if kept == 0:
        return {
            "valid": False,
            "reason": "nenhum cookie Google/YouTube foi encontrado",
            "kept": 0,
            "auth": 0,
        }

    if auth == 0:
        return {
            "valid": False,
            "reason": "nenhum cookie de autenticação do YouTube foi encontrado",
            "kept": kept,
            "auth": 0,
        }

    if live_auth == 0:
        return {
            "valid": False,
            "reason": "os cookies de autenticação encontrados já expiraram",
            "kept": kept,
            "auth": auth,
        }

    return {
        "valid": True,
        "reason": None,
        "kept": kept,
        "auth": auth,
        "live_auth": live_auth,
        "netscape_header": True,
    }


def import_cookie_file(source_path):
    """Atomically import only Google/YouTube cookies into the managed cache.

    Validation happens before the current cache is touched, so choosing an
    invalid export cannot destroy the last known cache.  The user's source file
    is only read and is never modified.
    """
    inspection = inspect_cookie_file(source_path)
    if not inspection["valid"]:
        raise ValueError(inspection["reason"])

    os.makedirs(cache_dir(), exist_ok=True)
    _harden_cache_permissions(cache_dir(), directory=True)
    target = managed_cookie_file()

    fd, temp_path = tempfile.mkstemp(prefix="cookies-", suffix=".tmp", dir=cache_dir(), text=True)
    os.close(fd)
    kept = 0

    try:
        with open(source_path, "r", encoding="utf-8", errors="replace") as src, open(
            temp_path, "w", encoding="utf-8", newline="\n"
        ) as dst:
            dst.write("# Netscape HTTP Cookie File\n")
            dst.write("# Managed by YT-DLP TUI. Contains only Google/YouTube root domains.\n\n")
            for raw in src:
                line = raw.rstrip("\r\n")
                if not line or (line.startswith("#") and not line.startswith("#HttpOnly_")):
                    continue
                parts = line.split("\t")
                if len(parts) < 7:
                    continue
                if _domain_allowed(_normalized_domain(parts[0])):
                    dst.write(line + "\n")
                    kept += 1

        os.replace(temp_path, target)
        _harden_cache_permissions(target)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass

    return {"path": target, "kept": kept, **inspection}


def select_cookie_file_dialog():
    """Open a native file picker and return the selected cookie export path."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        root.update_idletasks()
        selected = filedialog.askopenfilename(
            parent=root,
            title="Selecione o cookies.txt do YouTube",
            filetypes=[("Cookies Netscape", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        return os.path.abspath(selected) if selected else None
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


def refresh_cookie_interactive(reason=None, *, initial=False, manual=False):
    """Import a cookie export through a concise TUI flow.

    ``reason`` is accepted for callback compatibility but intentionally is not
    printed: technical yt-dlp diagnostics belong to logs/control state, not the
    normal authentication UX.
    """
    del reason

    if initial:
        print("\n  Nenhuma sessão do YouTube foi configurada.")
        prompt = "  Pressione ENTER para selecionar cookies.txt, ou [q] para cancelar > "
    elif manual:
        print("\n  Atualização manual da sessão do YouTube.")
        prompt = "  Pressione ENTER para selecionar cookies.txt, ou [q] para cancelar > "
    else:
        print("\n  ⚠ Sua sessão do YouTube expirou.\n")
        print("  Exporte um novo cookies.txt.")
        prompt = "  Pressione ENTER para selecionar o arquivo, ou [q] para cancelar > "

    while True:
        answer = input(prompt).strip().lower()
        if answer in {"q", "quit", "sair"}:
            return False
        if answer:
            continue

        selected = select_cookie_file_dialog()
        if not selected:
            print("  seleção cancelada")
            return False

        try:
            result = import_cookie_file(selected)
        except Exception as e:
            print(f"  ✗ cookies.txt inválido » {e}")
            prompt = "  Pressione ENTER para selecionar outro arquivo, ou [q] para cancelar > "
            continue

        os.environ["YT_DLP_TUI_COOKIES"] = result["path"]
        print(f"  ✓ sessão atualizada ({result['kept']} cookies Google/YouTube)")
        return True
