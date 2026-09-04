from __future__ import annotations

from ktools_core.host import get_active_host_provider


def get_clipboard() -> str:
    """Reads clipboard text via active HostProvider."""
    return get_active_host_provider().read_clipboard()


def set_clipboard(text: str) -> None:
    """Writes clipboard text via active HostProvider."""
    get_active_host_provider().write_clipboard(text)
