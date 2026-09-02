from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class TextMergeError(ValueError):
    pass


@dataclass(frozen=True)
class TextDocument:
    name: str
    text: str


def render_merged_text(documents: Sequence[TextDocument], separator_mode: str = "completo") -> str:
    raise NotImplementedError("RED: Text merge capability is not implemented yet")
