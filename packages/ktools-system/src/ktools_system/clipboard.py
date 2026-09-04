from __future__ import annotations

import sys
import subprocess

# In-memory clipboard cache for head-less/testing fallback
_IN_MEMORY_CLIPBOARD: str = ""


def get_clipboard() -> str:
    global _IN_MEMORY_CLIPBOARD
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.OpenClipboard.restype = wintypes.BOOL
            user32.CloseClipboard.argtypes = []
            user32.CloseClipboard.restype = wintypes.BOOL
            user32.GetClipboardData.argtypes = [wintypes.UINT]
            user32.GetClipboardData.restype = wintypes.HANDLE
            kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalUnlock.restype = wintypes.BOOL

            CF_UNICODETEXT = 13
            if user32.OpenClipboard(None):
                try:
                    h_clip = user32.GetClipboardData(CF_UNICODETEXT)
                    if h_clip:
                        p_text = kernel32.GlobalLock(h_clip)
                        if p_text:
                            try:
                                return ctypes.wstring_at(p_text)
                            finally:
                                kernel32.GlobalUnlock(h_clip)
                finally:
                    user32.CloseClipboard()
        except Exception:
            pass

    return _IN_MEMORY_CLIPBOARD


def set_clipboard(text: str) -> None:
    global _IN_MEMORY_CLIPBOARD
    _IN_MEMORY_CLIPBOARD = text

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            GMEM_MOVEABLE = 0x0002
            CF_UNICODETEXT = 13

            user32.OpenClipboard.argtypes = [wintypes.HWND]
            user32.OpenClipboard.restype = wintypes.BOOL
            user32.EmptyClipboard.argtypes = []
            user32.EmptyClipboard.restype = wintypes.BOOL
            user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
            user32.SetClipboardData.restype = wintypes.HANDLE
            user32.CloseClipboard.argtypes = []
            user32.CloseClipboard.restype = wintypes.BOOL

            kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
            kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
            kernel32.GlobalUnlock.restype = wintypes.BOOL

            if user32.OpenClipboard(None):
                try:
                    user32.EmptyClipboard()
                    encoded = text.encode("utf-16-le") + b"\x00\x00"
                    h_glob = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
                    if h_glob:
                        ptr = kernel32.GlobalLock(h_glob)
                        if ptr:
                            ctypes.memmove(ptr, encoded, len(encoded))
                            kernel32.GlobalUnlock(h_glob)
                            user32.SetClipboardData(CF_UNICODETEXT, h_glob)
                finally:
                    user32.CloseClipboard()
        except Exception:
            pass
