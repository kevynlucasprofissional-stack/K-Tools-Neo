from __future__ import annotations

import unittest

from ktools_text.capability import TextDocument, TextMergeError, render_merged_text


DOCS = (
    TextDocument(name="a.md", text="Alpha"),
    TextDocument(name="b.txt", text="Beta"),
)


class RenderMergedTextCharacterizationTests(unittest.TestCase):
    def test_complete_separator_matches_legacy_bytes(self) -> None:
        expected = (
            "\n---\n<!-- INÍCIO DO ARQUIVO: a.md -->\n---\n\nAlpha"
            "\n\n---\n<!-- FIM DO ARQUIVO: a.md -->\n---\n\n"
            "\n---\n<!-- INÍCIO DO ARQUIVO: b.txt -->\n---\n\nBeta"
            "\n\n---\n<!-- FIM DO ARQUIVO: b.txt -->\n---\n\n"
        )
        self.assertEqual(render_merged_text(DOCS, "completo"), expected)

    def test_simple_separator_matches_legacy_bytes(self) -> None:
        expected = "\n\n# a.md\n\nAlpha\n\n\n\n# b.txt\n\nBeta\n\n"
        self.assertEqual(render_merged_text(DOCS, "simples"), expected)

    def test_no_separator_matches_legacy_bytes(self) -> None:
        self.assertEqual(render_merged_text(DOCS, "nenhum"), "Alpha\n\nBeta\n\n")

    def test_empty_documents_and_unknown_mode_are_rejected(self) -> None:
        with self.assertRaises(TextMergeError):
            render_merged_text((), "completo")
        with self.assertRaises(TextMergeError):
            render_merged_text(DOCS, "unsupported")


if __name__ == "__main__":
    unittest.main()
