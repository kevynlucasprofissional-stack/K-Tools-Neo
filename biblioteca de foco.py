#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copiador da Biblioteca de Foco, Execução e Gestão de Alta Performance.

O aplicativo:

1. Permite escolher a pasta onde está a biblioteca original.
2. Localiza os livros definidos neste arquivo.
3. Permite revisar quais livros foram encontrados.
4. Cria uma segunda biblioteca organizada.
5. Copia os arquivos para seis categorias.
6. Nunca move, altera ou apaga os documentos originais.
7. Gera relatórios CSV e JSON.
8. Instala automaticamente o CustomTkinter quando necessário.

Recomendado para Windows 11 e Python 3.10 ou superior.
"""

from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Literal


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

APP_NAME = "Biblioteca de Foco, Execução e Alta Performance"
APP_VERSION = "1.0.0"

DEFAULT_SOURCE = Path(r"G:\Meu Drive\LIVROS")
DEFAULT_DESTINATION_NAME = "Biblioteca de Foco e Execução Organizada"
REPORT_FOLDER_NAME = "_Relatórios da organização"

ConflictMode = Literal["skip", "overwrite", "rename"]


# =============================================================================
# LIVROS E CATEGORIAS
# =============================================================================

CATEGORY_FOCUS = "01 - Foco e priorização"
CATEGORY_DISCIPLINE = "02 - Disciplina, hábitos e execução"
CATEGORY_MANAGEMENT = "03 - Gestão e liderança"
CATEGORY_PROJECTS = "04 - Gestão de projetos e processos"
CATEGORY_DECISIONS = "05 - Decisão e resolução de problemas"
CATEGORY_REFERENCES = "06 - Referências técnicas"


@dataclass(frozen=True)
class BookSpec:
    category: str
    title: str
    source_relative: str


BOOKS: tuple[BookSpec, ...] = (
    # -------------------------------------------------------------------------
    # 01 - Foco e priorização
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_FOCUS,
        "A Única Coisa — Gary Keller e Jay Papasan",
        "A única coisa (Gary Keller Jay Papasan) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_FOCUS,
        "Incrivelmente Simples — Ken Segall",
        (
            "Incrivelmente simples a obsessão que levou a Apple ao sucesso "
            "(Ken Segall) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_FOCUS,
        "O Melhor do Mundo — Seth Godin",
        "O Melhor Do Mundo (Seth Godin) (Z-Library).txt",
    ),
    BookSpec(
        CATEGORY_FOCUS,
        "Trabalhe 4 Horas por Semana — Timothy Ferriss",
        "Timothy Ferriss - Trabalhe 4 Horas Por Semana.pdf",
    ),

    # -------------------------------------------------------------------------
    # 02 - Disciplina, hábitos e execução
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_DISCIPLINE,
        "A Guerra da Arte — Steven Pressfield",
        "A guerra da arte (Steven Pressfield) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "Torne-se um Profissional — Steven Pressfield",
        (
            "Torne-se um profissional como superar seus limites internos "
            "e triunfar nas batalhas da vida "
            "(Steven Pressfield) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "O Poder do Hábito",
        "O poder do hábito.pdf",
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "Mindset: A Nova Psicologia do Sucesso — Carol Dweck",
        "Mindset-A-Nova-Psicologia-do-Sucesso-Carol-Dweck1.pdf.pdf",
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "Nada Pode Me Ferir — David Goggins, edição 1",
        "Nada pode me ferir (David Goggins) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "Nada Pode Me Ferir — David Goggins, edição 2",
        "Nada pode me ferir PDF.pdf",
    ),
    BookSpec(
        CATEGORY_DISCIPLINE,
        "Desperte o Gigante Interior — Anthony Robbins",
        "Desperte o Gigante Interior (Anthony Robbins) (Z-Library).pdf",
    ),

    # -------------------------------------------------------------------------
    # 03 - Gestão e liderança
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Gestão de Alta Performance — Andrew S. Grove",
        "Gestão de Alta Performance (Andrew S. Grove) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Management 3.0 — Jurgen Appelo",
        "Management 3.0 (Jurgen Appelo) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Gestão de Pessoas 3.0",
        "Gestão de pessoas 3.0.pdf",
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Reinvente sua Empresa — Jason Fried e David Heinemeier Hansson",
        (
            "Reinvente sua empresa "
            "(Jason Fried, David Heinemeier Hansson) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Gestão Estratégica do Design — Brunner e Emery",
        "Gestão estrategica do design (Brunner e Emery) (Z-Library).pdf",
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Pequenas Agências, Grandes Resultados",
        "pequenas-agencias-grandes-resultados.pdf",
    ),
    BookSpec(
        CATEGORY_MANAGEMENT,
        "Quebre as Regras e Reinvente — Seth Godin",
        "Quebre as regras e reivente (Seth Godin) (Z-Library).txt",
    ),

    # -------------------------------------------------------------------------
    # 04 - Gestão de projetos e processos
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_PROJECTS,
        "Gestão de Projetos",
        "Gestão de projetos.pdf",
    ),
    BookSpec(
        CATEGORY_PROJECTS,
        "A Arte do Gerenciamento de Projetos — Scott Berkun",
        (
            r"Gestão de Projetos\A Arte do Gerenciamento de Projetos "
            r"(Scott Berkun) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_PROJECTS,
        "Gerenciamento da Qualidade em Projetos — Alexandre Varanda Rocha",
        (
            r"Gestão de Projetos\Gerenciamento da qualidade em projetos "
            r"(Alexandre Varanda Rocha) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_PROJECTS,
        "Gerenciamento de Projetos: Fundamentos e Prática Integrada",
        (
            r"Gestão de Projetos\Gerenciamento de Projetos Fundamentos "
            r"e Pratica Integrada (Marta Rocha Camargo) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_PROJECTS,
        "Gerenciamento de Stakeholders em Projetos",
        (
            r"Gestão de Projetos\Gerenciamento de stakeholders em projetos "
            r"(Jose Angelo Santos Do Valle) (Z-Library).pdf"
        ),
    ),
    BookSpec(
        CATEGORY_PROJECTS,
        "PMBOK — 8ª edição",
        r"Gestão de Projetos\PMBOK 8ed.pdf",
    ),

    # -------------------------------------------------------------------------
    # 05 - Decisão e resolução de problemas
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_DECISIONS,
        "Dados Demais — Thomas Davenport e Jo Ho-Kim",
        (
            "Dados Demais Como Desenvolver Habilidades Analíticas para "
            "Resolver Problemas Complexos, Reduzir Riscos e Decidir Melhor "
            "(Thomas Davenport Jo Ho-Kim [Davenport etc.) "
            "(z-library.sk, 1lib.sk, z-lib.sk).pdf"
        ),
    ),

    # -------------------------------------------------------------------------
    # 06 - Referências técnicas
    # -------------------------------------------------------------------------
    BookSpec(
        CATEGORY_REFERENCES,
        "Comparativo PMBOK 6ª × 7ª × 8ª edição",
        (
            r"Gestão de Projetos\boyadjian-comparativo-pmbok-6a-ed-x-"
            r"pmbok-7a-ed-x-pmbok-8a-ed.pdf"
        ),
    ),
    BookSpec(
        CATEGORY_REFERENCES,
        "Estudo sobre o PMBOK 8ª edição",
        r"Gestão de Projetos\Estudo sobre o PMBOK 8ed.pdf",
    ),
)


CATEGORIES = tuple(
    dict.fromkeys(book.category for book in BOOKS)
)


# =============================================================================
# INSTALAÇÃO AUTOMÁTICA
# =============================================================================

def install_package(package: str) -> None:
    """Instala um pacote usando pip, tentando mais de uma estratégia."""

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", package]
        )
        return
    except subprocess.CalledProcessError:
        pass

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--user", package]
    )


def ensure_dependencies() -> None:
    """Instala CustomTkinter caso ainda não esteja disponível."""

    if importlib.util.find_spec("customtkinter") is not None:
        return

    print("CustomTkinter não encontrado.")
    print("Instalando automaticamente...")

    try:
        import ensurepip

        ensurepip.bootstrap()
    except Exception:
        pass

    try:
        install_package("customtkinter>=5.2.2")
    except Exception as exc:
        raise RuntimeError(
            "Não foi possível instalar o CustomTkinter automaticamente.\n\n"
            "Verifique sua conexão com a internet e execute:\n\n"
            f'"{sys.executable}" -m pip install customtkinter\n\n'
            f"Detalhe técnico: {exc}"
        ) from exc

    importlib.invalidate_caches()


ensure_dependencies()


# Imports realizados somente depois da instalação.
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk


# =============================================================================
# MODELOS
# =============================================================================

@dataclass
class LocatedBook:
    category: str
    title: str
    expected_relative: str
    source_path: Path | None
    destination_path: Path
    status: str
    detail: str
    size_bytes: int = 0


@dataclass
class CopyRecord:
    category: str
    title: str
    source_path: str
    destination_path: str
    size_bytes: int
    status: str
    detail: str


# =============================================================================
# UTILIDADES
# =============================================================================

class OperationCancelled(Exception):
    pass


def human_size(value: int) -> str:
    size = float(max(0, value))

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            if unit == "B":
                return f"{size:.0f} {unit}"

            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{value} B"


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    return "".join(
        character.casefold()
        for character in without_accents
        if character.isalnum()
    )


def windows_parts(value: str) -> tuple[str, ...]:
    return tuple(
        part
        for part in PureWindowsPath(value).parts
        if part not in ("", ".")
    )


def source_path_from_relative(root: Path, relative: str) -> Path:
    return root.joinpath(*windows_parts(relative))


def expected_filename(relative: str) -> str:
    return PureWindowsPath(relative).name


def is_subpath(candidate: Path, parent: Path) -> bool:
    try:
        candidate.resolve().relative_to(parent.resolve())
        return True
    except (ValueError, OSError):
        return False


def choose_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    number = 2

    while True:
        candidate = path.with_name(
            f"{path.stem}__copia_{number}{path.suffix}"
        )

        if not candidate.exists():
            return candidate

        number += 1


def iter_files(
    root: Path,
    stop_event: threading.Event | None = None,
):
    for current_root, directories, filenames in os.walk(root):
        if stop_event and stop_event.is_set():
            raise OperationCancelled()

        directories[:] = [
            directory
            for directory in directories
            if not directory.startswith(".")
        ]

        current = Path(current_root)

        for filename in filenames:
            if stop_event and stop_event.is_set():
                raise OperationCancelled()

            yield current / filename


def build_file_indexes(
    root: Path,
    stop_event: threading.Event | None = None,
    callback=None,
) -> tuple[
    dict[str, list[Path]],
    dict[str, list[Path]],
]:
    exact_index: dict[str, list[Path]] = defaultdict(list)
    normalized_index: dict[str, list[Path]] = defaultdict(list)

    scanned = 0

    for path in iter_files(root, stop_event):
        exact_index[path.name.casefold()].append(path)
        normalized_index[normalize_text(path.name)].append(path)

        scanned += 1

        if callback and scanned % 100 == 0:
            callback(
                0.15,
                f"Examinando a biblioteca: {scanned} arquivos encontrados",
            )

    return exact_index, normalized_index


def locate_book(
    spec: BookSpec,
    source_root: Path,
    destination_root: Path,
    exact_index: dict[str, list[Path]],
    normalized_index: dict[str, list[Path]],
) -> LocatedBook:
    expected_path = source_path_from_relative(
        source_root,
        spec.source_relative,
    )

    source_path: Path | None = None
    detail = ""
    status = "ausente"

    if expected_path.is_file():
        source_path = expected_path
        status = "encontrado"
        detail = "Encontrado no caminho original esperado."

    if source_path is None:
        filename = expected_filename(spec.source_relative)
        exact_matches = exact_index.get(filename.casefold(), [])

        if len(exact_matches) == 1:
            source_path = exact_matches[0]
            status = "encontrado"
            detail = "Encontrado em outra subpasta pelo nome exato."

        elif len(exact_matches) > 1:
            status = "ambíguo"
            detail = (
                f"Foram encontrados {len(exact_matches)} arquivos "
                "com o mesmo nome."
            )

    if source_path is None and status != "ambíguo":
        filename = expected_filename(spec.source_relative)
        normalized_matches = normalized_index.get(
            normalize_text(filename),
            [],
        )

        if len(normalized_matches) == 1:
            source_path = normalized_matches[0]
            status = "encontrado"
            detail = (
                "Encontrado por comparação normalizada de nome, "
                "ignorando acentos e pontuação."
            )

        elif len(normalized_matches) > 1:
            status = "ambíguo"
            detail = (
                f"Foram encontrados {len(normalized_matches)} arquivos "
                "com nomes normalizados equivalentes."
            )

    size_bytes = 0

    if source_path is not None:
        try:
            size_bytes = source_path.stat().st_size
        except OSError as exc:
            source_path = None
            status = "erro"
            detail = str(exc)

    destination_filename = (
        source_path.name
        if source_path is not None
        else expected_filename(spec.source_relative)
    )

    destination_path = (
        destination_root
        / spec.category
        / destination_filename
    )

    return LocatedBook(
        category=spec.category,
        title=spec.title,
        expected_relative=spec.source_relative,
        source_path=source_path,
        destination_path=destination_path,
        status=status,
        detail=detail,
        size_bytes=size_bytes,
    )


def validate_library(
    source_root: Path,
    destination_root: Path,
    stop_event: threading.Event | None = None,
    callback=None,
    log=None,
) -> list[LocatedBook]:
    if log:
        log("Criando índice dos arquivos da biblioteca original...")

    exact_index, normalized_index = build_file_indexes(
        source_root,
        stop_event,
        callback,
    )

    if log:
        log(
            f"Índice concluído: "
            f"{sum(len(paths) for paths in exact_index.values())} arquivos."
        )

    results: list[LocatedBook] = []

    for index, spec in enumerate(BOOKS, start=1):
        if stop_event and stop_event.is_set():
            raise OperationCancelled()

        located = locate_book(
            spec,
            source_root,
            destination_root,
            exact_index,
            normalized_index,
        )

        results.append(located)

        if log:
            if located.source_path:
                log(
                    f"[ENCONTRADO] {spec.title} → "
                    f"{located.source_path}"
                )
            else:
                log(
                    f"[{located.status.upper()}] "
                    f"{spec.title}: {located.detail}"
                )

        if callback:
            callback(
                0.20 + 0.80 * index / len(BOOKS),
                f"Validando livro {index}/{len(BOOKS)}",
            )

    return results


def copy_library(
    items: list[LocatedBook],
    destination_root: Path,
    conflict_mode: ConflictMode,
    stop_event: threading.Event | None = None,
    callback=None,
    log=None,
) -> list[CopyRecord]:
    destination_root.mkdir(parents=True, exist_ok=True)

    for category in CATEGORIES:
        (destination_root / category).mkdir(
            parents=True,
            exist_ok=True,
        )

    available = [
        item
        for item in items
        if item.source_path is not None
    ]

    records: list[CopyRecord] = []

    for index, item in enumerate(available, start=1):
        if stop_event and stop_event.is_set():
            raise OperationCancelled()

        assert item.source_path is not None

        destination = item.destination_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        status = "copiado"
        detail = item.detail

        try:
            if destination.exists():
                if conflict_mode == "skip":
                    status = "já existente"
                    detail = (
                        "O arquivo já existia no destino e foi preservado."
                    )

                elif conflict_mode == "overwrite":
                    shutil.copy2(item.source_path, destination)
                    status = "sobrescrito"
                    detail = (
                        "O arquivo existente no destino foi substituído."
                    )

                else:
                    destination = choose_unique_path(destination)
                    shutil.copy2(item.source_path, destination)
                    status = "copiado com novo nome"
                    detail = (
                        "Foi criado um novo nome para evitar conflito."
                    )
            else:
                shutil.copy2(item.source_path, destination)

            if status != "já existente":
                copied_size = destination.stat().st_size
                original_size = item.source_path.stat().st_size

                if copied_size != original_size:
                    raise OSError(
                        "O tamanho da cópia não corresponde ao original: "
                        f"{original_size} bytes na origem e "
                        f"{copied_size} bytes no destino."
                    )

            records.append(
                CopyRecord(
                    category=item.category,
                    title=item.title,
                    source_path=str(item.source_path),
                    destination_path=str(destination),
                    size_bytes=item.size_bytes,
                    status=status,
                    detail=detail,
                )
            )

            if log:
                log(
                    f"[{status.upper()}] "
                    f"{item.source_path.name} → "
                    f"{destination.parent}"
                )

        except OSError as exc:
            records.append(
                CopyRecord(
                    category=item.category,
                    title=item.title,
                    source_path=str(item.source_path),
                    destination_path=str(destination),
                    size_bytes=item.size_bytes,
                    status="erro",
                    detail=str(exc),
                )
            )

            if log:
                log(
                    f"[ERRO] {item.source_path}: {exc}"
                )

        if callback:
            callback(
                index / max(1, len(available)),
                f"Copiando arquivo {index}/{len(available)}",
            )

    for item in items:
        if item.source_path is not None:
            continue

        records.append(
            CopyRecord(
                category=item.category,
                title=item.title,
                source_path="",
                destination_path=str(item.destination_path),
                size_bytes=0,
                status=item.status,
                detail=item.detail,
            )
        )

    return records


def write_reports(
    destination_root: Path,
    source_root: Path,
    records: list[CopyRecord],
) -> tuple[Path, Path]:
    report_folder = destination_root / REPORT_FOLDER_NAME
    report_folder.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = (
        report_folder
        / f"relatorio_foco_execucao_{stamp}.csv"
    )

    json_path = (
        report_folder
        / f"relatorio_foco_execucao_{stamp}.json"
    )

    with csv_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "category",
                "title",
                "source_path",
                "destination_path",
                "size_bytes",
                "status",
                "detail",
            ],
        )

        writer.writeheader()

        for record in records:
            writer.writerow(asdict(record))

    counts = Counter(
        record.status
        for record in records
    )

    payload = {
        "application": APP_NAME,
        "version": APP_VERSION,
        "generated_at": datetime.now().isoformat(),
        "source_root": str(source_root),
        "destination_root": str(destination_root),
        "categories": list(CATEGORIES),
        "expected_files": len(BOOKS),
        "status_counts": dict(counts),
        "records": [
            asdict(record)
            for record in records
        ],
    }

    json_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return csv_path, json_path


def open_folder(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]

    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])

    else:
        subprocess.Popen(["xdg-open", str(path)])


# =============================================================================
# INTERFACE
# =============================================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class LibraryCopyApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title(
            f"{APP_NAME} — v{APP_VERSION}"
        )

        self.geometry("1320x850")
        self.minsize(1050, 700)

        source_default = (
            str(DEFAULT_SOURCE)
            if DEFAULT_SOURCE.is_dir()
            else ""
        )

        destination_default = ""

        if source_default:
            destination_default = str(
                DEFAULT_SOURCE.parent
                / DEFAULT_DESTINATION_NAME
            )

        self.source_var = tk.StringVar(
            value=source_default
        )

        self.destination_var = tk.StringVar(
            value=destination_default
        )

        self.conflict_var = tk.StringVar(
            value="Pular arquivos que já existem"
        )

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(
            value="Todos"
        )

        self.events: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()

        self.validation: list[LocatedBook] = []
        self.validated_source: Path | None = None
        self.validated_destination: Path | None = None

        self.working = False

        self._configure_style()
        self._build_interface()

        self.after(
            100,
            self._process_events,
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self._on_close,
        )

    # -------------------------------------------------------------------------
    # Aparência
    # -------------------------------------------------------------------------

    def _configure_style(self) -> None:
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Focus.Treeview",
            background="#0E1817",
            fieldbackground="#0E1817",
            foreground="#E7F5F0",
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 9),
        )

        style.configure(
            "Focus.Treeview.Heading",
            background="#1F3934",
            foreground="#FFFFFF",
            relief="flat",
            font=("Segoe UI Semibold", 9),
        )

        style.map(
            "Focus.Treeview",
            background=[
                ("selected", "#2F8068")
            ],
            foreground=[
                ("selected", "#FFFFFF")
            ],
        )

    # -------------------------------------------------------------------------
    # Construção da interface
    # -------------------------------------------------------------------------

    def _build_interface(self) -> None:
        self.grid_columnconfigure(
            0,
            weight=1,
        )

        self.grid_rowconfigure(
            1,
            weight=1,
        )

        self._build_header()
        self._build_tabs()
        self._build_footer()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(
            self,
            fg_color="#0F1B1A",
            corner_radius=0,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        header.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            header,
            text=(
                "BIBLIOTECA DE FOCO, EXECUÇÃO "
                "E ALTA PERFORMANCE"
            ),
            font=ctk.CTkFont(
                "Segoe UI",
                23,
                weight="bold",
            ),
            text_color="#F1FFF9",
        ).grid(
            row=0,
            column=0,
            padx=24,
            pady=(18, 0),
            sticky="w",
        )

        ctk.CTkLabel(
            header,
            text=(
                "Crie uma segunda biblioteca com cópias físicas dos livros, "
                "organizadas em seis categorias. "
                "Os documentos originais permanecem intactos."
            ),
            font=ctk.CTkFont(
                "Segoe UI",
                13,
            ),
            text_color="#B8D4CC",
        ).grid(
            row=1,
            column=0,
            padx=24,
            pady=(5, 16),
            sticky="w",
        )

        ctk.CTkLabel(
            header,
            text="CÓPIA REAL",
            fg_color="#315C45",
            corner_radius=10,
            text_color="#CEFFE3",
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            padx=24,
            pady=25,
        )

    def _build_tabs(self) -> None:
        self.tabs = ctk.CTkTabview(
            self,
            fg_color="#0A1212",
            corner_radius=14,
            segmented_button_fg_color="#17302B",
            segmented_button_selected_color="#2E7D65",
            segmented_button_selected_hover_color="#38977A",
        )

        self.tabs.grid(
            row=1,
            column=0,
            padx=18,
            pady=(0, 10),
            sticky="nsew",
        )

        self.tabs.add("Criar biblioteca")
        self.tabs.add("Prévia dos arquivos")
        self.tabs.add("Registro")

        self._build_main_tab()
        self._build_preview_tab()
        self._build_log_tab()

    def _build_main_tab(self) -> None:
        tab = self.tabs.tab(
            "Criar biblioteca"
        )

        tab.grid_columnconfigure(
            0,
            weight=3,
        )

        tab.grid_columnconfigure(
            1,
            weight=2,
        )

        tab.grid_rowconfigure(
            0,
            weight=1,
        )

        left = ctk.CTkScrollableFrame(
            tab,
            fg_color="transparent",
        )

        left.grid(
            row=0,
            column=0,
            padx=(8, 10),
            pady=10,
            sticky="nsew",
        )

        left.grid_columnconfigure(
            0,
            weight=1,
        )

        right = ctk.CTkFrame(
            tab,
            fg_color="#101C1A",
            corner_radius=14,
        )

        right.grid(
            row=0,
            column=1,
            padx=(10, 8),
            pady=10,
            sticky="nsew",
        )

        right.grid_columnconfigure(
            0,
            weight=1,
        )

        self._section(
            left,
            "1. Escolha a biblioteca original e o destino",
            0,
        )

        paths = ctk.CTkFrame(
            left,
            fg_color="#101C1A",
            corner_radius=14,
        )

        paths.grid(
            row=1,
            column=0,
            pady=(5, 16),
            sticky="ew",
        )

        paths.grid_columnconfigure(
            0,
            weight=1,
        )

        self._path_field(
            paths,
            0,
            "Biblioteca original",
            self.source_var,
            self._choose_source,
            "Escolher origem",
        )

        self._path_field(
            paths,
            1,
            "Nova biblioteca organizada",
            self.destination_var,
            self._choose_destination,
            "Escolher destino",
        )

        self._section(
            left,
            "2. Resultado que será criado",
            2,
        )

        explanation = ctk.CTkFrame(
            left,
            fg_color="#101C1A",
            corner_radius=14,
        )

        explanation.grid(
            row=3,
            column=0,
            pady=(5, 16),
            sticky="ew",
        )

        explanation.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            explanation,
            text=(
                "BIBLIOTECA ORIGINAL\n"
                "G:\\Meu Drive\\LIVROS\\A única coisa.pdf\n\n"
                "↓ será criada uma cópia física ↓\n\n"
                "NOVA BIBLIOTECA ORGANIZADA\n"
                "01 - Foco e priorização\\A única coisa.pdf"
            ),
            justify="left",
            anchor="w",
            fg_color="#19302B",
            corner_radius=10,
            padx=18,
            pady=16,
            text_color="#DDF5EC",
            font=ctk.CTkFont(
                "Consolas",
                12,
            ),
        ).grid(
            row=0,
            column=0,
            padx=16,
            pady=16,
            sticky="ew",
        )

        self._section(
            left,
            "3. Arquivos já existentes",
            4,
        )

        options = ctk.CTkFrame(
            left,
            fg_color="#101C1A",
            corner_radius=14,
        )

        options.grid(
            row=5,
            column=0,
            pady=(5, 16),
            sticky="ew",
        )

        options.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkOptionMenu(
            options,
            values=[
                "Pular arquivos que já existem",
                "Sobrescrever arquivos existentes",
                "Criar outra cópia com novo nome",
            ],
            variable=self.conflict_var,
            height=38,
            fg_color="#24473E",
            button_color="#2E7D65",
            button_hover_color="#38977A",
        ).grid(
            row=0,
            column=0,
            padx=16,
            pady=(16, 8),
            sticky="ew",
        )

        ctk.CTkLabel(
            options,
            text=(
                "A opção recomendada é pular os arquivos existentes. "
                "Isso permite executar novamente o programa depois de "
                "uma interrupção sem duplicar o que já foi copiado."
            ),
            wraplength=670,
            justify="left",
            text_color="#9DB6AF",
            font=ctk.CTkFont(
                size=11,
            ),
        ).grid(
            row=1,
            column=0,
            padx=16,
            pady=(0, 16),
            sticky="w",
        )

        self._section(
            left,
            "4. Validar e criar a biblioteca",
            6,
        )

        actions = ctk.CTkFrame(
            left,
            fg_color="#101C1A",
            corner_radius=14,
        )

        actions.grid(
            row=7,
            column=0,
            pady=(5, 12),
            sticky="ew",
        )

        actions.grid_columnconfigure(
            (0, 1),
            weight=1,
        )

        self.validate_button = ctk.CTkButton(
            actions,
            text="1. VALIDAR ARQUIVOS",
            command=self._start_validation,
            height=48,
            fg_color="#315E8A",
            hover_color="#3B70A3",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        )

        self.validate_button.grid(
            row=0,
            column=0,
            padx=(16, 8),
            pady=16,
            sticky="ew",
        )

        self.copy_button = ctk.CTkButton(
            actions,
            text="2. CRIAR CÓPIA ORGANIZADA",
            command=self._start_copy,
            state="disabled",
            height=48,
            fg_color="#2E7654",
            hover_color="#398D66",
            font=ctk.CTkFont(
                size=13,
                weight="bold",
            ),
        )

        self.copy_button.grid(
            row=0,
            column=1,
            padx=(8, 16),
            pady=16,
            sticky="ew",
        )

        self.cancel_button = ctk.CTkButton(
            actions,
            text="Cancelar operação",
            command=self._cancel_operation,
            state="disabled",
            fg_color="#552B37",
            hover_color="#6D3546",
        )

        self.cancel_button.grid(
            row=1,
            column=0,
            columnspan=2,
            padx=16,
            pady=(0, 16),
            sticky="ew",
        )

        ctk.CTkLabel(
            right,
            text="RESUMO DA NOVA BIBLIOTECA",
            font=ctk.CTkFont(
                size=15,
                weight="bold",
            ),
            text_color="#D7EEE6",
        ).grid(
            row=0,
            column=0,
            padx=18,
            pady=(20, 12),
            sticky="w",
        )

        self.stat_labels: dict[str, ctk.CTkLabel] = {}

        stats = [
            ("categories", "Pastas de categoria", str(len(CATEGORIES))),
            ("expected", "Arquivos previstos", str(len(BOOKS))),
            ("found", "Arquivos encontrados", "—"),
            ("missing", "Ausentes ou ambíguos", "—"),
            ("size", "Tamanho total das cópias", "—"),
        ]

        for row, (
            key,
            caption,
            value,
        ) in enumerate(
            stats,
            start=1,
        ):
            card = ctk.CTkFrame(
                right,
                fg_color="#19302B",
                corner_radius=10,
            )

            card.grid(
                row=row,
                column=0,
                padx=18,
                pady=6,
                sticky="ew",
            )

            card.grid_columnconfigure(
                0,
                weight=1,
            )

            ctk.CTkLabel(
                card,
                text=caption,
                text_color="#9DB9B1",
            ).grid(
                row=0,
                column=0,
                padx=14,
                pady=(10, 1),
                sticky="w",
            )

            label = ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(
                    size=22,
                    weight="bold",
                ),
                text_color="#ECFFF8",
            )

            label.grid(
                row=1,
                column=0,
                padx=14,
                pady=(0, 10),
                sticky="w",
            )

            self.stat_labels[key] = label

        ctk.CTkLabel(
            right,
            text=(
                "SEGURANÇA\n\n"
                "✓ cria somente cópias\n"
                "✓ usa shutil.copy2\n"
                "✓ preserva datas dos arquivos\n"
                "✓ nunca apaga os originais\n"
                "✓ impede destino dentro da origem\n"
                "✓ verifica o tamanho da cópia"
            ),
            justify="left",
            anchor="w",
            fg_color="#1C2B24",
            corner_radius=10,
            text_color="#C9F4D9",
            font=ctk.CTkFont(
                size=11,
            ),
        ).grid(
            row=6,
            column=0,
            padx=18,
            pady=(18, 10),
            sticky="ew",
        )

        self.open_button = ctk.CTkButton(
            right,
            text="Abrir nova biblioteca",
            command=self._open_destination,
            state="disabled",
            fg_color="#213B37",
            hover_color="#2C514A",
        )

        self.open_button.grid(
            row=7,
            column=0,
            padx=18,
            pady=(4, 18),
            sticky="ew",
        )

    def _build_preview_tab(self) -> None:
        tab = self.tabs.tab(
            "Prévia dos arquivos"
        )

        tab.grid_columnconfigure(
            0,
            weight=1,
        )

        tab.grid_rowconfigure(
            1,
            weight=1,
        )

        controls = ctk.CTkFrame(
            tab,
            fg_color="#101C1A",
            corner_radius=12,
        )

        controls.grid(
            row=0,
            column=0,
            padx=8,
            pady=(10, 6),
            sticky="ew",
        )

        controls.grid_columnconfigure(
            0,
            weight=1,
        )

        search = ctk.CTkEntry(
            controls,
            textvariable=self.search_var,
            placeholder_text=(
                "Pesquisar categoria, título ou arquivo..."
            ),
            height=36,
        )

        search.grid(
            row=0,
            column=0,
            padx=(12, 8),
            pady=12,
            sticky="ew",
        )

        search.bind(
            "<KeyRelease>",
            lambda _event: self._refresh_preview(),
        )

        ctk.CTkOptionMenu(
            controls,
            values=[
                "Todos",
                "Encontrados",
                "Ausentes ou ambíguos",
            ],
            variable=self.filter_var,
            command=lambda _value: self._refresh_preview(),
            width=180,
        ).grid(
            row=0,
            column=1,
            padx=(8, 12),
            pady=12,
        )

        tree_frame = ctk.CTkFrame(
            tab,
            fg_color="#0E1817",
            corner_radius=12,
        )

        tree_frame.grid(
            row=1,
            column=0,
            padx=8,
            pady=(6, 10),
            sticky="nsew",
        )

        tree_frame.grid_columnconfigure(
            0,
            weight=1,
        )

        tree_frame.grid_rowconfigure(
            0,
            weight=1,
        )

        columns = (
            "status",
            "category",
            "title",
            "source",
            "destination",
        )

        self.preview_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="Focus.Treeview",
        )

        headings = {
            "status": "Situação",
            "category": "Categoria",
            "title": "Título",
            "source": "Origem",
            "destination": "Novo destino",
        }

        widths = {
            "status": 110,
            "category": 230,
            "title": 260,
            "source": 330,
            "destination": 350,
        }

        for column in columns:
            self.preview_tree.heading(
                column,
                text=headings[column],
            )

            self.preview_tree.column(
                column,
                width=widths[column],
                minwidth=80,
                stretch=True,
            )

        vertical = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.preview_tree.yview,
        )

        horizontal = ttk.Scrollbar(
            tree_frame,
            orient="horizontal",
            command=self.preview_tree.xview,
        )

        self.preview_tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )

        self.preview_tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        vertical.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        horizontal.grid(
            row=1,
            column=0,
            sticky="ew",
        )

    def _build_log_tab(self) -> None:
        tab = self.tabs.tab(
            "Registro"
        )

        tab.grid_columnconfigure(
            0,
            weight=1,
        )

        tab.grid_rowconfigure(
            0,
            weight=1,
        )

        self.log_text = ctk.CTkTextbox(
            tab,
            fg_color="#09100F",
            text_color="#D9EAE5",
            font=ctk.CTkFont(
                "Consolas",
                11,
            ),
            corner_radius=12,
        )

        self.log_text.grid(
            row=0,
            column=0,
            padx=8,
            pady=(10, 6),
            sticky="nsew",
        )

        ctk.CTkButton(
            tab,
            text="Limpar registro",
            command=lambda: self.log_text.delete(
                "1.0",
                "end",
            ),
            width=130,
            fg_color="#213B37",
            hover_color="#2C514A",
        ).grid(
            row=1,
            column=0,
            padx=8,
            pady=(6, 10),
            sticky="e",
        )

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(
            self,
            fg_color="#0F1B1A",
            corner_radius=0,
        )

        footer.grid(
            row=2,
            column=0,
            sticky="ew",
        )

        footer.grid_columnconfigure(
            0,
            weight=1,
        )

        self.status_label = ctk.CTkLabel(
            footer,
            text=(
                "Escolha a origem e o destino; "
                "depois valide os arquivos."
            ),
            text_color="#B7CDC6",
        )

        self.status_label.grid(
            row=0,
            column=0,
            padx=20,
            pady=(10, 2),
            sticky="w",
        )

        self.progress = ctk.CTkProgressBar(
            footer,
            height=8,
            progress_color="#3E9077",
        )

        self.progress.grid(
            row=1,
            column=0,
            padx=20,
            pady=(2, 12),
            sticky="ew",
        )

        self.progress.set(0)

        ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION}",
            text_color="#78928B",
        ).grid(
            row=0,
            column=1,
            rowspan=2,
            padx=20,
        )

    def _section(
        self,
        parent,
        text: str,
        row: int,
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(
                size=14,
                weight="bold",
            ),
            text_color="#CCE9DF",
        ).grid(
            row=row,
            column=0,
            sticky="w",
        )

    def _path_field(
        self,
        parent,
        row: int,
        label: str,
        variable: tk.StringVar,
        command,
        button_text: str,
    ) -> None:
        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
        )

        frame.grid(
            row=row,
            column=0,
            padx=16,
            pady=(
                14 if row == 0 else 7,
                14 if row == 1 else 7,
            ),
            sticky="ew",
        )

        frame.grid_columnconfigure(
            0,
            weight=1,
        )

        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(
                size=12,
                weight="bold",
            ),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            pady=(0, 5),
            sticky="w",
        )

        ctk.CTkEntry(
            frame,
            textvariable=variable,
            height=37,
            fg_color="#09100F",
            border_color="#29463F",
        ).grid(
            row=1,
            column=0,
            padx=(0, 8),
            sticky="ew",
        )

        ctk.CTkButton(
            frame,
            text=button_text,
            command=command,
            width=145,
            height=37,
            fg_color="#223F39",
            hover_color="#2C554B",
        ).grid(
            row=1,
            column=1,
        )

    # -------------------------------------------------------------------------
    # Seleção de pastas
    # -------------------------------------------------------------------------

    def _choose_source(self) -> None:
        selected = filedialog.askdirectory(
            title="Escolha a biblioteca original"
        )

        if not selected:
            return

        self.source_var.set(selected)

        source = Path(selected)

        self.destination_var.set(
            str(
                source.parent
                / DEFAULT_DESTINATION_NAME
            )
        )

        self._invalidate_validation()

    def _choose_destination(self) -> None:
        selected = filedialog.askdirectory(
            title=(
                "Escolha ou crie a nova "
                "biblioteca organizada"
            )
        )

        if not selected:
            return

        self.destination_var.set(selected)
        self._invalidate_validation()

    def _validate_paths(
        self,
    ) -> tuple[Path, Path] | None:
        source_text = self.source_var.get().strip()
        destination_text = (
            self.destination_var.get().strip()
        )

        if not source_text or not destination_text:
            messagebox.showerror(
                "Pastas incompletas",
                "Escolha a pasta original e a pasta de destino.",
            )

            return None

        source = Path(source_text).expanduser()
        destination = Path(
            destination_text
        ).expanduser()

        if not source.is_dir():
            messagebox.showerror(
                "Origem inválida",
                f"A biblioteca original não existe:\n\n{source}",
            )

            return None

        try:
            same_path = (
                source.resolve()
                == destination.resolve()
            )
        except OSError:
            same_path = False

        overlapping = (
            same_path
            or is_subpath(destination, source)
            or is_subpath(source, destination)
        )

        if overlapping:
            messagebox.showerror(
                "Destino inseguro",
                (
                    "A biblioteca de destino deve estar completamente "
                    "separada da biblioteca original.\n\n"
                    "Não escolha a própria pasta LIVROS, uma subpasta dela "
                    "ou uma pasta que contenha a biblioteca original."
                ),
            )

            return None

        return source, destination

    def _invalidate_validation(self) -> None:
        self.validation = []
        self.validated_source = None
        self.validated_destination = None

        self.copy_button.configure(
            state="disabled"
        )

    # -------------------------------------------------------------------------
    # Validação
    # -------------------------------------------------------------------------

    def _start_validation(self) -> None:
        paths = self._validate_paths()

        if paths is None or self.working:
            return

        source, destination = paths

        self.validation = []
        self.stop_event.clear()

        self._set_working(
            True,
            "Examinando a biblioteca original...",
        )

        self.tabs.set("Registro")

        self._log("-" * 88)
        self._log(f"Origem: {source}")
        self._log(f"Destino: {destination}")
        self._log(
            f"Livros previstos: {len(BOOKS)}"
        )

        thread = threading.Thread(
            target=self._validation_worker,
            args=(source, destination),
            daemon=True,
        )

        thread.start()

    def _validation_worker(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        try:
            results = validate_library(
                source,
                destination,
                stop_event=self.stop_event,
                callback=lambda value, text: (
                    self.events.put(
                        (
                            "progress",
                            value,
                            text,
                        )
                    )
                ),
                log=lambda text: self.events.put(
                    (
                        "log",
                        text,
                    )
                ),
            )

            self.events.put(
                (
                    "validation_done",
                    source,
                    destination,
                    results,
                )
            )

        except OperationCancelled:
            self.events.put(
                (
                    "cancelled",
                    "Validação cancelada.",
                )
            )

        except Exception as exc:
            self.events.put(
                (
                    "error",
                    "Falha na validação",
                    str(exc),
                )
            )

    def _finish_validation(
        self,
        source: Path,
        destination: Path,
        results: list[LocatedBook],
    ) -> None:
        self.validation = results
        self.validated_source = source
        self.validated_destination = destination

        found = [
            item
            for item in results
            if item.source_path is not None
        ]

        missing = [
            item
            for item in results
            if item.source_path is None
        ]

        total_size = sum(
            item.size_bytes
            for item in found
        )

        self.stat_labels["found"].configure(
            text=str(len(found))
        )

        self.stat_labels["missing"].configure(
            text=str(len(missing))
        )

        self.stat_labels["size"].configure(
            text=human_size(total_size)
        )

        self.copy_button.configure(
            state="normal" if found else "disabled"
        )

        self.progress.set(1)

        self._set_working(
            False,
            (
                "Validação concluída. "
                "Revise a prévia ou inicie a cópia."
            ),
        )

        self._refresh_preview()
        self.tabs.set("Prévia dos arquivos")

        if missing:
            messagebox.showwarning(
                "Validação concluída",
                (
                    f"Foram encontrados {len(found)} "
                    f"de {len(results)} arquivos.\n\n"
                    f"{len(missing)} arquivo(s) estão ausentes "
                    "ou possuem correspondência ambígua.\n\n"
                    "Consulte a aba Prévia dos arquivos."
                ),
            )

        else:
            messagebox.showinfo(
                "Tudo pronto",
                (
                    f"Todos os {len(found)} arquivos foram encontrados.\n\n"
                    "Clique em CRIAR CÓPIA ORGANIZADA."
                ),
            )

    # -------------------------------------------------------------------------
    # Cópia
    # -------------------------------------------------------------------------

    def _start_copy(self) -> None:
        paths = self._validate_paths()

        if paths is None or self.working:
            return

        source, destination = paths

        if (
            not self.validation
            or self.validated_source is None
            or self.validated_destination is None
        ):
            messagebox.showwarning(
                "Validação necessária",
                "Clique primeiro em VALIDAR ARQUIVOS.",
            )

            return

        try:
            configuration_changed = (
                source.resolve()
                != self.validated_source.resolve()
                or destination.resolve()
                != self.validated_destination.resolve()
            )
        except OSError:
            configuration_changed = True

        if configuration_changed:
            messagebox.showwarning(
                "Configuração alterada",
                (
                    "A origem ou o destino mudou depois da validação.\n\n"
                    "Valide os arquivos novamente."
                ),
            )

            self._invalidate_validation()
            return

        found = [
            item
            for item in self.validation
            if item.source_path is not None
        ]

        missing = [
            item
            for item in self.validation
            if item.source_path is None
        ]

        if not found:
            messagebox.showerror(
                "Nada para copiar",
                "Nenhum livro foi encontrado.",
            )

            return

        total_size = sum(
            item.size_bytes
            for item in found
        )

        try:
            destination.mkdir(
                parents=True,
                exist_ok=True,
            )

            free_space = shutil.disk_usage(
                destination
            ).free

        except OSError as exc:
            messagebox.showerror(
                "Destino inacessível",
                str(exc),
            )

            return

        if total_size > free_space:
            messagebox.showerror(
                "Espaço insuficiente",
                (
                    f"As cópias precisam de aproximadamente "
                    f"{human_size(total_size)}.\n\n"
                    f"O destino possui somente "
                    f"{human_size(free_space)} livres."
                ),
            )

            return

        warning = ""

        if missing:
            warning = (
                f"\n\n{len(missing)} arquivo(s) ausentes "
                "não serão copiados."
            )

        confirmed = messagebox.askyesno(
            "Criar biblioteca organizada",
            (
                f"O programa criará {len(CATEGORIES)} pastas "
                f"e copiará {len(found)} arquivos físicos.\n\n"
                f"Tamanho aproximado: {human_size(total_size)}.\n\n"
                "A biblioteca original não será modificada."
                f"{warning}\n\n"
                "Deseja continuar?"
            ),
        )

        if not confirmed:
            return

        self.stop_event.clear()

        self._set_working(
            True,
            "Criando pastas e copiando os arquivos...",
        )

        self.tabs.set("Registro")

        self._log("-" * 88)
        self._log(
            "CÓPIA REAL INICIADA"
        )
        self._log(
            f"Destino: {destination}"
        )

        thread = threading.Thread(
            target=self._copy_worker,
            args=(source, destination),
            daemon=True,
        )

        thread.start()

    def _copy_worker(
        self,
        source: Path,
        destination: Path,
    ) -> None:
        try:
            records = copy_library(
                self.validation,
                destination,
                self._conflict_mode(),
                stop_event=self.stop_event,
                callback=lambda value, text: (
                    self.events.put(
                        (
                            "progress",
                            value,
                            text,
                        )
                    )
                ),
                log=lambda text: self.events.put(
                    (
                        "log",
                        text,
                    )
                ),
            )

            csv_path, json_path = write_reports(
                destination,
                source,
                records,
            )

            self.events.put(
                (
                    "copy_done",
                    destination,
                    records,
                    csv_path,
                    json_path,
                )
            )

        except OperationCancelled:
            self.events.put(
                (
                    "cancelled",
                    (
                        "Cópia cancelada. "
                        "Os arquivos já copiados foram preservados."
                    ),
                )
            )

        except Exception as exc:
            self.events.put(
                (
                    "error",
                    "Falha durante a cópia",
                    str(exc),
                )
            )

    def _finish_copy(
        self,
        destination: Path,
        records: list[CopyRecord],
        csv_path: Path,
        json_path: Path,
    ) -> None:
        counts = Counter(
            record.status
            for record in records
        )

        summary = ", ".join(
            f"{status}: {amount}"
            for status, amount in sorted(
                counts.items()
            )
        )

        self.progress.set(1)

        self._set_working(
            False,
            "Nova biblioteca organizada criada.",
        )

        self.open_button.configure(
            state="normal"
        )

        self._log(
            f"CÓPIA CONCLUÍDA — {summary}"
        )

        self._log(
            f"Relatório CSV: {csv_path}"
        )

        self._log(
            f"Relatório JSON: {json_path}"
        )

        messagebox.showinfo(
            "Biblioteca criada",
            (
                "A nova biblioteca foi criada em:\n\n"
                f"{destination}\n\n"
                f"{summary}\n\n"
                "Os arquivos originais permaneceram intactos."
            ),
        )

    # -------------------------------------------------------------------------
    # Eventos e auxiliares
    # -------------------------------------------------------------------------

    def _process_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]

                if kind == "progress":
                    _, value, text = event

                    self.progress.set(
                        max(
                            0.0,
                            min(
                                1.0,
                                float(value),
                            ),
                        )
                    )

                    self.status_label.configure(
                        text=text
                    )

                elif kind == "log":
                    self._log(event[1])

                elif kind == "validation_done":
                    self._finish_validation(
                        *event[1:]
                    )

                elif kind == "copy_done":
                    self._finish_copy(
                        *event[1:]
                    )

                elif kind == "cancelled":
                    self._log(event[1])

                    self._set_working(
                        False,
                        event[1],
                    )

                elif kind == "error":
                    _, title, detail = event

                    self._log(
                        f"ERRO: {detail}"
                    )

                    self._set_working(
                        False,
                        "A operação falhou.",
                    )

                    messagebox.showerror(
                        title,
                        detail,
                    )

        except queue.Empty:
            pass

        finally:
            self.after(
                100,
                self._process_events,
            )

    def _refresh_preview(self) -> None:
        self.preview_tree.delete(
            *self.preview_tree.get_children()
        )

        if not self.validation:
            return

        search = (
            self.search_var
            .get()
            .strip()
            .casefold()
        )

        filter_value = self.filter_var.get()

        for item in self.validation:
            found = item.source_path is not None

            if (
                filter_value == "Encontrados"
                and not found
            ):
                continue

            if (
                filter_value == "Ausentes ou ambíguos"
                and found
            ):
                continue

            source_text = (
                str(item.source_path)
                if item.source_path
                else item.expected_relative
            )

            searchable = " ".join(
                (
                    item.category,
                    item.title,
                    source_text,
                    str(item.destination_path),
                    item.status,
                )
            ).casefold()

            if search and search not in searchable:
                continue

            self.preview_tree.insert(
                "",
                "end",
                values=(
                    (
                        "Encontrado"
                        if found
                        else item.status.capitalize()
                    ),
                    item.category,
                    item.title,
                    source_text,
                    str(item.destination_path),
                ),
            )

    def _conflict_mode(self) -> ConflictMode:
        mapping: dict[str, ConflictMode] = {
            "Pular arquivos que já existem": "skip",
            "Sobrescrever arquivos existentes": "overwrite",
            "Criar outra cópia com novo nome": "rename",
        }

        return mapping.get(
            self.conflict_var.get(),
            "skip",
        )

    def _cancel_operation(self) -> None:
        if not self.working:
            return

        self.stop_event.set()

        self.status_label.configure(
            text=(
                "Cancelamento solicitado; "
                "concluindo o arquivo atual..."
            )
        )

        self.cancel_button.configure(
            state="disabled"
        )

    def _set_working(
        self,
        working: bool,
        status: str,
    ) -> None:
        self.working = working

        self.status_label.configure(
            text=status
        )

        self.validate_button.configure(
            state=(
                "disabled"
                if working
                else "normal"
            )
        )

        self.cancel_button.configure(
            state=(
                "normal"
                if working
                else "disabled"
            )
        )

        if working:
            self.copy_button.configure(
                state="disabled"
            )

            self.progress.set(0)

        elif self.validation:
            found = any(
                item.source_path is not None
                for item in self.validation
            )

            self.copy_button.configure(
                state=(
                    "normal"
                    if found
                    else "disabled"
                )
            )

    def _log(self, text: str) -> None:
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.log_text.insert(
            "end",
            f"[{timestamp}] {text}\n",
        )

        self.log_text.see("end")

    def _open_destination(self) -> None:
        destination_text = (
            self.destination_var.get().strip()
        )

        if not destination_text:
            return

        destination = Path(
            destination_text
        )

        if not destination.is_dir():
            messagebox.showwarning(
                "Pasta inexistente",
                (
                    "A nova biblioteca ainda não existe. "
                    "Execute a cópia primeiro."
                ),
            )

            return

        try:
            open_folder(destination)

        except OSError as exc:
            messagebox.showerror(
                "Não foi possível abrir a pasta",
                str(exc),
            )

    def _on_close(self) -> None:
        if self.working:
            confirmed = messagebox.askyesno(
                "Operação em andamento",
                (
                    "Há uma operação em andamento.\n\n"
                    "Deseja solicitar o cancelamento e fechar?"
                ),
            )

            if not confirmed:
                return

            self.stop_event.set()

        self.destroy()


# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def main() -> int:
    app = LibraryCopyApp()
    app.mainloop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())