# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, copy_metadata


datas = []
binaries = []
hiddenimports = ['yt_dlp_tui.cli', 'yt_dlp_tui.downloader', 'yt_dlp_tui.auth_cache', 'yt_dlp_tui.control', 'yt_dlp_tui.errors', 'yt_dlp_tui.retry_policy']

for package in ('yt_dlp', 'yt_dlp_ejs', 'imageio_ffmpeg'):
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception:
        pass

for distribution in ('yt-dlp-tui', 'yt-dlp', 'yt-dlp-ejs'):
    try:
        datas += copy_metadata(distribution)
    except Exception:
        pass


a = Analysis(
    ['yt_dlp_tui/__main__.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='yt-dlp-tui',
    debug=False,
    console=True,
    icon=None,
)
