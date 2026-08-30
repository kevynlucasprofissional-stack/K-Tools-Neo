"""
K-Tools Neo v0.4.2 - Correção final

Esta versão consolida o shell visual em CustomTkinter, componentes reutilizáveis e telas funcionais de Markdown/TXT, Áudio, Vídeo, Arquivos/Pastas e Configurações:
- SidebarButton;
- ToolCard;
- ActionButton;
- StatusBadge;
- FileTable;
- EmptyState;
- ProgressPanel;
- ToastMessage.
- Tela Markdown/TXT funcional.
- Seção Áudio funcional.
- Seção Vídeo funcional para juntar vídeos.
- Seção Arquivos/Pastas funcional para diagnóstico e exportação de relatórios.
- Tela Configurações funcional para aparência, FFmpeg, dependências, saída e logs.

Importante:
- As telas Markdown/TXT, Áudio, Vídeo, Arquivos/Pastas e Configurações já executam tarefas reais.
- O layout usa grid como padrão. Não há mistura de pack() e grid() no mesmo container.
"""

from __future__ import annotations

import importlib
import csv
import json
import subprocess
import sys
import tkinter as tk
import threading
import re
import os
import shutil
import tempfile
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


# -----------------------------------------------------------------------------
# Dependências
# -----------------------------------------------------------------------------

def _pip_install(package: str) -> None:
    """Instala/atualiza uma dependência com fallback --user para Windows sem permissão administrativa."""
    base_cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package]
    try:
        subprocess.check_call(base_cmd)
    except subprocess.CalledProcessError:
        subprocess.check_call(base_cmd + ["--user"])


def ensure_package(import_name: str, pip_name: Optional[str] = None) -> object:
    """Importa um pacote e tenta instalar automaticamente se estiver ausente ou quebrado."""
    package = pip_name or import_name
    try:
        return importlib.import_module(import_name)
    except ImportError as first_error:
        # Python 3.13 removeu audioop; algumas versões do pydub falham pedindo audioop/pyaudioop.
        if import_name == "pydub" or "audioop" in str(first_error).lower() or "pyaudioop" in str(first_error).lower():
            try:
                print("[K-Tools Neo] Instalando compatibilidade de áudio: audioop-lts")
                _pip_install("audioop-lts")
                importlib.invalidate_caches()
            except Exception:
                pass
        print(f"[K-Tools Neo] Instalando dependência ausente: {package}")
        _pip_install(package)
        importlib.invalidate_caches()
        try:
            return importlib.import_module(import_name)
        except ImportError as second_error:
            if import_name == "pydub":
                _pip_install("audioop-lts")
                importlib.invalidate_caches()
                return importlib.import_module(import_name)
            raise second_error


try:
    ctk = ensure_package("customtkinter")
except Exception as exc:  # pragma: no cover - fallback de inicialização
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "K-Tools Neo - erro de dependência",
        "Não foi possível instalar/importar o CustomTkinter.\n\n"
        f"Erro técnico:\n{exc}\n\n"
        "Tente executar manualmente:\npython -m pip install customtkinter",
    )
    raise SystemExit(1)


# -----------------------------------------------------------------------------
# Tema / tokens visuais
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Theme:
    """Tokens visuais centrais do K-Tools Neo."""

    bg_root: str = "#0D1017"
    bg_sidebar: str = "#121722"
    bg_header: str = "#10141D"
    bg_surface: str = "#1A1F2B"
    bg_surface_alt: str = "#202736"
    bg_surface_hover: str = "#273144"
    bg_input: str = "#161A23"
    bg_table: str = "#141821"
    bg_table_header: str = "#1F2430"

    border_soft: str = "#2B3240"
    border_medium: str = "#3A4252"
    border_hover: str = "#4A9BFF"

    primary: str = "#2F80ED"
    primary_hover: str = "#3B8CFF"
    primary_pressed: str = "#1F5FBF"
    primary_active: str = "#173A66"
    primary_soft: str = "#1F3B66"

    success: str = "#22C55E"
    warning: str = "#F59E0B"
    danger: str = "#EF4444"
    info: str = "#38BDF8"

    text_primary: str = "#F5F7FA"
    text_secondary: str = "#AAB2C0"
    text_muted: str = "#6F7887"
    text_inverse: str = "#FFFFFF"

    font_family: str = "Segoe UI"
    mono_font: str = "Consolas"


THEME = Theme()

APP_VERSION = "0.4.2"

ACCENT_COLORS = {
    "Azul": "#2F80ED",
    "Ciano": "#38BDF8",
    "Verde": "#22C55E",
    "Roxo": "#8B5CF6",
    "Laranja": "#F59E0B",
}

DEPENDENCY_CHECKS = [
    ("customtkinter", "customtkinter", "Interface moderna"),
    ("imageio_ffmpeg", "imageio-ffmpeg", "FFmpeg automático"),
    ("moviepy", "moviepy", "Processamento de vídeo"),
    ("audioop", "audioop-lts", "Compatibilidade de áudio no Python 3.13+"),
    ("pydub", "pydub", "Corte/manipulação de áudio"),
    ("pandas", "pandas", "Relatórios e planilhas"),
    ("openpyxl", "openpyxl", "Exportação XLSX"),
]


def get_app_data_dir() -> Path:
    """Diretório persistente para configurações e logs do K-Tools Neo."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "K-Tools Neo"
    return Path.home() / ".k_tools_neo"


def default_output_dir() -> Path:
    """Pasta padrão segura para resultados."""
    return Path.home() / "K-Tools Outputs"


def default_settings_config() -> Dict[str, object]:
    return {
        "appearance_mode": "Escuro",
        "accent_color": "Azul",
        "default_output_folder": str(default_output_dir()),
        "open_folder_on_finish": True,
        "confirm_overwrite": True,
        "save_last_folder": True,
    }


def load_settings_config(config_path: Path) -> Dict[str, object]:
    """Carrega config.json; se não existir ou estiver inválido, usa padrões seguros."""
    config = default_settings_config()
    try:
        if config_path.exists():
            loaded = json.loads(config_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
    except Exception:
        # Se estiver corrompido, mantém padrões. A UI avisará ao salvar novamente.
        pass
    # O visual do K-Tools Neo agora é fixo: fundo escuro com destaque azul.
    config["appearance_mode"] = "Escuro"
    config["accent_color"] = "Azul"
    return config


def save_settings_config(config_path: Path, config: Dict[str, object]) -> None:
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def appearance_to_ctk(value: str) -> str:
    mapping = {"Escuro": "dark", "Claro": "light", "Sistema": "system"}
    return mapping.get(value, "dark")


def open_path_in_os(path: Path) -> None:
    """Abre pasta/arquivo no explorador padrão do sistema."""
    path = Path(path)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])

# -----------------------------------------------------------------------------
# Utilidades funcionais da tela Markdown/TXT
# -----------------------------------------------------------------------------

TEXT_EXTENSIONS = {".md", ".txt"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".wma", ".aiff", ".mka"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".m4v"}


def get_ffmpeg_exe() -> str:
    """Localiza FFmpeg no sistema ou via imageio-ffmpeg, instalando sob demanda."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    imageio_ffmpeg = ensure_package("imageio_ffmpeg", "imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def subprocess_creationflags() -> int:
    """Oculta a janela de console do FFmpeg no Windows quando possível."""
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def run_ffmpeg(args: Sequence[str]) -> subprocess.CompletedProcess:
    """Executa FFmpeg com captura de erro para mensagens amigáveis."""
    command = [get_ffmpeg_exe(), *map(str, args)]
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=subprocess_creationflags(),
    )


def audio_codec_args(output_path: Path) -> List[str]:
    """Define codec de saída conforme extensão escolhida."""
    ext = output_path.suffix.lower()
    if ext == ".mp3":
        return ["-c:a", "libmp3lame", "-q:a", "2"]
    if ext in {".m4a", ".aac"}:
        return ["-c:a", "aac", "-b:a", "192k"]
    if ext == ".wav":
        return ["-c:a", "pcm_s16le"]
    if ext == ".flac":
        return ["-c:a", "flac"]
    if ext == ".ogg":
        return ["-c:a", "libvorbis", "-q:a", "5"]
    return ["-c:a", "aac", "-b:a", "192k"]


def ensure_audio_extension(path: Path, fmt: str) -> Path:
    fmt = (fmt or "m4a").lower().lstrip(".")
    if fmt not in {"mp3", "m4a", "wav", "flac", "aac", "ogg"}:
        fmt = "m4a"
    return path.with_suffix(f".{fmt}") if path.suffix.lower() != f".{fmt}" else path


def is_supported_audio_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    except OSError:
        return False


def is_supported_video_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    except OSError:
        return False


def concat_file_line(path: Path) -> str:
    # FFmpeg concat demuxer aceita / no Windows. Escapa aspas simples.
    text = str(path.resolve()).replace("\\", "/").replace("'", "\\'")
    return f"file '{text}'\n"


def ffmpeg_error_message(result: subprocess.CompletedProcess, fallback: str) -> str:
    stderr = (result.stderr or "").strip()
    if not stderr:
        return fallback
    # Mantém a mensagem curta para UI, mas preserva informação útil.
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    tail = "\n".join(lines[-6:])
    return f"{fallback}\n\nDetalhes:\n{tail}"


def convert_media_audio_to_wav(input_path: Path, wav_path: Path) -> None:
    result = run_ffmpeg([
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "2",
        "-ar", "44100",
        "-c:a", "pcm_s16le",
        str(wav_path),
    ])
    if result.returncode != 0 or not wav_path.exists():
        raise RuntimeError(ffmpeg_error_message(result, f"Não foi possível converter/extrair áudio de: {input_path.name}"))


def join_audio_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Junta áudios convertendo entradas para WAV temporário e concatenando com FFmpeg."""
    files = [Path(p) for p in input_files if is_supported_audio_file(Path(p))]
    if not files:
        raise ValueError("Nenhum arquivo de áudio compatível foi selecionado.")
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ktools_audio_join_") as temp_dir:
        temp_path = Path(temp_dir)
        wavs: List[Path] = []
        total_steps = len(files) + 1
        for index, src in enumerate(files, start=1):
            if progress_callback:
                progress_callback((index - 1) / total_steps, f"Convertendo {index} de {len(files)}: {src.name}")
            wav_path = temp_path / f"part_{index:04d}.wav"
            convert_media_audio_to_wav(src, wav_path)
            wavs.append(wav_path)

        concat_list = temp_path / "concat_list.txt"
        concat_list.write_text("".join(concat_file_line(p) for p in wavs), encoding="utf-8")
        if progress_callback:
            progress_callback(len(files) / total_steps, "Unindo áudios e salvando arquivo final...")
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            *audio_codec_args(output_file),
            str(output_file),
        ])
        if result.returncode != 0 or not output_file.exists():
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível juntar os áudios."))
        if progress_callback:
            progress_callback(1.0, "Áudio final gerado com sucesso.")
    return output_file


def get_media_duration_seconds(path: Path) -> float:
    """Obtém duração lendo a saída do FFmpeg."""
    result = run_ffmpeg(["-i", str(path)])
    output = (result.stderr or "") + "\n" + (result.stdout or "")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not match:
        raise RuntimeError("Não foi possível identificar a duração do arquivo com FFmpeg.")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def split_audio_file(
    input_file: Path,
    output_folder: Path,
    parts: int,
    output_format: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """Divide um áudio em partes iguais."""
    input_file = Path(input_file)
    if not is_supported_audio_file(input_file):
        raise ValueError("Selecione um arquivo de áudio compatível.")
    if parts < 2:
        raise ValueError("O número de partes deve ser pelo menos 2.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    duration = get_media_duration_seconds(input_file)
    if duration <= 0:
        raise RuntimeError("A duração do áudio é inválida.")
    part_duration = duration / parts
    fmt = output_format.lower().lstrip(".") or "m4a"
    outputs: List[Path] = []
    for index in range(1, parts + 1):
        start = (index - 1) * part_duration
        current_duration = duration - start if index == parts else part_duration
        out = output_folder / f"{input_file.stem}_parte_{index:02d}_de_{parts:02d}.{fmt}"
        if progress_callback:
            progress_callback((index - 1) / parts, f"Gerando parte {index} de {parts}...")
        result = run_ffmpeg([
            "-y",
            "-i", str(input_file),
            "-ss", f"{start:.3f}",
            "-t", f"{current_duration:.3f}",
            "-vn",
            *audio_codec_args(out),
            str(out),
        ])
        if result.returncode != 0 or not out.exists():
            raise RuntimeError(ffmpeg_error_message(result, f"Não foi possível gerar a parte {index}."))
        outputs.append(out)
    if progress_callback:
        progress_callback(1.0, "Áudio dividido com sucesso.")
    return outputs


def extract_audio_from_video(
    video_file: Path,
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    video_file = Path(video_file)
    if not is_supported_video_file(video_file):
        raise ValueError("Selecione um arquivo de vídeo compatível.")
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if progress_callback:
        progress_callback(0.15, "Extraindo áudio do vídeo...")
    result = run_ffmpeg([
        "-y",
        "-i", str(video_file),
        "-vn",
        *audio_codec_args(output_file),
        str(output_file),
    ])
    if result.returncode != 0 or not output_file.exists():
        raise RuntimeError(ffmpeg_error_message(result, "Não foi possível extrair áudio deste vídeo."))
    if progress_callback:
        progress_callback(1.0, "Áudio extraído com sucesso.")
    return output_file


def extract_and_join_audio_from_videos(
    video_files: Sequence[Path],
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Extrai áudio de vários vídeos e une em um único áudio final."""
    files = [Path(p) for p in video_files if is_supported_video_file(Path(p))]
    if not files:
        raise ValueError("Nenhum vídeo compatível foi selecionado.")
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    skipped: List[str] = []
    with tempfile.TemporaryDirectory(prefix="ktools_video_audio_") as temp_dir:
        temp_path = Path(temp_dir)
        wavs: List[Path] = []
        total_steps = len(files) + 1
        for index, src in enumerate(files, start=1):
            if progress_callback:
                progress_callback((index - 1) / total_steps, f"Extraindo áudio {index} de {len(files)}: {src.name}")
            wav_path = temp_path / f"video_audio_{index:04d}.wav"
            try:
                convert_media_audio_to_wav(src, wav_path)
                wavs.append(wav_path)
            except Exception:
                skipped.append(src.name)
        if not wavs:
            raise RuntimeError("Nenhum dos vídeos selecionados possui áudio extraível.")
        concat_list = temp_path / "concat_video_audio.txt"
        concat_list.write_text("".join(concat_file_line(p) for p in wavs), encoding="utf-8")
        if progress_callback:
            msg = "Unindo áudios extraídos..."
            if skipped:
                msg += f" ({len(skipped)} vídeo(s) ignorado(s) sem áudio ou com erro)"
            progress_callback(len(files) / total_steps, msg)
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            *audio_codec_args(output_file),
            str(output_file),
        ])
        if result.returncode != 0 or not output_file.exists():
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível unir os áudios extraídos dos vídeos."))
        if progress_callback:
            progress_callback(1.0, "Áudio dos vídeos gerado com sucesso.")
    return output_file



def ensure_video_extension(path: Path) -> Path:
    """Garante saída .mp4 para a V1 do módulo de vídeo."""
    return path.with_suffix(".mp4") if path.suffix.lower() != ".mp4" else path


def join_video_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Junta vídeos em MP4 usando FFmpeg.

    Estratégia:
    1. tenta concatenação rápida sem recodificar (-c copy);
    2. se falhar, normaliza os vídeos para MP4/H.264/AAC e concatena novamente.

    Isso mantém o processamento leve quando os vídeos são compatíveis e oferece
    uma rota mais tolerante quando vêm de celulares/câmeras diferentes.
    """
    files = [Path(p) for p in input_files if is_supported_video_file(Path(p))]
    if not files:
        raise ValueError("Nenhum arquivo de vídeo compatível foi selecionado.")

    output_file = ensure_video_extension(Path(output_file))
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        output_resolved = output_file.resolve() if output_file.exists() else output_file.absolute()
        input_resolved = [p.resolve() if p.exists() else p.absolute() for p in files]
        if output_resolved in input_resolved:
            raise ValueError("O vídeo final não pode ser um dos vídeos de entrada.")
    except ValueError:
        raise
    except Exception:
        pass

    with tempfile.TemporaryDirectory(prefix="ktools_video_join_") as temp_dir:
        temp_path = Path(temp_dir)
        concat_list = temp_path / "concat_videos.txt"
        concat_list.write_text("".join(concat_file_line(p) for p in files), encoding="utf-8")

        if progress_callback:
            progress_callback(0.05, "Tentando juntar vídeos no modo rápido...")
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_file),
        ])
        if result.returncode == 0 and output_file.exists() and safe_stat_size(output_file) > 0:
            if progress_callback:
                progress_callback(1.0, "Vídeo final gerado com sucesso.")
            return output_file

        # O modo rápido pode falhar quando os vídeos têm codecs/resoluções diferentes.
        # Remove arquivo parcial antes da rota compatível.
        try:
            if output_file.exists():
                output_file.unlink()
        except OSError:
            pass

        normalized: List[Path] = []
        total_steps = len(files) + 1
        for index, src in enumerate(files, start=1):
            if progress_callback:
                progress_callback((index - 1) / total_steps, f"Normalizando vídeo {index} de {len(files)}: {src.name}")
            temp_video = temp_path / f"video_{index:04d}.mp4"
            # -map 0:a? preserva áudio quando existir e não falha se o arquivo estiver sem áudio.
            result = run_ffmpeg([
                "-y",
                "-i", str(src),
                "-map", "0:v:0",
                "-map", "0:a?",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                str(temp_video),
            ])
            if result.returncode != 0 or not temp_video.exists():
                raise RuntimeError(ffmpeg_error_message(result, f"Não foi possível preparar o vídeo: {src.name}"))
            normalized.append(temp_video)

        concat_normalized = temp_path / "concat_normalized.txt"
        concat_normalized.write_text("".join(concat_file_line(p) for p in normalized), encoding="utf-8")
        if progress_callback:
            progress_callback(len(files) / total_steps, "Unindo vídeos normalizados e salvando MP4 final...")
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_normalized),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_file),
        ])
        if result.returncode != 0 or not output_file.exists():
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível juntar os vídeos."))
        if progress_callback:
            progress_callback(1.0, "Vídeo final gerado com sucesso.")
    return output_file


def natural_key(value: object):
    """Chave de ordenação natural: arquivo2 vem antes de arquivo10."""
    text = str(value).lower()
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


def safe_stat_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def format_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def sort_paths(paths: Sequence[Path], mode: str = "natural") -> List[Path]:
    """Ordena uma lista de Paths por modo visual escolhido na tela."""
    mode = (mode or "natural").lower()
    if mode == "name":
        return sorted(paths, key=lambda p: str(p.name).lower())
    if mode == "modified":
        return sorted(paths, key=lambda p: (safe_mtime(p), natural_key(p.name)))
    return sorted(paths, key=lambda p: natural_key(p.name))


def is_supported_text_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS
    except OSError:
        return False


def read_text_with_fallback(path: Path) -> str:
    """Lê texto tentando codificações comuns em arquivos exportados do Windows/Obsidian."""
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    return path.read_text(encoding="utf-8")


def merge_text_files(
    input_files: Sequence[Path],
    output_file: Path,
    separator_mode: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Path:
    """Une arquivos .md/.txt em um único arquivo final, preservando a origem quando solicitado."""
    if not input_files:
        raise ValueError("Nenhum arquivo .md ou .txt foi selecionado.")

    normalized_inputs: List[Path] = []
    for path in input_files:
        p = Path(path)
        if not is_supported_text_file(p):
            raise ValueError(f"Arquivo inválido ou incompatível: {p}")
        normalized_inputs.append(p)

    output_file = Path(output_file)
    if output_file.suffix.lower() not in TEXT_EXTENSIONS:
        output_file = output_file.with_suffix(".md")

    # Impede o caso perigoso: o arquivo final também estar na lista de entrada.
    output_resolved = output_file.resolve() if output_file.exists() else output_file.absolute()
    input_resolved = []
    for path in normalized_inputs:
        try:
            input_resolved.append(path.resolve())
        except OSError:
            input_resolved.append(path.absolute())
    if output_resolved in input_resolved:
        raise ValueError(
            "O arquivo final não pode ser um dos arquivos de entrada. "
            "Escolha outro nome ou outra pasta de saída."
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    total = len(normalized_inputs)

    with output_file.open("w", encoding="utf-8", newline="\n") as out:
        for index, path in enumerate(normalized_inputs, start=1):
            if progress_callback:
                progress_callback(index, total, f"Unindo arquivo {index} de {total}: {path.name}")

            if separator_mode == "completo":
                out.write("\n---\n")
                out.write(f"<!-- INÍCIO DO ARQUIVO: {path.name} -->\n")
                out.write("---\n\n")
            elif separator_mode == "simples":
                out.write(f"\n\n# {path.name}\n\n")

            out.write(read_text_with_fallback(path))

            if separator_mode == "completo":
                out.write("\n\n---\n")
                out.write(f"<!-- FIM DO ARQUIVO: {path.name} -->\n")
                out.write("---\n\n")
            else:
                out.write("\n\n")

    return output_file



# -----------------------------------------------------------------------------
# Utilidades funcionais da tela Arquivos/Pastas
# -----------------------------------------------------------------------------

def is_hidden_like(path: Path, root: Optional[Path] = None) -> bool:
    """Detecta arquivos/pastas ocultos pelo nome, mantendo compatibilidade simples entre sistemas."""
    try:
        parts = path.relative_to(root).parts if root else path.parts
    except Exception:
        parts = path.parts
    return any(part.startswith(".") for part in parts if part not in (".", ".."))


def safe_modified_iso(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def folder_entry(path: Path, root: Path, kind: str) -> Dict[str, object]:
    """Cria uma linha padronizada para arquivos e diretórios."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = Path(path.name)
    size = safe_stat_size(path) if kind == "Arquivo" else 0
    return {
        "tipo": kind,
        "nome": path.name,
        "extensao": path.suffix.lower() if kind == "Arquivo" else "",
        "tamanho_bytes": size,
        "tamanho": format_size(size) if kind == "Arquivo" else "—",
        "pasta": str(path.parent),
        "caminho_relativo": str(relative),
        "caminho_absoluto": str(path.resolve()) if path.exists() else str(path.absolute()),
        "modificado_em": safe_modified_iso(path),
    }


def scan_folder_structure(
    root_folder: Path,
    include_files: bool = True,
    include_dirs: bool = True,
    include_hidden: bool = False,
    include_subfolders: bool = True,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, object]:
    """Varre uma pasta e retorna entradas, erros e estatísticas para a UI/exportação."""
    root_folder = Path(root_folder)
    if not root_folder.exists() or not root_folder.is_dir():
        raise ValueError("Selecione uma pasta raiz válida.")

    entries: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []
    total_size = 0

    def onerror(error: OSError) -> None:
        errors.append({"caminho": str(getattr(error, "filename", "")), "erro": str(error)})

    processed_dirs = 0
    for dirpath, dirnames, filenames in os.walk(root_folder, onerror=onerror):
        current = Path(dirpath)
        processed_dirs += 1

        if not include_hidden:
            dirnames[:] = [name for name in dirnames if not is_hidden_like(current / name, root_folder)]
            filenames = [name for name in filenames if not is_hidden_like(current / name, root_folder)]

        # Diretórios são registrados antes dos arquivos para manter leitura parecida com árvore.
        if include_dirs:
            for dirname in sorted(dirnames, key=natural_key):
                path = current / dirname
                try:
                    entries.append(folder_entry(path, root_folder, "Pasta"))
                except OSError as exc:
                    errors.append({"caminho": str(path), "erro": str(exc)})

        if include_files:
            for filename in sorted(filenames, key=natural_key):
                path = current / filename
                try:
                    entry = folder_entry(path, root_folder, "Arquivo")
                    total_size += int(entry["tamanho_bytes"])
                    entries.append(entry)
                except OSError as exc:
                    errors.append({"caminho": str(path), "erro": str(exc)})

        if progress_callback and processed_dirs % 10 == 0:
            progress_callback(0.15, f"Analisando pastas... {processed_dirs} diretório(s) visitado(s), {len(entries)} item(ns) encontrados.")

        if not include_subfolders:
            dirnames[:] = []

    file_count = sum(1 for entry in entries if entry.get("tipo") == "Arquivo")
    dir_count = sum(1 for entry in entries if entry.get("tipo") == "Pasta")
    stats = {
        "pasta_raiz": str(root_folder),
        "total_itens": len(entries),
        "total_arquivos": file_count,
        "total_pastas": dir_count,
        "tamanho_total_bytes": total_size,
        "tamanho_total": format_size(total_size),
        "erros_acesso": len(errors),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
    if progress_callback:
        progress_callback(0.45, f"Análise concluída: {file_count} arquivo(s), {dir_count} pasta(s), {len(errors)} erro(s).")
    return {"entries": entries, "errors": errors, "stats": stats}


def report_base_name(mode: str) -> str:
    return "lista_arquivos" if mode == "list" else "estrutura_pastas"


def write_txt_report(scan_result: Dict[str, object], output_path: Path, mode: str) -> None:
    stats = scan_result["stats"]
    entries = scan_result["entries"]
    errors = scan_result["errors"]
    title = "LISTA DE ARQUIVOS" if mode == "list" else "ESTRUTURA DE PASTAS"
    with output_path.open("w", encoding="utf-8", newline="\n") as out:
        out.write(f"{title}\n")
        out.write("=" * len(title) + "\n\n")
        out.write(f"Pasta raiz: {stats['pasta_raiz']}\n")
        out.write(f"Gerado em: {stats['gerado_em']}\n")
        out.write(f"Total de arquivos: {stats['total_arquivos']}\n")
        out.write(f"Total de pastas: {stats['total_pastas']}\n")
        out.write(f"Tamanho total: {stats['tamanho_total']}\n")
        out.write(f"Erros de acesso: {stats['erros_acesso']}\n\n")
        out.write("ITENS\n-----\n")
        for entry in entries:
            out.write(f"[{entry['tipo']}] {entry['caminho_relativo']} | {entry['tamanho']}\n")
        if errors:
            out.write("\nERROS\n-----\n")
            for error in errors:
                out.write(f"{error.get('caminho', '')}: {error.get('erro', '')}\n")


def write_json_report(scan_result: Dict[str, object], output_path: Path) -> None:
    output_path.write_text(json.dumps(scan_result, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv_report(scan_result: Dict[str, object], output_path: Path) -> None:
    entries = scan_result["entries"]
    fieldnames = ["tipo", "nome", "extensao", "tamanho_bytes", "tamanho", "pasta", "caminho_relativo", "caminho_absoluto", "modificado_em"]
    with output_path.open("w", encoding="utf-8-sig", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)


def write_xlsx_report(scan_result: Dict[str, object], output_path: Path) -> None:
    openpyxl = ensure_package("openpyxl")
    Workbook = openpyxl.Workbook
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Resumo"
    stats = scan_result["stats"]
    ws_summary.append(["Métrica", "Valor"])
    for key, value in stats.items():
        ws_summary.append([key, value])

    ws_items = wb.create_sheet("Itens")
    headers = ["tipo", "nome", "extensao", "tamanho_bytes", "tamanho", "pasta", "caminho_relativo", "caminho_absoluto", "modificado_em"]
    ws_items.append(headers)
    for entry in scan_result["entries"]:
        ws_items.append([entry.get(header, "") for header in headers])

    ws_errors = wb.create_sheet("Erros")
    ws_errors.append(["caminho", "erro"])
    for error in scan_result["errors"]:
        ws_errors.append([error.get("caminho", ""), error.get("erro", "")])

    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 70)

    wb.save(output_path)


def export_folder_reports(
    scan_result: Dict[str, object],
    output_folder: Path,
    formats: Sequence[str],
    mode: str = "structure",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Path]:
    """Exporta relatórios selecionados e retorna caminhos gerados."""
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    selected = [fmt.lower() for fmt in formats]
    if not selected:
        raise ValueError("Selecione pelo menos um formato de exportação.")

    generated: Dict[str, Path] = {}
    total = len(selected)
    base = report_base_name(mode)
    for index, fmt in enumerate(selected, start=1):
        if progress_callback:
            progress_callback(0.45 + (index - 1) / max(total, 1) * 0.5, f"Gerando relatório {fmt.upper()} ({index}/{total})...")
        path = output_folder / f"{base}.{fmt}"
        if fmt == "txt":
            write_txt_report(scan_result, path, mode)
        elif fmt == "json":
            write_json_report(scan_result, path)
        elif fmt == "csv":
            write_csv_report(scan_result, path)
        elif fmt == "xlsx":
            write_xlsx_report(scan_result, path)
        else:
            continue
        generated[fmt] = path
    if progress_callback:
        progress_callback(1.0, "Relatórios exportados com sucesso.")
    return generated

# -----------------------------------------------------------------------------
# Componentes reutilizáveis
# -----------------------------------------------------------------------------

class StatusBadge(ctk.CTkFrame):
    """Badge compacto para status como OK, erro, alerta e processando."""

    COLORS = {
        "success": ("#12261A", THEME.success, "#BBF7D0"),
        "warning": ("#2A2112", THEME.warning, "#FDE68A"),
        "danger": ("#2A1717", THEME.danger, "#FECACA"),
        "info": ("#102536", THEME.info, "#BAE6FD"),
        "processing": (THEME.primary_active, THEME.primary, "#DCEBFF"),
        "neutral": (THEME.bg_surface_alt, THEME.border_medium, THEME.text_secondary),
        "disabled": ("#171B24", THEME.border_soft, THEME.text_muted),
    }

    def __init__(self, master, text: str, status: str = "neutral", icon: str = "", **kwargs) -> None:
        bg, border, text_color = self.COLORS.get(status, self.COLORS["neutral"])
        super().__init__(
            master,
            fg_color=bg,
            border_color=border,
            border_width=1,
            corner_radius=999,
            **kwargs,
        )
        self.status = status
        self.grid_columnconfigure(0, weight=1)
        label_text = f"{icon} {text}".strip()
        self.label = ctk.CTkLabel(
            self,
            text=label_text,
            text_color=text_color,
            font=(THEME.font_family, 11, "bold"),
            padx=10,
            pady=3,
        )
        self.label.grid(row=0, column=0, sticky="nsew")

    def set_status(self, text: str, status: str, icon: str = "") -> None:
        bg, border, text_color = self.COLORS.get(status, self.COLORS["neutral"])
        self.status = status
        self.configure(fg_color=bg, border_color=border)
        self.label.configure(text=f"{icon} {text}".strip(), text_color=text_color)


class ActionButton(ctk.CTkButton):
    """Botão padrão com variantes e feedback visual de clique."""

    VARIANTS = {
        "primary": {
            "fg": THEME.primary,
            "hover": THEME.primary_hover,
            "pressed": THEME.primary_pressed,
            "text": THEME.text_inverse,
            "border_width": 0,
            "border": THEME.bg_surface_alt,
        },
        "secondary": {
            "fg": THEME.bg_surface_alt,
            "hover": "#303746",
            "pressed": "#1F2937",
            "text": THEME.text_primary,
            "border_width": 1,
            "border": THEME.border_medium,
        },
        "ghost": {
            "fg": "transparent",
            "hover": THEME.bg_surface_hover,
            "pressed": "#303746",
            "text": THEME.text_secondary,
            "border_width": 0,
            "border": THEME.bg_surface_alt,
        },
    }

    def __init__(
        self,
        master,
        text: str,
        variant: str = "secondary",
        command: Optional[Callable[[], None]] = None,
        icon: str = "",
        **kwargs,
    ) -> None:
        self.variant = variant if variant in self.VARIANTS else "secondary"
        self.palette = self.VARIANTS[self.variant]
        self.user_command = command
        self.base_text = f"{icon} {text}".strip()
        self.loading = False
        button_height = kwargs.pop("height", 40)

        super().__init__(
            master,
            text=self.base_text,
            command=self._on_press,
            height=button_height,
            corner_radius=12,
            font=(THEME.font_family, 13, "bold"),
            fg_color=self.palette["fg"],
            hover_color=self.palette["hover"],
            text_color=self.palette["text"],
            border_width=self.palette["border_width"],
            border_color=self.palette["border"],
            **kwargs,
        )

    def _on_press(self) -> None:
        if self.loading:
            return
        self.configure(fg_color=self.palette["pressed"])
        if self.user_command:
            self.after(80, self.user_command)
        self.after(120, self._restore_color)

    def _restore_color(self) -> None:
        if not self.loading:
            self.configure(fg_color=self.palette["fg"])

    def set_loading(self, loading: bool, text: str = "Processando...") -> None:
        self.loading = loading
        if loading:
            self.configure(
                text=text,
                state="disabled",
                fg_color=THEME.primary_pressed,
                text_color="#DCEBFF",
            )
        else:
            self.configure(
                text=self.base_text,
                state="normal",
                fg_color=self.palette["fg"],
                text_color=self.palette["text"],
            )


class SidebarButton(ctk.CTkButton):
    """Botão reutilizável do menu lateral com estado ativo."""

    def __init__(self, master, text: str, icon: str, command: Callable[[], None], **kwargs) -> None:
        self.raw_text = text
        self.icon = icon
        self.active = False
        super().__init__(
            master,
            text=f"{icon}  {text}",
            command=command,
            anchor="w",
            height=42,
            corner_radius=12,
            border_width=0,
            font=(THEME.font_family, 14, "bold"),
            fg_color="transparent",
            hover_color=THEME.bg_surface_hover,
            text_color=THEME.text_secondary,
            **kwargs,
        )

    def set_active(self, active: bool) -> None:
        self.active = active
        if active:
            self.configure(
                fg_color=THEME.primary_active,
                hover_color=THEME.primary_active,
                text_color=THEME.text_inverse,
                border_width=1,
                border_color=THEME.primary,
            )
        else:
            self.configure(
                fg_color="transparent",
                hover_color=THEME.bg_surface_hover,
                text_color=THEME.text_secondary,
                border_width=0,
            )


class ToolCard(ctk.CTkFrame):
    """Card clicável usado no Dashboard e nas seções."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        description: str,
        category: str,
        command: Callable[[], None],
        enabled: bool = True,
        active: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=THEME.primary_active if active else (THEME.bg_surface if enabled else "#171B24"),
            border_color=THEME.primary if active else THEME.border_soft,
            border_width=1,
            corner_radius=18,
            **kwargs,
        )
        self.command = command
        self.enabled = enabled
        self.active = active
        self.normal_fg = THEME.primary_active if active else (THEME.bg_surface if enabled else "#171B24")
        self.hover_fg = THEME.bg_surface_hover if enabled and not active else self.normal_fg
        self.normal_border = THEME.primary if active else THEME.border_soft
        self.hover_border = THEME.border_hover if enabled else THEME.border_soft

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.icon_label = ctk.CTkLabel(
            self,
            text=icon,
            font=(THEME.font_family, 28),
            text_color=THEME.text_inverse if active else (THEME.primary if enabled else THEME.text_muted),
        )
        self.icon_label.grid(row=0, column=0, sticky="w", padx=18, pady=(18, 4))

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=(THEME.font_family, 17, "bold"),
            text_color=THEME.text_primary if enabled else THEME.text_muted,
            anchor="w",
        )
        self.title_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 4))

        self.description_label = ctk.CTkLabel(
            self,
            text=description,
            font=(THEME.font_family, 12),
            text_color="#DCEBFF" if active else (THEME.text_secondary if enabled else THEME.text_muted),
            justify="left",
            anchor="nw",
            wraplength=260,
        )
        self.description_label.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))

        badge_status = "info" if enabled else "disabled"
        badge_text = category if enabled else f"{category} · Em breve"
        self.badge = StatusBadge(self, badge_text, badge_status)
        self.badge.grid(row=3, column=0, sticky="w", padx=18, pady=(0, 18))

        self._bind_mouse_events(self)
        for child in self.winfo_children():
            self._bind_mouse_events(child)

    def _bind_mouse_events(self, widget) -> None:
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        widget.bind("<Button-1>", self._on_click)
        try:
            widget.configure(cursor="hand2" if self.enabled else "arrow")
        except Exception:
            pass

    def _on_enter(self, _event=None) -> None:
        if not self.enabled:
            return
        self.configure(fg_color=self.hover_fg, border_color=self.hover_border)
        self.title_label.configure(text_color=THEME.text_inverse)
        self.icon_label.configure(text_color=THEME.primary_hover)

    def _on_leave(self, _event=None) -> None:
        self.configure(fg_color=self.normal_fg, border_color=self.normal_border)
        self.title_label.configure(text_color=THEME.text_primary if self.enabled else THEME.text_muted)
        self.icon_label.configure(text_color=THEME.text_inverse if self.active else (THEME.primary if self.enabled else THEME.text_muted))

    def _on_click(self, _event=None) -> None:
        if not self.enabled:
            return
        self.configure(fg_color=THEME.primary_active, border_color=THEME.primary)
        self.after(90, self.command)


class EmptyState(ctk.CTkFrame):
    """Estado vazio padronizado para tabelas/listas sem conteúdo."""

    def __init__(
        self,
        master,
        icon: str,
        title: str,
        message: str,
        primary_label: Optional[str] = None,
        primary_command: Optional[Callable[[], None]] = None,
        secondary_label: Optional[str] = None,
        secondary_command: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=18,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=icon,
            font=(THEME.font_family, 34),
            text_color=THEME.primary,
        ).grid(row=0, column=0, pady=(26, 6))
        ctk.CTkLabel(
            self,
            text=title,
            font=(THEME.font_family, 18, "bold"),
            text_color=THEME.text_primary,
        ).grid(row=1, column=0, pady=(0, 4))
        ctk.CTkLabel(
            self,
            text=message,
            font=(THEME.font_family, 13),
            text_color=THEME.text_secondary,
            justify="center",
            wraplength=420,
        ).grid(row=2, column=0, pady=(0, 18))

        if primary_label or secondary_label:
            button_row = ctk.CTkFrame(self, fg_color="transparent")
            button_row.grid(row=3, column=0, pady=(0, 26))
            button_row.grid_columnconfigure((0, 1), weight=0)
            if primary_label:
                ActionButton(
                    button_row,
                    text=primary_label,
                    variant="primary",
                    command=primary_command,
                    width=150,
                ).grid(row=0, column=0, padx=6)
            if secondary_label:
                ActionButton(
                    button_row,
                    text=secondary_label,
                    variant="secondary",
                    command=secondary_command,
                    width=150,
                ).grid(row=0, column=1, padx=6)


class ProgressPanel(ctk.CTkFrame):
    """Painel de progresso moderno, determinado ou indeterminado."""

    def __init__(self, master, title: str = "Progresso", **kwargs) -> None:
        super().__init__(
            master,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=18,
            **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)
        self.is_indeterminate = False

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=(THEME.font_family, 15, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 2))

        self.status_label = ctk.CTkLabel(
            self,
            text="Pronto.",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="w",
        )
        self.status_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))

        self.progress = ctk.CTkProgressBar(
            self,
            height=12,
            corner_radius=999,
            mode="determinate",
            progress_color=THEME.primary,
            fg_color=THEME.bg_surface_alt,
        )
        self.progress.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))
        self.progress.set(0)

    def set_progress(self, value: float, text: Optional[str] = None) -> None:
        self.is_indeterminate = False
        self.progress.configure(mode="determinate")
        self.progress.stop()
        self.progress.set(max(0, min(1, value)))
        if text is not None:
            self.status_label.configure(text=text)

    def start_indeterminate(self, text: str = "Processando...") -> None:
        self.is_indeterminate = True
        self.status_label.configure(text=text)
        self.progress.configure(mode="indeterminate")
        self.progress.start()

    def stop(self, text: str = "Pronto.") -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress.set(0)
        self.is_indeterminate = False
        self.status_label.configure(text=text)

    def complete(self, text: str = "Concluído com sucesso.") -> None:
        self.progress.stop()
        self.progress.configure(mode="determinate", progress_color=THEME.success)
        self.progress.set(1)
        self.status_label.configure(text=text, text_color="#BBF7D0")

    def reset_success_color(self) -> None:
        self.progress.configure(progress_color=THEME.primary)
        self.status_label.configure(text_color=THEME.text_secondary)


class ToastMessage(ctk.CTkFrame):
    """Toast de sucesso/erro/alerta exibido sobre a área central."""

    VARIANTS = {
        "success": ("#12261A", THEME.success, "#BBF7D0", "✓"),
        "error": ("#2A1717", THEME.danger, "#FECACA", "×"),
        "warning": ("#2A2112", THEME.warning, "#FDE68A", "!"),
        "info": ("#102536", THEME.info, "#BAE6FD", "i"),
    }

    def __init__(
        self,
        master,
        title: str,
        message: str,
        variant: str = "success",
        duration_ms: int = 3600,
        on_close: Optional[Callable[[], None]] = None,
        **kwargs,
    ) -> None:
        bg, border, text_color, icon = self.VARIANTS.get(variant, self.VARIANTS["info"])
        super().__init__(
            master,
            fg_color=bg,
            border_color=border,
            border_width=1,
            corner_radius=16,
            **kwargs,
        )
        self.duration_ms = duration_ms
        self.on_close = on_close
        self.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=icon,
            font=(THEME.font_family, 20, "bold"),
            text_color=text_color,
            width=28,
        ).grid(row=0, column=0, rowspan=2, sticky="n", padx=(14, 8), pady=14)
        ctk.CTkLabel(
            self,
            text=title,
            font=(THEME.font_family, 13, "bold"),
            text_color=text_color,
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(12, 0))
        ctk.CTkLabel(
            self,
            text=message,
            font=(THEME.font_family, 12),
            text_color=text_color,
            anchor="w",
            wraplength=320,
        ).grid(row=1, column=1, sticky="ew", padx=(0, 12), pady=(0, 12))
        close_btn = ctk.CTkButton(
            self,
            text="×",
            width=26,
            height=26,
            corner_radius=8,
            fg_color="transparent",
            hover_color=THEME.bg_surface_hover,
            text_color=text_color,
            command=self._safe_destroy,
        )
        close_btn.grid(row=0, column=2, sticky="ne", padx=(0, 8), pady=8)
        self.after(self.duration_ms, self._safe_destroy)

    def _safe_destroy(self) -> None:
        try:
            self.destroy()
        except tk.TclError:
            pass
        finally:
            if self.on_close:
                try:
                    self.on_close()
                except Exception:
                    pass


class FileTable(ctk.CTkFrame):
    """Tabela/lista reutilizável para arquivos, com hover e seleção."""

    DEFAULT_COLUMNS = ("Ordem", "Nome", "Tipo", "Tamanho", "Pasta", "Status")

    def __init__(self, master, on_select: Optional[Callable[[List[str]], None]] = None, **kwargs) -> None:
        super().__init__(
            master,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=18,
            **kwargs,
        )
        self.on_select = on_select
        self.items: List[Tuple[str, ...]] = []
        self._base_tags: Dict[str, Tuple[str, ...]] = {}
        self._hover_iid: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            header,
            text="Arquivos",
            font=(THEME.font_family, 15, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        self.count_label = ctk.CTkLabel(
            header,
            text="0 itens",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="e",
        )
        self.count_label.grid(row=0, column=1, sticky="e")

        table_frame = ctk.CTkFrame(self, fg_color=THEME.bg_table, corner_radius=12)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        self._configure_tree_style()
        self.tree = ttk.Treeview(
            table_frame,
            columns=self.DEFAULT_COLUMNS,
            show="headings",
            selectmode="extended",
            style="KTools.Treeview",
        )
        for col in self.DEFAULT_COLUMNS:
            anchor = "center" if col in ("Ordem", "Tipo", "Tamanho", "Status") else "w"
            width = {
                "Ordem": 70,
                "Nome": 240,
                "Tipo": 70,
                "Tamanho": 90,
                "Pasta": 260,
                "Status": 110,
            }.get(col, 120)
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=60, stretch=True, anchor=anchor)

        self.scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")

        self.tree.tag_configure("even", background=THEME.bg_table, foreground=THEME.text_primary)
        self.tree.tag_configure("odd", background="#171C26", foreground=THEME.text_primary)
        self.tree.tag_configure("hover", background=THEME.bg_surface_hover, foreground=THEME.text_primary)
        self.tree.tag_configure("success", foreground="#BBF7D0")
        self.tree.tag_configure("warning", foreground="#FDE68A")
        self.tree.tag_configure("danger", foreground="#FECACA")

        self.tree.bind("<<TreeviewSelect>>", self._handle_select)
        self.tree.bind("<Motion>", self._handle_motion)
        self.tree.bind("<Leave>", self._handle_leave)

    def _configure_tree_style(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "KTools.Treeview",
            background=THEME.bg_table,
            foreground=THEME.text_primary,
            fieldbackground=THEME.bg_table,
            borderwidth=0,
            rowheight=32,
            font=(THEME.font_family, 11),
        )
        style.configure(
            "KTools.Treeview.Heading",
            background=THEME.bg_table_header,
            foreground=THEME.text_secondary,
            borderwidth=0,
            font=(THEME.font_family, 11, "bold"),
        )
        style.map(
            "KTools.Treeview",
            background=[("selected", THEME.primary_soft)],
            foreground=[("selected", THEME.text_inverse)],
        )

    def set_items(self, items: Sequence[Tuple[str, ...]]) -> None:
        self.clear()
        for item in items:
            self.add_item(item)

    def add_item(self, values: Tuple[str, ...]) -> None:
        row_index = len(self.tree.get_children())
        base_tag = "even" if row_index % 2 == 0 else "odd"
        status = values[-1].lower() if values else ""
        extra_tag = "neutral"
        if "ok" in status or "pronto" in status or "concluído" in status:
            extra_tag = "success"
        elif "erro" in status:
            extra_tag = "danger"
        elif "alerta" in status or "ignorado" in status:
            extra_tag = "warning"
        tags = (base_tag, extra_tag)
        iid = self.tree.insert("", "end", values=values, tags=tags)
        self._base_tags[iid] = tags
        self.items.append(values)
        self._update_count()

    def clear(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self.items.clear()
        self._base_tags.clear()
        self._hover_iid = None
        self._update_count()

    def remove_selected(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            return
        for iid in selected:
            self.tree.delete(iid)
            self._base_tags.pop(iid, None)
        self._renumber_rows()
        self._update_count()
        self._handle_select()

    def move_selected_up(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            return
        for iid in selected:
            index = self.tree.index(iid)
            if index > 0:
                self.tree.move(iid, "", index - 1)
        self._renumber_rows()

    def move_selected_down(self) -> None:
        selected = list(self.tree.selection())
        if not selected:
            return
        for iid in reversed(selected):
            index = self.tree.index(iid)
            if index < len(self.tree.get_children()) - 1:
                self.tree.move(iid, "", index + 1)
        self._renumber_rows()

    def get_all_values(self) -> List[Tuple[str, ...]]:
        return [tuple(self.tree.item(iid, "values")) for iid in self.tree.get_children()]

    def _renumber_rows(self) -> None:
        for index, iid in enumerate(self.tree.get_children(), start=1):
            values = list(self.tree.item(iid, "values"))
            if values:
                values[0] = f"{index:03d}"
                self.tree.item(iid, values=values)
            base_tag = "even" if (index - 1) % 2 == 0 else "odd"
            old_tags = tuple(t for t in self._base_tags.get(iid, ()) if t not in ("even", "odd"))
            tags = (base_tag, *old_tags)
            self._base_tags[iid] = tags
            self.tree.item(iid, tags=tags)

    def _update_count(self) -> None:
        count = len(self.tree.get_children())
        self.count_label.configure(text=f"{count} item" if count == 1 else f"{count} itens")

    def _handle_select(self, _event=None) -> None:
        if self.on_select:
            self.on_select(list(self.tree.selection()))

    def _handle_motion(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if iid == self._hover_iid:
            return
        self._clear_hover()
        if iid and iid not in self.tree.selection():
            self._hover_iid = iid
            base_tags = self._base_tags.get(iid, ())
            self.tree.item(iid, tags=(*base_tags, "hover"))

    def _handle_leave(self, _event=None) -> None:
        self._clear_hover()

    def _clear_hover(self) -> None:
        if self._hover_iid and self.tree.exists(self._hover_iid):
            self.tree.item(self._hover_iid, tags=self._base_tags.get(self._hover_iid, ()))
        self._hover_iid = None


# -----------------------------------------------------------------------------
# Aplicação visual
# -----------------------------------------------------------------------------

class KToolsNeoApp(ctk.CTk):
    """Janela principal do K-Tools Neo v0.4.2 com correções finais."""

    SECTION_DATA = {
        "dashboard": {
            "icon": "🏠",
            "title": "Dashboard",
            "subtitle": "Acesso rápido às ferramentas de mídia, arquivos, texto e diagnóstico.",
        },
        "audio": {
            "icon": "🎧",
            "title": "Áudio",
            "subtitle": "Junte, corte e extraia áudio com FFmpeg automático e interface Neo.",
        },
        "video": {
            "icon": "🎬",
            "title": "Vídeo",
            "subtitle": "Junte vídeos em MP4 com seleção por arquivos/pasta, ordenação e progresso visual.",
        },
        "folders": {
            "icon": "🗂",
            "title": "Arquivos/Pastas",
            "subtitle": "Análise, listagem e exportação de relatórios de pastas.",
        },
        "markdown": {
            "icon": "📝",
            "title": "Markdown/TXT",
            "subtitle": "Selecione, varra, ordene e una arquivos .md e .txt em um documento final.",
        },
        "settings": {
            "icon": "⚙",
            "title": "Configurações",
            "subtitle": "Ambiente técnico, dependências, pasta padrão, logs e comportamento do app.",
        },
    }

    def __init__(self) -> None:
        super().__init__()

        self.app_data_dir = get_app_data_dir()
        self.logs_dir = self.app_data_dir / "logs"
        self.config_path = self.app_data_dir / "config.json"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.settings_config = load_settings_config(self.config_path)
        # Visual fixo por decisão de produto: modo escuro + destaque azul.
        self.settings_config["appearance_mode"] = "Escuro"
        self.settings_config["accent_color"] = "Azul"
        self.accent_color_name = "Azul"
        self.accent_color = THEME.primary

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("K-Tools Neo v0.4.2 - Correção final")
        self.geometry("1320x860")
        self.minsize(1120, 720)
        self.configure(fg_color=THEME.bg_root)

        self.sidebar_buttons: Dict[str, SidebarButton] = {}
        self.current_section = "dashboard"
        self.progress_job: Optional[str] = None
        self.demo_progress_value = 0.0

        self._configure_root_grid()
        self._build_sidebar()
        self._build_workspace()
        self.show_section("dashboard")

    def _configure_root_grid(self) -> None:
        self.grid_columnconfigure(0, minsize=250, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=THEME.bg_sidebar)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(
            self.sidebar,
            text="K-Tools Neo",
            font=(THEME.font_family, 26, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=22, pady=(26, 2))

        ctk.CTkLabel(
            self.sidebar,
            text="Painel operacional",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=22, pady=(0, 24))

        nav_items = [
            ("dashboard", "🏠", "Dashboard"),
            ("audio", "🎧", "Áudio"),
            ("video", "🎬", "Vídeo"),
            ("folders", "🗂", "Arquivos/Pastas"),
            ("markdown", "📝", "Markdown/TXT"),
            ("settings", "⚙", "Configurações"),
        ]

        for idx, (section_id, icon, text) in enumerate(nav_items, start=2):
            button = SidebarButton(
                self.sidebar,
                text=text,
                icon=icon,
                command=lambda sid=section_id: self.show_section(sid),
            )
            button.grid(row=idx, column=0, sticky="ew", padx=16, pady=4)
            self.sidebar_buttons[section_id] = button

        status_box = ctk.CTkFrame(
            self.sidebar,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=16,
        )
        status_box.grid(row=10, column=0, sticky="ew", padx=16, pady=(12, 18))
        status_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status_box,
            text="Ambiente",
            font=(THEME.font_family, 13, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        StatusBadge(status_box, "FFmpeg auto", "info").grid(row=1, column=0, sticky="w", padx=14, pady=3)
        StatusBadge(status_box, "Markdown OK", "success").grid(row=2, column=0, sticky="w", padx=14, pady=3)
        ctk.CTkLabel(
            status_box,
            text="v0.4.2 final",
            font=(THEME.font_family, 11),
            text_color=THEME.text_muted,
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", padx=14, pady=(8, 12))

    def _build_workspace(self) -> None:
        self.workspace = ctk.CTkFrame(self, corner_radius=0, fg_color=THEME.bg_root)
        self.workspace.grid(row=0, column=1, sticky="nsew")
        self.workspace.grid_columnconfigure(0, weight=1)
        self.workspace.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self.workspace, height=92, fg_color=THEME.bg_header, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)
        self.header.grid_columnconfigure(1, weight=0)

        self.header_title = ctk.CTkLabel(
            self.header,
            text="Dashboard",
            font=(THEME.font_family, 24, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        )
        self.header_title.grid(row=0, column=0, sticky="ew", padx=28, pady=(20, 0))

        self.header_subtitle = ctk.CTkLabel(
            self.header,
            text="Escolha uma ferramenta para começar.",
            font=(THEME.font_family, 13),
            text_color=THEME.text_secondary,
            anchor="w",
        )
        self.header_subtitle.grid(row=1, column=0, sticky="ew", padx=28, pady=(2, 18))

        self.header_actions = ctk.CTkFrame(self.header, fg_color="transparent")
        self.header_actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=28, pady=20)
        self.header_actions.grid_columnconfigure((0, 1), weight=0)
        StatusBadge(self.header_actions, "Visual Neo", "info").grid(row=0, column=0, padx=(0, 8))
        StatusBadge(self.header_actions, "Pronto", "success").grid(row=0, column=1)

        self.content = ctk.CTkFrame(self.workspace, fg_color=THEME.bg_root, corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew", padx=24, pady=24)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # Camada de toast sobre a área central. Usa grid no mesmo container, sem pack.
        self.toast_layer = ctk.CTkFrame(self.workspace, fg_color="transparent")
        self.toast_layer.grid_columnconfigure(0, weight=1)
        # A camada só aparece enquanto houver toast. Isso evita o retângulo preto residual.
        self.toast_layer.grid(row=1, column=0, sticky="se", padx=28, pady=28)
        self.toast_layer.grid_remove()

        self.status_bar = ctk.CTkFrame(self.workspace, height=42, fg_color=THEME.bg_header, corner_radius=0)
        self.status_bar.grid(row=2, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)
        self.status_bar.grid_columnconfigure(1, weight=0)

        self.status_text = ctk.CTkLabel(
            self.status_bar,
            text="Pronto. Interface refinada carregada.",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="w",
        )
        self.status_text.grid(row=0, column=0, sticky="ew", padx=24, pady=10)

        self.status_progress = ctk.CTkProgressBar(
            self.status_bar,
            width=160,
            height=10,
            corner_radius=999,
            progress_color=THEME.primary,
            fg_color=THEME.bg_surface_alt,
        )
        self.status_progress.grid(row=0, column=1, sticky="e", padx=24, pady=14)
        self.status_progress.set(0)

    def clear_content(self) -> None:
        for child in self.content.winfo_children():
            child.destroy()

    def show_section(self, section_id: str) -> None:
        self.current_section = section_id
        for sid, button in self.sidebar_buttons.items():
            button.set_active(sid == section_id)

        data = self.SECTION_DATA[section_id]
        self.header_title.configure(text=f"{data['icon']} {data['title']}")
        self.header_subtitle.configure(text=data["subtitle"])
        self.clear_content()

        if section_id == "dashboard":
            self._build_dashboard_view()
            self.status_text.configure(text="Pronto. Dashboard carregado.")
        elif section_id == "audio":
            if not hasattr(self, "audio_tool"):
                self.audio_tool = "join"
            self._build_audio_view()
            self.status_text.configure(text="Áudio pronto. Selecione a ferramenta, revise a ordem e execute.")
        elif section_id == "video":
            self._build_video_view()
            self.status_text.configure(text="Vídeo pronto. Adicione arquivos, ajuste a ordem e gere o MP4 final.")
        elif section_id == "markdown":
            self._build_markdown_view()
            self.status_text.configure(text="Markdown/TXT pronto. Selecione arquivos, faça varredura e gere o documento final.")
        elif section_id == "folders":
            if not hasattr(self, "folders_mode"):
                self.folders_mode = "structure"
            self._build_folders_view()
            self.status_text.configure(text="Arquivos/Pastas pronto. Escolha a pasta raiz, formatos e exporte relatórios.")
        elif section_id == "settings":
            self._build_settings_view()
            self.status_text.configure(text="Configurações prontas. Ajuste aparência, ambiente, saída e logs.")
        else:
            self._build_placeholder_view(section_id)
            self.status_text.configure(text=f"Seção {data['title']} aberta. Componentes visuais disponíveis.")

    # ------------------------------------------------------------------
    # Dashboard com laboratório visual
    # ------------------------------------------------------------------
    def _build_dashboard_view(self) -> None:
        """Dashboard refinado: acesso rápido, status de ambiente e próximos passos."""
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure((0, 1, 2), weight=1, uniform="dashboard_cards")

        # Hero: orienta sem parecer laboratório técnico.
        hero = ctk.CTkFrame(
            root,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=22,
        )
        hero.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 18))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            hero,
            text="Central de utilitários pronta para uso",
            font=(THEME.font_family, 22, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 3))
        ctk.CTkLabel(
            hero,
            text="Escolha uma ferramenta, selecione arquivos ou pastas, revise a ordem e acompanhe o progresso sem abrir o terminal.",
            font=(THEME.font_family, 13),
            text_color=THEME.text_secondary,
            anchor="w",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 22))

        hero_actions = ctk.CTkFrame(hero, fg_color="transparent")
        hero_actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=24, pady=22)
        hero_actions.grid_columnconfigure(0, weight=1)
        ActionButton(
            hero_actions,
            text="Testar FFmpeg",
            variant="primary",
            command=lambda: self.show_section("settings"),
            width=150,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ActionButton(
            hero_actions,
            text="Abrir configurações",
            variant="secondary",
            command=lambda: self.show_section("settings"),
            width=150,
        ).grid(row=1, column=0, sticky="ew")

        ctk.CTkLabel(
            root,
            text="Ferramentas principais",
            font=(THEME.font_family, 16, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 8))

        card_data = [
            ("🎧", "Juntar áudios", "Una vários áudios em um arquivo final, com ordenação natural e saída segura.", "Áudio", "audio"),
            ("🎬", "Juntar vídeos", "Combine vídeos na ordem exibida e gere um MP4 final.", "Vídeo", "video"),
            ("📝", "Juntar Markdown/TXT", "Una transcrições e notas em um documento com separadores.", "Texto", "markdown"),
            ("🗂", "Diagnosticar pastas", "Liste arquivos, conte pastas e exporte relatórios em TXT, JSON, CSV e XLSX.", "Arquivos", "folders"),
            ("🔊", "Extrair áudio", "Extraia áudio de vídeos ou una o áudio de vários vídeos.", "Mídia", "audio"),
            ("⚙", "Configurações", "Ajuste aparência, pasta padrão, dependências, FFmpeg e logs.", "Sistema", "settings"),
        ]
        for index, (icon, title, desc, category, target) in enumerate(card_data):
            card = ToolCard(
                root,
                icon=icon,
                title=title,
                description=desc,
                category=category,
                command=lambda sid=target: self.show_section(sid),
            )
            card.grid(row=2 + index // 3, column=index % 3, sticky="nsew", padx=8, pady=8)

        ctk.CTkLabel(
            root,
            text="Status do ambiente",
            font=(THEME.font_family, 16, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=4, column=0, columnspan=3, sticky="ew", pady=(22, 8))

        status_cards = ctk.CTkFrame(root, fg_color="transparent")
        status_cards.grid(row=5, column=0, columnspan=3, sticky="ew")
        status_cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="status_cards")

        status_items = [
            ("FFmpeg", "Motor de mídia", "Usado para áudio e vídeo. Teste em Configurações.", "info", "Testar"),
            ("Dependências", "Bibliotecas", "CustomTkinter, FFmpeg, MoviePy, Pandas e OpenPyXL.", "success", "Verificar"),
            ("Saída padrão", "Resultados", str(self.settings_config.get("default_output_folder", default_output_dir())), "neutral", "Definir"),
        ]
        for idx, (title, subtitle, detail, status, action) in enumerate(status_items):
            card = ctk.CTkFrame(status_cards, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=18)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0 if idx == 2 else 8))
            card.grid_columnconfigure(0, weight=1)
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 2))
            top.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(top, text=title, font=(THEME.font_family, 15, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew")
            StatusBadge(top, subtitle, status).grid(row=0, column=1, sticky="e")
            ctk.CTkLabel(card, text=detail, font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w", justify="left", wraplength=320).grid(row=1, column=0, sticky="ew", padx=18, pady=(4, 14))
            ActionButton(card, text=action, variant="secondary", command=lambda: self.show_section("settings")).grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

        # Rodapé informativo da dashboard.
        tips = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=18)
        tips.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(18, 0))
        tips.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            tips,
            text="Fluxo recomendado",
            font=(THEME.font_family, 15, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(
            tips,
            text="1. Escolha a ferramenta  •  2. Adicione arquivos/pastas  •  3. Revise a ordem  •  4. Escolha a saída  •  5. Execute e acompanhe o progresso",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="w",
            wraplength=980,
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))


    # ------------------------------------------------------------------
    # Áudio funcional
    # ------------------------------------------------------------------
    def _set_audio_tool(self, tool_id: str) -> None:
        self.audio_tool = tool_id
        self.clear_content()
        self._build_audio_view()

    def _build_audio_view(self) -> None:
        self.audio_is_busy = False
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(hero, text="🎧 Áudio", font=(THEME.font_family, 20, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 2))
        ctk.CTkLabel(hero, text="Junte, corte e extraia áudio usando FFmpeg automático. Processos pesados rodam em thread.", font=(THEME.font_family, 13), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 18))
        StatusBadge(hero, "FFmpeg automático", "info").grid(row=0, column=1, rowspan=2, sticky="e", padx=20, pady=20)

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="audio_cards")
        tool_cards = [
            ("join", "🎧", "Juntar áudios", "Una vários áudios em um arquivo final.", "Áudio"),
            ("split", "✂", "Cortar áudio", "Divida um áudio em partes iguais.", "Áudio"),
            ("extract", "🔊", "Extrair de vídeo", "Extraia áudio de um vídeo.", "Mídia"),
            ("batch", "🎞", "Áudio de vídeos", "Extraia e una áudio de vários vídeos.", "Mídia"),
        ]
        for index, (tool_id, icon, title, desc, cat) in enumerate(tool_cards):
            ToolCard(
                cards,
                icon=icon,
                title=title,
                description=desc,
                category=cat,
                command=lambda tid=tool_id: self._set_audio_tool(tid),
                active=getattr(self, "audio_tool", "join") == tool_id,
            ).grid(row=0, column=index, sticky="nsew", padx=8)

        self.audio_body = ctk.CTkFrame(root, fg_color="transparent")
        self.audio_body.grid(row=2, column=0, sticky="nsew")
        self.audio_body.grid_columnconfigure(0, weight=1)
        tool = getattr(self, "audio_tool", "join")
        if tool == "split":
            self._build_audio_split_tool(self.audio_body)
        elif tool == "extract":
            self._build_audio_extract_tool(self.audio_body)
        elif tool == "batch":
            self._build_audio_batch_tool(self.audio_body)
        else:
            self._build_audio_join_tool(self.audio_body)

    def _audio_filetypes(self):
        return [("Áudios", " ".join(f"*{ext}" for ext in sorted(AUDIO_EXTENSIONS))), ("Todos os arquivos", "*.*")]

    def _video_filetypes(self):
        return [("Vídeos", " ".join(f"*{ext}" for ext in sorted(VIDEO_EXTENSIONS))), ("Todos os arquivos", "*.*")]

    def _paths_to_rows(self, paths: Sequence[Path]) -> List[Tuple[str, str, str, str, str, str]]:
        rows = []
        for index, path in enumerate(paths, start=1):
            rows.append((f"{index:03d}", path.name, path.suffix.upper().lstrip("."), format_size(safe_stat_size(path)), str(path.parent), "Pronto"))
        return rows

    def _paths_from_table(self, table: FileTable) -> List[Path]:
        result = []
        for values in table.get_all_values():
            if len(values) >= 5:
                result.append(Path(values[4]) / values[1])
        return result

    def _sort_table_paths(self, table: FileTable, mode_label: str) -> None:
        mode = {"Nome A-Z": "name", "Data de modificação": "modified"}.get(mode_label, "natural")
        paths = sort_paths(self._paths_from_table(table), mode)
        table.set_items(self._paths_to_rows(paths))

    def _add_unique_to_table(self, table: FileTable, new_paths: Iterable[Path], valid_func: Callable[[Path], bool], sort_label: str = "Natural") -> int:
        current = self._paths_from_table(table)
        seen = set()
        merged: List[Path] = []
        for path in [*current, *new_paths]:
            p = Path(path)
            if not valid_func(p):
                continue
            try:
                key = str(p.resolve()).lower()
            except OSError:
                key = str(p.absolute()).lower()
            if key not in seen:
                seen.add(key)
                merged.append(p)
        mode = {"Nome A-Z": "name", "Data de modificação": "modified"}.get(sort_label, "natural")
        merged = sort_paths(merged, mode)
        before = len(current)
        table.set_items(self._paths_to_rows(merged))
        return max(0, len(merged) - before)

    def _confirm_overwrite(self, output_path: Path) -> bool:
        if not output_path.exists():
            return True
        return messagebox.askyesno("Arquivo já existe", f"O arquivo abaixo já existe:\n\n{output_path}\n\nDeseja substituir?")

    # -------------------------- Juntar áudios --------------------------
    def _build_audio_join_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(panel, text="🎧 Juntar áudios", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Adicione arquivos ou uma pasta. A ordem exibida na tabela será usada no áudio final.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        for i in range(9): actions.grid_columnconfigure(i, weight=0)
        actions.grid_columnconfigure(9, weight=1)
        ActionButton(actions, "Adicionar áudios", "secondary", self._audio_join_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._audio_join_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self._audio_remove_selected(self.audio_join_table)).grid(row=0, column=2, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._audio_clear_table(self.audio_join_table)).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Subir", "secondary", lambda: self.audio_join_table.move_selected_up()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Descer", "secondary", lambda: self.audio_join_table.move_selected_down()).grid(row=0, column=5, padx=4)
        self.audio_join_sort = tk.StringVar(value="Natural")
        ctk.CTkComboBox(actions, variable=self.audio_join_sort, values=["Natural", "Nome A-Z", "Data de modificação"], command=lambda _v: self._sort_table_paths(self.audio_join_table, self.audio_join_sort.get()), width=180, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt, button_hover_color=THEME.bg_surface_hover, border_color=THEME.border_medium, dropdown_fg_color=THEME.bg_surface, dropdown_hover_color=THEME.bg_surface_hover, text_color=THEME.text_primary).grid(row=0, column=6, padx=4)

        table_shell = ctk.CTkFrame(panel, fg_color="transparent")
        table_shell.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        table_shell.grid_columnconfigure(0, weight=1)
        table_shell.grid_rowconfigure(0, weight=1)
        self.audio_join_table = FileTable(table_shell)
        self.audio_join_table.grid(row=0, column=0, sticky="nsew")

        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(output, text="Formato", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")
        self.audio_join_format = tk.StringVar(value="m4a")
        ctk.CTkComboBox(output, variable=self.audio_join_format, values=["m4a", "mp3", "wav", "flac"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface, button_hover_color=THEME.bg_surface_hover).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        ctk.CTkLabel(output, text="Arquivo final", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=1, padx=(0, 10), pady=(14, 6), sticky="w")
        self.audio_join_output = tk.StringVar(value="")
        ctk.CTkEntry(output, textvariable=self.audio_join_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._audio_join_choose_output).grid(row=1, column=2, padx=(0, 14), pady=(0, 14))

        self.audio_join_progress = ProgressPanel(panel, title="Progresso")
        self.audio_join_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.audio_join_btn = ActionButton(panel, "Juntar áudios", "primary", self._audio_join_run, icon="▶")
        self.audio_join_btn.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _audio_join_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecione os áudios", filetypes=self._audio_filetypes())
        if files:
            added = self._add_unique_to_table(self.audio_join_table, [Path(f) for f in files], is_supported_audio_file, self.audio_join_sort.get())
            self.show_toast("Áudios adicionados", f"{added} novo(s) arquivo(s) entraram na lista.", "success")

    def _audio_join_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta com áudios")
        if folder:
            paths = [p for p in Path(folder).iterdir() if is_supported_audio_file(p)]
            added = self._add_unique_to_table(self.audio_join_table, paths, is_supported_audio_file, self.audio_join_sort.get())
            self.show_toast("Pasta adicionada", f"{added} áudio(s) encontrados nesta pasta.", "success" if added else "warning")

    def _audio_join_choose_output(self) -> None:
        fmt = self.audio_join_format.get().lower()
        filename = filedialog.asksaveasfilename(title="Salvar áudio final", defaultextension=f".{fmt}", initialfile=f"audio_unificado.{fmt}", filetypes=[("Áudio", f"*.{fmt}"), ("Todos os arquivos", "*.*")])
        if filename:
            self.audio_join_output.set(str(ensure_audio_extension(Path(filename), fmt)))

    def _audio_join_run(self) -> None:
        paths = self._paths_from_table(self.audio_join_table)
        if not paths:
            self.show_toast("Nenhum áudio", "Adicione pelo menos um arquivo de áudio.", "warning")
            return
        raw_output = self.audio_join_output.get().strip()
        if not raw_output:
            self.show_toast("Escolha a saída", "Escolha o arquivo final antes de juntar.", "warning")
            return
        output = ensure_audio_extension(Path(raw_output), self.audio_join_format.get())
        self.audio_join_output.set(str(output))
        if not self._confirm_overwrite(output):
            return
        self.audio_join_btn.set_loading(True, "Juntando...")
        self.audio_join_progress.reset_success_color()
        self.audio_join_progress.set_progress(0, "Preparando áudios...")
        self.status_text.configure(text="Áudio: juntando arquivos...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.audio_join_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = join_audio_files(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._audio_join_finish(result, error))
        threading.Thread(target=worker, daemon=True).start()

    def _audio_join_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_join_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_join_progress.stop("Erro ao juntar áudios.")
            self.status_text.configure(text="Áudio: erro ao juntar arquivos.")
            self.show_toast("Erro ao juntar áudios", str(error), "error")
            return
        self.audio_join_progress.complete(f"Áudio final gerado: {result}")
        self.status_text.configure(text="Áudio: arquivo final gerado com sucesso.")
        self.show_toast("Áudio gerado", f"Arquivo salvo em: {result}", "success")

    def _audio_remove_selected(self, table: FileTable) -> None:
        table.remove_selected()
        self.status_text.configure(text="Itens selecionados removidos.")

    def _audio_clear_table(self, table: FileTable) -> None:
        if table.get_all_values() and not messagebox.askyesno("Limpar lista", "Deseja limpar todos os arquivos da lista?"):
            return
        table.clear()
        self.status_text.configure(text="Lista limpa.")

    # -------------------------- Cortar áudio --------------------------
    def _build_audio_split_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text="✂ Cortar áudio em partes", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Selecione um áudio, defina o número de partes e escolha a pasta de saída.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 16))
        self.audio_split_input = tk.StringVar(value="")
        self.audio_split_folder = tk.StringVar(value="")
        self.audio_split_parts = tk.StringVar(value="3")
        self.audio_split_format = tk.StringVar(value="m4a")
        ctk.CTkLabel(panel, text="Arquivo de áudio", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_split_input, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Selecionar", "secondary", self._audio_split_choose_input).grid(row=2, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Pasta de saída", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_split_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._audio_split_choose_folder).grid(row=3, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Partes", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        options = ctk.CTkFrame(panel, fg_color="transparent")
        options.grid(row=4, column=1, sticky="w", padx=8, pady=6)
        ctk.CTkEntry(options, textvariable=self.audio_split_parts, width=90, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=0, column=0, padx=(0, 10))
        ctk.CTkComboBox(options, variable=self.audio_split_format, values=["m4a", "mp3", "wav", "flac"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=0, column=1)
        self.audio_split_progress = ProgressPanel(panel, title="Progresso")
        self.audio_split_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 14))
        self.audio_split_btn = ActionButton(panel, "Cortar áudio", "primary", self._audio_split_run, icon="▶")
        self.audio_split_btn.grid(row=6, column=2, sticky="e", padx=18, pady=(0, 18))

    def _audio_split_choose_input(self) -> None:
        file = filedialog.askopenfilename(title="Selecione um áudio", filetypes=self._audio_filetypes())
        if file:
            self.audio_split_input.set(file)
            if not self.audio_split_folder.get().strip():
                self.audio_split_folder.set(str(Path(file).parent))

    def _audio_split_choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta de saída")
        if folder:
            self.audio_split_folder.set(folder)

    def _audio_split_run(self) -> None:
        try:
            input_raw = self.audio_split_input.get().strip()
            folder_raw = self.audio_split_folder.get().strip()
            parts = int(self.audio_split_parts.get().strip())
            input_path = Path(input_raw) if input_raw else Path("")
            output_folder = Path(folder_raw) if folder_raw else Path("")
        except Exception:
            self.show_toast("Dados inválidos", "Informe arquivo, pasta e número de partes válido.", "warning")
            return
        if not input_raw or not folder_raw or not input_path.exists() or not is_supported_audio_file(input_path):
            self.show_toast("Entrada incompleta", "Selecione o arquivo de áudio e a pasta de saída.", "warning")
            return
        fmt = self.audio_split_format.get().lower()
        planned = [output_folder / f"{input_path.stem}_parte_{i:02d}_de_{parts:02d}.{fmt}" for i in range(1, parts + 1)]
        if any(p.exists() for p in planned):
            if not messagebox.askyesno("Arquivos já existem", "Uma ou mais partes já existem. Deseja substituir?"):
                return
        self.audio_split_btn.set_loading(True, "Cortando...")
        self.audio_split_progress.reset_success_color()
        self.audio_split_progress.set_progress(0, "Preparando corte...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.audio_split_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = split_audio_file(input_path, output_folder, parts, fmt, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._audio_split_finish(result, error))
        threading.Thread(target=worker, daemon=True).start()

    def _audio_split_finish(self, result: Optional[List[Path]], error: Optional[Exception]) -> None:
        self.audio_split_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_split_progress.stop("Erro ao cortar áudio.")
            self.show_toast("Erro ao cortar", str(error), "error")
            return
        self.audio_split_progress.complete(f"{len(result or [])} parte(s) geradas com sucesso.")
        self.show_toast("Áudio cortado", f"{len(result or [])} arquivo(s) gerados.", "success")

    # -------------------------- Extrair áudio de vídeo --------------------------
    def _build_audio_extract_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text="🔊 Extrair áudio de vídeo", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Selecione um vídeo e gere um arquivo de áudio final.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 16))
        self.audio_extract_video = tk.StringVar(value="")
        self.audio_extract_output = tk.StringVar(value="")
        self.audio_extract_format = tk.StringVar(value="mp3")
        ctk.CTkLabel(panel, text="Vídeo", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_extract_video, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Selecionar", "secondary", self._audio_extract_choose_video).grid(row=2, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Formato", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkComboBox(panel, variable=self.audio_extract_format, values=["mp3", "m4a", "wav", "flac", "aac", "ogg"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=3, column=1, sticky="w", padx=8, pady=6)
        ctk.CTkLabel(panel, text="Arquivo final", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_extract_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=4, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._audio_extract_choose_output).grid(row=4, column=2, padx=18, pady=6)
        self.audio_extract_progress = ProgressPanel(panel, title="Progresso")
        self.audio_extract_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 14))
        self.audio_extract_btn = ActionButton(panel, "Extrair áudio", "primary", self._audio_extract_run, icon="▶")
        self.audio_extract_btn.grid(row=6, column=2, sticky="e", padx=18, pady=(0, 18))

    def _audio_extract_choose_video(self) -> None:
        file = filedialog.askopenfilename(title="Selecione um vídeo", filetypes=self._video_filetypes())
        if file:
            self.audio_extract_video.set(file)
            fmt = self.audio_extract_format.get().lower()
            self.audio_extract_output.set(str(Path(file).with_name(f"{Path(file).stem}_audio.{fmt}")))

    def _audio_extract_choose_output(self) -> None:
        fmt = self.audio_extract_format.get().lower()
        file = filedialog.asksaveasfilename(title="Salvar áudio extraído", defaultextension=f".{fmt}", initialfile=f"audio_extraido.{fmt}", filetypes=[("Áudio", f"*.{fmt}"), ("Todos os arquivos", "*.*")])
        if file:
            self.audio_extract_output.set(str(ensure_audio_extension(Path(file), fmt)))

    def _audio_extract_run(self) -> None:
        video_raw = self.audio_extract_video.get().strip()
        output_raw = self.audio_extract_output.get().strip()
        if not video_raw or not output_raw:
            self.show_toast("Entrada incompleta", "Selecione o vídeo e o arquivo final.", "warning")
            return
        video = Path(video_raw)
        output = ensure_audio_extension(Path(output_raw), self.audio_extract_format.get())
        if not video.exists() or not is_supported_video_file(video):
            self.show_toast("Vídeo inválido", "Selecione um arquivo de vídeo compatível.", "warning")
            return
        self.audio_extract_output.set(str(output))
        if not self._confirm_overwrite(output): return
        self.audio_extract_btn.set_loading(True, "Extraindo...")
        self.audio_extract_progress.reset_success_color()
        self.audio_extract_progress.start_indeterminate("Extraindo áudio do vídeo...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.audio_extract_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = extract_audio_from_video(video, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._audio_extract_finish(result, error))
        threading.Thread(target=worker, daemon=True).start()

    def _audio_extract_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_extract_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_extract_progress.stop("Erro ao extrair áudio.")
            self.show_toast("Erro na extração", str(error), "error")
            return
        self.audio_extract_progress.complete(f"Áudio extraído: {result}")
        self.show_toast("Áudio extraído", f"Arquivo salvo em: {result}", "success")

    # -------------------------- Extrair e unir áudio de vários vídeos --------------------------
    def _build_audio_batch_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="🎞 Extrair e unir áudio de vários vídeos", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Adicione vídeos. O app extrai o áudio de cada vídeo e gera um único áudio final.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        for i in range(8): actions.grid_columnconfigure(i, weight=0)
        ActionButton(actions, "Adicionar vídeos", "secondary", self._audio_batch_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._audio_batch_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self._audio_remove_selected(self.audio_batch_table)).grid(row=0, column=2, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._audio_clear_table(self.audio_batch_table)).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Subir", "secondary", lambda: self.audio_batch_table.move_selected_up()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Descer", "secondary", lambda: self.audio_batch_table.move_selected_down()).grid(row=0, column=5, padx=4)
        self.audio_batch_sort = tk.StringVar(value="Natural")
        ctk.CTkComboBox(actions, variable=self.audio_batch_sort, values=["Natural", "Nome A-Z", "Data de modificação"], command=lambda _v: self._sort_table_paths(self.audio_batch_table, self.audio_batch_sort.get()), width=180, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt, button_hover_color=THEME.bg_surface_hover, border_color=THEME.border_medium, dropdown_fg_color=THEME.bg_surface, dropdown_hover_color=THEME.bg_surface_hover, text_color=THEME.text_primary).grid(row=0, column=6, padx=4)
        self.audio_batch_table = FileTable(panel)
        self.audio_batch_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(output, text="Formato", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")
        self.audio_batch_format = tk.StringVar(value="mp3")
        ctk.CTkComboBox(output, variable=self.audio_batch_format, values=["mp3", "m4a", "wav", "flac"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        self.audio_batch_output = tk.StringVar(value="")
        ctk.CTkLabel(output, text="Arquivo final", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=1, padx=(0, 10), pady=(14, 6), sticky="w")
        ctk.CTkEntry(output, textvariable=self.audio_batch_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._audio_batch_choose_output).grid(row=1, column=2, padx=(0, 14), pady=(0, 14))
        self.audio_batch_progress = ProgressPanel(panel, title="Progresso")
        self.audio_batch_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.audio_batch_btn = ActionButton(panel, "Extrair e unir", "primary", self._audio_batch_run, icon="▶")
        self.audio_batch_btn.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _audio_batch_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecione os vídeos", filetypes=self._video_filetypes())
        if files:
            added = self._add_unique_to_table(self.audio_batch_table, [Path(f) for f in files], is_supported_video_file, self.audio_batch_sort.get())
            self.show_toast("Vídeos adicionados", f"{added} novo(s) vídeo(s) entraram na lista.", "success")

    def _audio_batch_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta com vídeos")
        if folder:
            paths = [p for p in Path(folder).iterdir() if is_supported_video_file(p)]
            added = self._add_unique_to_table(self.audio_batch_table, paths, is_supported_video_file, self.audio_batch_sort.get())
            self.show_toast("Pasta adicionada", f"{added} vídeo(s) encontrados nesta pasta.", "success" if added else "warning")

    def _audio_batch_choose_output(self) -> None:
        fmt = self.audio_batch_format.get().lower()
        filename = filedialog.asksaveasfilename(title="Salvar áudio dos vídeos", defaultextension=f".{fmt}", initialfile=f"audio_dos_videos.{fmt}", filetypes=[("Áudio", f"*.{fmt}"), ("Todos os arquivos", "*.*")])
        if filename:
            self.audio_batch_output.set(str(ensure_audio_extension(Path(filename), fmt)))

    def _audio_batch_run(self) -> None:
        paths = self._paths_from_table(self.audio_batch_table)
        if not paths:
            self.show_toast("Nenhum vídeo", "Adicione pelo menos um vídeo.", "warning")
            return
        raw_output = self.audio_batch_output.get().strip()
        if not raw_output:
            self.show_toast("Escolha a saída", "Escolha o arquivo final antes de executar.", "warning")
            return
        output = ensure_audio_extension(Path(raw_output), self.audio_batch_format.get())
        self.audio_batch_output.set(str(output))
        if not self._confirm_overwrite(output): return
        self.audio_batch_btn.set_loading(True, "Extraindo...")
        self.audio_batch_progress.reset_success_color()
        self.audio_batch_progress.set_progress(0, "Preparando vídeos...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.audio_batch_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = extract_and_join_audio_from_videos(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._audio_batch_finish(result, error))
        threading.Thread(target=worker, daemon=True).start()

    def _audio_batch_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_batch_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_batch_progress.stop("Erro ao extrair/unir áudio dos vídeos.")
            self.show_toast("Erro nos vídeos", str(error), "error")
            return
        self.audio_batch_progress.complete(f"Áudio dos vídeos gerado: {result}")
        self.show_toast("Áudio dos vídeos gerado", f"Arquivo salvo em: {result}", "success")

    # ------------------------------------------------------------------
    # Markdown/TXT funcional
    # ------------------------------------------------------------------
    def _build_markdown_view(self) -> None:
        self.markdown_selected_folder: Optional[Path] = None
        self.markdown_is_busy = False

        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(
            root,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=20,
        )
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(
            hero,
            text="📝 Juntar Markdown/TXT",
            font=(THEME.font_family, 20, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 2))
        ctk.CTkLabel(
            hero,
            text="Selecione arquivos .md/.txt ou faça varredura em uma pasta. A ordem exibida será usada no documento final.",
            font=(THEME.font_family, 13),
            text_color=THEME.text_secondary,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 18))
        StatusBadge(hero, "Funcional", "success").grid(row=0, column=1, rowspan=2, sticky="e", padx=20, pady=20)

        controls = ctk.CTkFrame(
            root,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=20,
        )
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        controls.grid_columnconfigure(1, weight=1)
        controls.grid_columnconfigure(3, weight=0)

        ctk.CTkLabel(
            controls,
            text="Entrada",
            font=(THEME.font_family, 16, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=18, pady=(16, 8))

        action_row = ctk.CTkFrame(controls, fg_color="transparent")
        action_row.grid(row=1, column=0, columnspan=4, sticky="ew", padx=18, pady=(0, 10))
        for idx in range(8):
            action_row.grid_columnconfigure(idx, weight=0)
        action_row.grid_columnconfigure(8, weight=1)

        self.md_add_files_btn = ActionButton(action_row, "Adicionar arquivos", "secondary", self._md_add_files, icon="＋")
        self.md_add_files_btn.grid(row=0, column=0, padx=(0, 8))
        self.md_select_folder_btn = ActionButton(action_row, "Selecionar pasta", "secondary", self._md_select_folder, icon="📁")
        self.md_select_folder_btn.grid(row=0, column=1, padx=4)
        self.md_scan_btn = ActionButton(action_row, "Fazer varredura", "primary", self._md_scan_folder, icon="🔎")
        self.md_scan_btn.grid(row=0, column=2, padx=4)
        self.md_remove_btn = ActionButton(action_row, "Remover", "secondary", self._md_remove_selected)
        self.md_remove_btn.grid(row=0, column=3, padx=4)
        self.md_clear_btn = ActionButton(action_row, "Limpar lista", "ghost", self._md_clear_files)
        self.md_clear_btn.grid(row=0, column=4, padx=4)
        self.md_up_btn = ActionButton(action_row, "Subir", "secondary", self._md_move_up)
        self.md_up_btn.grid(row=0, column=5, padx=4)
        self.md_down_btn = ActionButton(action_row, "Descer", "secondary", self._md_move_down)
        self.md_down_btn.grid(row=0, column=6, padx=4)

        ctk.CTkLabel(
            controls,
            text="Pasta selecionada",
            font=(THEME.font_family, 12, "bold"),
            text_color=THEME.text_secondary,
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=(18, 10), pady=(0, 12))
        self.md_folder_var = tk.StringVar(value="Nenhuma pasta selecionada.")
        self.md_folder_entry = ctk.CTkEntry(
            controls,
            textvariable=self.md_folder_var,
            height=36,
            fg_color=THEME.bg_input,
            border_color=THEME.border_medium,
            text_color=THEME.text_secondary,
            state="readonly",
        )
        self.md_folder_entry.grid(row=2, column=1, sticky="ew", padx=(0, 12), pady=(0, 12))

        self.md_include_subfolders = tk.BooleanVar(value=True)
        self.md_subfolders_check = ctk.CTkCheckBox(
            controls,
            text="Incluir subpastas",
            variable=self.md_include_subfolders,
            fg_color=THEME.primary,
            hover_color=THEME.primary_hover,
            border_color=THEME.border_medium,
            text_color=THEME.text_primary,
            font=(THEME.font_family, 12),
        )
        self.md_subfolders_check.grid(row=2, column=2, sticky="w", padx=(0, 12), pady=(0, 12))

        self.md_sort_mode = tk.StringVar(value="Natural")
        self.md_sort_combo = ctk.CTkComboBox(
            controls,
            variable=self.md_sort_mode,
            values=["Natural", "Nome A-Z", "Data de modificação"],
            command=lambda _value: self._md_sort_current(),
            width=180,
            height=36,
            fg_color=THEME.bg_input,
            button_color=THEME.bg_surface_alt,
            button_hover_color=THEME.bg_surface_hover,
            border_color=THEME.border_medium,
            dropdown_fg_color=THEME.bg_surface,
            dropdown_hover_color=THEME.bg_surface_hover,
            text_color=THEME.text_primary,
            font=(THEME.font_family, 12),
        )
        self.md_sort_combo.grid(row=2, column=3, sticky="e", padx=(0, 18), pady=(0, 12))

        table_shell = ctk.CTkFrame(root, fg_color="transparent")
        table_shell.grid(row=2, column=0, sticky="nsew", pady=(0, 16))
        table_shell.grid_columnconfigure(0, weight=1)
        table_shell.grid_rowconfigure(0, weight=1)

        self.md_empty_state = EmptyState(
            table_shell,
            icon="📝",
            title="Nenhum arquivo selecionado",
            message="Adicione arquivos manualmente ou selecione uma pasta e clique em Fazer varredura.",
            primary_label="Adicionar arquivos",
            primary_command=self._md_add_files,
            secondary_label="Selecionar pasta",
            secondary_command=self._md_select_folder,
        )
        self.md_empty_state.grid(row=0, column=0, sticky="nsew")

        self.md_table = FileTable(table_shell, on_select=self._md_on_table_select)
        self.md_table.grid(row=0, column=0, sticky="nsew")
        self.md_table.grid_remove()

        output_panel = ctk.CTkFrame(
            root,
            fg_color=THEME.bg_surface,
            border_color=THEME.border_soft,
            border_width=1,
            corner_radius=20,
        )
        output_panel.grid(row=3, column=0, sticky="ew", pady=(0, 16))
        output_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            output_panel,
            text="Saída",
            font=(THEME.font_family, 16, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, columnspan=4, sticky="ew", padx=18, pady=(16, 8))

        ctk.CTkLabel(
            output_panel,
            text="Separador",
            font=(THEME.font_family, 12, "bold"),
            text_color=THEME.text_secondary,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=(18, 10), pady=(0, 12))
        self.md_separator_mode = tk.StringVar(value="completo")
        self.md_separator_combo = ctk.CTkComboBox(
            output_panel,
            variable=self.md_separator_mode,
            values=["completo", "simples", "nenhum"],
            width=130,
            height=36,
            fg_color=THEME.bg_input,
            button_color=THEME.bg_surface_alt,
            button_hover_color=THEME.bg_surface_hover,
            border_color=THEME.border_medium,
            dropdown_fg_color=THEME.bg_surface,
            dropdown_hover_color=THEME.bg_surface_hover,
            text_color=THEME.text_primary,
            font=(THEME.font_family, 12),
        )
        self.md_separator_combo.grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 12))

        ctk.CTkLabel(
            output_panel,
            text="Arquivo final",
            font=(THEME.font_family, 12, "bold"),
            text_color=THEME.text_secondary,
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=(18, 10), pady=(0, 16))
        self.md_output_var = tk.StringVar(value="")
        self.md_output_entry = ctk.CTkEntry(
            output_panel,
            textvariable=self.md_output_var,
            placeholder_text="Escolha onde salvar textos_unidos.md",
            height=36,
            fg_color=THEME.bg_input,
            border_color=THEME.border_medium,
            text_color=THEME.text_primary,
        )
        self.md_output_entry.grid(row=2, column=1, columnspan=2, sticky="ew", padx=(0, 10), pady=(0, 16))
        ActionButton(output_panel, "Escolher", "secondary", self._md_choose_output).grid(row=2, column=3, sticky="e", padx=(0, 18), pady=(0, 16))

        progress_row = ctk.CTkFrame(root, fg_color="transparent")
        progress_row.grid(row=4, column=0, sticky="ew")
        progress_row.grid_columnconfigure(0, weight=1)
        progress_row.grid_columnconfigure(1, weight=0)

        self.md_progress = ProgressPanel(progress_row, title="Progresso")
        self.md_progress.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        self.md_join_btn = ActionButton(progress_row, "Juntar textos", "primary", self._md_join_texts, icon="✓", width=180, height=46)
        self.md_join_btn.grid(row=0, column=1, sticky="se")

        self._md_update_empty_state()

    def _md_supported_filetypes(self):
        return [("Markdown e texto", "*.md *.txt"), ("Markdown", "*.md"), ("Texto", "*.txt"), ("Todos os arquivos", "*.*")]

    def _md_current_paths(self) -> List[Path]:
        paths: List[Path] = []
        if not hasattr(self, "md_table"):
            return paths
        for values in self.md_table.get_all_values():
            try:
                name = values[1]
                folder = values[4]
                path = Path(folder) / name
                if path.suffix.lower() in TEXT_EXTENSIONS:
                    paths.append(path)
            except Exception:
                continue
        return paths

    def _md_path_rows(self, paths: Sequence[Path]) -> List[Tuple[str, str, str, str, str, str]]:
        rows = []
        for index, path in enumerate(paths, start=1):
            rows.append((
                f"{index:03d}",
                path.name,
                path.suffix.lower().lstrip(".").upper() or "—",
                format_size(safe_stat_size(path)),
                str(path.parent),
                "Pronto",
            ))
        return rows

    def _md_refresh_table(self, paths: Sequence[Path]) -> None:
        self.md_table.set_items(self._md_path_rows(paths))
        self._md_update_empty_state()
        self.status_text.configure(text=f"Markdown/TXT: {len(paths)} arquivo(s) na lista.")

    def _md_update_empty_state(self) -> None:
        count = len(self.md_table.tree.get_children()) if hasattr(self, "md_table") else 0
        if count:
            self.md_empty_state.grid_remove()
            self.md_table.grid()
        else:
            self.md_table.grid_remove()
            self.md_empty_state.grid()

    def _md_add_unique_paths(self, new_paths: Iterable[Path], sort_mode: str = "natural") -> int:
        current = self._md_current_paths()
        existing = set()
        for path in current:
            try:
                existing.add(path.resolve())
            except OSError:
                existing.add(path.absolute())

        added = 0
        for path in new_paths:
            path = Path(path)
            if not is_supported_text_file(path):
                continue
            try:
                key = path.resolve()
            except OSError:
                key = path.absolute()
            if key not in existing:
                current.append(path)
                existing.add(key)
                added += 1
        current = sort_paths(current, sort_mode)
        self._md_refresh_table(current)
        return added

    def _md_add_files(self) -> None:
        selected = filedialog.askopenfilenames(title="Selecione arquivos .md ou .txt", filetypes=self._md_supported_filetypes())
        if not selected:
            return
        added = self._md_add_unique_paths([Path(p) for p in selected], self._md_sort_mode_to_key())
        if added:
            self.show_toast("Arquivos adicionados", f"{added} arquivo(s) novo(s) entraram na lista.", "success")
        else:
            self.show_toast("Nenhum arquivo novo", "Os arquivos selecionados já estavam na lista ou eram incompatíveis.", "warning")

    def _md_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta para varredura")
        if not folder:
            return
        self.markdown_selected_folder = Path(folder)
        self.md_folder_var.set(str(self.markdown_selected_folder))
        self.status_text.configure(text="Pasta selecionada. Clique em Fazer varredura para buscar .md e .txt.")
        self.show_toast("Pasta selecionada", "Agora clique em Fazer varredura para listar os arquivos.", "info")

    def _md_scan_folder(self) -> None:
        if self.markdown_is_busy:
            return
        folder = self.markdown_selected_folder
        if folder is None:
            self.show_toast("Selecione uma pasta", "Escolha uma pasta antes de fazer a varredura.", "warning")
            return
        if not folder.exists() or not folder.is_dir():
            self.show_toast("Pasta inválida", "A pasta selecionada não existe mais ou não é acessível.", "error")
            return

        recursive = bool(self.md_include_subfolders.get())
        mode_text = "com subpastas" if recursive else "somente nesta pasta"
        self.markdown_is_busy = True
        self.md_scan_btn.set_loading(True, "Varrendo...")
        self.md_progress.reset_success_color()
        self.md_progress.start_indeterminate(f"Pesquisando arquivos .md e .txt {mode_text}...")
        self.status_text.configure(text=f"Markdown/TXT: fazendo varredura {mode_text}.")

        def worker() -> None:
            error: Optional[Exception] = None
            found: List[Path] = []
            try:
                iterator = folder.rglob("*") if recursive else folder.iterdir()
                for path in iterator:
                    if is_supported_text_file(path):
                        found.append(path)
                found = sort_paths(found, self._md_sort_mode_to_key())
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._md_finish_scan(found, error, recursive))

        threading.Thread(target=worker, daemon=True).start()

    def _md_finish_scan(self, found: List[Path], error: Optional[Exception], recursive: bool) -> None:
        self.markdown_is_busy = False
        self.md_scan_btn.set_loading(False)
        if error:
            self.md_progress.stop("Erro na varredura.")
            self.status_text.configure(text="Markdown/TXT: erro ao fazer varredura.")
            self.show_toast("Erro na varredura", str(error), "error")
            return
        added = self._md_add_unique_paths(found, self._md_sort_mode_to_key())
        mode_text = "com subpastas" if recursive else "sem subpastas"
        if found:
            self.md_progress.complete(f"Varredura concluída: {len(found)} encontrado(s), {added} novo(s) adicionado(s).")
            self.show_toast("Varredura concluída", f"{len(found)} arquivo(s) encontrado(s) {mode_text}.", "success")
        else:
            self.md_progress.stop("Nenhum arquivo compatível encontrado.")
            self.show_toast("Nada encontrado", "Nenhum arquivo .md ou .txt foi encontrado nessa pasta.", "warning")
        self.status_text.configure(text=f"Markdown/TXT: {len(self._md_current_paths())} arquivo(s) na lista.")

    def _md_sort_mode_to_key(self) -> str:
        label = self.md_sort_mode.get() if hasattr(self, "md_sort_mode") else "Natural"
        if label == "Nome A-Z":
            return "name"
        if label == "Data de modificação":
            return "modified"
        return "natural"

    def _md_sort_current(self) -> None:
        paths = self._md_current_paths()
        if not paths:
            return
        self._md_refresh_table(sort_paths(paths, self._md_sort_mode_to_key()))
        self.show_toast("Lista ordenada", f"Ordenação aplicada: {self.md_sort_mode.get()}.", "info")

    def _md_remove_selected(self) -> None:
        if not len(self.md_table.tree.selection()):
            self.show_toast("Nada selecionado", "Selecione um ou mais arquivos para remover.", "warning")
            return
        self.md_table.remove_selected()
        self._md_update_empty_state()
        self.status_text.configure(text=f"Markdown/TXT: {len(self._md_current_paths())} arquivo(s) na lista.")

    def _md_clear_files(self) -> None:
        if not self._md_current_paths():
            return
        self.md_table.clear()
        self._md_update_empty_state()
        self.md_progress.stop("Lista limpa.")
        self.status_text.configure(text="Markdown/TXT: lista limpa.")

    def _md_move_up(self) -> None:
        self.md_table.move_selected_up()
        self.status_text.configure(text="Markdown/TXT: ordem atualizada.")

    def _md_move_down(self) -> None:
        self.md_table.move_selected_down()
        self.status_text.configure(text="Markdown/TXT: ordem atualizada.")

    def _md_on_table_select(self, selected: List[str]) -> None:
        count = len(selected)
        self.status_text.configure(text=f"Markdown/TXT: {count} arquivo(s) selecionado(s)." if count else "Markdown/TXT: nenhum arquivo selecionado.")

    def _md_choose_output(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Escolha o arquivo final",
            defaultextension=".md",
            initialfile="textos_unidos.md",
            filetypes=[("Markdown", "*.md"), ("Texto", "*.txt")],
        )
        if filename:
            self.md_output_var.set(filename)
            self.status_text.configure(text="Markdown/TXT: arquivo final selecionado.")

    def _md_join_texts(self) -> None:
        if self.markdown_is_busy:
            return
        paths = self._md_current_paths()
        if not paths:
            self.show_toast("Nenhum arquivo", "Adicione pelo menos um arquivo .md ou .txt.", "warning")
            return
        raw_output = self.md_output_var.get().strip()
        if not raw_output:
            self.show_toast("Escolha a saída", "Escolha o arquivo final antes de juntar os textos.", "warning")
            return
        output_path = Path(raw_output)
        if output_path.suffix.lower() not in TEXT_EXTENSIONS:
            output_path = output_path.with_suffix(".md")
            self.md_output_var.set(str(output_path))

        # Bloqueio visual antes da thread, para erro aparecer imediatamente.
        try:
            output_resolved = output_path.resolve() if output_path.exists() else output_path.absolute()
            input_resolved = [p.resolve() if p.exists() else p.absolute() for p in paths]
            if output_resolved in input_resolved:
                raise ValueError("O arquivo final não pode estar na lista de arquivos de entrada.")
        except Exception as exc:
            self.show_toast("Saída inválida", str(exc), "error")
            self.md_progress.stop("Escolha outro arquivo final.")
            return

        if output_path.exists():
            if not messagebox.askyesno("Arquivo já existe", "O arquivo final já existe. Deseja substituir?"):
                return

        self.markdown_is_busy = True
        self.md_join_btn.set_loading(True, "Juntando...")
        self.md_progress.reset_success_color()
        self.md_progress.set_progress(0, f"Preparando união de {len(paths)} arquivo(s)...")
        self.status_text.configure(text="Markdown/TXT: juntando textos...")

        separator = self.md_separator_mode.get()

        def progress_callback(index: int, total: int, message: str) -> None:
            value = index / total if total else 0
            self.after(0, lambda: self.md_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))

        def worker() -> None:
            error: Optional[Exception] = None
            result: Optional[Path] = None
            try:
                result = merge_text_files(paths, output_path, separator, progress_callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._md_finish_join(result, error))

        threading.Thread(target=worker, daemon=True).start()

    def _md_finish_join(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.markdown_is_busy = False
        self.md_join_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.md_progress.stop("Erro ao juntar textos.")
            self.status_text.configure(text="Markdown/TXT: erro ao juntar textos.")
            self.show_toast("Erro ao juntar textos", str(error), "error")
            return
        self.md_progress.complete(f"Documento final gerado: {result}")
        self.status_text.configure(text="Markdown/TXT: documento final gerado com sucesso.")
        self.show_toast("Documento gerado", f"Arquivo salvo em: {result}", "success")
    # ------------------------------------------------------------------
    # Vídeo funcional
    # ------------------------------------------------------------------
    def _build_video_view(self) -> None:
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(hero, text="🎬 Vídeo", font=(THEME.font_family, 20, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 2))
        ctk.CTkLabel(hero, text="Junte vídeos em MP4 com seleção por arquivos/pasta, ordem manual e FFmpeg automático.", font=(THEME.font_family, 13), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 18))
        StatusBadge(hero, "Thread + FFmpeg", "info").grid(row=0, column=1, rowspan=2, sticky="e", padx=20, pady=20)

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="video_cards")
        ToolCard(
            cards,
            icon="🎬",
            title="Juntar vídeos",
            description="Combine vídeos na ordem exibida na tabela.",
            category="Vídeo",
            command=lambda: self.show_toast("Juntar vídeos", "Esta ferramenta já está ativa.", "info"),
            active=True,
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ToolCard(
            cards,
            icon="🔊",
            title="Extrair áudio dos vídeos",
            description="Use a ferramenta Áudio de vídeos na seção Áudio.",
            category="Atalho",
            command=lambda: self._go_to_audio_batch_from_video(),
            enabled=True,
        ).grid(row=0, column=1, sticky="nsew", padx=8)
        ToolCard(
            cards,
            icon="🗜",
            title="Comprimir vídeo",
            description="Planejado para uma versão futura.",
            category="Futuro",
            command=lambda: None,
            enabled=False,
        ).grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        self._build_video_join_tool(root)

    def _go_to_audio_batch_from_video(self) -> None:
        self.audio_tool = "batch"
        self.show_section("audio")

    def _build_video_join_tool(self, master) -> None:
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(panel, text="🎬 Juntar vídeos", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Adicione vídeos, ajuste a ordem manualmente se necessário e gere um MP4 final.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        for i in range(9):
            actions.grid_columnconfigure(i, weight=0)
        actions.grid_columnconfigure(9, weight=1)
        ActionButton(actions, "Adicionar vídeos", "secondary", self._video_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._video_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self._video_remove_selected()).grid(row=0, column=2, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._video_clear_table()).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Subir", "secondary", lambda: self.video_table.move_selected_up()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Descer", "secondary", lambda: self.video_table.move_selected_down()).grid(row=0, column=5, padx=4)
        self.video_sort = tk.StringVar(value="Natural")
        ctk.CTkComboBox(
            actions,
            variable=self.video_sort,
            values=["Natural", "Nome A-Z", "Data de modificação"],
            command=lambda _v: self._sort_table_paths(self.video_table, self.video_sort.get()),
            width=180,
            fg_color=THEME.bg_input,
            button_color=THEME.bg_surface_alt,
            button_hover_color=THEME.bg_surface_hover,
            border_color=THEME.border_medium,
            dropdown_fg_color=THEME.bg_surface,
            dropdown_hover_color=THEME.bg_surface_hover,
            text_color=THEME.text_primary,
        ).grid(row=0, column=6, padx=4)

        table_shell = ctk.CTkFrame(panel, fg_color="transparent")
        table_shell.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        table_shell.grid_columnconfigure(0, weight=1)
        table_shell.grid_rowconfigure(0, weight=1)
        self.video_table = FileTable(table_shell)
        self.video_table.grid(row=0, column=0, sticky="nsew")

        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(output, text="Arquivo final", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        self.video_output = tk.StringVar(value="")
        ctk.CTkEntry(output, textvariable=self.video_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(14, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._video_choose_output).grid(row=1, column=2, padx=(0, 14), pady=(0, 14))

        self.video_progress = ProgressPanel(panel, title="Progresso")
        self.video_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.video_join_btn = ActionButton(panel, "Juntar vídeos", "primary", self._video_join_run, icon="▶")
        self.video_join_btn.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _video_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecione os vídeos", filetypes=self._video_filetypes())
        if files:
            added = self._add_unique_to_table(self.video_table, [Path(f) for f in files], is_supported_video_file, self.video_sort.get())
            self.show_toast("Vídeos adicionados", f"{added} novo(s) vídeo(s) entraram na lista.", "success" if added else "warning")
            self.status_text.configure(text=f"Vídeo: {len(self.video_table.get_all_values())} item(ns) na lista.")

    def _video_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta com vídeos")
        if folder:
            try:
                paths = [p for p in Path(folder).iterdir() if is_supported_video_file(p)]
            except OSError as exc:
                self.show_toast("Erro ao ler pasta", str(exc), "error")
                return
            added = self._add_unique_to_table(self.video_table, paths, is_supported_video_file, self.video_sort.get())
            self.show_toast("Pasta adicionada", f"{added} vídeo(s) encontrados nesta pasta.", "success" if added else "warning")
            self.status_text.configure(text=f"Vídeo: {len(self.video_table.get_all_values())} item(ns) na lista.")

    def _video_choose_output(self) -> None:
        filename = filedialog.asksaveasfilename(
            title="Salvar vídeo final",
            defaultextension=".mp4",
            initialfile="video_unificado.mp4",
            filetypes=[("Vídeo MP4", "*.mp4"), ("Todos os arquivos", "*.*")],
        )
        if filename:
            self.video_output.set(str(ensure_video_extension(Path(filename))))
            self.status_text.configure(text="Vídeo: arquivo final selecionado.")

    def _video_remove_selected(self) -> None:
        self.video_table.remove_selected()
        self.status_text.configure(text="Vídeo: itens selecionados removidos.")

    def _video_clear_table(self) -> None:
        if self.video_table.get_all_values() and not messagebox.askyesno("Limpar lista", "Deseja limpar todos os vídeos da lista?"):
            return
        self.video_table.clear()
        self.status_text.configure(text="Vídeo: lista limpa.")

    def _video_join_run(self) -> None:
        paths = self._paths_from_table(self.video_table)
        if not paths:
            self.show_toast("Nenhum vídeo", "Adicione pelo menos um arquivo de vídeo.", "warning")
            return
        raw_output = self.video_output.get().strip()
        if not raw_output:
            self.show_toast("Escolha a saída", "Escolha o arquivo final antes de juntar.", "warning")
            return
        output = ensure_video_extension(Path(raw_output))
        self.video_output.set(str(output))

        try:
            output_resolved = output.resolve() if output.exists() else output.absolute()
            input_resolved = [p.resolve() if p.exists() else p.absolute() for p in paths]
            if output_resolved in input_resolved:
                raise ValueError("O vídeo final não pode estar dentro da lista de entrada.")
        except ValueError as exc:
            self.show_toast("Saída inválida", str(exc), "error")
            self.video_progress.stop("Escolha outro arquivo final.")
            return
        except Exception:
            pass

        if not self._confirm_overwrite(output):
            return

        self.video_join_btn.set_loading(True, "Juntando...")
        self.video_progress.reset_success_color()
        self.video_progress.set_progress(0, "Preparando vídeos...")
        self.status_text.configure(text="Vídeo: juntando arquivos...")
        self.status_progress.set(0)

        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.video_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))

        def worker() -> None:
            result = None
            error = None
            try:
                result = join_video_files(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._video_join_finish(result, error))

        threading.Thread(target=worker, daemon=True).start()

    def _video_join_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.video_join_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.video_progress.stop("Erro ao juntar vídeos.")
            self.status_text.configure(text="Vídeo: erro ao juntar arquivos.")
            self.show_toast("Erro ao juntar vídeos", str(error), "error")
            return
        self.video_progress.complete(f"Vídeo final gerado: {result}")
        self.status_text.configure(text="Vídeo: arquivo final gerado com sucesso.")
        self.show_toast("Vídeo gerado", f"Arquivo salvo em: {result}", "success")

    # ------------------------------------------------------------------
    # Arquivos/Pastas funcional
    # ------------------------------------------------------------------
    def _set_folders_mode(self, mode: str) -> None:
        self.folders_mode = mode
        self.clear_content()
        self._build_folders_view()

    def _build_folders_view(self) -> None:
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0)
        ctk.CTkLabel(hero, text="🗂 Arquivos/Pastas", font=(THEME.font_family, 20, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 2))
        ctk.CTkLabel(hero, text="Diagnostique pastas, liste arquivos e exporte relatórios em TXT, JSON, CSV e XLSX.", font=(THEME.font_family, 13), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 18))
        StatusBadge(hero, "Painel diagnóstico", "info").grid(row=0, column=1, rowspan=2, sticky="e", padx=20, pady=20)

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="folder_cards")
        ToolCard(
            cards,
            icon="🗂",
            title="Gerar estrutura",
            description="Cria árvore, estatísticas, prévia e relatórios.",
            category="Diagnóstico",
            command=lambda: self._set_folders_mode("structure"),
            active=getattr(self, "folders_mode", "structure") == "structure",
        ).grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ToolCard(
            cards,
            icon="📄",
            title="Listar arquivos",
            description="Exporta uma lista simples de arquivos da pasta.",
            category="Listagem",
            command=lambda: self._set_folders_mode("list"),
            active=getattr(self, "folders_mode", "structure") == "list",
        ).grid(row=0, column=1, sticky="nsew", padx=8)
        ToolCard(
            cards,
            icon="📊",
            title="Resumo final",
            description="Cards com totais, tamanho e erros de acesso.",
            category="Resumo",
            command=lambda: self.show_toast("Resumo", "O resumo aparece após gerar ou listar.", "info"),
        ).grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        self._build_folders_panel(root)

    def _build_folders_panel(self, master) -> None:
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(4, weight=1)

        mode = getattr(self, "folders_mode", "structure")
        title = "🗂 Gerar estrutura de pastas" if mode == "structure" else "📄 Listar arquivos rapidamente"
        description = "Analise arquivos e diretórios, gere resumo e exporte relatórios." if mode == "structure" else "Liste apenas arquivos e exporte uma relação simples."
        ctk.CTkLabel(panel, text=title, font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text=description, font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        selectors = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        selectors.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        selectors.grid_columnconfigure(1, weight=1)
        selectors.grid_columnconfigure(3, weight=1)

        self.folders_root_var = getattr(self, "folders_root_var", tk.StringVar(value=""))
        self.folders_output_var = getattr(self, "folders_output_var", tk.StringVar(value=""))
        ctk.CTkLabel(selectors, text="Pasta raiz", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=(14, 6))
        ctk.CTkEntry(selectors, textvariable=self.folders_root_var, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(14, 8), pady=(0, 14))
        ActionButton(selectors, "Escolher", "secondary", self._folders_choose_root).grid(row=1, column=2, padx=(0, 12), pady=(0, 14))

        ctk.CTkLabel(selectors, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=3, sticky="w", padx=(10, 8), pady=(14, 6))
        ctk.CTkEntry(selectors, textvariable=self.folders_output_var, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=3, sticky="ew", padx=(10, 8), pady=(0, 14))
        ActionButton(selectors, "Escolher", "secondary", self._folders_choose_output).grid(row=1, column=4, padx=(0, 14), pady=(0, 14))

        options = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        options.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 14))
        for idx in range(9):
            options.grid_columnconfigure(idx, weight=0)
        options.grid_columnconfigure(9, weight=1)

        self.folders_include_files = getattr(self, "folders_include_files", tk.BooleanVar(value=True))
        self.folders_include_dirs = getattr(self, "folders_include_dirs", tk.BooleanVar(value=True))
        self.folders_include_hidden = getattr(self, "folders_include_hidden", tk.BooleanVar(value=False))
        self.folders_include_subfolders = getattr(self, "folders_include_subfolders", tk.BooleanVar(value=True))
        self.folders_fmt_txt = getattr(self, "folders_fmt_txt", tk.BooleanVar(value=True))
        self.folders_fmt_json = getattr(self, "folders_fmt_json", tk.BooleanVar(value=True))
        self.folders_fmt_csv = getattr(self, "folders_fmt_csv", tk.BooleanVar(value=True))
        self.folders_fmt_xlsx = getattr(self, "folders_fmt_xlsx", tk.BooleanVar(value=True))

        ctk.CTkLabel(options, text="Incluir", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=(14, 12), pady=(14, 4))
        ctk.CTkCheckBox(options, text="Arquivos", variable=self.folders_include_files, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=1, sticky="w", padx=6, pady=(14, 4))
        ctk.CTkCheckBox(options, text="Diretórios", variable=self.folders_include_dirs, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, sticky="w", padx=6, pady=(14, 4))
        ctk.CTkCheckBox(options, text="Ocultos", variable=self.folders_include_hidden, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=3, sticky="w", padx=6, pady=(14, 4))
        ctk.CTkCheckBox(options, text="Subpastas", variable=self.folders_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=4, sticky="w", padx=6, pady=(14, 4))

        ctk.CTkLabel(options, text="Exportar", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=1, column=0, sticky="w", padx=(14, 12), pady=(4, 14))
        ctk.CTkCheckBox(options, text="TXT", variable=self.folders_fmt_txt, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=1, sticky="w", padx=6, pady=(4, 14))
        ctk.CTkCheckBox(options, text="JSON", variable=self.folders_fmt_json, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=2, sticky="w", padx=6, pady=(4, 14))
        ctk.CTkCheckBox(options, text="CSV", variable=self.folders_fmt_csv, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=3, sticky="w", padx=6, pady=(4, 14))
        ctk.CTkCheckBox(options, text="XLSX", variable=self.folders_fmt_xlsx, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=4, sticky="w", padx=6, pady=(4, 14))

        summary = ctk.CTkFrame(panel, fg_color="transparent")
        summary.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        summary.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="folder_summary")
        self.folder_stat_labels: Dict[str, ctk.CTkLabel] = {}
        self._folder_summary_card(summary, 0, "Arquivos", "—", "total_arquivos")
        self._folder_summary_card(summary, 1, "Pastas", "—", "total_pastas")
        self._folder_summary_card(summary, 2, "Tamanho", "—", "tamanho_total")
        self._folder_summary_card(summary, 3, "Erros", "—", "erros_acesso")

        preview = ctk.CTkFrame(panel, fg_color="transparent")
        preview.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 14))
        preview.grid_columnconfigure(0, weight=1)
        preview.grid_rowconfigure(0, weight=1)
        self.folders_table = FileTable(preview)
        self.folders_table.grid(row=0, column=0, sticky="nsew")

        self.folders_progress = ProgressPanel(panel, title="Progresso")
        self.folders_progress.grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 14))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=7, column=0, sticky="ew", padx=18, pady=(0, 18))
        actions.grid_columnconfigure(0, weight=1)
        ActionButton(actions, "Abrir pasta de saída", "secondary", self._folders_open_output, icon="↗").grid(row=0, column=1, padx=(0, 8))
        self.folders_run_btn = ActionButton(actions, "Listar arquivos" if mode == "list" else "Gerar relatório", "primary", self._folders_run, icon="▶")
        self.folders_run_btn.grid(row=0, column=2)

    def _folder_summary_card(self, master, col: int, title: str, value: str, key: str) -> None:
        card = ctk.CTkFrame(master, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        card.grid(row=0, column=col, sticky="nsew", padx=6)
        ctk.CTkLabel(card, text=title, font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        label = ctk.CTkLabel(card, text=value, font=(THEME.font_family, 20, "bold"), text_color=THEME.text_primary, anchor="w")
        label.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        self.folder_stat_labels[key] = label

    def _folders_choose_root(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta raiz")
        if folder:
            self.folders_root_var.set(folder)
            if not self.folders_output_var.get().strip():
                self.folders_output_var.set(str(Path(folder) / "relatorios_k_tools"))
            self.status_text.configure(text="Arquivos/Pastas: pasta raiz selecionada.")

    def _folders_choose_output(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta de saída")
        if folder:
            self.folders_output_var.set(folder)
            self.status_text.configure(text="Arquivos/Pastas: pasta de saída selecionada.")

    def _folders_selected_formats(self) -> List[str]:
        formats = []
        if self.folders_fmt_txt.get():
            formats.append("txt")
        if self.folders_fmt_json.get():
            formats.append("json")
        if self.folders_fmt_csv.get():
            formats.append("csv")
        if self.folders_fmt_xlsx.get():
            formats.append("xlsx")
        return formats

    def _folders_expected_outputs(self, output_folder: Path, formats: Sequence[str], mode: str) -> List[Path]:
        base = report_base_name(mode)
        return [Path(output_folder) / f"{base}.{fmt.lower()}" for fmt in formats]

    def _folders_open_output(self) -> None:
        folder_text = self.folders_output_var.get().strip() if hasattr(self, "folders_output_var") else ""
        if not folder_text:
            self.show_toast("Sem pasta de saída", "Escolha uma pasta de saída primeiro.", "warning")
            return
        folder = Path(folder_text)
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            self.show_toast("Não foi possível abrir", str(exc), "error")

    def _folders_update_summary(self, stats: Dict[str, object]) -> None:
        for key, label in getattr(self, "folder_stat_labels", {}).items():
            value = stats.get(key, "—")
            label.configure(text=str(value))

    def _folders_rows_from_entries(self, entries: Sequence[Dict[str, object]], limit: int = 500) -> List[Tuple[str, str, str, str, str, str]]:
        rows = []
        for index, entry in enumerate(entries[:limit], start=1):
            tipo = "DIR" if entry.get("tipo") == "Pasta" else str(entry.get("extensao") or "FILE").upper().lstrip(".")
            status = "Diretório" if entry.get("tipo") == "Pasta" else "Arquivo"
            rows.append((
                f"{index:03d}",
                str(entry.get("nome", "")),
                tipo,
                str(entry.get("tamanho", "—")),
                str(entry.get("pasta", "")),
                status,
            ))
        return rows

    def _folders_run(self) -> None:
        root_text = self.folders_root_var.get().strip()
        output_text = self.folders_output_var.get().strip()
        if not root_text:
            self.show_toast("Pasta raiz obrigatória", "Escolha a pasta que será analisada.", "warning")
            return
        if not output_text:
            self.show_toast("Pasta de saída obrigatória", "Escolha onde os relatórios serão salvos.", "warning")
            return
        formats = self._folders_selected_formats()
        if not formats:
            self.show_toast("Formato obrigatório", "Marque pelo menos TXT, JSON, CSV ou XLSX.", "warning")
            return

        root_path = Path(root_text)
        output_folder = Path(output_text)
        mode = getattr(self, "folders_mode", "structure")
        expected = self._folders_expected_outputs(output_folder, formats, mode)
        existing = [p for p in expected if p.exists()]
        if existing:
            names = "\n".join(str(p) for p in existing[:8])
            if len(existing) > 8:
                names += f"\n... e mais {len(existing) - 8} arquivo(s)."
            if not messagebox.askyesno("Relatórios já existem", f"Os relatórios abaixo já existem:\n\n{names}\n\nDeseja substituir?"):
                return

        self.folders_run_btn.set_loading(True, "Analisando...")
        self.folders_progress.reset_success_color()
        self.folders_progress.set_progress(0.03, "Preparando análise...")
        self.status_text.configure(text="Arquivos/Pastas: analisando pasta...")
        self.status_progress.set(0.03)

        include_files = True if mode == "list" else bool(self.folders_include_files.get())
        include_dirs = False if mode == "list" else bool(self.folders_include_dirs.get())
        include_hidden = bool(self.folders_include_hidden.get())
        include_subfolders = bool(self.folders_include_subfolders.get())

        def callback(value: float, message: str) -> None:
            self.after(0, lambda: self.folders_progress.set_progress(value, message))
            self.after(0, lambda: self.status_progress.set(value))

        def worker() -> None:
            result = None
            generated = None
            error = None
            try:
                result = scan_folder_structure(
                    root_path,
                    include_files=include_files,
                    include_dirs=include_dirs,
                    include_hidden=include_hidden,
                    include_subfolders=include_subfolders,
                    progress_callback=callback,
                )
                generated = export_folder_reports(result, output_folder, formats, mode=mode, progress_callback=callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda: self._folders_finish(result, generated, error))

        threading.Thread(target=worker, daemon=True).start()

    def _folders_finish(self, result: Optional[Dict[str, object]], generated: Optional[Dict[str, Path]], error: Optional[Exception]) -> None:
        self.folders_run_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.folders_progress.stop("Erro ao analisar/exportar relatórios.")
            self.status_text.configure(text="Arquivos/Pastas: erro ao gerar relatórios.")
            self.show_toast("Erro em Arquivos/Pastas", str(error), "error")
            return
        if not result or generated is None:
            self.folders_progress.stop("Nenhum resultado foi gerado.")
            self.show_toast("Sem resultado", "A análise terminou sem dados para exportar.", "warning")
            return
        stats = result.get("stats", {})
        entries = result.get("entries", [])
        self._folders_update_summary(stats)  # type: ignore[arg-type]
        self.folders_table.set_items(self._folders_rows_from_entries(entries))  # type: ignore[arg-type]
        generated_names = ", ".join(fmt.upper() for fmt in generated.keys())
        self.folders_progress.complete(f"Relatórios gerados: {generated_names}")
        self.status_text.configure(text=f"Arquivos/Pastas: {stats.get('total_itens', 0)} item(ns) analisados. Relatórios: {generated_names}.")
        self.show_toast("Relatórios gerados", f"{stats.get('total_arquivos', 0)} arquivo(s), {stats.get('total_pastas', 0)} pasta(s).", "success")

    # ------------------------------------------------------------------
    # Configurações
    # ------------------------------------------------------------------
    def _build_settings_view(self) -> None:
        """Tela funcional de configurações: ambiente técnico, saída, logs e comportamento."""
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        # Variáveis da tela
        self.settings_appearance_var = ctk.StringVar(value=str(self.settings_config.get("appearance_mode", "Escuro")))
        self.settings_accent_var = ctk.StringVar(value=str(self.settings_config.get("accent_color", "Azul")))
        self.settings_output_var = ctk.StringVar(value=str(self.settings_config.get("default_output_folder", str(default_output_dir()))))
        self.settings_open_finish_var = ctk.StringVar(value="on" if self.settings_config.get("open_folder_on_finish", True) else "off")
        self.settings_confirm_overwrite_var = ctk.StringVar(value="on" if self.settings_config.get("confirm_overwrite", True) else "off")
        self.settings_save_last_var = ctk.StringVar(value="on" if self.settings_config.get("save_last_folder", True) else "off")

        # ------------------------------------------------------------------
        # Card: Visual fixo
        # ------------------------------------------------------------------
        visual_card = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        visual_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 18))
        visual_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            visual_card,
            text="🎨 Visual Neo",
            font=(THEME.font_family, 18, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))
        ctk.CTkLabel(
            visual_card,
            text="Interface fixa em modo escuro com destaque azul. A personalização visual foi removida para manter consistência e evitar quebras de tema.",
            font=(THEME.font_family, 12),
            text_color=THEME.text_secondary,
            anchor="w",
            wraplength=480,
        ).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        StatusBadge(visual_card, "Escuro", "info").grid(row=2, column=0, sticky="w", padx=18, pady=(0, 6))
        StatusBadge(visual_card, "Destaque azul", "success").grid(row=3, column=0, sticky="w", padx=18, pady=(0, 18))

        # ------------------------------------------------------------------
        # Card: Ambiente técnico
        # ------------------------------------------------------------------
        env_card = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        env_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 18))
        env_card.grid_columnconfigure(0, weight=1)
        env_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(env_card, text="⚙ Ambiente técnico", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 4))
        ctk.CTkLabel(env_card, text="Teste FFmpeg e instale automaticamente bibliotecas ausentes.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14))

        ffmpeg_box = ctk.CTkFrame(env_card, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        ffmpeg_box.grid(row=2, column=0, sticky="nsew", padx=(18, 8), pady=(0, 18))
        ffmpeg_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(ffmpeg_box, text="FFmpeg", font=(THEME.font_family, 15, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        self.ffmpeg_status_badge = StatusBadge(ffmpeg_box, "Não testado", "neutral")
        self.ffmpeg_status_badge.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))
        self.ffmpeg_path_label = ctk.CTkLabel(ffmpeg_box, text="Caminho: —", font=(THEME.font_family, 11), text_color=THEME.text_muted, anchor="w", wraplength=300)
        self.ffmpeg_path_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.ffmpeg_test_btn = ActionButton(ffmpeg_box, text="Testar FFmpeg", variant="secondary", command=self._settings_test_ffmpeg, width=145)
        self.ffmpeg_test_btn.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 14))

        deps_box = ctk.CTkFrame(env_card, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        deps_box.grid(row=2, column=1, sticky="nsew", padx=(8, 18), pady=(0, 18))
        deps_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(deps_box, text="Dependências", font=(THEME.font_family, 15, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 4))
        self.dependencies_status_badge = StatusBadge(deps_box, "Não verificadas", "neutral")
        self.dependencies_status_badge.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 8))
        self.dependencies_detail_label = ctk.CTkLabel(deps_box, text="Clique para verificar e corrigir dependências automaticamente.", font=(THEME.font_family, 11), text_color=THEME.text_muted, anchor="w", wraplength=300)
        self.dependencies_detail_label.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.dependencies_check_btn = ActionButton(deps_box, text="Verificar dependências", variant="secondary", command=self._settings_check_dependencies, width=190)
        self.dependencies_check_btn.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 14))

        # ------------------------------------------------------------------
        # Card: Saída e comportamento
        # ------------------------------------------------------------------
        behavior_card = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        behavior_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 18))
        behavior_card.grid_columnconfigure(0, weight=1)
        behavior_card.grid_columnconfigure(1, weight=0)

        ctk.CTkLabel(behavior_card, text="📁 Saída e comportamento", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=2, sticky="ew", padx=18, pady=(18, 4))
        ctk.CTkLabel(behavior_card, text="Defina pasta padrão e preferências de segurança.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14))

        self.output_entry = ctk.CTkEntry(behavior_card, textvariable=self.settings_output_var, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary, height=38)
        self.output_entry.grid(row=2, column=0, sticky="ew", padx=(18, 8), pady=(0, 14))
        ActionButton(behavior_card, text="Escolher pasta", variant="secondary", command=self._settings_choose_output_folder, width=150).grid(row=2, column=1, sticky="e", padx=(8, 18), pady=(0, 14))

        switches = ctk.CTkFrame(behavior_card, fg_color="transparent")
        switches.grid(row=3, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))
        switches.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkSwitch(switches, text="Abrir pasta ao concluir", variable=self.settings_open_finish_var, onvalue="on", offvalue="off", progress_color=THEME.primary, button_color=THEME.text_primary, text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=(0, 10), pady=4)
        ctk.CTkSwitch(switches, text="Confirmar sobrescrita", variable=self.settings_confirm_overwrite_var, onvalue="on", offvalue="off", progress_color=THEME.primary, button_color=THEME.text_primary, text_color=THEME.text_secondary).grid(row=0, column=1, sticky="w", padx=10, pady=4)
        ctk.CTkSwitch(switches, text="Salvar última pasta usada", variable=self.settings_save_last_var, onvalue="on", offvalue="off", progress_color=THEME.primary, button_color=THEME.text_primary, text_color=THEME.text_secondary).grid(row=0, column=2, sticky="w", padx=10, pady=4)

        # ------------------------------------------------------------------
        # Card: Logs e manutenção
        # ------------------------------------------------------------------
        maintenance_card = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        maintenance_card.grid(row=2, column=0, sticky="nsew", padx=(0, 10), pady=(0, 18))
        maintenance_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(maintenance_card, text="🧾 Logs e manutenção", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))
        ctk.CTkLabel(maintenance_card, text=f"Pasta de logs:\n{self.logs_dir}", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w", wraplength=480).grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        log_buttons = ctk.CTkFrame(maintenance_card, fg_color="transparent")
        log_buttons.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 18))
        ActionButton(log_buttons, text="Abrir pasta de logs", variant="secondary", command=self._settings_open_logs, width=160).grid(row=0, column=0, padx=(0, 8))
        ActionButton(log_buttons, text="Restaurar padrões", variant="ghost", command=self._settings_restore_defaults, width=150).grid(row=0, column=1, padx=8)

        # ------------------------------------------------------------------
        # Card: Progresso e salvar
        # ------------------------------------------------------------------
        save_card = ctk.CTkFrame(root, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        save_card.grid(row=2, column=1, sticky="nsew", padx=(10, 0), pady=(0, 18))
        save_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(save_card, text="✅ Estado das configurações", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 4))
        ctk.CTkLabel(save_card, text="Salve para manter as preferências nas próximas execuções.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.settings_progress = ProgressPanel(save_card, title="Configurações")
        self.settings_progress.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        self.settings_progress.stop("Pronto para salvar ou verificar ambiente.")
        action_row = ctk.CTkFrame(save_card, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        action_row.grid_columnconfigure(0, weight=1)
        self.save_settings_btn = ActionButton(action_row, text="Salvar configurações", variant="primary", command=self._settings_save, width=180)
        self.save_settings_btn.grid(row=0, column=0, sticky="e")

    def _settings_collect_config(self) -> Dict[str, object]:
        return {
            "appearance_mode": "Escuro",
            "accent_color": "Azul",
            "default_output_folder": self.settings_output_var.get().strip() or str(default_output_dir()),
            "open_folder_on_finish": self.settings_open_finish_var.get() == "on",
            "confirm_overwrite": self.settings_confirm_overwrite_var.get() == "on",
            "save_last_folder": self.settings_save_last_var.get() == "on",
        }

    def _settings_apply_appearance_preview(self) -> None:
        # Visual fixo: sempre escuro. Mantido como método para compatibilidade interna.
        ctk.set_appearance_mode("Dark")
        self.status_text.configure(text="Visual Neo fixo: modo escuro com destaque azul.")

    def _settings_apply_accent_preview(self) -> None:
        # Visual fixo: sempre azul. Mantido como método para compatibilidade interna.
        self.accent_color_name = "Azul"
        self.accent_color = THEME.primary
        try:
            self.status_progress.configure(progress_color=THEME.primary)
        except Exception:
            pass
        self.status_text.configure(text="Visual Neo fixo: destaque azul.")

    def _settings_choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta padrão de saída")
        if folder:
            self.settings_output_var.set(folder)
            self.status_text.configure(text="Pasta padrão de saída selecionada.")

    def _settings_save(self) -> None:
        config = self._settings_collect_config()
        try:
            output = Path(str(config["default_output_folder"])).expanduser()
            output.mkdir(parents=True, exist_ok=True)
            save_settings_config(self.config_path, config)
            self.settings_config = config
            self._settings_apply_appearance_preview()
            self._settings_apply_accent_preview()
            self.settings_progress.complete("Configurações salvas com sucesso.")
            self.status_text.configure(text=f"Configurações salvas em {self.config_path}.")
            self.show_toast("Configurações salvas", "Preferências atualizadas para as próximas execuções.", "success")
        except Exception as exc:
            self.settings_progress.stop("Erro ao salvar configurações.")
            self.status_text.configure(text="Erro ao salvar configurações.")
            self.show_toast("Erro ao salvar", str(exc), "error")

    def _settings_restore_defaults(self) -> None:
        if not messagebox.askyesno("Restaurar padrões", "Deseja restaurar as configurações padrão do K-Tools Neo?"):
            return
        defaults = default_settings_config()
        self.settings_appearance_var.set(str(defaults["appearance_mode"]))
        self.settings_accent_var.set(str(defaults["accent_color"]))
        self.settings_output_var.set(str(defaults["default_output_folder"]))
        self.settings_open_finish_var.set("on" if defaults["open_folder_on_finish"] else "off")
        self.settings_confirm_overwrite_var.set("on" if defaults["confirm_overwrite"] else "off")
        self.settings_save_last_var.set("on" if defaults["save_last_folder"] else "off")
        self._settings_apply_appearance_preview()
        self._settings_apply_accent_preview()
        self.settings_progress.stop("Padrões restaurados. Clique em Salvar configurações.")
        self.show_toast("Padrões restaurados", "Revise e salve para manter os padrões.", "warning")

    def _settings_open_logs(self) -> None:
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            # Cria um arquivo de exemplo para a pasta não ficar vazia na primeira abertura.
            marker = self.logs_dir / "README_logs.txt"
            if not marker.exists():
                marker.write_text("Pasta de logs do K-Tools Neo.\n", encoding="utf-8")
            open_path_in_os(self.logs_dir)
            self.show_toast("Logs abertos", "A pasta de logs foi aberta.", "success")
        except Exception as exc:
            self.show_toast("Erro ao abrir logs", str(exc), "error")

    def _settings_test_ffmpeg(self) -> None:
        self.ffmpeg_test_btn.set_loading(True, "Testando...")
        self.ffmpeg_status_badge.set_status("Testando", "processing")
        self.ffmpeg_path_label.configure(text="Caminho: verificando...")
        self.settings_progress.start_indeterminate("Testando FFmpeg...")
        self.status_text.configure(text="Configurações: testando FFmpeg...")

        def worker() -> None:
            try:
                exe = get_ffmpeg_exe()
                result = subprocess.run(
                    [exe, "-version"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    creationflags=subprocess_creationflags(),
                )
                if result.returncode != 0:
                    raise RuntimeError((result.stderr or "FFmpeg retornou erro ao executar -version.").strip())
                version_line = (result.stdout or "").splitlines()[0] if result.stdout else "FFmpeg OK"
                self.after(0, lambda: self._settings_finish_ffmpeg_test(exe, version_line, None))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._settings_finish_ffmpeg_test("", "", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _settings_finish_ffmpeg_test(self, exe: str, version_line: str, error: Optional[Exception]) -> None:
        self.ffmpeg_test_btn.set_loading(False)
        if error:
            self.ffmpeg_status_badge.set_status("Erro", "danger")
            self.ffmpeg_path_label.configure(text=f"Erro: {error}")
            self.settings_progress.stop("Falha ao testar FFmpeg.")
            self.status_text.configure(text="Configurações: FFmpeg com erro.")
            self.show_toast("FFmpeg com erro", str(error), "error")
            return
        self.ffmpeg_status_badge.set_status("OK", "success")
        self.ffmpeg_path_label.configure(text=f"Caminho: {exe}\n{version_line}")
        self.settings_progress.complete("FFmpeg funcionando corretamente.")
        self.status_text.configure(text="Configurações: FFmpeg funcionando.")
        self.show_toast("FFmpeg OK", "FFmpeg foi localizado e respondeu corretamente.", "success")

    def _settings_check_dependencies(self) -> None:
        self.dependencies_check_btn.set_loading(True, "Corrigindo...")
        self.dependencies_status_badge.set_status("Corrigindo", "processing")
        self.dependencies_detail_label.configure(text="Verificando e instalando automaticamente o que estiver ausente...")
        self.settings_progress.start_indeterminate("Verificando e corrigindo dependências...")
        self.status_text.configure(text="Configurações: verificando e corrigindo dependências...")

        def worker() -> None:
            ok: List[str] = []
            failed: List[str] = []
            for import_name, pip_name, _description in DEPENDENCY_CHECKS:
                try:
                    # Compatibilidade: pydub no Python 3.13 pode precisar de audioop-lts.
                    if import_name == "pydub":
                        try:
                            ensure_package("audioop", "audioop-lts")
                        except Exception:
                            pass
                    ensure_package(import_name, pip_name)
                    ok.append(pip_name)
                except Exception as exc:
                    # Segunda tentativa explícita de reparo antes de marcar falha.
                    try:
                        if import_name == "pydub":
                            _pip_install("audioop-lts")
                        _pip_install(pip_name)
                        importlib.invalidate_caches()
                        importlib.import_module(import_name)
                        ok.append(pip_name)
                    except Exception as retry_exc:
                        failed.append(f"{pip_name}: {retry_exc or exc}")
            self.after(0, lambda: self._settings_finish_dependencies(ok, failed))

        threading.Thread(target=worker, daemon=True).start()

    def _settings_finish_dependencies(self, ok: List[str], failed: List[str]) -> None:
        self.dependencies_check_btn.set_loading(False)
        if failed:
            self.dependencies_status_badge.set_status("Atenção", "warning")
            self.dependencies_detail_label.configure(text=f"Corrigidas/OK: {len(ok)} | Ainda com falha: {len(failed)}\n" + "\n".join(failed[:3]))
            self.settings_progress.stop("Algumas dependências ainda falharam após tentativa automática.")
            self.status_text.configure(text="Configurações: dependências com alerta.")
            self.show_toast("Dependências com alerta", f"{len(failed)} dependência(s) ainda falharam após tentativa automática.", "warning")
            return
        self.dependencies_status_badge.set_status("OK", "success")
        self.dependencies_detail_label.configure(text=f"{len(ok)} dependência(s) disponíveis/instaladas com sucesso.")
        self.settings_progress.complete("Dependências verificadas e corrigidas com sucesso.")
        self.status_text.configure(text="Configurações: dependências OK.")
        self.show_toast("Dependências OK", "Todas as dependências principais estão disponíveis ou foram instaladas.", "success")

    def _build_placeholder_view(self, section_id: str) -> None:
        data = self.SECTION_DATA[section_id]
        root = ctk.CTkFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure((0, 1, 2), weight=1, uniform="section_cards")
        root.grid_rowconfigure(2, weight=1)

        cards = self._get_placeholder_cards(section_id)
        for index, (icon, title, desc, category, enabled) in enumerate(cards):
            row = index // 3
            col = index % 3
            ToolCard(
                root,
                icon=icon,
                title=title,
                description=desc,
                category=category,
                command=lambda t=title: self.show_toast(t, "Card visual clicado. Função real ainda não conectada.", "info"),
                enabled=enabled,
            ).grid(row=row, column=col, sticky="nsew", padx=8, pady=8)

        EmptyState(
            root,
            icon=data["icon"],
            title=f"{data['title']} ainda está em modo visual",
            message="Os componentes já funcionam, mas o processamento real será conectado nas próximas etapas da migração.",
            primary_label="Voltar ao Dashboard",
            primary_command=lambda: self.show_section("dashboard"),
            secondary_label="Toast de teste",
            secondary_command=lambda: self.show_toast("Teste", "Toast funcionando nesta seção.", "success"),
        ).grid(row=2, column=0, columnspan=3, sticky="nsew", padx=8, pady=(18, 8))

    def _get_placeholder_cards(self, section_id: str):
        if section_id == "audio":
            return [
                ("🎧", "Juntar áudios", "Une arquivos em um único áudio final.", "Áudio", True),
                ("✂", "Cortar áudio", "Divide áudio em partes iguais.", "Áudio", True),
                ("🔊", "Extrair áudio", "Extrai áudio de vídeo.", "Mídia", True),
            ]
        if section_id == "video":
            return [
                ("🎬", "Juntar vídeos", "Combina vídeos em sequência final.", "Vídeo", True),
                ("🔊", "Extrair áudio dos vídeos", "Redirecionará para Áudio.", "Mídia", True),
                ("🗜", "Comprimir vídeo", "Planejado para versão futura.", "Futuro", False),
            ]
        if section_id == "folders":
            return [
                ("🗂", "Gerar estrutura", "Cria árvore e relatórios de pastas.", "Arquivos", True),
                ("📄", "Listar arquivos", "Exporta lista simples de arquivos.", "Arquivos", True),
                ("📊", "Resumo da pasta", "Cards com totais e estatísticas.", "Arquivos", True),
            ]
        if section_id == "markdown":
            return [
                ("📝", "Juntar Markdown/TXT", "Une arquivos com separadores.", "Próxima tela", True),
                ("🔎", "Fazer varredura", "Busca MD/TXT em pastas e subpastas.", "Próxima tela", True),
                ("👁", "Prévia da união", "Planejado para versão futura.", "Futuro", False),
            ]
        if section_id == "settings":
            return [
                ("🎨", "Visual Neo", "Fundo escuro e azul fixos.", "Config", True),
                ("⚙", "FFmpeg", "Teste e caminho do FFmpeg.", "Config", True),
                ("📦", "Dependências", "Verificar bibliotecas do app.", "Config", True),
            ]
        return []

    # ------------------------------------------------------------------
    # Demonstrações das microinterações/componentes
    # ------------------------------------------------------------------
    def show_toast(self, title: str, message: str, variant: str = "success") -> None:
        for child in self.toast_layer.winfo_children():
            child.destroy()
        self.toast_layer.grid(row=1, column=0, sticky="se", padx=28, pady=28)
        self.toast_layer.lift()

        def hide_if_empty() -> None:
            try:
                if not self.toast_layer.winfo_children():
                    self.toast_layer.grid_remove()
            except tk.TclError:
                pass

        toast = ToastMessage(self.toast_layer, title=title, message=message, variant=variant, on_close=hide_if_empty)
        toast.grid(row=0, column=0, sticky="se")
        toast.lift()

    def _flash_status(self, text: str) -> None:
        self.status_text.configure(text=text)
        self.status_progress.set(0.18)
        self.after(900, lambda: self.status_progress.set(0))

    def _on_demo_table_select(self, selected: List[str]) -> None:
        count = len(selected)
        if count:
            self.status_text.configure(text=f"{count} arquivo(s) selecionado(s) na FileTable.")
        else:
            self.status_text.configure(text="Nenhum arquivo selecionado na FileTable.")

    def _add_demo_table_row(self) -> None:
        index = len(self.demo_table.tree.get_children()) + 1
        fake_files = [
            ("TXT", "observacoes.txt", "12 KB", "C:/Projeto/Textos"),
            ("M4A", "audio_extraido.m4a", "14 MB", "C:/Projeto/Saidas"),
            ("XLSX", "estrutura_pastas.xlsx", "52 KB", "C:/Projeto/Relatorios"),
            ("MD", "dossie_evento.md", "88 KB", "C:/Projeto/Dossies"),
        ]
        kind, name, size, folder = fake_files[index % len(fake_files)]
        self.demo_table.add_item((f"{index:03d}", name, kind, size, folder, "Pronto"))
        self.show_toast("Arquivo visual adicionado", f"{name} entrou na FileTable.", "success")

    def _start_progress_demo(self) -> None:
        if self.progress_job is not None:
            return
        self.demo_progress_value = 0.0
        self.progress_panel.reset_success_color()
        self.progress_panel.set_progress(0, "Iniciando simulação visual...")
        self.status_text.configure(text="Simulando ProgressPanel...")
        self._run_progress_step()

    def _run_progress_step(self) -> None:
        self.demo_progress_value += 0.08
        if self.demo_progress_value >= 1:
            self.progress_panel.complete("Concluído. ProgressPanel funcionando.")
            self.status_progress.set(1)
            self.status_text.configure(text="Simulação concluída.")
            self.show_toast("Progresso concluído", "A barra de progresso moderna chegou a 100%.", "success")
            self.progress_job = None
            self.after(1200, lambda: self.status_progress.set(0))
            return
        percent = int(self.demo_progress_value * 100)
        self.progress_panel.set_progress(self.demo_progress_value, f"Processando etapa visual... {percent}%")
        self.status_progress.set(self.demo_progress_value)
        self.progress_job = self.after(160, self._run_progress_step)


if __name__ == "__main__":
    app = KToolsNeoApp()
    app.mainloop()
