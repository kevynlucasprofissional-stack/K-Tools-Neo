#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extrator de Transcrição tl;dv com GUI CustomTkinter
Autor: versão melhorada para Kevyn Lucas

O que faz:
- Seleciona um HTML salvo/exportado do tl;dv.
- Encontra o bloco id="transcript-container".
- Extrai falas, timestamps, oradores e texto.
- Salva em TXT, CSV, JSON, Markdown e/ou SRT.
- Instala automaticamente dependências ausentes quando executado como .py.

Observação sobre EXE:
- A auto-instalação de bibliotecas funciona melhor rodando como script Python.
- Para empacotar com Auto Py To Exe/PyInstaller, inclua customtkinter e beautifulsoup4 no build.
- Para CustomTkinter, prefira "One Directory" em vez de "One File", porque a biblioteca usa arquivos de tema/fonte.
"""

from __future__ import annotations

import csv
import importlib
import json
import os
import platform
import re
import subprocess
import sys
import threading
import traceback
import webbrowser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable

# ============================================================
# Bootstrap de dependências
# ============================================================

DEPENDENCIES = {
    # import_name: pip_name
    "bs4": "beautifulsoup4",
    "customtkinter": "customtkinter",
}


def _running_from_frozen_exe() -> bool:
    return bool(getattr(sys, "frozen", False))


def ensure_dependencies() -> None:
    """
    Instala automaticamente as dependências que não estiverem disponíveis.

    Nota:
    - Em um executável congelado por PyInstaller, o pip geralmente não está disponível.
      Nesse caso, mostramos erro orientando a empacotar as libs junto.
    """
    missing: list[tuple[str, str]] = []

    for import_name, pip_name in DEPENDENCIES.items():
        try:
            importlib.import_module(import_name)
        except ImportError:
            missing.append((import_name, pip_name))

    if not missing:
        return

    if _running_from_frozen_exe():
        libs = ", ".join(pip_name for _, pip_name in missing)
        raise RuntimeError(
            "Dependências ausentes no executável: "
            f"{libs}. Recrie o EXE incluindo essas bibliotecas no PyInstaller/Auto Py To Exe."
        )

    print("Instalando dependências ausentes...")
    for _, pip_name in missing:
        print(f"  - {pip_name}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", pip_name]
        )

    # Invalida cache de importação depois da instalação.
    importlib.invalidate_caches()


try:
    ensure_dependencies()
except Exception as exc:
    print("\nErro ao instalar dependências automaticamente:")
    print(exc)
    input("\nPressione ENTER para sair...")
    raise SystemExit(1)


import customtkinter as ctk
from bs4 import BeautifulSoup
from bs4.element import Tag
from tkinter import filedialog, messagebox


# ============================================================
# Modelo e utilitários
# ============================================================

@dataclass
class TranscriptBlock:
    index: int
    timestamp: str
    start_ms: int
    speaker: str
    text: str


def ms_to_stamp(ms: int) -> str:
    """Converte milissegundos para MM:SS ou HH:MM:SS."""
    ms = int(ms or 0)
    seconds = max(0, ms // 1000)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def ms_to_srt_stamp(ms: int) -> str:
    """Converte milissegundos para padrão SRT: HH:MM:SS,mmm."""
    ms = max(0, int(ms or 0))
    milliseconds = ms % 1000
    total_seconds = ms // 1000
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d},{milliseconds:03d}"


def clean_text_from_words(words: Iterable[str]) -> str:
    """
    Junta palavras vindas dos spans do tl;dv e corrige espaços antes de pontuação.
    """
    text = " ".join(w.strip() for w in words if w and w.strip())

    # Remove espaços antes de pontuação.
    text = re.sub(r"\s+([,.!?;:%])", r"\1", text)

    # Corrige espaços com parênteses/colchetes.
    text = re.sub(r"\s+([\)\]\}])", r"\1", text)
    text = re.sub(r"([\(\[\{])\s+", r"\1", text)

    # Corrige aspas simples mais comuns.
    text = re.sub(r"\s+([”’])", r"\1", text)
    text = re.sub(r"([“‘])\s+", r"\1", text)

    # Normaliza espaços repetidos.
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


def safe_filename_stem(value: str) -> str:
    value = (value or "transcricao_tldv").strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value or "transcricao_tldv"


def open_folder(path: Path) -> None:
    path = path.resolve()
    system = platform.system().lower()

    try:
        if system == "windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif system == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception:
        webbrowser.open(path.as_uri())


# ============================================================
# Extração tl;dv
# ============================================================

def _is_transcript_start_marker(node: Tag) -> bool:
    return node.name == "p" and node.get("data-index") is not None


def _tag_and_descendants(tag: Tag) -> list[Tag]:
    tags: list[Tag] = [tag]
    tags.extend(child for child in tag.find_all(True))
    return tags


def _extract_speaker_from_tag(tag: Tag) -> str:
    """
    No HTML do tl;dv, o orador costuma aparecer em:
    <div class="inline">Nome</div>
    """
    for candidate in _tag_and_descendants(tag):
        if candidate.name != "div":
            continue

        classes = candidate.get("class") or []
        if "inline" not in classes:
            continue

        text = candidate.get_text(" ", strip=True)
        if text:
            return text

    return ""


def _extract_words_from_tag(tag: Tag) -> list[str]:
    """
    No HTML do tl;dv, cada palavra costuma aparecer como:
    <span data-speaker="false" data-time="...">palavra</span>
    """
    words: list[str] = []

    for candidate in _tag_and_descendants(tag):
        if candidate.name != "span":
            continue

        if candidate.get("data-speaker") != "false":
            continue

        word = candidate.get_text(" ", strip=True)
        if word:
            words.append(word)

    return words


def extract_tldv_transcript(html_path: str | Path) -> list[TranscriptBlock]:
    html_path = Path(html_path)

    if not html_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {html_path}")

    html = html_path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find(id="transcript-container")
    if container is None:
        raise RuntimeError(
            "Não encontrei o bloco id='transcript-container'.\n\n"
            "Possíveis causas:\n"
            "1. O HTML foi salvo antes de abrir/carregar a aba de transcrição no tl;dv.\n"
            "2. O navegador salvou uma versão incompleta da página.\n"
            "3. O layout do tl;dv mudou.\n\n"
            "Tente abrir a reunião no tl;dv, entrar na aba Transcrição, rolar/carregar o conteúdo "
            "e salvar a página novamente como HTML completo."
        )

    marker_nodes = [
        tag for tag in container.find_all("p")
        if isinstance(tag, Tag) and _is_transcript_start_marker(tag)
    ]

    if not marker_nodes:
        raise RuntimeError(
            "Encontrei id='transcript-container', mas não encontrei falas com "
            "<p data-index='...'>. O HTML pode estar incompleto ou o tl;dv pode ter mudado o layout."
        )

    blocks: list[TranscriptBlock] = []

    for marker in marker_nodes:
        raw_index = marker.get("data-index", "0")
        raw_start_ms = marker.get("data-time", "0")

        try:
            index = int(raw_index)
        except ValueError:
            index = len(blocks)

        try:
            start_ms = int(raw_start_ms)
        except ValueError:
            start_ms = 0

        speaker = ""
        words: list[str] = []

        # Alguns layouts podem colocar palavras dentro do próprio marker.
        words.extend(_extract_words_from_tag(marker))

        # O padrão observado no tl;dv é: marker <p>, depois div do orador,
        # depois os spans da fala até o próximo marker <p data-index>.
        for sibling in marker.next_siblings:
            if not isinstance(sibling, Tag):
                continue

            if _is_transcript_start_marker(sibling):
                break

            if not speaker:
                speaker = _extract_speaker_from_tag(sibling)

            words.extend(_extract_words_from_tag(sibling))

        text = clean_text_from_words(words)
        if not text and not speaker:
            continue

        blocks.append(
            TranscriptBlock(
                index=index,
                timestamp=ms_to_stamp(start_ms),
                start_ms=start_ms,
                speaker=speaker or "Desconhecido",
                text=text,
            )
        )

    # Remove eventuais duplicatas por índice mantendo a primeira ocorrência útil.
    unique: dict[int, TranscriptBlock] = {}
    for block in blocks:
        if block.index not in unique:
            unique[block.index] = block

    blocks = sorted(unique.values(), key=lambda b: (b.index, b.start_ms))

    if not blocks:
        raise RuntimeError("A extração rodou, mas nenhum bloco de transcrição foi encontrado.")

    return blocks


# ============================================================
# Salvamento
# ============================================================

def save_txt(blocks: list[TranscriptBlock], output_path: Path) -> None:
    output_path.write_text(
        "\n\n".join(
            f"[{b.timestamp}] {b.speaker}: {b.text}"
            for b in blocks
        ),
        encoding="utf-8",
    )


def save_csv(blocks: list[TranscriptBlock], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["index", "timestamp", "start_ms", "speaker", "text"],
        )
        writer.writeheader()
        writer.writerows(asdict(block) for block in blocks)


def save_json(blocks: list[TranscriptBlock], output_path: Path) -> None:
    output_path.write_text(
        json.dumps([asdict(block) for block in blocks], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_markdown(blocks: list[TranscriptBlock], output_path: Path, title: str) -> None:
    lines = [
        f"# {title}",
        "",
        f"- Blocos extraídos: **{len(blocks)}**",
        f"- Início: **{blocks[0].timestamp}**",
        f"- Fim: **{blocks[-1].timestamp}**",
        "",
        "---",
        "",
    ]

    for block in blocks:
        lines.append(f"## [{block.timestamp}] {block.speaker}")
        lines.append("")
        lines.append(block.text)
        lines.append("")

    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def save_srt(blocks: list[TranscriptBlock], output_path: Path) -> None:
    cues: list[str] = []

    for i, block in enumerate(blocks, start=1):
        start = block.start_ms

        if i < len(blocks):
            next_start = blocks[i].start_ms
            end = max(start + 1200, next_start - 120)
        else:
            # Última fala: duração aproximada proporcional ao tamanho do texto,
            # com mínimo de 3s e máximo de 12s.
            estimated = max(3000, min(12000, 1500 + len(block.text) * 35))
            end = start + estimated

        line = f"{block.speaker}: {block.text}" if block.speaker else block.text

        cues.append(
            f"{i}\n"
            f"{ms_to_srt_stamp(start)} --> {ms_to_srt_stamp(end)}\n"
            f"{line}"
        )

    output_path.write_text("\n\n".join(cues) + "\n", encoding="utf-8")


SAVE_HANDLERS: dict[str, Callable[..., None]] = {
    "txt": save_txt,
    "csv": save_csv,
    "json": save_json,
    "md": save_markdown,
    "srt": save_srt,
}


# ============================================================
# GUI
# ============================================================

class TldvExtractorApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Extrator de Transcrição tl;dv")
        self.geometry("980x720")
        self.minsize(900, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.html_path_var = ctk.StringVar(value="")
        self.output_dir_var = ctk.StringVar(value="")
        self.filename_stem_var = ctk.StringVar(value="transcricao_tldv")
        self.status_var = ctk.StringVar(value="Selecione um HTML do tl;dv para começar.")
        self.open_folder_var = ctk.BooleanVar(value=True)

        self.format_vars: dict[str, ctk.BooleanVar] = {
            "txt": ctk.BooleanVar(value=True),
            "csv": ctk.BooleanVar(value=True),
            "json": ctk.BooleanVar(value=False),
            "md": ctk.BooleanVar(value=True),
            "srt": ctk.BooleanVar(value=False),
        }

        self.generated_files: list[Path] = []
        self.last_blocks: list[TranscriptBlock] = []

        self._build_layout()

    # ---------------- UI builders ----------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, corner_radius=18)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Extrator de Transcrição tl;dv",
            font=ctk.CTkFont(size=24, weight="bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, padx=18, pady=(14, 2), sticky="ew")

        subtitle = ctk.CTkLabel(
            header,
            text="Selecione o HTML salvo do tl;dv, escolha os formatos e exporte a transcrição em poucos cliques.",
            font=ctk.CTkFont(size=14),
            text_color=("gray25", "gray75"),
            anchor="w",
        )
        subtitle.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="ew")

        file_card = ctk.CTkFrame(self, corner_radius=18)
        file_card.grid(row=1, column=0, padx=18, pady=8, sticky="ew")
        file_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(file_card, text="HTML do tl;dv", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 6), sticky="w"
        )

        self.html_entry = ctk.CTkEntry(
            file_card,
            textvariable=self.html_path_var,
            placeholder_text="Nenhum arquivo selecionado...",
        )
        self.html_entry.grid(row=0, column=1, padx=10, pady=(16, 6), sticky="ew")

        ctk.CTkButton(file_card, text="Selecionar HTML", command=self.choose_html).grid(
            row=0, column=2, padx=(0, 16), pady=(16, 6), sticky="e"
        )

        ctk.CTkLabel(file_card, text="Pasta de saída", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, padx=16, pady=6, sticky="w"
        )

        self.output_entry = ctk.CTkEntry(
            file_card,
            textvariable=self.output_dir_var,
            placeholder_text="Por padrão, usa a mesma pasta do HTML...",
        )
        self.output_entry.grid(row=1, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkButton(file_card, text="Escolher pasta", command=self.choose_output_dir).grid(
            row=1, column=2, padx=(0, 16), pady=6, sticky="e"
        )

        ctk.CTkLabel(file_card, text="Nome base", font=ctk.CTkFont(weight="bold")).grid(
            row=2, column=0, padx=16, pady=(6, 16), sticky="w"
        )

        self.name_entry = ctk.CTkEntry(
            file_card,
            textvariable=self.filename_stem_var,
            placeholder_text="Ex.: reuniao_acirv_01_06_2026",
        )
        self.name_entry.grid(row=2, column=1, padx=10, pady=(6, 16), sticky="ew")

        ctk.CTkCheckBox(
            file_card,
            text="Abrir pasta ao finalizar",
            variable=self.open_folder_var,
        ).grid(row=2, column=2, padx=(0, 16), pady=(6, 16), sticky="w")

        options_card = ctk.CTkFrame(self, corner_radius=18)
        options_card.grid(row=2, column=0, padx=18, pady=8, sticky="ew")
        options_card.grid_columnconfigure(0, weight=1)

        options_top = ctk.CTkFrame(options_card, fg_color="transparent")
        options_top.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="ew")
        options_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            options_top,
            text="Formatos de saída",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        quick_buttons = ctk.CTkFrame(options_top, fg_color="transparent")
        quick_buttons.grid(row=0, column=1, sticky="e")

        ctk.CTkButton(
            quick_buttons,
            text="Selecionar todos",
            width=130,
            command=lambda: self.set_all_formats(True),
        ).grid(row=0, column=0, padx=(0, 8))

        ctk.CTkButton(
            quick_buttons,
            text="Limpar",
            width=80,
            fg_color="gray35",
            hover_color="gray25",
            command=lambda: self.set_all_formats(False),
        ).grid(row=0, column=1)

        formats = ctk.CTkFrame(options_card, fg_color="transparent")
        formats.grid(row=1, column=0, padx=16, pady=(4, 14), sticky="ew")

        labels = {
            "txt": "TXT — leitura simples",
            "md": "Markdown — Obsidian/Notion",
            "csv": "CSV — planilhas",
            "json": "JSON — automações",
            "srt": "SRT — legenda",
        }

        for col, fmt in enumerate(["txt", "md", "csv", "json", "srt"]):
            formats.grid_columnconfigure(col, weight=1)
            ctk.CTkCheckBox(
                formats,
                text=labels[fmt],
                variable=self.format_vars[fmt],
            ).grid(row=0, column=col, padx=8, pady=6, sticky="w")

        body = ctk.CTkFrame(self, corner_radius=18)
        body.grid(row=3, column=0, padx=18, pady=8, sticky="nsew")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(1, weight=1)

        preview_header = ctk.CTkFrame(body, fg_color="transparent")
        preview_header.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        preview_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            preview_header,
            text="Prévia da extração",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            preview_header,
            text="Copiar prévia",
            width=110,
            command=self.copy_preview,
        ).grid(row=0, column=1, sticky="e")

        self.preview_box = ctk.CTkTextbox(body, wrap="word")
        self.preview_box.grid(row=1, column=0, padx=(16, 8), pady=(0, 16), sticky="nsew")
        self.preview_box.insert("1.0", "A prévia aparecerá aqui depois da extração.")
        self.preview_box.configure(state="disabled")

        log_header = ctk.CTkFrame(body, fg_color="transparent")
        log_header.grid(row=0, column=1, padx=(8, 16), pady=(14, 8), sticky="ew")
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header,
            text="Status e logs",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.log_box = ctk.CTkTextbox(body, wrap="word")
        self.log_box.grid(row=1, column=1, padx=(8, 16), pady=(0, 16), sticky="nsew")
        self.log("Pronto. Selecione o HTML do tl;dv.")

        footer = ctk.CTkFrame(self, corner_radius=18)
        footer.grid(row=4, column=0, padx=18, pady=(8, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            textvariable=self.status_var,
            anchor="w",
            text_color=("gray25", "gray75"),
        )
        self.status_label.grid(row=0, column=0, padx=16, pady=14, sticky="ew")

        self.progress = ctk.CTkProgressBar(footer, width=180, mode="indeterminate")
        self.progress.grid(row=0, column=1, padx=10, pady=14)
        self.progress.set(0)

        self.extract_button = ctk.CTkButton(
            footer,
            text="Extrair e salvar",
            width=150,
            height=38,
            command=self.start_extraction,
        )
        self.extract_button.grid(row=0, column=2, padx=(0, 16), pady=14)

    # ---------------- UI helpers ----------------

    def log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_preview(self, text: str) -> None:
        self.preview_box.configure(state="normal")
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("1.0", text)
        self.preview_box.configure(state="disabled")

    def set_all_formats(self, value: bool) -> None:
        for var in self.format_vars.values():
            var.set(value)

    def get_selected_formats(self) -> list[str]:
        return [fmt for fmt, var in self.format_vars.items() if var.get()]

    def choose_html(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o HTML salvo do tl;dv",
            filetypes=[
                ("Arquivos HTML", "*.html *.htm"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not path:
            return

        html_path = Path(path)
        self.html_path_var.set(str(html_path))

        if not self.output_dir_var.get().strip():
            self.output_dir_var.set(str(html_path.parent))

        current_stem = self.filename_stem_var.get().strip()
        if current_stem in {"", "transcricao_tldv"}:
            self.filename_stem_var.set(safe_filename_stem(html_path.stem + "_transcricao"))

        self.status_var.set("HTML selecionado. Escolha os formatos e clique em Extrair e salvar.")
        self.log(f"HTML selecionado: {html_path}")

    def choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Escolha a pasta de saída")

        if not path:
            return

        self.output_dir_var.set(path)
        self.log(f"Pasta de saída definida: {path}")

    def copy_preview(self) -> None:
        text = self.preview_box.get("1.0", "end").strip()
        if not text:
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        self.status_var.set("Prévia copiada para a área de transferência.")
        self.log("Prévia copiada.")

    # ---------------- Extração ----------------

    def validate_inputs(self) -> tuple[Path, Path, str, list[str]]:
        html_value = self.html_path_var.get().strip()
        if not html_value:
            raise ValueError("Selecione um arquivo HTML do tl;dv.")

        html_path = Path(html_value)
        if not html_path.exists():
            raise ValueError(f"O HTML selecionado não existe:\n{html_path}")

        output_value = self.output_dir_var.get().strip()
        output_dir = Path(output_value) if output_value else html_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        filename_stem = safe_filename_stem(self.filename_stem_var.get())

        selected_formats = self.get_selected_formats()
        if not selected_formats:
            raise ValueError("Escolha pelo menos um formato de saída.")

        return html_path, output_dir, filename_stem, selected_formats

    def start_extraction(self) -> None:
        try:
            html_path, output_dir, filename_stem, selected_formats = self.validate_inputs()
        except Exception as exc:
            messagebox.showwarning("Ajuste necessário", str(exc))
            self.status_var.set("Ajuste as opções antes de extrair.")
            return

        self.extract_button.configure(state="disabled", text="Extraindo...")
        self.progress.start()
        self.status_var.set("Extraindo transcrição...")
        self.log("Iniciando extração...")

        thread = threading.Thread(
            target=self._worker_extract_and_save,
            args=(html_path, output_dir, filename_stem, selected_formats),
            daemon=True,
        )
        thread.start()

    def _worker_extract_and_save(
        self,
        html_path: Path,
        output_dir: Path,
        filename_stem: str,
        selected_formats: list[str],
    ) -> None:
        try:
            blocks = extract_tldv_transcript(html_path)
            generated_files: list[Path] = []

            for fmt in selected_formats:
                output_path = output_dir / f"{filename_stem}.{fmt}"
                handler = SAVE_HANDLERS[fmt]

                if fmt == "md":
                    handler(blocks, output_path, title=filename_stem)  # type: ignore[misc]
                else:
                    handler(blocks, output_path)  # type: ignore[misc]

                generated_files.append(output_path)

            self.after(
                0,
                lambda: self._on_success(blocks, generated_files, output_dir),
            )

        except Exception as exc:
            details = traceback.format_exc()
            self.after(0, lambda: self._on_error(exc, details))

    def _build_preview(self, blocks: list[TranscriptBlock], generated_files: list[Path]) -> str:
        lines: list[str] = [
            f"Blocos extraídos: {len(blocks)}",
            f"Início: [{blocks[0].timestamp}] {blocks[0].speaker}: {blocks[0].text}",
            f"Fim:    [{blocks[-1].timestamp}] {blocks[-1].speaker}: {blocks[-1].text}",
            "",
            "Arquivos gerados:",
        ]

        for path in generated_files:
            lines.append(f"- {path}")

        lines.extend(["", "---", "", "Prévia:", ""])

        preview_blocks = blocks[:8]
        if len(blocks) > 10:
            preview_blocks = blocks[:6] + blocks[-2:]

        for block in preview_blocks:
            lines.append(f"[{block.timestamp}] {block.speaker}: {block.text}")
            lines.append("")

        if len(blocks) > 10:
            lines.insert(-4, f"... {len(blocks) - 8} blocos ocultos na prévia ...\n")

        return "\n".join(lines).strip()

    def _on_success(
        self,
        blocks: list[TranscriptBlock],
        generated_files: list[Path],
        output_dir: Path,
    ) -> None:
        self.progress.stop()
        self.extract_button.configure(state="normal", text="Extrair e salvar")

        self.last_blocks = blocks
        self.generated_files = generated_files

        preview = self._build_preview(blocks, generated_files)
        self.set_preview(preview)

        self.status_var.set(f"Concluído: {len(blocks)} blocos extraídos em {len(generated_files)} arquivo(s).")
        self.log(f"Extração concluída: {len(blocks)} blocos.")
        for path in generated_files:
            self.log(f"Arquivo gerado: {path}")

        messagebox.showinfo(
            "Extração concluída",
            f"Transcrição extraída com sucesso.\n\n"
            f"Blocos: {len(blocks)}\n"
            f"Arquivos gerados: {len(generated_files)}",
        )

        if self.open_folder_var.get():
            open_folder(output_dir)

    def _on_error(self, exc: Exception, details: str) -> None:
        self.progress.stop()
        self.extract_button.configure(state="normal", text="Extrair e salvar")

        self.status_var.set("Erro ao extrair. Veja os logs.")
        self.log("ERRO:")
        self.log(str(exc))
        self.log(details)

        messagebox.showerror(
            "Erro ao extrair",
            f"{exc}\n\nVeja a área de logs para mais detalhes.",
        )


def main() -> None:
    app = TldvExtractorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
