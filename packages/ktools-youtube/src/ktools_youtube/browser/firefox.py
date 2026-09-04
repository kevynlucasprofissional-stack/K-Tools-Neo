from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Callable

OFFICIAL_FIREFOX_WIN64_URL = (
    "https://download-installer.cdn.mozilla.net/pub/firefox/releases/135.0/win64/en-US/Firefox%20Setup%20135.0.exe"
)

# Firefox preferences that suppress first-run onboarding, default-browser prompts,
# Mozilla telemetry registration and promotional UX. Applied to the K-Tools-managed profile.
KTOOLS_FIREFOX_USER_PREFS = """
// K-Tools Neo: Managed Firefox Runtime — Private Application Runtime
// These preferences suppress all first-run UX, browser registration prompts,
// and desktop/taskbar integration that is irrelevant to a private runtime.

// Disable default browser check
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.shell.didSkipDefaultBrowserCheckOnFirstRun", true);

// Disable first-run / onboarding pages
user_pref("browser.startup.firstrunSkipsHomepage", true);
user_pref("startup.homepage_override_url", "");
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.upgradeDialog.enabled", false);
user_pref("browser.newtabpage.activity-stream.showSponsored", false);
user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);

// Disable Firefox update checks (runtime is managed by K-Tools)
user_pref("app.update.auto", false);
user_pref("app.update.enabled", false);
user_pref("app.update.service.enabled", false);

// Disable Mozilla telemetry
user_pref("datareporting.healthreport.uploadEnabled", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.unified", false);
user_pref("toolkit.telemetry.enabled", false);

// Disable "What's New" tab / notification
user_pref("browser.startup.couldRestoreSession.count", 0);
user_pref("browser.laterrun.enabled", false);
user_pref("browser.laterrun.bookkeeping.profileCreationTime", 0);

// Disable pin/import prompts
user_pref("browser.toolbars.bookmarks.visibility", "never");
user_pref("browser.migrate.content-modal.about-welcome-behavior", "autoclose");

// Disable crash reporter
user_pref("breakpad.reportURL", "");
user_pref("browser.crashReports.unsubmittedCheck.enabled", false);

// Suppress sync and account onboarding
user_pref("identity.fxaccounts.enabled", false);

// Set blank startup page when no URL is specified
user_pref("browser.startup.page", 0);
user_pref("browser.startup.homepage", "about:blank");
"""

# Enterprise Policies JSON to suppress registration, default browser, and taskbar integration.
# Placed at <install_dir>/distribution/policies.json — official Firefox enterprise mechanism.
KTOOLS_FIREFOX_POLICIES = {
    "policies": {
        "DisableAppUpdate": True,
        "DontCheckDefaultBrowser": True,
        "DisableTelemetry": True,
        "DisableFirefoxStudies": True,
        "DisableFeedbackCommands": True,
        "DisableFirefoxAccounts": True,
        "DisableMasterPasswordCreation": False,
        "NoDefaultBookmarks": True,
        "OverrideFirstRunPage": "",
        "OverridePostUpdatePage": "",
        "DisplayBookmarksToolbar": "never",
        "DisableDefaultBrowserAgent": True,
    }
}


def default_firefox_runtime_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "K-Tools-Neo" / "runtimes" / "firefox"
    return Path.home() / ".ktools-neo" / "runtimes" / "firefox"


def default_firefox_profile_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "K-Tools-Neo" / "browser-profiles" / "youtube"
    return Path.home() / ".ktools-neo" / "browser-profiles" / "youtube"


def _find_7zip() -> str | None:
    """Locate 7-Zip executable. Returns path or None."""
    candidates = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        os.environ.get("LOCALAPPDATA", "") + r"\Programs\7-Zip\7z.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return shutil.which("7z") or shutil.which("7za")


def _extract_with_7zip(installer: Path, dest: Path, seven_zip: str) -> bool:
    """Extract NSIS installer contents to dest/core/ using 7-Zip.
    Returns True on success.
    """
    # 7z e ... extracts flat, x ... extracts with structure
    # NSIS stores binaries inside a 'core' sub-archive — first level extraction gives 'core' dir + setup.exe
    result = subprocess.run(
        [seven_zip, "x", str(installer), f"-o{dest}", "-y", "-bso0", "-bsp0"],
        capture_output=True,
    )
    if result.returncode != 0:
        return False
    # The NSIS payload lands in dest/core/ — that contains firefox.exe
    core_dir = dest / "core"
    return core_dir.is_dir() and (core_dir / "firefox.exe").is_file()


class FirefoxRuntime:
    """K-Tools Private Managed Firefox Runtime.

    Provisions Firefox binaries into an isolated K-Tools-private directory
    WITHOUT any Windows system registration:
    - No Start Menu shortcuts
    - No Desktop shortcuts
    - No default browser registration
    - No file/protocol associations
    - No Mozilla Maintenance Service
    - No Windows autostart
    - No uninstall registry entries

    Uses 7-Zip to extract the official Mozilla NSIS installer directly
    to the private runtime directory, bypassing the installer's Windows integration.
    """

    def __init__(
        self,
        install_dir: Path | str | None = None,
        download_url: str = OFFICIAL_FIREFOX_WIN64_URL,
    ):
        self._install_dir = Path(install_dir) if install_dir else default_firefox_runtime_dir()
        self._download_url = download_url
        self._cached_version: str | None = None

    @property
    def name(self) -> str:
        return "firefox"

    @property
    def install_dir(self) -> Path:
        return self._install_dir

    @property
    def executable_path(self) -> Path:
        """Always returns the private K-Tools runtime path. Never uses system Firefox."""
        if os.name == "nt":
            return self._install_dir / "firefox.exe"
        return self._install_dir / "firefox"

    def is_installed(self) -> bool:
        exe = self.executable_path
        return exe.is_file() and os.access(exe, os.R_OK)

    def get_version(self) -> str | None:
        """Reads version from application.ini (fast, no process spawn needed)."""
        ini_path = self._install_dir / "application.ini"
        if ini_path.is_file():
            try:
                for line in ini_path.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("Version="):
                        ver = line.split("=", 1)[1].strip()
                        self._cached_version = ver
                        return ver
            except Exception:
                pass
        # Fallback: spawn process (slower but reliable)
        if not self.is_installed():
            return None
        try:
            res = subprocess.run(
                [str(self.executable_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            out = res.stdout.strip() or res.stderr.strip()
            if out:
                self._cached_version = out
                return out
        except Exception:
            pass
        return None

    def install(self, progress_callback: Callable[[float, str], None] | None = None) -> bool:
        """Provisions Firefox as a private K-Tools runtime using 7-Zip extraction.

        DOES NOT:
        - Run Firefox installer conventionally
        - Register Firefox as a Windows application
        - Create Start Menu or Desktop shortcuts
        - Register as default browser
        - Install Mozilla Maintenance Service
        - Create file/protocol associations
        - Create Windows autostart entries

        DOES:
        - Download official Mozilla installer as a source archive
        - Extract binaries via 7-Zip into the private K-Tools runtime directory
        - Configure Firefox policies to suppress all first-run Windows integration UX
        - Save runtime metadata for version management
        """
        if os.name != "nt":
            raise NotImplementedError(
                "Provisionamento automático do Firefox Runtime suportado apenas no Windows."
            )

        # Locate 7-Zip
        seven_zip = _find_7zip()
        if not seven_zip:
            if progress_callback:
                progress_callback(-1.0, "7-Zip não encontrado. Instale 7-Zip para provisionar o Firefox Runtime.")
            return False

        # Prepare directories
        self._install_dir.mkdir(parents=True, exist_ok=True)
        downloads_dir = self._install_dir.parent.parent / "runtime-downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        installer_file = downloads_dir / "firefox_setup_cached.exe"

        try:
            # Step 1: Download installer (only if not already cached)
            needs_download = (
                not installer_file.is_file() or installer_file.stat().st_size < 10_000_000
            )
            if needs_download:
                if progress_callback:
                    progress_callback(0.0, "Baixando instalador oficial do Firefox (fonte Mozilla)...")
                req = urllib.request.Request(
                    self._download_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) K-Tools-Neo/1.0"},
                )
                with urllib.request.urlopen(req, timeout=120) as resp:
                    total_bytes = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    with open(installer_file, "wb") as out_f:
                        while chunk := resp.read(512 * 1024):
                            out_f.write(chunk)
                            downloaded += len(chunk)
                            if progress_callback and total_bytes > 0:
                                pct = min(0.55, (downloaded / total_bytes) * 0.55)
                                mb = downloaded / 1024 / 1024
                                total_mb = total_bytes / 1024 / 1024
                                progress_callback(
                                    pct,
                                    f"Baixando Firefox: {mb:.1f} MB / {total_mb:.1f} MB",
                                )
            else:
                if progress_callback:
                    progress_callback(0.55, "Usando instalador Firefox em cache...")

            # Step 2: Extract with 7-Zip (no Windows registration)
            if progress_callback:
                progress_callback(0.60, "Extraindo binários do Firefox (sem instalação no sistema)...")

            # Extract to a temp staging dir first, then move to final destination
            staging_dir = self._install_dir.parent / "firefox_staging"
            if staging_dir.exists():
                shutil.rmtree(staging_dir, ignore_errors=True)
            staging_dir.mkdir(parents=True, exist_ok=True)

            success = _extract_with_7zip(installer_file, staging_dir, seven_zip)
            if not success:
                raise RuntimeError("Extração do Firefox com 7-Zip falhou. Verifique o instalador baixado.")

            # The NSIS extractor puts files in staging_dir/core/
            core_src = staging_dir / "core"
            if not (core_src / "firefox.exe").is_file():
                raise FileNotFoundError(f"firefox.exe não encontrado em {core_src} após extração.")

            # Move core/ contents to install_dir
            if self._install_dir.exists():
                shutil.rmtree(self._install_dir, ignore_errors=True)
            shutil.move(str(core_src), str(self._install_dir))
            shutil.rmtree(staging_dir, ignore_errors=True)

            if progress_callback:
                progress_callback(0.85, "Configurando runtime privado...")

            # Step 3: Apply enterprise policies to suppress Windows integration UX
            self._apply_policies()

            # Step 4: Verify
            if not self.is_installed():
                raise FileNotFoundError(f"firefox.exe não encontrado em {self._install_dir} após extração.")

            version = self.get_version()
            self._save_metadata(version)

            if progress_callback:
                progress_callback(1.0, f"Firefox Runtime privado instalado: {version}")

            return True

        except Exception as exc:
            if progress_callback:
                progress_callback(-1.0, f"Erro ao provisionar Firefox Runtime: {exc}")
            return False

    def _apply_policies(self) -> None:
        """Write Firefox enterprise policies.json and distribute user.js to suppress
        all Windows integration UX. This is an official Firefox enterprise mechanism."""
        # 1. Enterprise policies file (applied to ALL profiles from this installation)
        dist_dir = self._install_dir / "distribution"
        dist_dir.mkdir(parents=True, exist_ok=True)
        policies_file = dist_dir / "policies.json"
        try:
            with open(policies_file, "w", encoding="utf-8") as f:
                json.dump(KTOOLS_FIREFOX_POLICIES, f, indent=2)
        except Exception:
            pass  # Non-fatal — prefs in profile will still suppress most UX

    def apply_profile_prefs(self, profile_dir: Path | str) -> None:
        """Write user.js into a Firefox profile to suppress first-run UX.
        Call this after creating/opening a new profile directory.
        """
        p = Path(profile_dir)
        p.mkdir(parents=True, exist_ok=True)
        user_js = p / "user.js"
        try:
            with open(user_js, "w", encoding="utf-8") as f:
                f.write(KTOOLS_FIREFOX_USER_PREFS)
        except Exception:
            pass

    def launch(
        self,
        profile_dir: Path | str,
        url: str | None = None,
        headless: bool = False,
        extra_args: list[str] | None = None,
    ) -> subprocess.Popen:
        """Launches the isolated Firefox runtime with an explicit private profile.

        Never touches the user's personal Firefox profile or system Firefox.
        Uses -no-remote to guarantee complete isolation.
        """
        if not self.is_installed():
            raise FileNotFoundError(
                f"Firefox Runtime privado não está em {self._install_dir}. Execute install() primeiro."
            )

        p_dir = Path(profile_dir)
        p_dir.mkdir(parents=True, exist_ok=True)

        # Ensure profile has suppression prefs before first launch
        if not (p_dir / "user.js").exists():
            self.apply_profile_prefs(p_dir)

        cmd = [
            str(self.executable_path),
            "-no-remote",    # Prevents communication with any other running Firefox instance
            "-profile",
            str(p_dir.resolve()),
        ]

        if headless:
            cmd.append("-headless")

        if extra_args:
            cmd.extend(extra_args)

        if url:
            cmd.append(url)

        creationflags = 0
        if os.name == "nt" and not headless:
            creationflags = subprocess.DETACHED_PROCESS

        return subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )

    def stop(self, proc: subprocess.Popen | None = None, timeout_sec: float = 5.0) -> bool:
        if proc is None:
            return True
        if proc.poll() is not None:
            return True
        try:
            proc.terminate()
            proc.wait(timeout=timeout_sec)
            return True
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=2.0)
                return True
            except Exception:
                return False

    def health_check(self) -> dict[str, Any]:
        installed = self.is_installed()
        version = self.get_version() if installed else None
        exe_path = str(self.executable_path) if installed else None
        policies_ok = (self._install_dir / "distribution" / "policies.json").is_file() if installed else False
        size_bytes = self.executable_path.stat().st_size if installed and self.executable_path.exists() else None

        return {
            "name": "firefox",
            "installed": installed,
            "executable_path": exe_path,
            "version": version,
            "size_bytes": size_bytes,
            "policies_applied": policies_ok,
            "runtime_dir": str(self._install_dir),
            "provisioning_method": "7-Zip extraction (no Windows registration)",
            "healthy": bool(installed and version is not None),
        }

    def _save_metadata(self, version: str | None) -> None:
        meta_dir = self._install_dir.parent.parent / "runtime-metadata"
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_file = meta_dir / "firefox.json"
        data = {
            "name": "firefox",
            "version": version,
            "installed_at": time.time(),
            "source_url": self._download_url,
            "executable": str(self.executable_path),
            "provisioning_method": "7-Zip extraction from NSIS installer",
            "windows_registration": "NONE",
            "start_menu": "NONE",
            "desktop_shortcut": "NONE",
            "default_browser": "NONE",
        }
        try:
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
