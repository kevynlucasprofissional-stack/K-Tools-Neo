from __future__ import annotations

import http.cookiejar
from enum import Enum
from typing import Protocol, runtime_checkable


class AuthState(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    NOT_CONNECTED = "NOT_CONNECTED"
    CONNECTING = "CONNECTING"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REAUTH_REQUIRED = "REAUTH_REQUIRED"
    ERROR = "ERROR"


@runtime_checkable
class AuthProvider(Protocol):
    @property
    def name(self) -> str:
        ...

    def is_available(self) -> bool:
        ...

    def get_state(self) -> AuthState:
        ...

    def get_cookiejar(self) -> http.cookiejar.CookieJar | None:
        ...

    def refresh(self) -> AuthState:
        ...

    def launch_login_flow(self) -> None:
        ...
