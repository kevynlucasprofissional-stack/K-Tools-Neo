from __future__ import annotations

import asyncio
import http.cookiejar
import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Mapping

import websockets

from .base import AuthProvider, AuthState
from .bridge import cdp_cookies_to_cookiejar, inspect_cookiejar_auth

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def resolve_edge_executable() -> str | None:
    for candidate in EDGE_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("msedge")
    if found and os.path.isfile(found):
        return found
    return None


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def default_profile_dir() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / "K-Tools-Neo" / "browser-profiles" / "edge-youtube"
    return Path.home() / ".ktools-neo" / "browser-profiles" / "edge-youtube"


class EdgeCdpAuthProvider:
    """Official Fallback Windows AuthProvider using Microsoft Edge and CDP."""

    def __init__(
        self,
        profile_dir: Path | str | None = None,
        edge_path: str | None = None,
    ):
        self._profile_dir = Path(profile_dir) if profile_dir else default_profile_dir()
        self._explicit_edge_path = edge_path
        self._cached_jar: http.cookiejar.CookieJar | None = None
        self._last_state: AuthState = AuthState.NOT_CONNECTED

    @property
    def name(self) -> str:
        return "edge_cdp"

    def is_available(self) -> bool:
        return resolve_edge_executable() is not None or (
            bool(self._explicit_edge_path) and os.path.isfile(self._explicit_edge_path)
        )

    def _edge_exe(self) -> str:
        if self._explicit_edge_path and os.path.isfile(self._explicit_edge_path):
            return self._explicit_edge_path
        resolved = resolve_edge_executable()
        if not resolved:
            raise FileNotFoundError("Microsoft Edge executable was not found on this system.")
        return resolved

    def get_cookiejar(self) -> http.cookiejar.CookieJar | None:
        if self._cached_jar is None:
            self.refresh()
        return self._cached_jar

    def get_state(self) -> AuthState:
        if self._cached_jar is None:
            return self.refresh()
        auth_info = inspect_cookiejar_auth(self._cached_jar)
        if auth_info["active"]:
            return AuthState.ACTIVE
        if auth_info["expired"]:
            return AuthState.REAUTH_REQUIRED
        return AuthState.NOT_CONNECTED

    def refresh(self) -> AuthState:
        """Attempts headless extraction of cookies from the dedicated Edge profile."""
        if not self.is_available():
            self._last_state = AuthState.NOT_CONNECTED
            return AuthState.NOT_CONNECTED

        if not self._profile_dir.exists():
            self._last_state = AuthState.NOT_CONNECTED
            return AuthState.NOT_CONNECTED

        try:
            cookies = asyncio.run(self._extract_cookies_headless())
            jar, kept = cdp_cookies_to_cookiejar(cookies)
            self._cached_jar = jar

            auth_info = inspect_cookiejar_auth(jar)
            if auth_info["active"]:
                self._last_state = AuthState.ACTIVE
            elif auth_info["expired"]:
                self._last_state = AuthState.REAUTH_REQUIRED
            else:
                self._last_state = AuthState.NOT_CONNECTED
        except Exception:
            self._last_state = AuthState.ERROR
        return self._last_state

    def launch_login_flow(self) -> None:
        """Opens a visible Edge window in the dedicated profile for the user to log in."""
        exe = self._edge_exe()
        self._profile_dir.mkdir(parents=True, exist_ok=True)
        login_url = "https://accounts.google.com/ServiceLogin?service=youtube"

        args = [
            exe,
            f"--user-data-dir={self._profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            login_url,
        ]
        # Launch non-blocking detached window
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS if os.name == "nt" else 0,
        )

    async def _extract_cookies_headless(self, timeout_sec: float = 12.0) -> list[dict[str, Any]]:
        exe = self._edge_exe()
        self._profile_dir.mkdir(parents=True, exist_ok=True)
        port = get_free_port()

        cmd = [
            exe,
            "--headless=new",
            f"--remote-debugging-port={port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={self._profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        browser_ws: str | None = None
        page_ws: str | None = None

        try:
            # Wait for CDP targets
            deadline = time.time() + timeout_sec
            v_url = f"http://127.0.0.1:{port}/json/version"
            l_url = f"http://127.0.0.1:{port}/json/list"

            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(v_url, timeout=1.0) as r1, urllib.request.urlopen(l_url, timeout=1.0) as r2:
                        if r1.status == 200 and r2.status == 200:
                            v_data = json.loads(r1.read().decode())
                            targets = json.loads(r2.read().decode())
                            browser_ws = v_data.get("webSocketDebuggerUrl")
                            for t in targets:
                                if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                                    page_ws = t["webSocketDebuggerUrl"]
                                    break
                            if browser_ws and page_ws:
                                break
                except Exception:
                    pass
                await asyncio.sleep(0.2)

            if not page_ws or not browser_ws:
                raise TimeoutError(f"Headless Edge on port {port} did not expose CDP page target.")

            # Query cookies via page target
            async with websockets.connect(page_ws, close_timeout=2) as ws:
                await ws.send(json.dumps({"id": 1, "method": "Storage.getCookies"}))
                resp = json.loads(await ws.recv())
                cookies = resp.get("result", {}).get("cookies", [])

            # Graceful shutdown via Browser.close
            try:
                async with websockets.connect(browser_ws, close_timeout=2) as ws_b:
                    await ws_b.send(json.dumps({"id": 2, "method": "Browser.close"}))
                proc.wait(timeout=3)
            except Exception:
                pass

            return cookies
        finally:
            if proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    proc.kill()
