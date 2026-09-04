# ADR 051: Official YouTube Download Node Pack (`ktools-youtube`)

## Date
2026-09-03

## Status
Accepted

## Context
The legacy application `apps/yt-dlp-tui/` existed as an isolated terminal tool in the monorepo. Workflows required a canonical node pack (`youtube.download`) to enable composing YouTube downloads with downstream processing nodes (such as joining video parts via `media.join_videos` or converting audio via `media.convert_audio`).

Furthermore, modern Windows environments (Chrome and Edge 127+) protect cookie stores using App-Bound Encryption, breaking direct disk extraction via `yt-dlp --cookies-from-browser edge`.

## Decision
1. **Layered Download Architecture**:
   - **Layer 1: Public First**: All requests execute with zero cookies by default. No login is triggered proactively.
   - **Layer 2: YouTubeAuthManager**: Coordinates authentication providers (`EdgeCdpAuthProvider`, `FirefoxAuthProvider`, `CookieFileAuthProvider`).
   - Reauth state machine: Detects expired sessions or Google challenges, transitioning to `REAUTH_REQUIRED` without attempting false "infinite silent renewal".

2. **Edge CDP Provider (`EdgeCdpAuthProvider`)**:
   - Uses native `msedge.exe` pre-installed on all Windows 10/11 machines with zero external installations.
   - Operates in a dedicated profile directory (`%LOCALAPPDATA%\K-Tools-Neo\browser-session\youtube`).
   - Binds remote debugging strictly to `127.0.0.1` on dynamically allocated ports.
   - Enforces graceful shutdown via CDP `Browser.close` to ensure SQLite cookie persistence to disk.
   - Extracts decrypted cookies in memory via CDP `Storage.getCookies` and normalizes them into `http.cookiejar.CookieJar`.
   - Injects cookies directly into in-memory `ydl.cookiejar`.

3. **Spike Empirical Validation**:
   - `EDGE_PROFILE_PERSISTENCE`: PASS (persisted across restart with `Browser.close`).
   - `EDGE_CDP_COOKIE_BRIDGE`: PASS (normalized into yt-dlp CookieJar).
   - `PUBLIC_DOWNLOAD`: PASS (extracted public video with 0 cookies).
   - `AUTHENTICATED_YTDLP`: PASS (correctly traps auth boundaries).
   - `AUTH_AFTER_BROWSER_RESTART`: PASS (relaunches on dynamic ports).
   - `HEADLESS_SESSION_REUSE`: PASS (headless Edge retrieves persisted cookies).
   - `REAUTH_FLOW`: PASS (detected empty session, sets `REAUTH_REQUIRED`).
   - `AUTH_SECURITY`: PASS (loopback only, zero secrets in logs, dynamic ports freed).

4. **Integration with Workflow Studio**:
   - Output `files: FILE_SET` connects directly to `media.join_videos: videos`.
   - Added production preset: "🎬 Baixar do YouTube e Juntar Vídeos (Pipeline Automático)".

## Consequences
- Complete end-to-end video downloading and merging within visual workflows.
- Zero extra browser installations required on Windows.
- Clean architectural separation between UI, auth providers, and yt-dlp adapter.
