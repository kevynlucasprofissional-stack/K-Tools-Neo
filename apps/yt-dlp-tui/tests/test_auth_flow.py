from pathlib import Path
from types import SimpleNamespace
import sys
import types

import pytest

from yt_dlp_tui import auth_cache
from yt_dlp_tui.errors import ErrorKind

if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp

import yt_dlp_tui.downloader as downloader


def _write_cookie_file(path: Path, *, domain='.youtube.com', name='SAPISID', expires='0'):
    path.write_text(
        '# Netscape HTTP Cookie File\n'
        f'{domain}\tTRUE\t/\tTRUE\t{expires}\t{name}\t' + ('x' * 12) + '\n',
        encoding='utf-8',
    )


def test_first_use_without_managed_cache_requests_file(monkeypatch):
    calls = []
    state = {'ready': False}

    monkeypatch.setattr(downloader, '_check_js_runtime', lambda: None)
    monkeypatch.setattr(downloader, 'active_cookie_file', lambda: 'managed.txt' if state['ready'] else None)
    monkeypatch.setattr(downloader, 'inspect_cookie_file', lambda path: {'valid': True})

    def callback(reason=None, *, initial=False):
        calls.append((reason, initial))
        state['ready'] = True
        return True

    assert downloader._preflight('audio', callback) is True
    assert calls == [(None, True)]


def test_valid_cache_does_not_prompt(monkeypatch):
    calls = []
    monkeypatch.setattr(downloader, '_check_js_runtime', lambda: None)
    monkeypatch.setattr(downloader, 'active_cookie_file', lambda: 'managed.txt')
    monkeypatch.setattr(downloader, 'inspect_cookie_file', lambda path: {'valid': True})

    assert downloader._preflight('audio', lambda *a, **k: calls.append((a, k)) or False) is True
    assert calls == []


def test_invalid_import_does_not_replace_previous_managed_cache(monkeypatch, tmp_path):
    cache = tmp_path / 'private-cache'
    monkeypatch.setattr(auth_cache, 'cache_dir', lambda: str(cache))
    cache.mkdir()

    good = tmp_path / 'good.txt'
    _write_cookie_file(good)
    auth_cache.import_cookie_file(str(good))
    before = Path(auth_cache.managed_cookie_file()).read_bytes()

    bad = tmp_path / 'bad.txt'
    bad.write_text('not a netscape cookie export\n', encoding='utf-8')
    with pytest.raises(ValueError):
        auth_cache.import_cookie_file(str(bad))

    assert Path(auth_cache.managed_cookie_file()).read_bytes() == before


def test_cancelled_picker_keeps_existing_cache_and_returns_false(monkeypatch, tmp_path):
    cache = tmp_path / 'private-cache'
    monkeypatch.setattr(auth_cache, 'cache_dir', lambda: str(cache))
    cache.mkdir()
    good = tmp_path / 'good.txt'
    _write_cookie_file(good)
    auth_cache.import_cookie_file(str(good))
    before = Path(auth_cache.managed_cookie_file()).read_bytes()

    monkeypatch.setattr('builtins.input', lambda prompt='': '')
    monkeypatch.setattr(auth_cache, 'select_cookie_file_dialog', lambda: None)

    assert auth_cache.refresh_cookie_interactive() is False
    assert Path(auth_cache.managed_cookie_file()).read_bytes() == before


def test_auth_expired_on_item_four_restarts_only_item_four(monkeypatch, tmp_path):
    task_dir = tmp_path / 'playlist'
    task_dir.mkdir()
    items = []
    for index in range(1, 5):
        items.append({
            'index': index,
            'video_id': f'v{index}',
            'title': f'Video {index}',
            'url': f'https://example.test/watch?v=v{index}',
            'available': True,
            'status': 'completed' if index < 4 else 'pending',
            'attempts': 1 if index < 4 else 0,
            'final_file': f'video-{index}.mp4' if index < 4 else None,
            'last_error': None,
            'last_error_kind': None,
            'progress': {'percent': 100.0 if index < 4 else 0.0, 'downloaded_bytes': 0, 'total_bytes': None},
        })
    state = {
        'schema_version': 3,
        'task_type': 'playlist',
        'playlist': {'id': 'p', 'title': 'P', 'source_url': 'https://example.test/playlist'},
        'mode': {'format': 'video', 'quality': 'best'},
        'status': 'in_progress',
        'items': items,
        'audit': {},
    }
    metadata = {'id': 'p', 'title': 'P', 'entries': items}
    calls = []
    first = {'auth': True}

    monkeypatch.setattr(downloader, '_extract_playlist', lambda url: metadata)
    monkeypatch.setattr(downloader, '_prepare_playlist_state', lambda *args: (str(task_dir), state))
    monkeypatch.setattr(downloader, '_audit_playlist', lambda *args: ([], 4))

    def fake_download(item, *args):
        calls.append(item['index'])
        if first['auth']:
            first['auth'] = False
            item['status'] = 'waiting_auth'
            item['last_error_kind'] = ErrorKind.AUTH_EXPIRED.value
            raise downloader.AuthCacheExpired('technical auth detail')
        item['status'] = 'completed'
        item['last_error'] = None
        item['last_error_kind'] = None
        return str(task_dir / 'video-4.mp4')

    observed_statuses = []

    def refresh(reason=None, *, initial=False):
        observed_statuses.append((state['items'][3]['status'], initial))
        return True

    monkeypatch.setattr(downloader, '_download_item_to_stage', fake_download)
    downloader._download_playlist('https://example.test/playlist', str(tmp_path), 'video', 'best', refresh)

    assert calls == [4, 4]
    assert observed_statuses == [('waiting_auth', False)]
    assert [item['status'] for item in state['items'][:3]] == ['completed', 'completed', 'completed']
    assert state['items'][3]['status'] == 'completed'


def test_auth_cancel_leaves_item_resumable(monkeypatch, tmp_path):
    task_dir = tmp_path / 'playlist'
    task_dir.mkdir()
    item = {
        'index': 1, 'video_id': 'v1', 'title': 'Video', 'url': 'https://example.test/watch?v=v1',
        'available': True, 'status': 'pending', 'attempts': 0, 'final_file': None,
        'last_error': None, 'last_error_kind': None,
        'progress': {'percent': 0.0, 'downloaded_bytes': 0, 'total_bytes': None},
    }
    state = {
        'schema_version': 3, 'task_type': 'playlist',
        'playlist': {'id': 'p', 'title': 'P', 'source_url': 'x'},
        'mode': {'format': 'audio', 'quality': 'best'}, 'status': 'in_progress',
        'items': [item], 'audit': {},
    }
    monkeypatch.setattr(downloader, '_extract_playlist', lambda url: {'id': 'p', 'title': 'P', 'entries': [item]})
    monkeypatch.setattr(downloader, '_prepare_playlist_state', lambda *args: (str(task_dir), state))

    def auth_fail(*args):
        item['status'] = 'waiting_auth'
        item['last_error_kind'] = ErrorKind.AUTH_EXPIRED.value
        raise downloader.AuthCacheExpired('auth')

    monkeypatch.setattr(downloader, '_download_item_to_stage', auth_fail)
    result = downloader._download_playlist('x', str(tmp_path), 'audio', 'best', lambda *a, **k: False)

    assert result == []
    assert state['status'] == 'interrupted_auth'
    assert item['status'] == 'waiting_auth'
    assert item['last_error_kind'] == ErrorKind.AUTH_EXPIRED.value


def test_js_preflight_failure_never_requests_cookies(monkeypatch, capsys):
    calls = []
    js_failure = downloader._js_preflight_failure('challenge solver indisponível')
    monkeypatch.setattr(downloader, '_check_js_runtime', lambda: js_failure)
    monkeypatch.setattr(downloader, 'active_cookie_file', lambda: None)

    assert downloader._preflight('audio', lambda *a, **k: calls.append((a, k)) or True) is False
    out = capsys.readouterr().out
    assert calls == []
    assert 'JavaScript' in out
    assert 'cookies.txt' not in out


def test_js_runtime_version_and_ejs_pin_are_checked(monkeypatch):
    monkeypatch.setattr(downloader.shutil, 'which', lambda name: 'deno.exe')
    monkeypatch.setattr(
        downloader.subprocess,
        'run',
        lambda *a, **k: SimpleNamespace(returncode=0, stdout='deno 2.9.5\nv8 x\n', stderr=''),
    )
    monkeypatch.setattr(downloader.importlib, 'import_module', lambda name: object())

    real_version = downloader.importlib.metadata.version
    real_requires = downloader.importlib.metadata.requires
    monkeypatch.setattr(
        downloader.importlib.metadata,
        'version',
        lambda name: '0.8.0' if name == 'yt-dlp-ejs' else real_version(name),
    )
    monkeypatch.setattr(
        downloader.importlib.metadata,
        'requires',
        lambda name: ['yt-dlp-ejs==0.8.0; extra == "default"'] if name == 'yt-dlp' else real_requires(name),
    )

    assert downloader._check_js_runtime() is None

    monkeypatch.setattr(
        downloader.importlib.metadata,
        'version',
        lambda name: '0.7.0' if name == 'yt-dlp-ejs' else real_version(name),
    )
    failure = downloader._check_js_runtime()
    assert failure.kind is ErrorKind.JS_RUNTIME
    assert 'incompatível' in failure.technical_message


def test_invalid_selection_reprompts_without_overwriting_then_accepts_valid(monkeypatch, tmp_path):
    cache = tmp_path / 'private-cache'
    monkeypatch.setattr(auth_cache, 'cache_dir', lambda: str(cache))
    cache.mkdir()

    original = tmp_path / 'original.txt'
    _write_cookie_file(original)
    auth_cache.import_cookie_file(str(original))
    before = Path(auth_cache.managed_cookie_file()).read_bytes()

    bad = tmp_path / 'bad.txt'
    bad.write_text('invalid export\n', encoding='utf-8')
    good = tmp_path / 'replacement.txt'
    _write_cookie_file(good, name='__Secure-3PSID')

    answers = iter(['', ''])
    selections = iter([str(bad), str(good)])
    snapshots = []

    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))

    def pick():
        selected = next(selections)
        if selected == str(good):
            snapshots.append(Path(auth_cache.managed_cookie_file()).read_bytes())
        return selected

    monkeypatch.setattr(auth_cache, 'select_cookie_file_dialog', pick)
    assert auth_cache.refresh_cookie_interactive() is True
    assert snapshots == [before]
    assert Path(auth_cache.managed_cookie_file()).read_bytes() != before


def test_expired_auth_message_hides_technical_reason(monkeypatch, capsys):
    monkeypatch.setattr('builtins.input', lambda prompt='': 'q')
    assert auth_cache.refresh_cookie_interactive('ERROR: huge internal yt-dlp diagnostic URL') is False
    out = capsys.readouterr().out
    assert 'Sua sessão do YouTube expirou' in out
    assert 'huge internal' not in out
    assert 'yt-dlp diagnostic' not in out


def test_cookie_export_without_auth_cookie_is_rejected(tmp_path):
    export = tmp_path / 'no-auth.txt'
    _write_cookie_file(export, name='PREF')
    result = auth_cache.inspect_cookie_file(str(export))
    assert result['valid'] is False
    assert result['auth'] == 0
    assert 'autenticação' in result['reason']
    with pytest.raises(ValueError):
        auth_cache.import_cookie_file(str(export))


def test_preflight_requires_ffmpeg_before_requesting_cookies(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(downloader, '_check_js_runtime', lambda: None)
    monkeypatch.setattr(downloader, '_ffmpeg_exe', lambda: None)
    monkeypatch.setattr(downloader, 'active_cookie_file', lambda: None)
    assert downloader._preflight('audio', lambda *a, **k: calls.append((a, k)) or True) is False
    assert calls == []
    assert 'FFmpeg' in capsys.readouterr().out


def test_auth_callback_internal_typeerror_is_not_swallowed_or_reinvoked():
    calls = []
    def broken(reason=None, *, initial=False):
        calls.append((reason, initial))
        raise TypeError('erro interno real')
    with pytest.raises(TypeError, match='erro interno real'):
        downloader._invoke_auth_refresh(broken, 'x', initial=True)
    assert calls == [('x', True)]


def test_legacy_one_argument_auth_callback_is_supported():
    calls = []
    def legacy(reason):
        calls.append(reason)
        return True
    assert downloader._invoke_auth_refresh(legacy, 'x', initial=True) is True
    assert calls == ['x']


def test_managed_cache_permissions_are_restricted_when_posix(monkeypatch, tmp_path):
    if auth_cache.os.name == 'nt':
        pytest.skip('modo POSIX não se aplica ao Windows')
    cache = tmp_path / 'private-cache'
    monkeypatch.setattr(auth_cache, 'cache_dir', lambda: str(cache))
    export = tmp_path / 'cookies-export.txt'
    _write_cookie_file(export)
    auth_cache.import_cookie_file(str(export))
    import stat
    assert stat.S_IMODE(cache.stat().st_mode) == 0o700
    assert stat.S_IMODE(Path(auth_cache.managed_cookie_file()).stat().st_mode) == 0o600


def test_repeated_server_auth_failure_is_bounded_in_metadata_flow(monkeypatch):
    calls = {"operation": 0, "refresh": 0}

    def operation():
        calls["operation"] += 1
        raise downloader.AuthCacheExpired("auth recusada")

    def refresh(reason=None, *, initial=False):
        calls["refresh"] += 1
        return True

    with pytest.raises(downloader.DownloadInterrupted, match="continuou sendo recusada"):
        downloader._call_with_recovery(operation, refresh, label="teste")

    assert calls["refresh"] == downloader.MAX_AUTH_REFRESHES_PER_OPERATION
    assert calls["operation"] == downloader.MAX_AUTH_REFRESHES_PER_OPERATION + 1


def test_repeated_server_auth_failure_is_bounded_for_single_download(monkeypatch, tmp_path, capsys):
    class AlwaysAuthFail:
        calls = 0
        def __init__(self, opts): self.opts = opts
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def download(self, urls):
            type(self).calls += 1
            self.opts["logger"].error("Sign in to confirm you're not a bot")
            raise RuntimeError("Sign in to confirm you're not a bot")

    refreshes = []
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", AlwaysAuthFail)
    result = downloader._download_single(
        "https://example.test/watch?v=x", str(tmp_path), "audio", "best",
        lambda reason=None, **kwargs: refreshes.append(reason) or True,
    )

    assert result == []
    assert len(refreshes) == downloader.MAX_AUTH_REFRESHES_PER_OPERATION
    assert AlwaysAuthFail.calls == downloader.MAX_AUTH_REFRESHES_PER_OPERATION + 1
    assert "continuou sendo recusada" in capsys.readouterr().out


def test_repeated_server_auth_failure_is_bounded_for_playlist_item(monkeypatch, tmp_path, capsys):
    task_dir = tmp_path / "playlist-auth-loop"
    task_dir.mkdir()
    item = {
        "index": 1, "video_id": "v1", "title": "Video",
        "url": "https://example.test/watch?v=v1", "available": True,
        "status": "pending", "attempts": 0, "retry_count": 0,
        "last_retry_at": None, "started_at": None, "completed_at": None,
        "final_file": None, "last_error": None, "last_error_kind": None,
        "audit_status": "not_run", "audit_at": None,
        "progress": {"percent": 0.0, "downloaded_bytes": 0, "total_bytes": None},
    }
    state = {
        "schema_version": 3, "task_type": "playlist",
        "playlist": {"id": "p", "title": "P", "source_url": "x"},
        "mode": {"format": "audio", "quality": "best"}, "status": "in_progress",
        "items": [item], "audit": {},
    }
    monkeypatch.setattr(downloader, "_extract_playlist", lambda url: {"id": "p", "title": "P", "entries": [item]})
    monkeypatch.setattr(downloader, "_prepare_playlist_state", lambda *args: (str(task_dir), state))

    calls = {"download": 0, "refresh": 0}
    def auth_fail(*args):
        calls["download"] += 1
        item["status"] = "waiting_auth"
        item["last_error_kind"] = ErrorKind.AUTH_EXPIRED.value
        raise downloader.AuthCacheExpired("auth")
    def refresh(reason=None, **kwargs):
        calls["refresh"] += 1
        return True

    monkeypatch.setattr(downloader, "_download_item_to_stage", auth_fail)
    result = downloader._download_playlist("x", str(tmp_path), "audio", "best", refresh)

    assert result == []
    assert calls["refresh"] == downloader.MAX_AUTH_REFRESHES_PER_OPERATION
    assert calls["download"] == downloader.MAX_AUTH_REFRESHES_PER_OPERATION + 1
    assert state["status"] == "interrupted_auth"
    assert item["status"] == "waiting_auth"
    assert "continuou sendo recusada" in capsys.readouterr().out


def test_expired_auth_cookie_export_is_rejected(tmp_path):
    export = tmp_path / "expired.txt"
    _write_cookie_file(export, expires="1")
    result = auth_cache.inspect_cookie_file(str(export))
    assert result["valid"] is False
    assert result["auth"] == 1
    assert "expiraram" in result["reason"]


def test_preflight_expired_managed_cache_requests_refresh(monkeypatch):
    calls = []
    state = {"refreshed": False}
    monkeypatch.setattr(downloader, "_check_js_runtime", lambda: None)
    monkeypatch.setattr(downloader, "_ffmpeg_exe", lambda: "ffmpeg")
    monkeypatch.setattr(downloader, "active_cookie_file", lambda: "managed.txt")

    def inspect(path):
        if state["refreshed"]:
            return {"valid": True}
        return {"valid": False, "reason": "os cookies de autenticação encontrados já expiraram"}

    def refresh(reason=None, *, initial=False):
        calls.append((reason, initial))
        state["refreshed"] = True
        return True

    monkeypatch.setattr(downloader, "inspect_cookie_file", inspect)
    assert downloader._preflight("audio", refresh) is True
    assert calls == [("os cookies de autenticação encontrados já expiraram", False)]


def test_search_auth_interruption_is_not_misreported_silently(monkeypatch, capsys):
    monkeypatch.setattr(downloader, "_preflight", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        downloader, "_call_with_recovery",
        lambda *args, **kwargs: (_ for _ in ()).throw(downloader.DownloadInterrupted("sessão recusada")),
    )
    assert downloader.fetch_search_results("teste", 3, lambda *args, **kwargs: True) == []
    assert "busca interrompida" in capsys.readouterr().out
