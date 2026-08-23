from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_downloader_uses_central_classifier_and_no_legacy_auth_string_classifier():
    source = (ROOT / "yt_dlp_tui" / "downloader.py").read_text(encoding="utf-8")
    assert "classify_failure" in source
    assert "is_auth_cache_error" not in source
    assert "_is_auth_failure" not in source
    assert "lower = str(e).lower()" not in source


def test_auth_cache_no_longer_owns_error_taxonomy():
    source = (ROOT / "yt_dlp_tui" / "auth_cache.py").read_text(encoding="utf-8")
    assert "AUTH_ERROR_MARKERS" not in source
    assert "the page needs to be reloaded" not in source.lower()
    assert "is_auth_cache_error" not in source


def test_raw_yt_dlp_error_is_not_printed_by_logger():
    errors_source = (ROOT / "yt_dlp_tui" / "errors.py").read_text(encoding="utf-8")
    downloader_source = (ROOT / "yt_dlp_tui" / "downloader.py").read_text(encoding="utf-8")
    assert 'print(f"Error:' not in errors_source
    assert 'print(f"Error:' not in downloader_source


def test_retry_policy_is_centralized_and_bounded():
    downloader_source = (ROOT / "yt_dlp_tui" / "downloader.py").read_text(encoding="utf-8")
    policy_source = (ROOT / "yt_dlp_tui" / "retry_policy.py").read_text(encoding="utf-8")
    assert "retry_decision" in downloader_source
    assert "yt_dlp_retry_options" in downloader_source
    assert "MAX_EXTERNAL_ATTEMPTS = 3" in policy_source
    assert "YT_DLP_RETRIES = 1" in policy_source
    assert "YT_DLP_FRAGMENT_RETRIES = 2" in policy_source
    assert '"retry_sleep_functions"' in policy_source


def test_no_bundled_cookie_or_remote_ejs_fetch_remains():
    assert not (ROOT / 'cookies.txt').exists()
    downloader_source = (ROOT / 'yt_dlp_tui' / 'downloader.py').read_text(encoding='utf-8')
    auth_source = (ROOT / 'yt_dlp_tui' / 'auth_cache.py').read_text(encoding='utf-8')
    build_source = (ROOT / 'GERAR_EXE_WINDOWS.bat').read_text(encoding='utf-8')
    assert ('remote_' + 'components') not in downloader_source
    assert ('ejs' + ':github') not in downloader_source
    assert 'bundled_cookie_file' not in auth_source
    assert 'bootstrap_managed_cache' not in auth_source
    assert 'copy /Y "cookies.txt"' not in build_source


def test_auth_cache_uses_only_private_managed_persistence():
    auth_source = (ROOT / 'yt_dlp_tui' / 'auth_cache.py').read_text(encoding='utf-8')
    assert 'YT_DLP_TUI_COOKIES' in auth_source
    assert 'LOCALAPPDATA' in auth_source
    assert 'app_dir()' not in auth_source
    assert 'env_path = os.environ.get' not in auth_source


def test_pyinstaller_bundle_preserves_ejs_and_package_metadata():
    spec = (ROOT / 'yt-dlp-tui.spec').read_text(encoding='utf-8')
    assert "'yt_dlp_ejs'" in spec
    assert 'copy_metadata' in spec
    assert "'yt-dlp'" in spec
    assert "'yt-dlp-ejs'" in spec


def test_pyinstaller_includes_retry_policy_module():
    spec = (ROOT / 'yt-dlp-tui.spec').read_text(encoding='utf-8')
    assert "'yt_dlp_tui.retry_policy'" in spec


def test_release_runtime_dependencies_are_pinned_for_reproducibility():
    pyproject = (ROOT / 'pyproject.toml').read_text(encoding='utf-8')
    assert 'yt-dlp[default]==2026.8.19' in pyproject
    assert 'imageio-ffmpeg==0.6.0' in pyproject
    assert 'version = "0.6.6"' in pyproject


def test_windows_build_script_stops_if_prepare_or_tests_fail():
    source = (ROOT / 'GERAR_EXE_WINDOWS.bat').read_text(encoding='utf-8')
    assert 'call INICIAR_YT-DLP-TUI.bat --prepare-only' in source
    assert 'if errorlevel 1 goto :err' in source
    assert '-m pytest -q' in source
    assert '-m compileall -q yt_dlp_tui' in source


def test_windows_launcher_enforces_python_310_or_newer():
    source = (ROOT / 'INICIAR_YT-DLP-TUI.bat').read_text(encoding='utf-8')
    assert 'sys.version_info >= (3,10)' in source


def test_pytest_can_resolve_source_package_from_project_config():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '[tool.pytest.ini_options]' in text
    assert 'pythonpath = ["."]' in text


def test_pyinstaller_preserves_own_distribution_metadata():
    text = (ROOT / "yt-dlp-tui.spec").read_text(encoding="utf-8")
    assert "('yt-dlp-tui', 'yt-dlp', 'yt-dlp-ejs')" in text
