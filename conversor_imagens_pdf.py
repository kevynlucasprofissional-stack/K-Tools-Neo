"""
Conversor de Imagens para PDF — CustomTkinter

Objetivo:
- Selecionar várias imagens.
- Definir a ordem das páginas.
- Gerar um único PDF sem compressão com perda e sem redimensionamento.
- Instalar automaticamente as dependências ausentes.

Dependências instaladas automaticamente:
- customtkinter
- img2pdf
- Pillow

Compatibilidade recomendada: Python 3.10 ou superior.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Iterable


# -----------------------------------------------------------------------------
# Instalação automática das dependências
# -----------------------------------------------------------------------------

DEPENDENCIES = {
    "customtkinter": "customtkinter",
    "img2pdf": "img2pdf",
    "PIL": "Pillow",
}


def _show_bootstrap_error(message: str) -> None:
    """Exibe um erro mesmo antes de o CustomTkinter estar disponível."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro ao preparar o aplicativo", message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def install_missing_dependencies() -> None:
    """Instala via pip apenas os pacotes que ainda não estão disponíveis."""
    missing_packages = [
        pip_name
        for module_name, pip_name in DEPENDENCIES.items()
        if importlib.util.find_spec(module_name) is None
    ]

    if not missing_packages:
        return

    if getattr(sys, "frozen", False):
        raise RuntimeError(
            "O executável não contém todas as dependências necessárias: "
            + ", ".join(missing_packages)
        )

    # Tenta garantir que o pip existe na instalação atual do Python.
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception:
        subprocess.run(
            [sys.executable, "-m", "ensurepip", "--upgrade"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        *missing_packages,
    ]

    creation_flags = 0
    if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        creation_flags = subprocess.CREATE_NO_WINDOW

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creation_flags,
    )

    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(
            "Não foi possível instalar automaticamente as bibliotecas.\n\n"
            f"Comando tentado:\n{' '.join(command)}\n\n"
            f"Detalhes:\n{details}"
        )

    importlib.invalidate_caches()


try:
    install_missing_dependencies()
except Exception as exc:
    _show_bootstrap_error(str(exc))
    raise SystemExit(1) from exc


# Importações realizadas somente depois da instalação automática.
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import img2pdf
from PIL import Image, ImageOps, UnidentifiedImageError


# -----------------------------------------------------------------------------
# Configurações gerais
# -----------------------------------------------------------------------------

APP_TITLE = "Imagens para PDF — Qualidade Original"
SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".jpe",
    ".jfif",
    ".png",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".webp",
    ".jp2",
    ".j2k",
    ".jpf",
    ".jpx",
    ".ico",
}

# Formatos que o img2pdf consegue normalmente incorporar diretamente.
DIRECT_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".jpe",
    ".jfif",
    ".png",
    ".gif",
    ".tif",
    ".tiff",
    ".jp2",
    ".j2k",
    ".jpf",
    ".jpx",
}

IMAGE_FILETYPES = [
    (
        "Imagens compatíveis",
        "*.jpg *.jpeg *.jpe *.jfif *.png *.gif *.tif *.tiff "
        "*.bmp *.webp *.jp2 *.j2k *.jpf *.jpx *.ico",
    ),
    ("JPEG", "*.jpg *.jpeg *.jpe *.jfif"),
    ("PNG", "*.png"),
    ("TIFF", "*.tif *.tiff"),
    ("WebP", "*.webp"),
    ("Todas as imagens", "*.*"),
]


def human_size(size_bytes: int) -> str:
    value = float(size_bytes)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.2f} {unit}"
        value /= 1024
    return f"{size_bytes} B"


def natural_sort_key(path: str) -> list[object]:
    """Ordena nomes como imagem2 antes de imagem10."""
    parts = re.split(r"(\d+)", Path(path).name.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def has_transparency(image: Image.Image) -> bool:
    """Detecta canal alfa ou transparência por paleta."""
    return image.mode in {"RGBA", "LA"} or (
        image.mode == "P" and "transparency" in image.info
    )


def image_summary(path: str) -> str:
    """Obtém dados leves para exibição na lista."""
    try:
        with Image.open(path) as image:
            width, height = image.size
            image_format = image.format or Path(path).suffix.lstrip(".").upper()
            frames = int(getattr(image, "n_frames", 1))
            frame_text = f" | {frames} quadros" if frames > 1 else ""
            return f"{width} × {height} px | {image_format}{frame_text}"
    except Exception:
        return "metadados indisponíveis"


def flatten_to_rgb(image: Image.Image) -> Image.Image:
    """
    Converte transparência para fundo branco e mantém os pixels visíveis.
    Nenhum redimensionamento é realizado.
    """
    if has_transparency(image):
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        composed = Image.alpha_composite(background, rgba)
        return composed.convert("RGB")

    if image.mode not in {"1", "L", "RGB", "CMYK"}:
        return image.convert("RGB")

    return image.copy()


def prepare_image_for_pdf(source: str, temp_directory: str) -> tuple[list[str], list[str]]:
    """
    Retorna os arquivos que serão enviados ao img2pdf e observações da conversão.

    JPEG/JPEG 2000, PNG, GIF e TIFF são mantidos diretamente sempre que possível.
    Formatos que não podem ser incorporados com segurança são transformados em PNG,
    que é um formato sem perda. Imagens animadas ou multipágina que precisem ser
    transformadas viram uma página PNG por quadro.
    """
    source_path = Path(source)
    extension = source_path.suffix.casefold()
    notes: list[str] = []

    try:
        with Image.open(source) as image:
            frame_count = int(getattr(image, "n_frames", 1))
            first_frame_transparent = has_transparency(image)

            can_use_directly = (
                extension in DIRECT_EXTENSIONS
                and not first_frame_transparent
            )

            if can_use_directly:
                return [source], notes

            if first_frame_transparent:
                notes.append(
                    f"{source_path.name}: transparência aplicada sobre fundo branco."
                )
            elif extension not in DIRECT_EXTENSIONS:
                notes.append(
                    f"{source_path.name}: convertido internamente para PNG sem perda."
                )

            prepared_files: list[str] = []
            safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", source_path.stem) or "imagem"

            for frame_index in range(frame_count):
                image.seek(frame_index)
                frame = ImageOps.exif_transpose(image.copy())
                frame = flatten_to_rgb(frame)

                output_name = f"{safe_stem}_{frame_index + 1:05d}.png"
                output_path = str(Path(temp_directory) / output_name)

                # PNG usa compressão reversível. compress_level altera apenas o
                # tamanho/tempo, não a qualidade dos pixels.
                frame.save(output_path, format="PNG", compress_level=6)
                prepared_files.append(output_path)

            if frame_count > 1:
                notes.append(
                    f"{source_path.name}: {frame_count} quadros convertidos em páginas."
                )

            return prepared_files, notes

    except UnidentifiedImageError as exc:
        raise ValueError(f"O arquivo não parece ser uma imagem válida: {source}") from exc
    except OSError as exc:
        raise ValueError(f"Não foi possível abrir a imagem: {source}\n{exc}") from exc


# -----------------------------------------------------------------------------
# Interface gráfica
# -----------------------------------------------------------------------------


class ImageToPDFApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.image_paths: list[str] = []
        self.output_path = tk.StringVar(value="")
        self.is_working = False

        self.title(APP_TITLE)
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()
        self._build_footer()
        self._update_list()

    # ------------------------------------------------------------------ UI

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Conversor de imagens para PDF",
            font=ctk.CTkFont(size=25, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 2))

        subtitle = ctk.CTkLabel(
            header,
            text=(
                "Cada imagem vira uma página, sem redimensionamento e sem "
                "compressão com perda."
            ),
            text_color=("gray35", "gray70"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 16))

        self.appearance_menu = ctk.CTkOptionMenu(
            header,
            values=["Sistema", "Claro", "Escuro"],
            width=120,
            command=self._change_appearance,
        )
        self.appearance_menu.set("Sistema")
        self.appearance_menu.grid(row=0, column=1, rowspan=2, padx=24, pady=18)

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=16)
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        guide = ctk.CTkLabel(
            content,
            text=(
                "1. Selecione as imagens   •   2. Organize as páginas   •   "
                "3. Escolha o destino   •   4. Gere o PDF"
            ),
            anchor="w",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        guide.grid(row=0, column=0, sticky="ew", padx=4, pady=(0, 10))

        body = ctk.CTkFrame(content)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(body, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        toolbar.grid_columnconfigure(5, weight=1)

        self.add_button = ctk.CTkButton(
            toolbar,
            text="Selecionar imagens",
            command=self.select_images,
            width=155,
        )
        self.add_button.grid(row=0, column=0, padx=(0, 8))

        self.sort_button = ctk.CTkButton(
            toolbar,
            text="Ordenar por nome",
            command=self.sort_by_name,
            width=140,
            fg_color="transparent",
            border_width=1,
        )
        self.sort_button.grid(row=0, column=1, padx=8)

        self.clear_button = ctk.CTkButton(
            toolbar,
            text="Limpar tudo",
            command=self.clear_images,
            width=105,
            fg_color="transparent",
            border_width=1,
        )
        self.clear_button.grid(row=0, column=2, padx=8)

        self.count_label = ctk.CTkLabel(toolbar, text="0 imagens")
        self.count_label.grid(row=0, column=6, sticky="e")

        list_area = ctk.CTkFrame(body, fg_color="transparent")
        list_area.grid(row=1, column=0, sticky="nsew", padx=14, pady=6)
        list_area.grid_columnconfigure(0, weight=1)
        list_area.grid_rowconfigure(0, weight=1)

        self.listbox = tk.Listbox(
            list_area,
            selectmode=tk.EXTENDED,
            activestyle="none",
            exportselection=False,
            font=("Segoe UI", 10),
            bd=0,
            highlightthickness=1,
            relief="flat",
        )
        self.listbox.grid(row=0, column=0, sticky="nsew")
        self.listbox.bind("<Delete>", lambda _event: self.remove_selected())
        self.listbox.bind("<Control-a>", self.select_all)
        self.listbox.bind("<Control-A>", self.select_all)

        scrollbar = ctk.CTkScrollbar(list_area, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(8, 0))
        self.listbox.configure(yscrollcommand=scrollbar.set)

        controls = ctk.CTkFrame(list_area, fg_color="transparent", width=130)
        controls.grid(row=0, column=2, sticky="ns", padx=(12, 0))

        self.up_button = ctk.CTkButton(
            controls, text="Mover acima", command=self.move_up, width=120
        )
        self.up_button.grid(row=0, column=0, pady=(0, 8))

        self.down_button = ctk.CTkButton(
            controls, text="Mover abaixo", command=self.move_down, width=120
        )
        self.down_button.grid(row=1, column=0, pady=8)

        self.remove_button = ctk.CTkButton(
            controls,
            text="Remover",
            command=self.remove_selected,
            width=120,
            fg_color="#B93838",
            hover_color="#922D2D",
        )
        self.remove_button.grid(row=2, column=0, pady=8)

        output_frame = ctk.CTkFrame(body, fg_color="transparent")
        output_frame.grid(row=2, column=0, sticky="ew", padx=14, pady=(8, 14))
        output_frame.grid_columnconfigure(1, weight=1)

        output_label = ctk.CTkLabel(
            output_frame,
            text="Arquivo de saída:",
            font=ctk.CTkFont(weight="bold"),
        )
        output_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.output_entry = ctk.CTkEntry(
            output_frame,
            textvariable=self.output_path,
            placeholder_text="Escolha onde salvar o PDF",
        )
        self.output_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        self.output_button = ctk.CTkButton(
            output_frame,
            text="Escolher...",
            command=self.choose_output,
            width=110,
        )
        self.output_button.grid(row=0, column=2)

        note = ctk.CTkLabel(
            body,
            text=(
                "Observação: o programa não diminui a resolução. Arquivos PNG, "
                "TIFF ou imagens transparentes podem gerar PDFs maiores."
            ),
            anchor="w",
            justify="left",
            text_color=("gray35", "gray70"),
        )
        note.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, corner_radius=0)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            text="Selecione as imagens que deverão formar o PDF.",
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=22, pady=(12, 4))

        self.progress = ctk.CTkProgressBar(footer)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 14))

        self.open_folder_button = ctk.CTkButton(
            footer,
            text="Abrir pasta",
            command=self.open_output_folder,
            width=110,
            state="disabled",
        )
        self.open_folder_button.grid(row=0, column=1, rowspan=2, padx=(0, 10), pady=12)

        self.convert_button = ctk.CTkButton(
            footer,
            text="Gerar PDF",
            command=self.start_conversion,
            width=145,
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
        )
        self.convert_button.grid(row=0, column=2, rowspan=2, padx=(0, 22), pady=12)

    # ------------------------------------------------------------- Aparência

    def _change_appearance(self, selected: str) -> None:
        mapping = {"Sistema": "system", "Claro": "light", "Escuro": "dark"}
        ctk.set_appearance_mode(mapping[selected])
        self._style_listbox()

    def _style_listbox(self) -> None:
        mode = ctk.get_appearance_mode().casefold()
        if mode == "dark":
            self.listbox.configure(
                bg="#252525",
                fg="#F1F1F1",
                selectbackground="#1F6AA5",
                selectforeground="#FFFFFF",
                highlightbackground="#3B3B3B",
                highlightcolor="#1F6AA5",
            )
        else:
            self.listbox.configure(
                bg="#FFFFFF",
                fg="#1A1A1A",
                selectbackground="#3B8ED0",
                selectforeground="#FFFFFF",
                highlightbackground="#C9C9C9",
                highlightcolor="#3B8ED0",
            )

    # ------------------------------------------------------------- Imagens

    def select_images(self) -> None:
        if self.is_working:
            return

        selected = filedialog.askopenfilenames(
            title="Selecione as imagens",
            filetypes=IMAGE_FILETYPES,
        )
        if not selected:
            return

        existing_normalized = {os.path.normcase(os.path.abspath(p)) for p in self.image_paths}
        added = 0
        ignored: list[str] = []

        for path in selected:
            normalized = os.path.normcase(os.path.abspath(path))
            extension = Path(path).suffix.casefold()

            if extension not in SUPPORTED_EXTENSIONS:
                ignored.append(Path(path).name)
                continue

            if normalized not in existing_normalized:
                self.image_paths.append(os.path.abspath(path))
                existing_normalized.add(normalized)
                added += 1

        if self.image_paths and not self.output_path.get().strip():
            default_output = Path(self.image_paths[0]).parent / "imagens.pdf"
            self.output_path.set(str(default_output))

        self._update_list()
        self.status_label.configure(text=f"{added} imagem(ns) adicionada(s).")

        if ignored:
            messagebox.showwarning(
                "Arquivos ignorados",
                "Alguns arquivos não possuem uma extensão compatível:\n\n"
                + "\n".join(ignored[:12])
                + ("\n..." if len(ignored) > 12 else ""),
            )

    def clear_images(self) -> None:
        if not self.image_paths or self.is_working:
            return
        if messagebox.askyesno("Limpar lista", "Remover todas as imagens da lista?"):
            self.image_paths.clear()
            self._update_list()
            self.status_label.configure(text="Lista de imagens limpa.")

    def remove_selected(self) -> None:
        if self.is_working:
            return
        indices = list(self.listbox.curselection())
        if not indices:
            return
        for index in reversed(indices):
            del self.image_paths[index]
        self._update_list()
        self.status_label.configure(text=f"{len(indices)} item(ns) removido(s).")

    def sort_by_name(self) -> None:
        if self.is_working or len(self.image_paths) < 2:
            return
        self.image_paths.sort(key=natural_sort_key)
        self._update_list()
        self.status_label.configure(text="Imagens ordenadas pelo nome do arquivo.")

    def move_up(self) -> None:
        if self.is_working:
            return
        selected = list(self.listbox.curselection())
        if not selected or selected[0] == 0:
            return

        selected_set = set(selected)
        for index in range(1, len(self.image_paths)):
            if index in selected_set and index - 1 not in selected_set:
                self.image_paths[index - 1], self.image_paths[index] = (
                    self.image_paths[index],
                    self.image_paths[index - 1],
                )

        new_selection = [index - 1 for index in selected]
        self._update_list(new_selection)

    def move_down(self) -> None:
        if self.is_working:
            return
        selected = list(self.listbox.curselection())
        if not selected or selected[-1] == len(self.image_paths) - 1:
            return

        selected_set = set(selected)
        for index in range(len(self.image_paths) - 2, -1, -1):
            if index in selected_set and index + 1 not in selected_set:
                self.image_paths[index], self.image_paths[index + 1] = (
                    self.image_paths[index + 1],
                    self.image_paths[index],
                )

        new_selection = [index + 1 for index in selected]
        self._update_list(new_selection)

    def select_all(self, _event: object | None = None) -> str:
        self.listbox.selection_set(0, tk.END)
        return "break"

    def _update_list(self, selected_indices: Iterable[int] | None = None) -> None:
        self.listbox.delete(0, tk.END)
        total_bytes = 0

        for index, path in enumerate(self.image_paths, start=1):
            try:
                size_bytes = os.path.getsize(path)
            except OSError:
                size_bytes = 0
            total_bytes += size_bytes

            line = (
                f"{index:03d}.  {Path(path).name}    "
                f"[{image_summary(path)} | {human_size(size_bytes)}]"
            )
            self.listbox.insert(tk.END, line)

        if selected_indices:
            for index in selected_indices:
                if 0 <= index < len(self.image_paths):
                    self.listbox.selection_set(index)
                    self.listbox.see(index)

        count = len(self.image_paths)
        noun = "imagem" if count == 1 else "imagens"
        self.count_label.configure(text=f"{count} {noun} • {human_size(total_bytes)}")
        self._style_listbox()
        self._update_control_states()

    # ------------------------------------------------------------- Saída

    def choose_output(self) -> None:
        if self.is_working:
            return

        initial_dir = None
        initial_file = "imagens.pdf"

        current = self.output_path.get().strip()
        if current:
            current_path = Path(current)
            initial_dir = str(current_path.parent)
            initial_file = current_path.name
        elif self.image_paths:
            initial_dir = str(Path(self.image_paths[0]).parent)

        selected = filedialog.asksaveasfilename(
            title="Salvar PDF como",
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialdir=initial_dir,
            initialfile=initial_file,
            confirmoverwrite=True,
        )
        if selected:
            if Path(selected).suffix.casefold() != ".pdf":
                selected += ".pdf"
            self.output_path.set(selected)

    def validate_before_conversion(self) -> tuple[list[str], str] | None:
        if not self.image_paths:
            messagebox.showwarning(
                "Nenhuma imagem",
                "Selecione pelo menos uma imagem antes de gerar o PDF.",
            )
            return None

        missing = [path for path in self.image_paths if not Path(path).is_file()]
        if missing:
            messagebox.showerror(
                "Arquivo não encontrado",
                "Uma ou mais imagens não existem mais:\n\n"
                + "\n".join(missing[:10]),
            )
            return None

        output = self.output_path.get().strip()
        if not output:
            self.choose_output()
            output = self.output_path.get().strip()
            if not output:
                return None

        output_path = Path(output).expanduser()
        if output_path.suffix.casefold() != ".pdf":
            output_path = output_path.with_suffix(".pdf")
            self.output_path.set(str(output_path))

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(
                "Destino inválido",
                f"Não foi possível preparar a pasta de saída:\n{exc}",
            )
            return None

        output_normalized = os.path.normcase(os.path.abspath(output_path))
        input_normalized = {
            os.path.normcase(os.path.abspath(path)) for path in self.image_paths
        }
        if output_normalized in input_normalized:
            messagebox.showerror(
                "Destino inválido",
                "O arquivo PDF não pode substituir uma das imagens de origem.",
            )
            return None

        return list(self.image_paths), str(output_path)

    # ------------------------------------------------------------- Conversão

    def start_conversion(self) -> None:
        if self.is_working:
            return

        validated = self.validate_before_conversion()
        if validated is None:
            return

        images, output = validated
        self.is_working = True
        self.progress.set(0)
        self.status_label.configure(text="Preparando as imagens...")
        self.open_folder_button.configure(state="disabled")
        self._update_control_states()

        worker = threading.Thread(
            target=self._conversion_worker,
            args=(images, output),
            daemon=True,
        )
        worker.start()

    def _conversion_worker(self, images: list[str], output: str) -> None:
        output_path = Path(output)
        temporary_pdf = output_path.with_name(
            f".{output_path.stem}.{os.getpid()}.temporario.pdf"
        )

        try:
            all_notes: list[str] = []
            prepared_images: list[str] = []
            total_steps = len(images) + 1

            with tempfile.TemporaryDirectory(prefix="imagens_para_pdf_") as temp_dir:
                for index, image_path in enumerate(images, start=1):
                    self._ui_status(
                        f"Preparando {index} de {len(images)}: {Path(image_path).name}"
                    )
                    converted_paths, notes = prepare_image_for_pdf(
                        image_path, temp_dir
                    )
                    prepared_images.extend(converted_paths)
                    all_notes.extend(notes)
                    self._ui_progress(index / total_steps)

                if not prepared_images:
                    raise RuntimeError("Nenhuma página pôde ser preparada.")

                self._ui_status(
                    f"Montando o PDF com {len(prepared_images)} página(s)..."
                )

                with open(temporary_pdf, "wb") as pdf_file:
                    # O img2pdf incorpora os arquivos sem redimensionar. JPEG e
                    # JPEG 2000 não são recodificados; os demais usam método sem perda.
                    img2pdf.convert(prepared_images, outputstream=pdf_file)
                    pdf_file.flush()
                    os.fsync(pdf_file.fileno())

                os.replace(temporary_pdf, output_path)

            self._ui_progress(1.0)
            self.after(
                0,
                lambda: self._conversion_success(
                    output=str(output_path),
                    page_count=len(prepared_images),
                    notes=all_notes,
                ),
            )

        except Exception as exc:
            try:
                if temporary_pdf.exists():
                    temporary_pdf.unlink()
            except OSError:
                pass
            self.after(0, lambda error=exc: self._conversion_failure(error))

    def _conversion_success(
        self, output: str, page_count: int, notes: list[str]
    ) -> None:
        self.is_working = False
        self._update_control_states()
        self.open_folder_button.configure(state="normal")

        try:
            output_size = human_size(Path(output).stat().st_size)
        except OSError:
            output_size = "tamanho indisponível"

        self.status_label.configure(
            text=f"PDF criado: {page_count} página(s), {output_size}."
        )

        details = (
            f"O PDF foi criado com sucesso.\n\n"
            f"Páginas: {page_count}\n"
            f"Tamanho: {output_size}\n"
            f"Arquivo:\n{output}"
        )
        if notes:
            details += "\n\nAjustes necessários:\n- " + "\n- ".join(notes[:12])
            if len(notes) > 12:
                details += "\n- ..."

        messagebox.showinfo("PDF concluído", details)

    def _conversion_failure(self, error: Exception) -> None:
        self.is_working = False
        self.progress.set(0)
        self._update_control_states()
        self.status_label.configure(text="Não foi possível gerar o PDF.")
        messagebox.showerror(
            "Erro durante a conversão",
            "O PDF não pôde ser criado.\n\n"
            f"Detalhes técnicos:\n{type(error).__name__}: {error}",
        )

    def _ui_status(self, text: str) -> None:
        self.after(0, lambda: self.status_label.configure(text=text))

    def _ui_progress(self, value: float) -> None:
        self.after(0, lambda: self.progress.set(max(0.0, min(1.0, value))))

    # ------------------------------------------------------------- Estado

    def _update_control_states(self) -> None:
        if self.is_working:
            state = "disabled"
            for widget in (
                self.add_button,
                self.sort_button,
                self.clear_button,
                self.up_button,
                self.down_button,
                self.remove_button,
                self.output_button,
                self.output_entry,
                self.convert_button,
                self.appearance_menu,
            ):
                widget.configure(state=state)
            self.listbox.configure(state=tk.DISABLED)
            return

        self.add_button.configure(state="normal")
        self.output_button.configure(state="normal")
        self.output_entry.configure(state="normal")
        self.appearance_menu.configure(state="normal")
        self.listbox.configure(state=tk.NORMAL)

        has_images = bool(self.image_paths)
        multiple_images = len(self.image_paths) > 1
        self.sort_button.configure(state="normal" if multiple_images else "disabled")
        self.clear_button.configure(state="normal" if has_images else "disabled")
        self.up_button.configure(state="normal" if multiple_images else "disabled")
        self.down_button.configure(state="normal" if multiple_images else "disabled")
        self.remove_button.configure(state="normal" if has_images else "disabled")
        self.convert_button.configure(state="normal" if has_images else "disabled")

    def open_output_folder(self) -> None:
        output = self.output_path.get().strip()
        if not output:
            return

        folder = str(Path(output).expanduser().resolve().parent)
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as exc:
            messagebox.showerror(
                "Não foi possível abrir a pasta",
                f"Abra manualmente este caminho:\n{folder}\n\n{exc}",
            )

    def on_close(self) -> None:
        if self.is_working:
            close = messagebox.askyesno(
                "Conversão em andamento",
                "A conversão ainda está em andamento. Deseja fechar mesmo assim?",
            )
            if not close:
                return
        self.destroy()


def main() -> None:
    app = ImageToPDFApp()
    app.mainloop()


if __name__ == "__main__":
    main()
