from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp

from yt_dlp_tui import downloader
from yt_dlp_tui.errors import ErrorKind


def _video_id(url):
    query = parse_qs(urlparse(url).query)
    return (query.get('v') or ['single'])[0]


class ScenarioYoutubeDL:
    scenarios = {}
    calls = {}
    seen_opts = []
    write_partial_on_failure = False

    def __init__(self, opts):
        self.opts = opts
        type(self).seen_opts.append(opts)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def download(self, urls):
        url = urls[0]
        video_id = _video_id(url)
        count = type(self).calls.get(video_id, 0) + 1
        type(self).calls[video_id] = count
        sequence = type(self).scenarios.get(video_id, ['success'])
        action = sequence[min(count - 1, len(sequence) - 1)]
        stage = Path(self.opts['outtmpl']).parent
        stage.mkdir(parents=True, exist_ok=True)

        if action != 'success':
            if type(self).write_partial_on_failure:
                (stage / f'partial-{video_id}.mp4.part').write_bytes(b'x' * 4096)
            if isinstance(action, BaseException):
                raise action
            logger = self.opts.get('logger')
            if logger:
                logger.error(str(action))
            raise RuntimeError(str(action))

        ext = 'm4a' if 'bestaudio' in str(self.opts.get('format', '')) else 'mp4'
        final = stage / f'Video [{video_id}].{ext}'
        final.write_bytes(b'x' * 4096)
        return 0


@pytest.fixture(autouse=True)
def reset_scenario(monkeypatch):
    ScenarioYoutubeDL.scenarios = {}
    ScenarioYoutubeDL.calls = {}
    ScenarioYoutubeDL.seen_opts = []
    ScenarioYoutubeDL.write_partial_on_failure = False
    monkeypatch.setattr(downloader.yt_dlp, 'YoutubeDL', ScenarioYoutubeDL)


def test_timeout_twice_then_success_on_third_attempt(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {
        'single': [
            "HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out.",
            "HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out.",
            'success',
        ]
    }
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    files = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)

    assert ScenarioYoutubeDL.calls['single'] == 3
    assert sleeps == [3.0, 6.0]
    assert len(files) == 1
    assert Path(files[0]).is_file()
    assert not (tmp_path / '.yt-dlp-tui-single').exists()


def test_http_503_retries_once_then_succeeds(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {'single': ['HTTP Error 503: Service Unavailable', 'success']}
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    files = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)

    assert ScenarioYoutubeDL.calls['single'] == 2
    assert sleeps == [3.0]
    assert len(files) == 1


def test_http_429_uses_larger_backoff(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {'single': ['HTTP Error 429: Too Many Requests', 'success']}
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    files = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)

    assert ScenarioYoutubeDL.calls['single'] == 2
    assert sleeps == [10.0]
    assert len(files) == 1


def test_permission_error_gets_zero_network_retries(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {'single': [PermissionError(13, 'Permission denied')]}
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)

    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 1
    assert sleeps == []


def test_private_video_gets_zero_network_retries(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {'single': ['ERROR: [youtube] x: video is private']}
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)

    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 1
    assert sleeps == []


def test_auth_uses_cookie_refresh_not_network_retry(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {
        'single': ["ERROR: [youtube] x: Sign in to confirm you're not a bot", 'success']
    }
    sleeps = []
    refresh_calls = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    result = downloader._download_single(
        'https://example.test/video', str(tmp_path), 'audio', 'best',
        lambda reason: refresh_calls.append(reason) or True,
    )

    assert len(result) == 1
    assert len(refresh_calls) == 1
    assert sleeps == []
    assert ScenarioYoutubeDL.calls['single'] == 2


def test_js_challenge_never_network_retries_or_refreshes_auth(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {
        'single': ['n challenge solving failed; The page needs to be reloaded.']
    }
    sleeps = []
    refresh_calls = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    result = downloader._download_single(
        'https://example.test/video', str(tmp_path), 'audio', 'best',
        lambda reason: refresh_calls.append(reason) or True,
    )

    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 1
    assert sleeps == []
    assert refresh_calls == []


def _playlist_item(index=1, video_id='v1'):
    return {
        'index': index,
        'video_id': video_id,
        'title': f'Video {index}',
        'url': f'https://example.test/watch?v={video_id}',
        'available': True,
        'status': 'pending',
        'attempts': 0,
        'retry_count': 0,
        'last_retry_at': None,
        'started_at': None,
        'completed_at': None,
        'final_file': None,
        'last_error': None,
        'last_error_kind': None,
        'progress': {'percent': 0.0, 'downloaded_bytes': 0, 'total_bytes': None},
    }


def _playlist_state(items):
    return {
        'schema_version': 3,
        'task_type': 'playlist',
        'playlist': {'id': 'p', 'title': 'Playlist', 'source_url': 'https://example.test/?list=p'},
        'mode': {'format': 'audio', 'quality': 'best'},
        'status': 'in_progress',
        'items': items,
        'audit': {},
    }


def test_ctrl_c_during_retry_leaves_playlist_item_resumable(monkeypatch, tmp_path):
    item = _playlist_item()
    state = _playlist_state([item])
    task_dir = tmp_path / 'playlist'
    task_dir.mkdir()
    ScenarioYoutubeDL.scenarios = {'v1': ["HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out."]}
    ScenarioYoutubeDL.write_partial_on_failure = True

    def interrupt_retry(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(downloader, '_retry_wait', interrupt_retry)

    with pytest.raises(KeyboardInterrupt):
        downloader._download_item_to_stage(item, str(task_dir), state, 'audio', 'best')

    assert item['status'] == 'pending'
    assert item['retry_count'] == 1
    assert not downloader.stage_dir(str(task_dir), 'v1') or not Path(downloader.stage_dir(str(task_dir), 'v1')).exists()


def test_exhausted_network_failure_leaves_no_part_file(monkeypatch, tmp_path):
    item = _playlist_item()
    state = _playlist_state([item])
    task_dir = tmp_path / 'playlist'
    task_dir.mkdir()
    ScenarioYoutubeDL.scenarios = {'v1': ["HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out."]}
    ScenarioYoutubeDL.write_partial_on_failure = True
    monkeypatch.setattr(downloader.time, 'sleep', lambda seconds: None)

    result = downloader._download_item_to_stage(item, str(task_dir), state, 'audio', 'best')

    assert result is None
    assert item['status'] == 'failed'
    assert item['attempts'] == 3
    assert item['retry_count'] == 2
    assert item['last_error_kind'] == ErrorKind.TRANSIENT_NETWORK.value
    assert not list(task_dir.rglob('*.part'))
    assert not Path(downloader.stage_dir(str(task_dir), 'v1')).exists()


def test_playlist_three_items_recovers_middle_timeout_and_audit_passes(monkeypatch, tmp_path):
    items = [_playlist_item(1, 'v1'), _playlist_item(2, 'v2'), _playlist_item(3, 'v3')]
    state = _playlist_state(items)
    task_dir = tmp_path / 'Playlist'
    task_dir.mkdir()
    metadata = {'id': 'p', 'title': 'Playlist', 'entries': items}
    ScenarioYoutubeDL.scenarios = {
        'v1': ['success'],
        'v2': ["HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out.", 'success'],
        'v3': ['success'],
    }
    monkeypatch.setattr(downloader.time, 'sleep', lambda seconds: None)
    monkeypatch.setattr(downloader, '_extract_playlist', lambda url: metadata)
    monkeypatch.setattr(downloader, '_prepare_playlist_state', lambda *args: (str(task_dir), state))
    monkeypatch.setattr(downloader, '_integrity_check', lambda path, ffmpeg_exe=None: (True, None))

    files = downloader._download_playlist(
        'https://example.test/?list=p', str(tmp_path), 'audio', 'best', None
    )

    assert len(files) == 3
    assert [item['status'] for item in items] == ['completed', 'completed', 'completed']
    assert items[1]['attempts'] == 2
    assert items[1]['retry_count'] == 1
    assert items[1]['last_error'] is None
    assert state['audit']['status'] == 'passed'
    assert state['status'] == 'completed'


def test_download_opts_override_large_yt_dlp_defaults_with_small_budget(tmp_path):
    logger = downloader.CaptureLogger()
    opts = downloader._build_download_opts(str(tmp_path), 'audio', 'best', None, logger)
    assert opts['retries'] == 1
    assert opts['fragment_retries'] == 2
    assert opts['extractor_retries'] == 1
    assert opts['file_access_retries'] == 1
    assert opts['socket_timeout'] == 15.0
    assert set(opts['retry_sleep_functions']) == {'http', 'fragment', 'extractor', 'file_access'}


def test_simple_video_exhaustion_is_clean_and_friendly(monkeypatch, tmp_path, capsys):
    ScenarioYoutubeDL.scenarios = {'single': ["HTTPSConnectionPool(host='x.googlevideo.com'): Read timed out."]}
    ScenarioYoutubeDL.write_partial_on_failure = True
    monkeypatch.setattr(downloader.time, 'sleep', lambda seconds: None)

    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)
    out = capsys.readouterr().out

    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 3
    assert 'continuou instável após 3 tentativas' in out
    assert not (tmp_path / '.yt-dlp-tui-single').exists()
    assert not list(tmp_path.rglob('*.part'))


def test_metadata_recovery_uses_same_bounded_classifier_policy(monkeypatch):
    from yt_dlp_tui.errors import ClassifiedFailureError, classify_failure

    calls = {'n': 0}
    sleeps = []
    monkeypatch.setattr(downloader.time, 'sleep', sleeps.append)

    def operation():
        calls['n'] += 1
        if calls['n'] < 3:
            raise ClassifiedFailureError(classify_failure(RuntimeError('HTTP Error 503: Service Unavailable')))
        return 'ok'

    assert downloader._call_with_recovery(operation, None, label='metadata') == 'ok'
    assert calls['n'] == 3
    assert sleeps == [3.0, 6.0]


def test_retry_wait_state_from_crash_is_restored_to_pending(monkeypatch, tmp_path):
    item = _playlist_item()
    item['status'] = 'retry_wait'
    item['last_error_kind'] = ErrorKind.TRANSIENT_NETWORK.value
    state = _playlist_state([item])
    task_dir = tmp_path / 'playlist'
    task_dir.mkdir()
    stage = Path(downloader.stage_dir(str(task_dir), 'v1'))
    stage.mkdir(parents=True)
    (stage / 'partial.part').write_bytes(b'x' * 10)

    downloader._recover_incomplete_state(str(task_dir), state)

    assert item['status'] == 'pending'
    assert not stage.exists()


def test_disk_full_gets_zero_network_retries_and_cleans_partial(monkeypatch, tmp_path):
    class DiskFullYDL(ScenarioYoutubeDL):
        calls = 0
        def download(self, urls):
            type(self).calls += 1
            stage = Path(self.opts['outtmpl']).parent
            stage.mkdir(parents=True, exist_ok=True)
            (stage / 'partial.part').write_bytes(b'partial')
            import errno
            raise OSError(errno.ENOSPC, 'No space left on device')
    monkeypatch.setattr(downloader.yt_dlp, 'YoutubeDL', DiskFullYDL)
    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)
    assert result == []
    assert DiskFullYDL.calls == 1
    assert not list(tmp_path.rglob('*.part'))


def test_format_error_gets_zero_network_retries(monkeypatch, tmp_path):
    ScenarioYoutubeDL.scenarios = {'single': ['ERROR: Requested format is not available']}
    result = downloader._download_single('https://example.test/video', str(tmp_path), 'video', '1080', None)
    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 1


def test_unknown_error_gets_zero_network_retries_and_remains_diagnostic(monkeypatch, tmp_path, capsys):
    ScenarioYoutubeDL.scenarios = {'single': ['mystery-failure-xyz']}
    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)
    assert result == []
    assert ScenarioYoutubeDL.calls['single'] == 1
    out = capsys.readouterr().out
    assert 'motivo não reconhecido' in out
    assert 'mystery-failure-xyz' in out


def test_connection_reset_retries_and_recovers(monkeypatch, tmp_path):
    class ResetYDL(ScenarioYoutubeDL):
        calls = 0
        def download(self, urls):
            type(self).calls += 1
            if type(self).calls == 1:
                raise ConnectionResetError('connection reset by peer')
            stage = Path(self.opts['outtmpl']).parent
            stage.mkdir(parents=True, exist_ok=True)
            (stage / 'Video [single].m4a').write_bytes(b'good' * 1200)
            return 0
    monkeypatch.setattr(downloader.yt_dlp, 'YoutubeDL', ResetYDL)
    result = downloader._download_single('https://example.test/video', str(tmp_path), 'audio', 'best', None)
    assert len(result) == 1
    assert ResetYDL.calls == 2
