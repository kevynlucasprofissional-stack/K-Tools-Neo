# Esse código serve para elecionar vários arquivos de áudio, organizar a ordem
# deles e gerar um único arquivo final juntando tudo.
# ============================================================
# ZONA DE CONFIGURAÇÃO
# ============================================================

APP_TITLE = "Juntador de Áudios"
WINDOW_SIZE = "980x620"

# Extensões aceitas para entrada
SUPPORTED_EXTENSIONS = {
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".aiff", ".mka"
}

# Quando você adiciona uma pasta, procurar também em subpastas?
SCAN_SUBFOLDERS = False

# Ordenação automática ao adicionar arquivos/pasta:
# "natural_name" = 1, 2, 10 em vez de 1, 10, 2
# "modified_time" = por data de modificação
AUTO_SORT_MODE = "natural_name"

# Configuração do áudio intermediário (usado para padronizar tudo)
INTERMEDIATE_SAMPLE_RATE = 48000
INTERMEDIATE_CHANNELS = 2

# Configuração padrão de saída
DEFAULT_OUTPUT_NAME = "audio_unificado.mp3"
DEFAULT_OUTPUT_EXTENSION = ".m4a"   # .mp3, .wav, .m4a, .flac
LOSSY_BITRATE = "192k"

# Abre a pasta final automaticamente quando terminar? (Windows)
AUTO_OPEN_OUTPUT_FOLDER = True

# ============================================================
# IMPORTS
# ============================================================

import importlib
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


# ============================================================
# UTILITÁRIOS
# ============================================================

def ensure_package(package_name: str, import_name: str | None = None) -> None:
    """
    Garante que um pacote exista. Se não existir, tenta instalar automaticamente.
    """
    target_import = import_name or package_name.replace("-", "_")
    try:
        importlib.import_module(target_import)
        return
    except ImportError:
        pass

    try:
        # Garante pip
        subprocess.run(
            [sys.executable, "-m", "ensurepip", "--upgrade"],
            check=False,
            capture_output=True,
            text=True,
        )

        # Instala o pacote
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Não consegui instalar automaticamente o pacote '{package_name}'.\n"
            f"Erro: {exc}"
        ) from exc


def get_ffmpeg_exe() -> str:
    """
    Garante imageio-ffmpeg instalado e retorna o caminho do ffmpeg.
    """
    ensure_package("imageio-ffmpeg", "imageio_ffmpeg")
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def natural_sort_key(text: str):
    """
    Ordenação natural: arquivo2 vem antes de arquivo10.
    """
    parts = re.split(r"(\d+)", text.lower())
    return [int(p) if p.isdigit() else p for p in parts]


def sort_paths(paths: list[Path], mode: str) -> list[Path]:
    if mode == "modified_time":
        return sorted(paths, key=lambda p: (p.stat().st_mtime, p.name.lower()))
    return sorted(paths, key=lambda p: natural_sort_key(p.name))


def is_supported_audio(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def output_codec_for_extension(ext: str) -> tuple[list[str], str]:
    """
    Retorna argumentos de codec do ffmpeg e descrição.
    """
    ext = ext.lower()

    if ext == ".mp3":
        return ["-c:a", "libmp3lame", "-b:a", LOSSY_BITRATE], "MP3"
    if ext == ".wav":
        return ["-c:a", "pcm_s16le"], "WAV"
    if ext == ".m4a":
        return ["-c:a", "aac", "-b:a", LOSSY_BITRATE], "M4A/AAC"
    if ext == ".flac":
        return ["-c:a", "flac"], "FLAC"

    # fallback
    return ["-c:a", "libmp3lame", "-b:a", LOSSY_BITRATE], "MP3 (fallback)"


def ffmpeg_concat_file_line(path: Path) -> str:
    """
    Gera uma linha segura para arquivo de concat do ffmpeg.
    """
    posix_path = path.resolve().as_posix()
    escaped = posix_path.replace("'", r"'\''")
    return f"file '{escaped}'\n"


# ============================================================
# APLICAÇÃO
# ============================================================

class AudioJoinerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(WINDOW_SIZE)
        self.minsize(900, 560)

        self.audio_files: list[Path] = []
        self.output_path = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="Pronto.")
        self.is_processing = False

        self._build_ui()

    # --------------------------------------------------------
    # UI
    # --------------------------------------------------------

    def _build_ui(self):
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill="both", expand=True)

        # Topo
        title = ttk.Label(
            outer,
            text="Juntador de Áudios",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(anchor="w", pady=(0, 10))

        subtitle = ttk.Label(
            outer,
            text=(
                "Adicione arquivos ou uma pasta, ajuste a ordem se quiser, "
                "escolha onde salvar e clique em 'Juntar áudios'."
            )
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        # Botões de ação
        actions = ttk.Frame(outer)
        actions.pack(fill="x", pady=(0, 10))

        ttk.Button(actions, text="Adicionar arquivos", command=self.add_files).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Adicionar pasta", command=self.add_folder).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Remover selecionado", command=self.remove_selected).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Limpar tudo", command=self.clear_all).pack(side="left", padx=(0, 6))

        # Área central
        center = ttk.Frame(outer)
        center.pack(fill="both", expand=True)

        left = ttk.Frame(center)
        left.pack(side="left", fill="both", expand=True)

        right = ttk.Frame(center, width=160)
        right.pack(side="left", fill="y", padx=(10, 0))
        right.pack_propagate(False)

        ttk.Label(left, text="Ordem final dos áudios:").pack(anchor="w", pady=(0, 6))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,
            font=("Consolas", 10)
        )
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        ttk.Button(right, text="Subir", command=self.move_up).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Descer", command=self.move_down).pack(fill="x", pady=(0, 6))
        ttk.Button(right, text="Ordenar automático", command=self.auto_sort).pack(fill="x", pady=(0, 6))

        # Saída
        output_frame = ttk.LabelFrame(outer, text="Salvar como", padding=10)
        output_frame.pack(fill="x", pady=(12, 10))

        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_path)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ttk.Button(output_frame, text="Escolher saída", command=self.choose_output).pack(side="left")

        # Rodapé
        bottom = ttk.Frame(outer)
        bottom.pack(fill="x", pady=(4, 0))

        self.status_label = ttk.Label(bottom, textvariable=self.status_text)
        self.status_label.pack(side="left")

        self.merge_button = ttk.Button(bottom, text="Juntar áudios", command=self.start_merge)
        self.merge_button.pack(side="right")

    # --------------------------------------------------------
    # Ações de lista
    # --------------------------------------------------------

    def refresh_listbox(self):
        self.listbox.delete(0, tk.END)
        for idx, path in enumerate(self.audio_files, start=1):
            self.listbox.insert(tk.END, f"{idx:03d} | {path.name}")

    def add_files(self):
        filetypes = [
            ("Arquivos de áudio", " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))),
            ("Todos os arquivos", "*.*"),
        ]
        selected = filedialog.askopenfilenames(
            title="Selecione os áudios",
            filetypes=filetypes
        )
        if not selected:
            return

        new_files = [Path(p) for p in selected if is_supported_audio(Path(p))]
        new_files = sort_paths(new_files, AUTO_SORT_MODE)

        existing = {p.resolve() for p in self.audio_files}
        for path in new_files:
            if path.resolve() not in existing:
                self.audio_files.append(path)

        self.refresh_listbox()
        self.set_status(f"{len(new_files)} arquivo(s) adicionado(s).")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Selecione a pasta com os áudios")
        if not folder:
            return

        base = Path(folder)
        if SCAN_SUBFOLDERS:
            files = [p for p in base.rglob("*") if is_supported_audio(p)]
        else:
            files = [p for p in base.iterdir() if is_supported_audio(p)]

        files = sort_paths(files, AUTO_SORT_MODE)

        existing = {p.resolve() for p in self.audio_files}
        added_count = 0
        for path in files:
            if path.resolve() not in existing:
                self.audio_files.append(path)
                added_count += 1

        self.refresh_listbox()
        self.set_status(f"{added_count} arquivo(s) adicionados da pasta.")

    def remove_selected(self):
        selected = list(self.listbox.curselection())
        if not selected:
            return

        for idx in reversed(selected):
            del self.audio_files[idx]

        self.refresh_listbox()
        self.set_status("Arquivo(s) removido(s).")

    def clear_all(self):
        self.audio_files.clear()
        self.refresh_listbox()
        self.set_status("Lista limpa.")

    def move_up(self):
        selected = list(self.listbox.curselection())
        if not selected or selected[0] == 0:
            return

        for idx in selected:
            self.audio_files[idx - 1], self.audio_files[idx] = self.audio_files[idx], self.audio_files[idx - 1]

        self.refresh_listbox()
        for idx in [i - 1 for i in selected]:
            self.listbox.selection_set(idx)

    def move_down(self):
        selected = list(self.listbox.curselection())
        if not selected or selected[-1] >= len(self.audio_files) - 1:
            return

        for idx in reversed(selected):
            self.audio_files[idx + 1], self.audio_files[idx] = self.audio_files[idx], self.audio_files[idx + 1]

        self.refresh_listbox()
        for idx in [i + 1 for i in selected]:
            self.listbox.selection_set(idx)

    def auto_sort(self):
        self.audio_files = sort_paths(self.audio_files, AUTO_SORT_MODE)
        self.refresh_listbox()
        self.set_status(f"Lista ordenada por: {AUTO_SORT_MODE}")

    # --------------------------------------------------------
    # Saída
    # --------------------------------------------------------

    def choose_output(self):
        filetypes = [
            ("MP3", "*.mp3"),
            ("WAV", "*.wav"),
            ("M4A", "*.m4a"),
            ("FLAC", "*.flac"),
        ]

        path = filedialog.asksaveasfilename(
            title="Salvar áudio final como...",
            initialfile=DEFAULT_OUTPUT_NAME,
            defaultextension=DEFAULT_OUTPUT_EXTENSION,
            filetypes=filetypes,
        )
        if path:
            self.output_path.set(path)
            self.set_status("Arquivo de saída definido.")

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    def start_merge(self):
        if self.is_processing:
            return

        if not self.audio_files:
            messagebox.showwarning("Aviso", "Adicione pelo menos 1 arquivo de áudio.")
            return

        if not self.output_path.get().strip():
            self.choose_output()
            if not self.output_path.get().strip():
                return

        output = Path(self.output_path.get().strip())
        output.parent.mkdir(parents=True, exist_ok=True)

        self.is_processing = True
        self.merge_button.config(state="disabled")
        self.set_status("Preparando...")

        thread = threading.Thread(target=self._merge_worker, daemon=True)
        thread.start()

    def _merge_worker(self):
        try:
            ffmpeg = get_ffmpeg_exe()

            ordered_files = list(self.audio_files)
            output_file = Path(self.output_path.get().strip())
            ext = output_file.suffix.lower() or DEFAULT_OUTPUT_EXTENSION
            codec_args, codec_name = output_codec_for_extension(ext)

            with tempfile.TemporaryDirectory(prefix="audio_joiner_") as temp_dir:
                temp_dir_path = Path(temp_dir)
                converted_files: list[Path] = []

                total = len(ordered_files)

                # 1) Converter tudo para WAV padronizado
                for index, input_file in enumerate(ordered_files, start=1):
                    self.set_status(f"Convertendo {index}/{total}: {input_file.name}")

                    temp_wav = temp_dir_path / f"{index:05d}.wav"

                    cmd = [
                        ffmpeg,
                        "-y",
                        "-hide_banner",
                        "-loglevel", "error",
                        "-i", str(input_file),
                        "-vn",
                        "-ar", str(INTERMEDIATE_SAMPLE_RATE),
                        "-ac", str(INTERMEDIATE_CHANNELS),
                        "-c:a", "pcm_s16le",
                        str(temp_wav),
                    ]

                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )

                    if result.returncode != 0 or not temp_wav.exists():
                        raise RuntimeError(
                            f"Falha ao converter:\n{input_file.name}\n\n"
                            f"Detalhes:\n{(result.stderr or result.stdout).strip()}"
                        )

                    converted_files.append(temp_wav)

                # 2) Criar arquivo de concat
                self.set_status("Montando sequência final...")

                concat_list = temp_dir_path / "concat_list.txt"
                with concat_list.open("w", encoding="utf-8") as f:
                    for wav in converted_files:
                        f.write(ffmpeg_concat_file_line(wav))

                # 3) Concatenar e gerar saída final
                self.set_status(f"Gerando arquivo final em {codec_name}...")

                final_cmd = [
                    ffmpeg,
                    "-y",
                    "-hide_banner",
                    "-loglevel", "error",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_list),
                    *codec_args,
                    str(output_file),
                ]

                result = subprocess.run(
                    final_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                if result.returncode != 0 or not output_file.exists():
                    raise RuntimeError(
                        f"Falha ao gerar o arquivo final.\n\n"
                        f"Detalhes:\n{(result.stderr or result.stdout).strip()}"
                    )

            self.set_status("Concluído com sucesso.")
            self._show_success(output_file)

        except Exception as exc:
            self.set_status("Erro.")
            self._show_error(str(exc))

        finally:
            self.is_processing = False
            self.after(0, lambda: self.merge_button.config(state="normal"))

    # --------------------------------------------------------
    # Helpers de UI thread-safe
    # --------------------------------------------------------

    def set_status(self, text: str):
        self.after(0, lambda: self.status_text.set(text))

    def _show_success(self, output_file: Path):
        def _ui():
            messagebox.showinfo(
                "Pronto",
                f"Áudio final criado com sucesso:\n\n{output_file}"
            )
            if AUTO_OPEN_OUTPUT_FOLDER and os.name == "nt":
                try:
                    os.startfile(str(output_file.parent))
                except Exception:
                    pass
        self.after(0, _ui)

    def _show_error(self, message: str):
        self.after(0, lambda: messagebox.showerror("Erro", message))


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    app = AudioJoinerApp()
    app.mainloop()