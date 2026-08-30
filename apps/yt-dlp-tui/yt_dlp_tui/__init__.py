try:
    from importlib.metadata import version
    __version__ = version("yt-dlp-tui")
except Exception:
    __version__ = "unknown"
