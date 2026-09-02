from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


class TextMergeError(ValueError):
    """Base classified error for the Text merge capability."""


@dataclass(frozen=True)
class TextDocument:
    name: str
    text: str


VALID_SEPARATOR_MODES = frozenset({"completo", "simples", "nenhum"})


def _validate_document(document: TextDocument) -> None:
    if not isinstance(document.name, str) or not document.name:
        raise TextMergeError("Text document name must be a non-empty string")
    if not isinstance(document.text, str):
        raise TextMergeError(f"Text document {document.name!r} content must be a string")


def render_document_block(document: TextDocument, separator_mode: str = "completo") -> str:
    """Render one source block using the exact supported legacy separators."""
    _validate_document(document)
    if separator_mode not in VALID_SEPARATOR_MODES:
        raise TextMergeError(
            f"separator_mode must be one of {sorted(VALID_SEPARATOR_MODES)}, got {separator_mode!r}"
        )

    if separator_mode == "completo":
        return (
            f"\n---\n<!-- INÍCIO DO ARQUIVO: {document.name} -->\n---\n\n"
            f"{document.text}"
            f"\n\n---\n<!-- FIM DO ARQUIVO: {document.name} -->\n---\n\n"
        )
    if separator_mode == "simples":
        return f"\n\n# {document.name}\n\n{document.text}\n\n"
    return f"{document.text}\n\n"


def render_merged_text(
    documents: Sequence[TextDocument], separator_mode: str = "completo"
) -> str:
    """Pure deterministic merge renderer used by tests and higher-level owners."""
    if not documents:
        raise TextMergeError("At least one text document is required")
    if separator_mode not in VALID_SEPARATOR_MODES:
        raise TextMergeError(
            f"separator_mode must be one of {sorted(VALID_SEPARATOR_MODES)}, got {separator_mode!r}"
        )
    return "".join(render_document_block(document, separator_mode) for document in documents)
