# Specification: YouTube Download Node Pack (`ktools-youtube`)

## Objective
Provide a resilient, layered YouTube download capability (`youtube.download`) within `packages/ktools-youtube`, enabling both human visual workflows and AI agents to download public or authenticated videos/playlists and pipe downloaded media directly into downstream processing nodes (e.g. `media.join_videos`, `media.convert_audio`).

## Architecture & Responsibilities

1. **Package Ownership**:
   - Package: `packages/ktools-youtube`
   - Node Type ID: `youtube.download`
   - Title: `Baixar do YouTube` (Narrative: "🔻 Baixar do YouTube")
   - Category: `Download & Mídia`
   - Cache Policy: `CachePolicy.NEVER` (external streams and live URLs)

2. **Layered Execution Contract**:
   - **Layer 1: Public Downloads First**:
     - All downloads default to running without cookies.
     - Never prompts or opens login for standard public videos.
   - **Layer 2: Auth Manager (`YouTubeAuthManager`)**:
     - Provides an extensible abstraction for authentication providers.
     - **Primary (Windows)**: `EdgeCdpAuthProvider`:
       - Launches native Microsoft Edge (`msedge.exe`) with dedicated isolated profile (`%LOCALAPPDATA%\K-Tools-Neo\browser-session\youtube`).
       - Binds remote debugging strictly to `127.0.0.1` on dynamically allocated loopback ports.
       - Enforces graceful shutdown via CDP `Browser.close` so that session cookies are cleanly flushed to disk.
       - Extracts cookies in memory via CDP `Storage.getCookies` from the page target, bypassing Windows App-Bound encryption.
       - Supports headless session reuse (`--headless=new`).
       - Detects expired / invalid sessions and transitions to `AuthState.REAUTH_REQUIRED`.
     - **Fallback 1**: `FirefoxAuthProvider` (utilizes yt-dlp `cookiesfrombrowser: ('firefox', ...)`).
     - **Fallback 2**: `CookieFileAuthProvider` (reads manual Netscape `cookies.txt`).
   - **Cookie Bridge (`bridge.py`)**:
     - Domain whitelist filter: restricts imported cookies strictly to `.youtube.com`, `.google.com`, `.accounts.google.com`, `youtube.com`, `google.com`.
     - Normalizes CDP dictionary schema into `http.cookiejar.Cookie` objects.
     - Injects directly into in-memory `ydl.cookiejar` without persisting insecure intermediary files.

3. **YouTube Engine & Runtimes (`adapter.py` & `service.py`)**:
   - Automatically detects JS runtimes (`node`, `deno`) and configures yt-dlp `js_runtimes` for JavaScript challenge solving (EJS).
   - Resolves FFmpeg via `imageio-ffmpeg` or system binary.
   - Normalizes yt-dlp exceptions into structured typed errors (`AuthRequiredError`, `ReauthRequiredError`, `PrivateVideoError`, `AgeRestrictedError`, `GeoBlockedError`, `PoTokenRequiredError`, etc.).

4. **Port Contract**:
   - **Inputs**:
     - `url`: `TEXT` (video or playlist link)
     - `media_type`: `TEXT` (`"video"` or `"audio"`, default `"video"`)
     - `quality`: `TEXT` (`"best"`, `"2160p"`, `"1440p"`, `"1080p"`, `"720p"`, default `"best"`)
     - `audio_format`: `TEXT` (`"m4a"`, `"mp3"`, `"wav"`, default `"m4a"`)
     - `output_dir`: `FOLDER` (optional output directory)
   - **Outputs**:
     - `files`: `FILE_SET` (ordered list of downloaded video or audio files)
     - `folder`: `FOLDER` (directory containing files)
     - `metadata`: `JSON` (title, id, channel, duration, playlist items)

5. **Visual Workflow Studio Integration**:
   - Registered in `catalog.json` with Simple Mode narrative fields.
   - Preset: **"🎬 Baixar do YouTube e Juntar Vídeos (Pipeline Automático)"** chaining `youtube.download` -> `media.join_videos` -> `system.notify`.
