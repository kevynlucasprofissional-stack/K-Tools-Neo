import json
from pathlib import Path
import sys
import types

import pytest

if "yt_dlp" not in sys.modules:
    fake_yt_dlp = types.ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = object
    sys.modules["yt_dlp"] = fake_yt_dlp

from yt_dlp_tui import control, downloader


def _item(video_id='v1', status='pending', available=True):
    return {
        'index': 1,
        'video_id': video_id,
        'title': 'Video 1',
        'url': f'https://example.test/watch?v={video_id}',
        'available': available,
        'status': status,
        'attempts': 1,
        'started_at': '2026-01-01T00:00:00+00:00',
        'completed_at': '2026-01-01T00:01:00+00:00' if status == 'completed' else None,
        'final_file': f'Video [{video_id}].m4a' if status == 'completed' else None,
        'last_error': None,
        'progress': {'percent': 100.0 if status == 'completed' else 0.0, 'downloaded_bytes': 4096 if status == 'completed' else 0, 'total_bytes': 4096 if status == 'completed' else None},
    }


def _state_v2(items):
    return {
        'schema_version': 2,
        'task_type': 'playlist',
        'playlist': {'id': 'p', 'title': 'Playlist', 'source_url': 'https://example.test/?list=p'},
        'mode': {'format': 'audio', 'quality': 'best'},
        'status': 'in_progress',
        'created_at': '2026-01-01T00:00:00+00:00',
        'updated_at': '2026-01-01T00:00:00+00:00',
        'items': items,
        'audit': {'status': 'not_run', 'last_run_at': None, 'checked': 0, 'ok': 0, 'failed': 0},
    }


def _metadata(items):
    fresh = []
    for i, old in enumerate(items, 1):
        fresh.append({
            'index': i,
            'video_id': old['video_id'],
            'title': old['title'],
            'url': old['url'],
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
        })
    return {'id': 'p', 'title': 'Playlist', 'entries': fresh}


def test_v2_control_migrates_without_losing_completed_progress(monkeypatch, tmp_path):
    task_dir = tmp_path / 'Playlist'
    task_dir.mkdir()
    completed = _item(status='completed')
    state = _state_v2([completed])
    (task_dir / completed['final_file']).write_bytes(b'x' * 4096)
    control.save_control(str(task_dir), state)
    monkeypatch.setattr(downloader, '_integrity_check', lambda path, ffmpeg_exe=None: (True, None))

    _, migrated = downloader._prepare_playlist_state(
        str(tmp_path), _metadata([completed]), 'https://example.test/?list=p', 'audio', 'best'
    )

    assert migrated['schema_version'] == 3
    assert migrated['items'][0]['status'] == 'completed'
    assert migrated['items'][0]['final_file'] == completed['final_file']
    assert migrated['items'][0]['retry_count'] == 0
    assert migrated['items'][0]['last_retry_at'] is None
    assert migrated['items'][0]['last_error_kind'] is None
    assert list(task_dir.glob('YT-DLP-TUI-controle-*.bak.json'))


def test_invalid_json_is_preserved_and_progress_reconstructed_from_integral_media(monkeypatch, tmp_path):
    task_dir = tmp_path / 'Playlist'
    task_dir.mkdir()
    control_file = task_dir / control.CONTROL_FILENAME
    original = '{this is broken json'
    control_file.write_text(original, encoding='utf-8')
    media = task_dir / 'Video 1 [v1].m4a'
    media.write_bytes(b'x' * 4096)

    item = _item(status='pending')
    monkeypatch.setattr(downloader, '_integrity_check', lambda path, ffmpeg_exe=None: (True, None))

    _, rebuilt = downloader._prepare_playlist_state(
        str(tmp_path), _metadata([item]), 'https://example.test/?list=p', 'audio', 'best'
    )

    preserved = list(task_dir.glob('YT-DLP-TUI-controle-*.corrupt.json'))
    assert len(preserved) == 1
    assert preserved[0].read_text(encoding='utf-8') == original
    assert rebuilt['schema_version'] == 3
    assert rebuilt['items'][0]['status'] == 'completed'
    assert rebuilt['items'][0]['final_file'] == media.name
    assert json.loads(control_file.read_text(encoding='utf-8'))['items'][0]['status'] == 'completed'


def test_corrupt_control_does_not_mark_bad_existing_media_completed(monkeypatch, tmp_path):
    task_dir = tmp_path / 'Playlist'
    task_dir.mkdir()
    (task_dir / control.CONTROL_FILENAME).write_text('{broken', encoding='utf-8')
    media = task_dir / 'Video 1 [v1].m4a'
    media.write_bytes(b'x' * 4096)
    item = _item(status='pending')
    monkeypatch.setattr(downloader, '_integrity_check', lambda path, ffmpeg_exe=None: (False, 'corrupt'))

    _, rebuilt = downloader._prepare_playlist_state(
        str(tmp_path), _metadata([item]), 'https://example.test/?list=p', 'audio', 'best'
    )

    assert rebuilt['items'][0]['status'] == 'pending'
    assert rebuilt['items'][0]['final_file'] is None
    assert not media.exists()


def test_structurally_invalid_control_is_not_treated_as_missing(tmp_path):
    task_dir = tmp_path / 'Playlist'
    task_dir.mkdir()
    (task_dir / control.CONTROL_FILENAME).write_text(
        json.dumps({'schema_version': 3, 'task_type': 'playlist', 'playlist': {'id': 'p'}, 'mode': {}, 'items': ['bad']}),
        encoding='utf-8',
    )

    with pytest.raises(control.CorruptControlError):
        control.load_control(str(task_dir))


@pytest.mark.parametrize("patch", [
    {"video_id": None},
    {"status": None},
    {"available": "yes"},
    {"final_file": 123},
    {"attempts": "many"},
    {"retry_count": "many"},
    {"progress": "bad"},
])
def test_semantically_corrupt_control_item_is_rejected(tmp_path, patch):
    task_dir = tmp_path / "Playlist"
    task_dir.mkdir()
    item = _item(status="pending")
    item.update(patch)
    state = _state_v2([item])
    state["schema_version"] = 3
    (task_dir / control.CONTROL_FILENAME).write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(control.CorruptControlError):
        control.load_control(str(task_dir))
