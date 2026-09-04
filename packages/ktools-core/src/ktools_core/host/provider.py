from __future__ import annotations

import sys
import threading
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class HostPlatform(str, Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    DARWIN = "darwin"
    UNKNOWN = "unknown"


class HostCapability(str, Enum):
    PROCESS_LAUNCH = "process_launch"
    CLIPBOARD_SYNC = "clipboard_sync"
    HOST_HEALTH = "host_health"
    NOTIFICATIONS = "notifications"
    ELEVATION = "elevation"
    FS_WATCH = "fs_watch"


class HostCapabilityUnsupportedError(RuntimeError):
    """Raised when an operation is invoked on a host provider that does not support it."""
    pass


class HostProvider(ABC):
    """Abstract contract for operating system host integration."""

    @property
    @abstractmethod
    def platform(self) -> HostPlatform:
        """The host platform classification."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider identifier."""
        pass

    @abstractmethod
    def supported_capabilities(self) -> Tuple[HostCapability, ...]:
        """List of capabilities supported natively and safely by this provider."""
        pass

    def is_capability_supported(self, capability: Union[HostCapability, str]) -> bool:
        """Query whether a capability is supported by this provider."""
        cap_val = capability.value if isinstance(capability, HostCapability) else str(capability)
        return any(c.value == cap_val for c in self.supported_capabilities())

    @abstractmethod
    def get_health_metrics(self, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Collect platform, resource, and storage metrics."""
        pass

    @abstractmethod
    def execute_process(
        self,
        command: Union[List[str], str],
        cwd: Optional[str] = None,
        timeout_seconds: float = 30.0,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Safely execute an external host subprocess."""
        pass

    @abstractmethod
    def read_clipboard(self) -> str:
        """Read system clipboard text."""
        pass

    @abstractmethod
    def write_clipboard(self, text: str) -> None:
        """Write system clipboard text."""
        pass

    @abstractmethod
    def send_notification(self, title: str, message: str, level: str = "info") -> bool:
        """Send a host notification / alert."""
        pass


_ACTIVE_HOST_PROVIDER: Optional[HostProvider] = None
_ACTIVE_PROVIDER_LOCK = threading.Lock()


def get_active_host_provider() -> HostProvider:
    """Returns the registered active HostProvider or auto-detects the platform provider."""
    global _ACTIVE_HOST_PROVIDER
    with _ACTIVE_PROVIDER_LOCK:
        if _ACTIVE_HOST_PROVIDER is not None:
            return _ACTIVE_HOST_PROVIDER

        if sys.platform == "win32":
            from .windows import WindowsHostProvider
            _ACTIVE_HOST_PROVIDER = WindowsHostProvider()
        elif sys.platform.startswith("linux"):
            from .linux import LinuxHostProvider
            _ACTIVE_HOST_PROVIDER = LinuxHostProvider()
        else:
            from .windows import WindowsHostProvider
            _ACTIVE_HOST_PROVIDER = WindowsHostProvider()
        return _ACTIVE_HOST_PROVIDER


def set_active_host_provider(provider: Optional[HostProvider]) -> None:
    """Explicitly inject a host provider (useful for cross-platform simulation and testing)."""
    global _ACTIVE_HOST_PROVIDER
    with _ACTIVE_PROVIDER_LOCK:
        _ACTIVE_HOST_PROVIDER = provider
