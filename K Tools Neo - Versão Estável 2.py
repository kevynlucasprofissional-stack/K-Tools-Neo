"""
K-Tools Neo v0.5.2 - Hotfix de Robustez

Esta versão consolida o shell visual em CustomTkinter, componentes reutilizáveis e telas funcionais de Markdown/TXT, Áudio, Vídeo, Arquivos/Pastas, PDF/Imagens, JSON e Configurações:
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
- Tela Configurações funcional para FFmpeg, dependências, saída, logs e comportamento.

Importante:
- As telas Markdown/TXT, Áudio, Vídeo, Arquivos/Pastas e Configurações já executam tarefas reais.
- O layout usa grid como padrão. Não há mistura de pack() e grid() no mesmo container.
"""

from __future__ import annotations

import importlib
import csv
import json
import copy
import subprocess
import sys
import tkinter as tk
import threading
import re
import os
import shutil
import tempfile
import math
import warnings
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

APP_VERSION = "0.5.2"

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
    ("pypdf", "pypdf", "PDFs: juntar e dividir"),
    ("PIL", "Pillow", "Imagens: PDF e WebP/PNG"),
    ("cryptography", "cryptography", "PDFs criptografados/AES"),
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
MAX_IMAGE_TOTAL_PIXELS = 80_000_000
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".mpeg", ".mpg", ".m4v"}
PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
WEBP_EXTENSIONS = {".webp"}
DOCUMENT_SPLIT_EXTENSIONS = {".md", ".txt", ".pdf"}


def get_ffmpeg_exe() -> str:
    """Localiza FFmpeg no sistema ou via imageio-ffmpeg, instalando sob demanda."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    imageio_ffmpeg = ensure_package("imageio_ffmpeg", "imageio-ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_ffprobe_exe() -> Optional[str]:
    """Localiza FFprobe quando ele estiver disponível junto do FFmpeg.

    Algumas instalações via imageio-ffmpeg trazem apenas o executável do ffmpeg.
    Por isso o app usa ffprobe quando possível e mantém fallback via ffmpeg.
    """
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    try:
        ffmpeg_path = Path(get_ffmpeg_exe())
        exe_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
        candidate = ffmpeg_path.with_name(exe_name)
        if candidate.exists():
            return str(candidate)
    except Exception:
        pass
    return None


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


def run_ffprobe(args: Sequence[str]) -> Optional[subprocess.CompletedProcess]:
    """Executa FFprobe quando disponível. Retorna None se não houver ffprobe."""
    ffprobe = get_ffprobe_exe()
    if not ffprobe:
        return None
    command = [ffprobe, *map(str, args)]
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


def temp_output_path_for(output_path: Path) -> Path:
    """Cria um caminho temporário na mesma pasta e com a mesma extensão do destino."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{output_path.stem}_ktools_",
        suffix=output_path.suffix,
        dir=str(output_path.parent),
    )
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        temp_path.unlink(missing_ok=True)
    except TypeError:
        if temp_path.exists():
            temp_path.unlink()
    return temp_path


def replace_temp_output(temp_path: Path, output_path: Path) -> None:
    """Move saída temporária para o destino final de forma atômica quando possível."""
    temp_path = Path(temp_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(temp_path), str(output_path))


def cleanup_partial_output(path: Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except TypeError:
        try:
            if Path(path).exists():
                Path(path).unlink()
        except Exception:
            pass
    except Exception:
        pass


def _safe_resolved_key(path: Path) -> str:
    """Chave normalizada para comparar caminhos mesmo quando o destino ainda não existe."""
    path = Path(path)
    try:
        return str(path.resolve()).lower()
    except Exception:
        try:
            return str(path.absolute()).lower()
        except Exception:
            return str(path).lower()


def ensure_output_not_in_inputs(output_path: Path, input_paths: Sequence[Path], description: str = "arquivo final") -> None:
    """Evita sobrescrever um arquivo de entrada com o resultado final."""
    output_key = _safe_resolved_key(Path(output_path))
    input_keys = {_safe_resolved_key(Path(item)) for item in input_paths}
    if output_key in input_keys:
        raise ValueError(f"O {description} não pode ser um dos arquivos de entrada. Escolha outro nome ou outra pasta de saída.")


def atomic_write_text_file(output_path: Path, content: str, encoding: str = "utf-8", newline: str = "\n") -> None:
    """Escreve texto em temporário na mesma pasta e substitui o destino só após sucesso."""
    output_path = Path(output_path)
    tmp_path = temp_output_path_for(output_path)
    try:
        tmp_path.write_text(content, encoding=encoding, newline=newline)
        replace_temp_output(tmp_path, output_path)
    except Exception:
        cleanup_partial_output(tmp_path)
        raise


def image_pixel_count(width: int, height: int) -> int:
    try:
        return int(width) * int(height)
    except Exception:
        return MAX_IMAGE_TOTAL_PIXELS + 1


def validate_image_size_or_raise(image_path: Path, size: Tuple[int, int]) -> None:
    width, height = size
    pixels = image_pixel_count(width, height)
    if width <= 0 or height <= 0:
        raise ValueError(f"A imagem '{image_path.name}' tem dimensões inválidas.")
    if pixels > MAX_IMAGE_TOTAL_PIXELS:
        raise ValueError(
            f"A imagem '{image_path.name}' é grande demais para processamento seguro "
            f"({width}x{height}, {pixels:,} pixels). Reduza a resolução e tente novamente."
        )


def configure_pillow_safety(Image) -> Tuple[type, type]:
    """Configura Pillow para tratar decompression bomb como erro amigável."""
    try:
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_TOTAL_PIXELS
    except Exception:
        pass
    warning_cls = getattr(Image, "DecompressionBombWarning", Warning)
    error_cls = getattr(Image, "DecompressionBombError", RuntimeError)
    return warning_cls, error_cls


def image_decompression_message(image_path: Path) -> str:
    return (
        f"A imagem '{image_path.name}' foi bloqueada por segurança porque é grande demais "
        "ou parece uma decompression bomb. Reduza a resolução/exporte novamente a imagem e tente outra vez."
    )


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
    ensure_output_not_in_inputs(output_file, files, "áudio final")
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
        temp_out = temp_output_path_for(output_file)
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            *audio_codec_args(output_file),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível juntar os áudios."))
        replace_temp_output(temp_out, output_file)
        if progress_callback:
            progress_callback(1.0, "Áudio final gerado com sucesso.")
    return output_file


def get_media_duration_seconds(path: Path) -> float:
    """Obtém duração com ffprobe quando possível e fallback via ffmpeg."""
    path = Path(path)
    probe = run_ffprobe(["-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)])
    if probe and probe.returncode == 0:
        value = (probe.stdout or "").strip().splitlines()
        if value:
            try:
                duration = float(value[0])
                if duration > 0:
                    return duration
            except ValueError:
                pass
    result = run_ffmpeg(["-i", str(path)])
    output = (result.stderr or "") + "\n" + (result.stdout or "")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not match:
        raise RuntimeError("Não foi possível identificar a duração do arquivo com FFmpeg.")
    hours, minutes, seconds = match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    if duration <= 0:
        raise RuntimeError("A duração do arquivo é inválida ou igual a zero.")
    return duration


def media_has_audio_stream(path: Path) -> bool:
    """Verifica se o arquivo possui uma faixa de áudio antes de tentar extrair/convertê-la."""
    path = Path(path)
    probe = run_ffprobe(["-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)])
    if probe is not None:
        return probe.returncode == 0 and bool((probe.stdout or "").strip())
    # Fallback quando não há ffprobe: usa a leitura de cabeçalho do ffmpeg.
    result = run_ffmpeg(["-i", str(path)])
    output = f"{result.stderr or ''}\n{result.stdout or ''}"
    return bool(re.search(r"Stream #\d+:\d+.*Audio:", output, flags=re.IGNORECASE))


def validate_audio_source(path: Path, *, label: str = "arquivo") -> None:
    path = Path(path)
    if not path.exists():
        raise ValueError(f"O {label} não existe: {path}")
    if not media_has_audio_stream(path):
        raise ValueError(f"O {label} não possui faixa de áudio detectável: {path.name}")


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
    validate_audio_source(input_file, label="arquivo de áudio")
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
        out = safe_unique_path(output_folder / f"{input_file.stem}_parte_{index:02d}_de_{parts:02d}.{fmt}")
        temp_out = temp_output_path_for(out)
        if progress_callback:
            progress_callback((index - 1) / parts, f"Gerando parte {index} de {parts}...")
        result = run_ffmpeg([
            "-y",
            "-i", str(input_file),
            "-ss", f"{start:.3f}",
            "-t", f"{current_duration:.3f}",
            "-vn",
            *audio_codec_args(out),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            raise RuntimeError(ffmpeg_error_message(result, f"Não foi possível gerar a parte {index}."))
        replace_temp_output(temp_out, out)
        outputs.append(out)
    if progress_callback:
        progress_callback(1.0, "Áudio dividido com sucesso.")
    return outputs


def audio_codec_args_with_bitrate(output_path: Path, bitrate: str = "Automático") -> List[str]:
    """Define codec de saída e aplica bitrate quando fizer sentido."""
    bitrate = (bitrate or "Automático").strip()
    ext = Path(output_path).suffix.lower()
    if bitrate and bitrate.lower() != "automático":
        if ext == ".mp3":
            return ["-c:a", "libmp3lame", "-b:a", bitrate]
        if ext in {".m4a", ".aac"}:
            return ["-c:a", "aac", "-b:a", bitrate]
        if ext == ".ogg":
            return ["-c:a", "libvorbis", "-b:a", bitrate]
    return audio_codec_args(Path(output_path))


def parse_timestamp_to_seconds(value: str) -> float:
    """Aceita segundos, MM:SS ou HH:MM:SS(.mmm) e retorna segundos.

    Valida minutos/segundos para evitar entradas confusas como 01:99.
    """
    raw = (value or "").strip()
    if not raw:
        raise ValueError("Informe um tempo válido, como 90, 01:30 ou 00:01:30.")
    raw = raw.replace(",", ".")
    if re.fullmatch(r"\d+(?:\.\d+)?", raw):
        seconds = float(raw)
    else:
        parts = raw.split(":")
        if not 2 <= len(parts) <= 3:
            raise ValueError(f"Tempo inválido: {value}")
        try:
            parts_f = [float(p) for p in parts]
        except ValueError as exc:
            raise ValueError(f"Tempo inválido: {value}") from exc
        if len(parts_f) == 2:
            minutes, secs = parts_f
            if minutes < 0 or not (0 <= secs < 60):
                raise ValueError(f"Tempo inválido: {value}. Use MM:SS com segundos entre 0 e 59.")
            seconds = minutes * 60 + secs
        else:
            hours, minutes, secs = parts_f
            if hours < 0 or not (0 <= minutes < 60) or not (0 <= secs < 60):
                raise ValueError(f"Tempo inválido: {value}. Use HH:MM:SS com minutos e segundos entre 0 e 59.")
            seconds = hours * 3600 + minutes * 60 + secs
    if seconds < 0:
        raise ValueError("O tempo não pode ser negativo.")
    return seconds

def format_seconds_for_ffmpeg(seconds: float) -> str:
    return f"{max(0, seconds):.3f}"


def parse_cut_points(value: str) -> List[float]:
    """Lê pontos de corte separados por vírgula, ponto e vírgula ou quebra de linha."""
    raw_items = re.split(r"[;\n,]+", value or "")
    points = []
    for raw in raw_items:
        raw = raw.strip()
        if not raw:
            continue
        points.append(parse_timestamp_to_seconds(raw))
    # Remove duplicatas preservando ordenação numérica.
    unique = sorted({round(p, 3) for p in points})
    return unique


def convert_audio_files_batch(
    input_files: Sequence[Path],
    output_folder: Path,
    output_format: str,
    bitrate: str = "Automático",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[List[Path], List[str]]:
    """Converte vários arquivos de áudio, ignorando itens incompatíveis sem abortar o lote inteiro."""
    files = [Path(p) for p in input_files if is_supported_audio_file(Path(p))]
    if not files:
        raise ValueError("Nenhum arquivo de áudio compatível foi selecionado.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    fmt = (output_format or "m4a").lower().lstrip(".")
    reserved: set[str] = set()
    outputs: List[Path] = []
    skipped: List[str] = []
    for index, src in enumerate(files, start=1):
        if progress_callback:
            progress_callback((index - 1) / len(files), f"Convertendo {index} de {len(files)}: {src.name}")
        try:
            validate_audio_source(src, label="arquivo de áudio")
        except Exception as exc:
            skipped.append(f"{src.name} — {exc}")
            continue
        out = safe_unique_path(output_folder / f"{src.stem}.{fmt}", reserved)
        temp_out = temp_output_path_for(out)
        result = run_ffmpeg([
            "-y",
            "-i", str(src),
            "-vn",
            *audio_codec_args_with_bitrate(out, bitrate),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            skipped.append(f"{src.name} — falha na conversão")
            continue
        replace_temp_output(temp_out, out)
        outputs.append(out)
    if not outputs:
        detail = "\n".join(skipped[:5])
        raise RuntimeError("Nenhum áudio foi convertido. Verifique se os arquivos têm faixa de áudio e se o formato é compatível." + (f"\n\nItens ignorados:\n{detail}" if detail else ""))
    if progress_callback:
        msg = f"{len(outputs)} áudio(s) convertido(s)."
        if skipped:
            msg += f" {len(skipped)} item(ns) ignorado(s)."
        progress_callback(1.0, msg)
    return outputs, skipped


def extract_audio_batch_from_videos(
    video_files: Sequence[Path],
    output_folder: Path,
    output_format: str,
    bitrate: str = "Automático",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[List[Path], List[str]]:
    """Extrai áudio de vários vídeos, validando faixa de áudio antes de processar."""
    files = [Path(p) for p in video_files if is_supported_video_file(Path(p))]
    if not files:
        raise ValueError("Nenhum vídeo compatível foi selecionado.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    fmt = (output_format or "m4a").lower().lstrip(".")
    reserved: set[str] = set()
    outputs: List[Path] = []
    skipped: List[str] = []
    for index, src in enumerate(files, start=1):
        if progress_callback:
            progress_callback((index - 1) / len(files), f"Extraindo áudio {index} de {len(files)}: {src.name}")
        if not media_has_audio_stream(src):
            skipped.append(f"{src.name} — sem faixa de áudio detectável")
            continue
        out = safe_unique_path(output_folder / f"{src.stem}_audio.{fmt}", reserved)
        temp_out = temp_output_path_for(out)
        result = run_ffmpeg([
            "-y",
            "-i", str(src),
            "-vn",
            *audio_codec_args_with_bitrate(out, bitrate),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            skipped.append(f"{src.name} — falha na extração")
            continue
        replace_temp_output(temp_out, out)
        outputs.append(out)
    if not outputs:
        detail = "\n".join(skipped[:5])
        raise RuntimeError("Não foi possível extrair áudio de nenhum vídeo. Eles podem estar sem faixa de áudio, corrompidos ou em formato incompatível." + (f"\n\nItens ignorados:\n{detail}" if detail else ""))
    if progress_callback:
        msg = f"{len(outputs)} áudio(s) extraído(s)."
        if skipped:
            msg += f" {len(skipped)} vídeo(s) ignorado(s)."
        progress_callback(1.0, msg)
    return outputs, skipped


def cut_audio_by_time_range(
    input_file: Path,
    output_file: Path,
    start_seconds: float,
    end_seconds: Optional[float],
    bitrate: str = "Automático",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Extrai um trecho de áudio por início e fim."""
    input_file = Path(input_file)
    output_file = Path(output_file)
    if not is_supported_audio_file(input_file):
        raise ValueError("Selecione um arquivo de áudio compatível.")
    if input_file.resolve() == output_file.resolve():
        raise ValueError("O arquivo final não pode ser o mesmo arquivo de entrada.")
    validate_audio_source(input_file, label="arquivo de áudio")
    duration = get_media_duration_seconds(input_file)
    if start_seconds >= duration:
        raise ValueError(f"O tempo inicial precisa ser menor que a duração do áudio ({duration:.2f}s).")
    if end_seconds is None:
        end_seconds = duration
    if end_seconds <= start_seconds:
        raise ValueError("O tempo final precisa ser maior que o tempo inicial.")
    end_seconds = min(end_seconds, duration)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if progress_callback:
        progress_callback(0.25, "Cortando trecho de áudio...")
    temp_out = temp_output_path_for(output_file)
    result = run_ffmpeg([
        "-y",
        "-ss", format_seconds_for_ffmpeg(start_seconds),
        "-i", str(input_file),
        "-t", format_seconds_for_ffmpeg(end_seconds - start_seconds),
        "-vn",
        *audio_codec_args_with_bitrate(output_file, bitrate),
        str(temp_out),
    ])
    if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
        cleanup_partial_output(temp_out)
        raise RuntimeError(ffmpeg_error_message(result, "Não foi possível cortar o trecho de áudio."))
    replace_temp_output(temp_out, output_file)
    if progress_callback:
        progress_callback(1.0, "Trecho de áudio gerado com sucesso.")
    return output_file


def split_audio_by_cut_points(
    input_file: Path,
    output_folder: Path,
    cut_points: Sequence[float],
    output_format: str,
    bitrate: str = "Automático",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """Divide áudio usando pontos de corte informados pelo usuário."""
    input_file = Path(input_file)
    if not is_supported_audio_file(input_file):
        raise ValueError("Selecione um arquivo de áudio compatível.")
    validate_audio_source(input_file, label="arquivo de áudio")
    duration = get_media_duration_seconds(input_file)
    points = sorted({round(p, 3) for p in cut_points if 0 < p < duration})
    if not points:
        raise ValueError(f"Informe pelo menos um ponto de corte válido dentro da duração do áudio ({duration:.2f}s).")
    boundaries = [0.0, *points, duration]
    segments = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1) if boundaries[i + 1] > boundaries[i]]
    if not segments:
        raise ValueError("Os pontos informados não geraram trechos válidos.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    fmt = (output_format or "m4a").lower().lstrip(".")
    reserved: set[str] = set()
    outputs: List[Path] = []
    total = len(segments)
    for index, (start, end) in enumerate(segments, start=1):
        if progress_callback:
            progress_callback((index - 1) / total, f"Gerando trecho {index} de {total}...")
        out = safe_unique_path(output_folder / f"{input_file.stem}_trecho_{index:02d}_de_{total:02d}.{fmt}", reserved)
        temp_out = temp_output_path_for(out)
        result = run_ffmpeg([
            "-y",
            "-ss", format_seconds_for_ffmpeg(start),
            "-i", str(input_file),
            "-t", format_seconds_for_ffmpeg(end - start),
            "-vn",
            *audio_codec_args_with_bitrate(out, bitrate),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            raise RuntimeError(ffmpeg_error_message(result, f"Não foi possível gerar o trecho {index}."))
        replace_temp_output(temp_out, out)
        outputs.append(out)
    if progress_callback:
        progress_callback(1.0, f"{len(outputs)} trecho(s) gerado(s) com sucesso.")
    return outputs


def extract_audio_from_video(
    video_file: Path,
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    video_file = Path(video_file)
    if not is_supported_video_file(video_file):
        raise ValueError("Selecione um arquivo de vídeo compatível.")
    if not media_has_audio_stream(video_file):
        raise ValueError("Este vídeo não possui faixa de áudio detectável.")
    output_file = Path(output_file)
    ensure_output_not_in_inputs(output_file, [video_file], "áudio final")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    if progress_callback:
        progress_callback(0.15, "Extraindo áudio do vídeo...")
    temp_out = temp_output_path_for(output_file)
    result = run_ffmpeg([
        "-y",
        "-i", str(video_file),
        "-vn",
        *audio_codec_args(output_file),
        str(temp_out),
    ])
    if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
        cleanup_partial_output(temp_out)
        raise RuntimeError(ffmpeg_error_message(result, "Não foi possível extrair áudio deste vídeo."))
    replace_temp_output(temp_out, output_file)
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
    ensure_output_not_in_inputs(output_file, files, "áudio final")
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
        temp_out = temp_output_path_for(output_file)
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            *audio_codec_args(output_file),
            str(temp_out),
        ])
        if result.returncode != 0 or not temp_out.exists() or temp_out.stat().st_size == 0:
            cleanup_partial_output(temp_out)
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível unir os áudios extraídos dos vídeos."))
        replace_temp_output(temp_out, output_file)
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

    ensure_output_not_in_inputs(output_file, files, "vídeo final")

    with tempfile.TemporaryDirectory(prefix="ktools_video_join_") as temp_dir:
        temp_path = Path(temp_dir)
        concat_list = temp_path / "concat_videos.txt"
        concat_list.write_text("".join(concat_file_line(p) for p in files), encoding="utf-8")

        if progress_callback:
            progress_callback(0.05, "Tentando juntar vídeos no modo rápido...")
        fast_temp = temp_output_path_for(output_file)
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            "-movflags", "+faststart",
            str(fast_temp),
        ])
        if result.returncode == 0 and fast_temp.exists() and safe_stat_size(fast_temp) > 0:
            replace_temp_output(fast_temp, output_file)
            if progress_callback:
                progress_callback(1.0, "Vídeo final gerado com sucesso.")
            return output_file
        cleanup_partial_output(fast_temp)

        # O modo rápido pode falhar quando os vídeos têm codecs/resoluções diferentes.
        # A rota compatível abaixo mantém a saída final protegida por arquivo temporário.

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
        final_temp = temp_output_path_for(output_file)
        result = run_ffmpeg([
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_normalized),
            "-c", "copy",
            "-movflags", "+faststart",
            str(final_temp),
        ])
        if result.returncode != 0 or not final_temp.exists() or safe_stat_size(final_temp) == 0:
            cleanup_partial_output(final_temp)
            raise RuntimeError(ffmpeg_error_message(result, "Não foi possível juntar os vídeos."))
        replace_temp_output(final_temp, output_file)
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
        if not p.exists():
            raise ValueError(f"Arquivo não encontrado: {p}")
        if not p.is_file():
            raise ValueError(f"O caminho não é um arquivo: {p}")
        if not is_supported_text_file(p):
            raise ValueError(f"Arquivo inválido ou incompatível: {p}")
        normalized_inputs.append(p)

    output_file = Path(output_file)
    if output_file.suffix.lower() not in TEXT_EXTENSIONS:
        output_file = output_file.with_suffix(".md")

    ensure_output_not_in_inputs(output_file, normalized_inputs, "arquivo final")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    total = len(normalized_inputs)

    temp_out = temp_output_path_for(output_file)
    try:
        with temp_out.open("w", encoding="utf-8", newline="\n") as out:
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
        replace_temp_output(temp_out, output_file)
    except Exception:
        cleanup_partial_output(temp_out)
        raise

    return output_file



# -----------------------------------------------------------------------------
# Utilidades funcionais da tela PDF/Imagens
# -----------------------------------------------------------------------------

def is_supported_pdf_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in PDF_EXTENSIONS
    except OSError:
        return False


def is_supported_image_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    except OSError:
        return False


def is_supported_webp_file(path: Path) -> bool:
    try:
        return path.is_file() and path.suffix.lower() in WEBP_EXTENSIONS
    except OSError:
        return False


def ensure_pdf_extension(path: Path) -> Path:
    path = Path(path)
    return path.with_suffix(".pdf") if path.suffix.lower() != ".pdf" else path


def safe_unique_path(path: Path, reserved: Optional[set[str]] = None) -> Path:
    """Retorna um caminho livre, evitando sobrescrita acidental e colisões de nomes em lote."""
    path = Path(path)
    reserved = reserved if reserved is not None else set()
    candidate = path
    index = 1
    while True:
        key = str(candidate.resolve() if candidate.exists() else candidate.absolute()).lower()
        if key not in reserved and not candidate.exists():
            reserved.add(key)
            return candidate
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        index += 1


def atomic_replace_file(temp_path: Path, output_path: Path) -> None:
    """Substitui o arquivo final só no fim, reduzindo risco de saída corrompida se a tarefa falhar."""
    temp_path = Path(temp_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    os.replace(str(temp_path), str(output_path))


def validate_pdf_path_or_raise(pdf_path: Path) -> None:
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise ValueError(f"O PDF não existe: {pdf_path}")
    if pdf_path.is_dir():
        raise ValueError(f"O caminho informado é uma pasta, não um PDF: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Extensão inválida para PDF: {pdf_path.name}")
    if safe_stat_size(pdf_path) == 0:
        raise ValueError(f"O PDF '{pdf_path.name}' está vazio.")


def open_pdf_reader_checked(pdf_path: Path):
    """Abre um PDF com mensagens claras para casos protegidos, criptografados ou corrompidos."""
    pdf_path = Path(pdf_path)
    validate_pdf_path_or_raise(pdf_path)
    pypdf = ensure_package("pypdf", "pypdf")
    PdfReader = pypdf.PdfReader
    try:
        reader = PdfReader(str(pdf_path), strict=False)
    except FileNotFoundError as exc:
        raise RuntimeError(f"O PDF '{pdf_path.name}' não foi encontrado.") from exc
    except PermissionError as exc:
        raise RuntimeError(f"Não foi possível abrir o PDF '{pdf_path.name}'. Verifique se ele está aberto em outro programa ou sem permissão de leitura.") from exc
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível abrir o PDF '{pdf_path.name}'.\n\n"
            "O arquivo pode estar corrompido, incompleto ou salvo em um formato de PDF incompatível."
        ) from exc

    if getattr(reader, "is_encrypted", False):
        try:
            ensure_package("cryptography", "cryptography")
        except Exception:
            pass
        try:
            decrypt_result = reader.decrypt("")
        except Exception as exc:
            raise RuntimeError(
                f"O PDF '{pdf_path.name}' está protegido por senha ou usa criptografia não suportada nesta instalação.\n\n"
                "Remova a senha/proteção no leitor de PDF e tente processar novamente."
            ) from exc
        if not decrypt_result:
            raise RuntimeError(
                f"O PDF '{pdf_path.name}' exige senha.\n\n"
                "O K-Tools não quebra senha nem contorna proteção. Remova a senha/proteção antes de tentar novamente."
            )

    try:
        page_count = len(reader.pages)
    except Exception as exc:
        raise RuntimeError(
            f"Não foi possível ler as páginas do PDF '{pdf_path.name}'.\n\n"
            "Ele pode estar protegido, parcialmente corrompido ou salvo em uma estrutura incompatível."
        ) from exc

    if page_count <= 0:
        raise RuntimeError(f"O PDF '{pdf_path.name}' não possui páginas legíveis.")
    return reader, page_count


def write_pdf_writer_atomic(writer, output_file: Path) -> None:
    """Escreve um PdfWriter em arquivo temporário e só então move para o destino final."""
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{output_file.stem}_", suffix=".tmp", dir=str(output_file.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with tmp_path.open("wb") as fh:
            writer.write(fh)
        atomic_replace_file(tmp_path, output_file)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def merge_pdf_files(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Junta PDFs usando pypdf, com validação para PDFs protegidos/corrompidos."""
    if not input_files:
        raise ValueError("Nenhum PDF foi selecionado.")
    files: List[Path] = []
    for item in input_files:
        pdf_path = Path(item)
        validate_pdf_path_or_raise(pdf_path)
        files.append(pdf_path)
    output_file = ensure_pdf_extension(Path(output_file))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    ensure_output_not_in_inputs(output_file, files, "PDF final")

    pypdf = ensure_package("pypdf", "pypdf")
    PdfWriter = pypdf.PdfWriter
    writer = PdfWriter()
    total = len(files)
    total_pages = 0
    try:
        for index, pdf_path in enumerate(files, start=1):
            if progress_callback:
                progress_callback((index - 1) / max(total, 1), f"Validando PDF {index} de {total}: {pdf_path.name}")
            reader, page_count = open_pdf_reader_checked(pdf_path)
            try:
                for page_number, page in enumerate(reader.pages, start=1):
                    try:
                        writer.add_page(page)
                    except Exception as page_exc:
                        raise RuntimeError(
                            f"Não foi possível copiar a página {page_number} do PDF '{pdf_path.name}'.\n\n"
                            "O arquivo pode estar protegido, corrompido ou ter recursos incompatíveis."
                        ) from page_exc
                total_pages += page_count
            except RuntimeError:
                raise
            except Exception as exc:
                raise RuntimeError(
                    f"Não foi possível copiar as páginas do PDF '{pdf_path.name}'.\n\n"
                    "O arquivo pode estar protegido, corrompido ou ter recursos incompatíveis."
                ) from exc
        if total_pages <= 0:
            raise RuntimeError("Nenhuma página legível foi encontrada nos PDFs selecionados.")
        if progress_callback:
            progress_callback(0.95, "Salvando PDF final...")
        write_pdf_writer_atomic(writer, output_file)
    finally:
        try:
            writer.close()
        except Exception:
            pass
    if progress_callback:
        progress_callback(1.0, f"PDF final gerado com sucesso ({total_pages} página(s)).")
    return output_file


def images_to_pdf(
    input_files: Sequence[Path],
    output_file: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Path:
    """Gera um PDF com uma imagem por página, normalizando orientação e transparência."""
    files = [Path(p) for p in input_files if is_supported_image_file(Path(p))]
    if not files:
        raise ValueError("Nenhuma imagem compatível foi selecionada.")
    output_file = ensure_pdf_extension(Path(output_file))
    output_file.parent.mkdir(parents=True, exist_ok=True)
    Image = ensure_package("PIL.Image", "Pillow")
    ImageOps = ensure_package("PIL.ImageOps", "Pillow")
    warning_cls, error_cls = configure_pillow_safety(Image)

    pages = []
    total = len(files)
    tmp_path = temp_output_path_for(output_file)
    try:
        for index, image_path in enumerate(files, start=1):
            if progress_callback:
                progress_callback((index - 1) / max(total, 1), f"Preparando imagem {index} de {total}: {image_path.name}")
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", warning_cls)
                    with Image.open(image_path) as opened:
                        validate_image_size_or_raise(image_path, opened.size)
                        animated = bool(getattr(opened, "is_animated", False))
                        try:
                            opened.seek(0)
                        except Exception:
                            pass
                        if animated and progress_callback:
                            progress_callback((index - 1) / max(total, 1), f"{image_path.name}: imagem animada detectada; usando apenas o primeiro frame.")
                        img = ImageOps.exif_transpose(opened)
                        validate_image_size_or_raise(image_path, img.size)
                        img.load()
                        # PDFs não preservam alpha de forma confiável entre visualizadores; compõe alpha em fundo branco.
                        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                            rgba = img.convert("RGBA")
                            background = Image.new("RGB", rgba.size, (255, 255, 255))
                            background.paste(rgba, mask=rgba.split()[-1])
                            img = background
                        else:
                            img = img.convert("RGB")
                        pages.append(img.copy())
            except (warning_cls, error_cls) as exc:
                raise RuntimeError(image_decompression_message(image_path)) from exc
            except ValueError:
                raise
            except Exception as exc:
                raise RuntimeError(
                    f"Não foi possível abrir a imagem '{image_path.name}'.\n\n"
                    "O arquivo pode estar corrompido, em formato incompatível ou sem permissão de leitura."
                ) from exc
        if not pages:
            raise RuntimeError("Nenhuma imagem válida foi preparada para gerar o PDF.")
        if progress_callback:
            progress_callback(0.95, "Salvando PDF com imagens...")
        first, rest = pages[0], pages[1:]
        first.save(str(tmp_path), "PDF", save_all=True, append_images=rest)
        if not tmp_path.exists() or safe_stat_size(tmp_path) == 0:
            raise RuntimeError("Não foi possível gerar o PDF de imagens.")
        atomic_replace_file(tmp_path, output_file)
    finally:
        for img in pages:
            try:
                img.close()
            except Exception:
                pass
        cleanup_partial_output(tmp_path)
    if progress_callback:
        progress_callback(1.0, "PDF de imagens gerado com sucesso.")
    return output_file


def convert_webp_to_png(
    input_files: Sequence[Path],
    output_folder: Path,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """Converte arquivos WebP para PNG preservando transparência e evitando colisões de nome."""
    files = [Path(p) for p in input_files if is_supported_webp_file(Path(p))]
    if not files:
        raise ValueError("Nenhum arquivo WebP foi selecionado.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    Image = ensure_package("PIL.Image", "Pillow")
    ImageOps = ensure_package("PIL.ImageOps", "Pillow")
    warning_cls, error_cls = configure_pillow_safety(Image)
    outputs: List[Path] = []
    reserved: set[str] = set()
    total = len(files)
    for index, webp_path in enumerate(files, start=1):
        if progress_callback:
            progress_callback((index - 1) / max(total, 1), f"Convertendo WebP {index} de {total}: {webp_path.name}")
        out = safe_unique_path(output_folder / f"{webp_path.stem}.png", reserved)
        temp_out = temp_output_path_for(out)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", warning_cls)
                with Image.open(webp_path) as opened:
                    validate_image_size_or_raise(webp_path, opened.size)
                    animated = bool(getattr(opened, "is_animated", False))
                    try:
                        opened.seek(0)
                    except Exception:
                        pass
                    if animated and progress_callback:
                        progress_callback((index - 1) / max(total, 1), f"{webp_path.name}: WebP animado detectado; usando apenas o primeiro frame.")
                    img = ImageOps.exif_transpose(opened)
                    validate_image_size_or_raise(webp_path, img.size)
                    img.load()
                    # PNG aceita alpha; RGBA preserva transparência real quando existir.
                    if img.mode in ("RGBA", "LA"):
                        img = img.convert("RGBA")
                    elif img.mode == "P" and "transparency" in img.info:
                        img = img.convert("RGBA")
                    elif img.mode not in ("RGB", "L"):
                        img = img.convert("RGBA")
                    img.save(temp_out, "PNG")
            if not temp_out.exists() or safe_stat_size(temp_out) == 0:
                raise RuntimeError(f"Não foi possível gerar o PNG de '{webp_path.name}'.")
            replace_temp_output(temp_out, out)
        except (warning_cls, error_cls) as exc:
            cleanup_partial_output(temp_out)
            raise RuntimeError(image_decompression_message(webp_path)) from exc
        except ValueError:
            cleanup_partial_output(temp_out)
            raise
        except Exception as exc:
            cleanup_partial_output(temp_out)
            raise RuntimeError(
                f"Não foi possível converter '{webp_path.name}'.\n\n"
                "O arquivo pode estar corrompido, não ser um WebP válido ou estar sem permissão de leitura."
            ) from exc
        outputs.append(out)
    if progress_callback:
        progress_callback(1.0, f"{len(outputs)} PNG(s) gerado(s) com sucesso.")
    return outputs


def split_pdf_into_parts(
    input_pdf: Path,
    output_folder: Path,
    parts: int,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[Path]:
    """Divide um PDF em partes equilibradas por páginas, com validação de proteção/corrupção."""
    input_pdf = Path(input_pdf)
    validate_pdf_path_or_raise(input_pdf)
    if parts < 2:
        raise ValueError("O número de partes deve ser pelo menos 2.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    pypdf = ensure_package("pypdf", "pypdf")
    PdfWriter = pypdf.PdfWriter
    reader, total_pages = open_pdf_reader_checked(input_pdf)
    parts = min(parts, total_pages)
    outputs: List[Path] = []
    reserved: set[str] = set()
    base = input_pdf.stem
    start_page = 0
    for index in range(1, parts + 1):
        remaining_pages = total_pages - start_page
        remaining_parts = parts - index + 1
        count = (remaining_pages + remaining_parts - 1) // remaining_parts
        end_page = min(total_pages, start_page + count)
        if progress_callback:
            progress_callback((index - 1) / parts, f"Gerando parte {index} de {parts} — páginas {start_page + 1} a {end_page}")
        writer = PdfWriter()
        try:
            for page_index in range(start_page, end_page):
                writer.add_page(reader.pages[page_index])
        except Exception as exc:
            raise RuntimeError(
                f"Não foi possível copiar páginas da parte {index} do PDF '{input_pdf.name}'.\n\n"
                "O PDF pode estar protegido ou parcialmente corrompido."
            ) from exc
        out = safe_unique_path(output_folder / f"{base}_parte_{index:02d}_de_{parts:02d}.pdf", reserved)
        write_pdf_writer_atomic(writer, out)
        try:
            writer.close()
        except Exception:
            pass
        outputs.append(out)
        start_page = end_page
    if progress_callback:
        progress_callback(1.0, f"PDF dividido em {len(outputs)} parte(s).")
    return outputs


def is_supported_document_split_file(path: Path) -> bool:
    """Aceita .md, .txt e .pdf para a ferramenta Dividir documentos em partes."""
    try:
        return path.is_file() and path.suffix.lower() in DOCUMENT_SPLIT_EXTENSIONS
    except OSError:
        return False


def read_text_document_with_fallback(path: Path) -> Tuple[str, str]:
    """Lê MD/TXT tentando encodings comuns de arquivos do Windows e exports variados."""
    encodings = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
    last_error: Optional[Exception] = None
    for encoding in encodings:
        try:
            return Path(path).read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except Exception as exc:
            raise RuntimeError(
                f"Não foi possível ler '{Path(path).name}'.\n\n"
                "O arquivo pode estar aberto em outro programa ou sem permissão de leitura."
            ) from exc
    raise RuntimeError(
        f"Não foi possível identificar o encoding de '{Path(path).name}'.\n\n"
        "Tente salvar o arquivo como UTF-8 e executar novamente."
    ) from last_error


def split_text_balanced(content: str, parts: int) -> List[str]:
    """Divide texto em partes equilibradas, tentando preservar linhas/parágrafos."""
    if parts < 2:
        raise ValueError("O número de partes deve ser pelo menos 2.")
    if not content:
        raise ValueError("O arquivo de texto está vazio; não há conteúdo para dividir.")

    # Mantém quebras de linha nos blocos. Cada linha vira unidade indivisível simples.
    units = content.splitlines(keepends=True)
    if not units:
        units = [content]
    parts = min(parts, max(1, len(units)))
    total_chars = sum(len(u) for u in units)
    target = max(1, total_chars / parts)

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0
    remaining_parts = parts

    for idx, unit in enumerate(units):
        units_left = len(units) - idx
        current.append(unit)
        current_len += len(unit)
        # Fecha chunk ao atingir alvo, garantindo que ainda restem unidades para as partes restantes.
        if remaining_parts > 1 and current_len >= target and units_left > remaining_parts - 1:
            chunk = "".join(current)
            if chunk.strip():
                chunks.append(chunk)
            current = []
            current_len = 0
            remaining_parts -= 1
            remaining_chars = sum(len(u) for u in units[idx + 1:])
            target = max(1, remaining_chars / remaining_parts) if remaining_parts else target

    tail = "".join(current)
    if tail.strip():
        chunks.append(tail)

    # Evita partes vazias e ajusta se o texto tiver muitas linhas vazias.
    chunks = [chunk for chunk in chunks if chunk.strip()]
    if not chunks:
        raise ValueError("A divisão gerou apenas partes vazias; verifique o conteúdo do arquivo.")
    return chunks


def write_text_document_parts(
    input_file: Path,
    output_folder: Path,
    parts: int,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    reserved: Optional[set[str]] = None,
) -> List[Path]:
    """Divide um arquivo MD/TXT em partes equilibradas e salva com nomes numerados."""
    input_file = Path(input_file)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    content, encoding = read_text_document_with_fallback(input_file)
    chunks = split_text_balanced(content, parts)
    total = len(chunks)
    reserved = reserved if reserved is not None else set()
    outputs: List[Path] = []
    for index, chunk in enumerate(chunks, start=1):
        if progress_callback:
            progress_callback((index - 1) / max(total, 1), f"Salvando {input_file.name} — parte {index} de {total}")
        out = safe_unique_path(output_folder / f"{input_file.stem}_parte_{index:02d}_de_{total:02d}{input_file.suffix.lower()}", reserved)
        tmp = out.with_name(f".{out.stem}_{os.getpid()}.tmp")
        try:
            tmp.write_text(chunk, encoding="utf-8", newline="")
            atomic_replace_file(tmp, out)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass
        outputs.append(out)
    if progress_callback:
        progress_callback(1.0, f"{input_file.name} dividido em {len(outputs)} parte(s).")
    return outputs


def split_document_files_into_parts(
    input_files: Sequence[Path],
    output_folder: Path,
    parts: int,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, object]:
    """Divide .md/.txt por texto e .pdf por páginas, sempre preservando arquivos válidos."""
    files = [Path(p) for p in input_files if is_supported_document_split_file(Path(p))]
    if not files:
        raise ValueError("Nenhum documento compatível foi selecionado. Use arquivos .md, .txt ou .pdf.")
    if parts < 2:
        raise ValueError("O número de partes deve ser pelo menos 2.")
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    outputs: List[Path] = []
    errors: List[str] = []
    reserved: set[str] = set()
    total_files = len(files)
    for file_index, file_path in enumerate(files, start=1):
        base_progress = (file_index - 1) / max(total_files, 1)
        span = 1 / max(total_files, 1)

        def local_cb(value: float, msg: str, base: float = base_progress, sp: float = span) -> None:
            if progress_callback:
                progress_callback(min(1.0, base + max(0.0, min(1.0, value)) * sp), msg)

        try:
            suffix = file_path.suffix.lower()
            if suffix == ".pdf":
                # Usa a lógica robusta já existente: valida PDF protegido/corrompido e salva por páginas.
                result = split_pdf_into_parts(file_path, output_folder, parts, local_cb)
            elif suffix in {".md", ".txt"}:
                result = write_text_document_parts(file_path, output_folder, parts, local_cb, reserved)
            else:
                continue
            outputs.extend(result)
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")

    if not outputs:
        details = "\n".join(errors[:5]) if errors else "Nenhuma parte foi gerada."
        raise RuntimeError(f"Não foi possível dividir os documentos.\n\n{details}")
    if progress_callback:
        progress_callback(1.0, f"Divisão concluída: {len(outputs)} arquivo(s) gerado(s).")
    return {
        "outputs": outputs,
        "errors": errors,
        "input_count": len(files),
        "output_count": len(outputs),
        "output_folder": output_folder,
    }


# -----------------------------------------------------------------------------
# Utilidades funcionais da tela Arquivos/Pastas
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# JSON: análise e divisão semântica
# -----------------------------------------------------------------------------

JSON_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252", "latin-1")
JSON_LARGE_FILE_WARNING_BYTES = 80 * 1024 * 1024


def read_json_file_with_fallback(path: Path) -> object:
    """Lê JSON tentando encodings comuns e retorna objeto Python.

    A função tenta separar claramente três problemas comuns:
    - encoding incompatível;
    - JSON inválido;
    - arquivo inacessível.
    """
    if not path.exists():
        raise ValueError("O arquivo JSON informado não existe.")
    if not path.is_file():
        raise ValueError("O caminho informado não é um arquivo JSON.")

    decode_errors: List[str] = []
    json_errors: List[Tuple[str, json.JSONDecodeError]] = []

    for encoding in JSON_ENCODINGS:
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
            continue
        except OSError as exc:
            raise ValueError(f"Não foi possível abrir o arquivo JSON: {exc}") from exc

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            json_errors.append((encoding, exc))
            continue

    if json_errors:
        encoding, exc = json_errors[0]
        raise ValueError(
            "JSON inválido. "
            f"Erro usando {encoding}: linha {exc.lineno}, coluna {exc.colno}. {exc.msg}."
        ) from exc

    detail = "; ".join(decode_errors[:3]) if decode_errors else "encoding não reconhecido"
    raise ValueError(f"Não foi possível ler o arquivo como JSON. Detalhes: {detail}")


def _json_path_label(path: Tuple[object, ...]) -> str:
    if not path:
        return "$"
    label = "$"
    for part in path:
        if isinstance(part, int):
            label += f"[{part}]"
        else:
            safe = str(part).replace("'", "\\'")
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", safe):
                label += f".{safe}"
            else:
                label += f"['{safe}']"
    return label


def _json_path_is_semantic(path: Tuple[object, ...]) -> bool:
    """Aceita raiz ou listas ligadas a chaves de objeto; evita listas dentro de itens isolados."""
    return not any(isinstance(part, int) for part in path)


def find_largest_json_list(data: object) -> Tuple[Tuple[object, ...], List[object]]:
    """Detecta a lista principal preservável.

    Regras:
    - se o JSON raiz for uma lista, ela é a lista principal;
    - se o JSON raiz for um objeto, escolhe a maior lista ligada a chaves de objeto;
    - evita escolher listas internas dentro de um item específico, porque isso costuma gerar
      partes semanticamente confusas.
    """
    if isinstance(data, list):
        return tuple(), data

    candidates: List[Tuple[Tuple[object, ...], List[object]]] = []

    def walk(obj: object, path: Tuple[object, ...]) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                child_path = path + (key,)
                if isinstance(value, list):
                    if _json_path_is_semantic(child_path):
                        candidates.append((child_path, value))
                    for index, item in enumerate(value):
                        if isinstance(item, (dict, list)):
                            walk(item, child_path + (index,))
                elif isinstance(value, dict):
                    walk(value, child_path)
        elif isinstance(obj, list):
            for index, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    walk(item, path + (index,))

    walk(data, tuple())
    if not candidates:
        return tuple(), []

    # Maior lista vence; empate favorece caminho mais curto, normalmente mais "principal".
    candidates.sort(key=lambda pair: (len(pair[1]), -len(pair[0])), reverse=True)
    return candidates[0]


def replace_json_path(data: object, path: Tuple[object, ...], value: object) -> object:
    """Copia o JSON e substitui a lista no caminho detectado por uma fatia."""
    if not path:
        return value
    clone = copy.deepcopy(data)
    cursor = clone
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value
    return clone


def split_list_evenly(items: Sequence[object], parts: int) -> List[List[object]]:
    if parts < 1:
        raise ValueError("O número de partes precisa ser maior que zero.")
    if not items:
        raise ValueError("A lista JSON detectada está vazia; não há itens para dividir.")
    real_parts = min(parts, len(items))
    base = len(items) // real_parts
    remainder = len(items) % real_parts
    chunks: List[List[object]] = []
    start = 0
    for index in range(real_parts):
        size = base + (1 if index < remainder else 0)
        chunk = list(items[start:start + size])
        if chunk:
            chunks.append(chunk)
        start += size
    if not chunks:
        raise ValueError("A divisão resultaria em partes vazias. Ajuste a quantidade de partes.")
    return chunks


def json_bytes_size(obj: object) -> int:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    return len(text.encode("utf-8"))


def _json_item_estimated_size(item: object) -> int:
    # Pequena folga para vírgula, quebras de linha e indentação dentro da lista.
    return len(json.dumps(item, ensure_ascii=False, indent=2).encode("utf-8")) + 4


def _estimate_json_chunk_size(data: object, list_path: Tuple[object, ...], chunk: Sequence[object]) -> int:
    # Estimativa rápida para prévia e divisão por tamanho sem reserializar o documento inteiro
    # a cada item. Para arquivos pequenos, a diferença visual é irrelevante; para arquivos
    # grandes, evita congelamentos e uso excessivo de CPU/memória.
    try:
        empty_overhead = json_bytes_size(replace_json_path(data, list_path, []))
    except Exception:
        empty_overhead = 2
    return empty_overhead + sum(_json_item_estimated_size(item) for item in chunk)


def split_json_by_target_size(data: object, list_path: Tuple[object, ...], items: Sequence[object], target_bytes: int) -> List[List[object]]:
    if target_bytes <= 0:
        raise ValueError("O tamanho aproximado precisa ser maior que zero.")
    if not items:
        raise ValueError("A lista JSON detectada está vazia; não há itens para dividir.")

    try:
        overhead = json_bytes_size(replace_json_path(data, list_path, []))
    except Exception:
        overhead = 2

    chunks: List[List[object]] = []
    current: List[object] = []
    current_size = overhead

    for item in items:
        item_size = _json_item_estimated_size(item)
        if current and current_size + item_size > target_bytes:
            chunks.append(current)
            current = [item]
            current_size = overhead + item_size
        else:
            current.append(item)
            current_size += item_size

    if current:
        chunks.append(current)
    if not chunks:
        raise ValueError("A divisão por tamanho resultaria em partes vazias. Aumente o tamanho aproximado.")
    return chunks


def build_json_output_paths(output_folder: Path, prefix: str, count: int) -> List[Path]:
    safe_prefix = re.sub(r"[^A-Za-z0-9_.\-À-ÿ]+", "_", prefix.strip()).strip("._") or "json_parte"
    width = max(2, len(str(count)))
    return [output_folder / f"{safe_prefix}_parte_{i:0{width}d}_de_{count:0{width}d}.json" for i in range(1, count + 1)]


def write_json_atomic(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".tmp", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        # os.replace é atômico quando origem e destino estão no mesmo filesystem.
        os.replace(str(temp_path), str(path))
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise


def analyze_json_split(input_path: Path, mode: str, parts: int = 2, target_mb: float = 5.0) -> Dict[str, object]:
    data = read_json_file_with_fallback(input_path)
    list_path, items = find_largest_json_list(data)
    if not isinstance(items, list) or not items:
        raise ValueError(
            "Não foi possível detectar uma lista principal para dividir sem quebrar a estrutura. "
            "O JSON precisa ser uma lista na raiz ou um objeto com uma lista principal."
        )
    if mode == "size":
        chunks = split_json_by_target_size(data, list_path, items, int(target_mb * 1024 * 1024))
    else:
        chunks = split_list_evenly(items, parts)
    estimated_sizes = [_estimate_json_chunk_size(data, list_path, chunk) for chunk in chunks]
    file_size = safe_stat_size(input_path)
    return {
        "root_type": type(data).__name__,
        "list_path": list_path,
        "list_path_label": _json_path_label(list_path),
        "item_count": len(items),
        "part_count": len(chunks),
        "input_size": file_size,
        "estimated_sizes": estimated_sizes,
        "large_file_warning": file_size >= JSON_LARGE_FILE_WARNING_BYTES,
    }


def split_json_file(
    input_path: Path,
    output_folder: Path,
    prefix: str,
    mode: str,
    parts: int = 2,
    target_mb: float = 5.0,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Tuple[List[Path], Dict[str, object]]:
    data = read_json_file_with_fallback(input_path)
    list_path, items = find_largest_json_list(data)
    if not isinstance(items, list) or not items:
        raise ValueError(
            "Não foi possível dividir semanticamente: nenhuma lista principal com itens foi encontrada."
        )
    if mode == "size":
        chunks = split_json_by_target_size(data, list_path, items, int(target_mb * 1024 * 1024))
    else:
        chunks = split_list_evenly(items, parts)
    output_paths = build_json_output_paths(output_folder, prefix, len(chunks))
    written: List[Path] = []
    total = max(1, len(chunks))
    for index, (chunk, output_path) in enumerate(zip(chunks, output_paths), start=1):
        if progress_callback:
            progress_callback((index - 1) / total, f"Gravando parte {index} de {total}...")
        part_data = replace_json_path(data, list_path, chunk)
        write_json_atomic(output_path, part_data)
        # Validação pós-gravação: garante que o arquivo gerado é JSON válido.
        _ = read_json_file_with_fallback(output_path)
        written.append(output_path)
    if progress_callback:
        progress_callback(1.0, f"Concluído: {len(written)} parte(s) gerada(s).")
    summary = {
        "root_type": type(data).__name__,
        "list_path_label": _json_path_label(list_path),
        "item_count": len(items),
        "part_count": len(chunks),
        "output_sizes": [safe_stat_size(p) for p in written],
    }
    return written, summary


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
    if mode == "names":
        return "nomes_arquivos"
    return "lista_arquivos" if mode == "list" else "estrutura_pastas"


def write_txt_report(scan_result: Dict[str, object], output_path: Path, mode: str) -> None:
    stats = scan_result["stats"]
    entries = scan_result["entries"]
    errors = scan_result["errors"]
    title = "LISTA DE ARQUIVOS" if mode == "list" else "ESTRUTURA DE PASTAS"
    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        with temp_out.open("w", encoding="utf-8", newline="\n") as out:
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
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


def write_json_report(scan_result: Dict[str, object], output_path: Path) -> None:
    atomic_write_text_file(Path(output_path), json.dumps(scan_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def write_csv_report(scan_result: Dict[str, object], output_path: Path) -> None:
    entries = scan_result["entries"]
    fieldnames = ["tipo", "nome", "extensao", "tamanho_bytes", "tamanho", "pasta", "caminho_relativo", "caminho_absoluto", "modificado_em"]
    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        with temp_out.open("w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry)
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


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

    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        wb.save(temp_out)
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


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
# Arquivos/Pastas: exportação simples de nomes de arquivos
# -----------------------------------------------------------------------------

def parse_extension_filter(raw: str) -> List[str]:
    """Normaliza filtro de extensões.

    Aceita entradas como: "pdf, .md, *.txt". Retorna extensões em lowercase,
    sempre iniciando com ponto. Lista vazia significa sem filtro.
    """
    if not raw or not raw.strip():
        return []
    parts = re.split(r"[,;\s]+", raw.strip())
    extensions: List[str] = []
    for part in parts:
        item = part.strip().lower()
        if not item:
            continue
        if item.startswith("*."):
            item = item[1:]
        elif item.startswith("*"):
            item = item.lstrip("*")
        if not item.startswith("."):
            item = f".{item}"
        if item != "." and item not in extensions:
            extensions.append(item)
    return extensions


def scan_simple_file_names(
    root_folder: Path,
    include_hidden: bool = False,
    include_subfolders: bool = True,
    extensions: Optional[Sequence[str]] = None,
    export_mode: str = "Nome simples",
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, object]:
    """Varre arquivos para exportação simples de nomes/caminhos.

    Diferente do relatório completo, esta função é propositalmente enxuta: ela
    exporta apenas a lista de nomes simples ou caminhos completos, com filtro por
    extensão. É uma melhoria inspirada no script listar_nomes.py.
    """
    root_folder = Path(root_folder)
    if not root_folder.exists() or not root_folder.is_dir():
        raise ValueError("Selecione uma pasta raiz válida.")

    normalized_exts = set(parse_extension_filter(",".join(extensions or [])))
    entries: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []
    total_size = 0
    processed_dirs = 0

    def onerror(error: OSError) -> None:
        errors.append({"caminho": str(getattr(error, "filename", "")), "erro": str(error)})

    for dirpath, dirnames, filenames in os.walk(root_folder, onerror=onerror):
        current = Path(dirpath)
        processed_dirs += 1
        if not include_hidden:
            dirnames[:] = [name for name in dirnames if not is_hidden_like(current / name, root_folder)]
            filenames = [name for name in filenames if not is_hidden_like(current / name, root_folder)]

        for filename in sorted(filenames, key=natural_key):
            path = current / filename
            try:
                suffix = path.suffix.lower()
                if normalized_exts and suffix not in normalized_exts:
                    continue
                entry = folder_entry(path, root_folder, "Arquivo")
                export_value = str(path.resolve()) if export_mode == "Caminho completo" else path.name
                entry["nome_exportado"] = export_value
                entries.append(entry)
                total_size += int(entry.get("tamanho_bytes", 0))
            except OSError as exc:
                errors.append({"caminho": str(path), "erro": str(exc)})

        if progress_callback and processed_dirs % 10 == 0:
            progress_callback(0.20, f"Listando nomes... {processed_dirs} pasta(s) visitada(s), {len(entries)} arquivo(s) encontrado(s).")

        if not include_subfolders:
            dirnames[:] = []

    stats = {
        "pasta_raiz": str(root_folder),
        "total_itens": len(entries),
        "total_arquivos": len(entries),
        "total_pastas": 0,
        "tamanho_total_bytes": total_size,
        "tamanho_total": format_size(total_size),
        "erros_acesso": len(errors),
        "filtro_extensoes": ", ".join(sorted(normalized_exts)) if normalized_exts else "Sem filtro",
        "modo_exportacao": export_mode,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
    if progress_callback:
        progress_callback(0.45, f"Prévia pronta: {len(entries)} arquivo(s) encontrado(s).")
    return {"entries": entries, "errors": errors, "stats": stats}


def write_simple_names_txt(scan_result: Dict[str, object], output_path: Path) -> None:
    stats = scan_result["stats"]
    entries = scan_result["entries"]
    errors = scan_result["errors"]
    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        with temp_out.open("w", encoding="utf-8", newline="\n") as out:
            out.write("NOMES DE ARQUIVOS\n")
            out.write("=================\n\n")
            out.write(f"Pasta raiz: {stats['pasta_raiz']}\n")
            out.write(f"Gerado em: {stats['gerado_em']}\n")
            out.write(f"Modo: {stats.get('modo_exportacao', '')}\n")
            out.write(f"Filtro: {stats.get('filtro_extensoes', '')}\n")
            out.write(f"Total de arquivos: {stats['total_arquivos']}\n")
            out.write(f"Erros de acesso: {stats['erros_acesso']}\n\n")
            for entry in entries:
                out.write(f"{entry.get('nome_exportado', entry.get('nome', ''))}\n")
            if errors:
                out.write("\nERROS\n-----\n")
                for error in errors:
                    out.write(f"{error.get('caminho', '')}: {error.get('erro', '')}\n")
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


def write_simple_names_csv(scan_result: Dict[str, object], output_path: Path) -> None:
    fieldnames = ["nome_exportado", "nome", "extensao", "tamanho_bytes", "tamanho", "pasta", "caminho_relativo", "caminho_absoluto", "modificado_em"]
    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        with temp_out.open("w", encoding="utf-8-sig", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for entry in scan_result["entries"]:
                writer.writerow(entry)
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


def write_simple_names_xlsx(scan_result: Dict[str, object], output_path: Path) -> None:
    openpyxl = ensure_package("openpyxl")
    Workbook = openpyxl.Workbook
    wb = Workbook()
    ws_summary = wb.active
    ws_summary.title = "Resumo"
    ws_summary.append(["Métrica", "Valor"])
    for key, value in scan_result["stats"].items():
        ws_summary.append([key, value])

    ws = wb.create_sheet("Nomes")
    headers = ["nome_exportado", "nome", "extensao", "tamanho", "pasta", "caminho_relativo", "caminho_absoluto", "modificado_em"]
    ws.append(headers)
    for entry in scan_result["entries"]:
        ws.append([entry.get(header, "") for header in headers])

    if scan_result.get("errors"):
        ws_errors = wb.create_sheet("Erros")
        ws_errors.append(["caminho", "erro"])
        for error in scan_result["errors"]:
            ws_errors.append([error.get("caminho", ""), error.get("erro", "")])

    for sheet in wb.worksheets:
        for column_cells in sheet.columns:
            max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            sheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 12), 80)

    output_path = Path(output_path)
    temp_out = temp_output_path_for(output_path)
    try:
        wb.save(temp_out)
        replace_temp_output(temp_out, output_path)
    except Exception:
        cleanup_partial_output(temp_out)
        raise


def export_simple_name_reports(
    scan_result: Dict[str, object],
    output_folder: Path,
    formats: Sequence[str],
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Path]:
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    selected = [fmt.lower() for fmt in formats if fmt.lower() in {"txt", "csv", "xlsx"}]
    if not selected:
        raise ValueError("Selecione pelo menos TXT, CSV ou XLSX.")
    generated: Dict[str, Path] = {}
    total = len(selected)
    for index, fmt in enumerate(selected, start=1):
        if progress_callback:
            progress_callback(0.50 + (index - 1) / max(total, 1) * 0.45, f"Exportando nomes em {fmt.upper()} ({index}/{total})...")
        path = output_folder / f"{report_base_name('names')}.{fmt}"
        if fmt == "txt":
            write_simple_names_txt(scan_result, path)
        elif fmt == "csv":
            write_simple_names_csv(scan_result, path)
        elif fmt == "xlsx":
            write_simple_names_xlsx(scan_result, path)
        generated[fmt] = path
    if progress_callback:
        progress_callback(1.0, "Lista de nomes exportada com sucesso.")
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
    """Janela principal do K-Tools Neo v0.5.2 com hotfix de robustez."""

    SECTION_DATA = {
        "dashboard": {
            "icon": "🏠",
            "title": "Dashboard",
            "subtitle": "Acesso rápido às ferramentas de mídia, arquivos, texto e diagnóstico.",
        },
        "audio": {
            "icon": "🎧",
            "title": "Áudio",
            "subtitle": "Junte, corte, converta e extraia áudio em lote com FFmpeg automático.",
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
        "pdf_images": {
            "icon": "🖼",
            "title": "PDF/Imagens",
            "subtitle": "Junte PDFs, transforme imagens em PDF, converta WebP para PNG e divida documentos em partes.",
        },
        "json_tools": {
            "icon": "{}",
            "title": "JSON",
            "subtitle": "Divida arquivos JSON grandes preservando a estrutura sempre que possível.",
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

        self.title("K-Tools Neo v0.5.2 - Hotfix de Robustez")
        self.geometry("1320x860")
        self.minsize(1120, 720)
        self.configure(fg_color=THEME.bg_root)

        self.sidebar_buttons: Dict[str, SidebarButton] = {}
        self.current_section = "dashboard"
        self.progress_job: Optional[str] = None
        self.demo_progress_value = 0.0
        self.active_tasks: Dict[str, threading.Thread] = {}
        self.is_closing = False
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)

        self._configure_root_grid()
        self._build_sidebar()
        self._build_workspace()
        self.show_section("dashboard")

    def _run_background_task(self, target: Callable[[], None], task_name: str = "Tarefa") -> None:
        """Executa trabalho pesado em thread não-daemon e centraliza controle de tarefas ativas."""
        task_id = f"{task_name}-{datetime.now().timestamp()}"

        def guarded() -> None:
            try:
                target()
            except Exception as exc:
                # Falha inesperada fora do fluxo normal de _finish/_fail: mantém a UI responsiva.
                try:
                    self.after(0, lambda exc=exc: self._handle_unexpected_task_error(task_name, exc))
                except Exception:
                    pass
            finally:
                try:
                    self.after(0, lambda task_id=task_id: self.active_tasks.pop(task_id, None))
                except Exception:
                    self.active_tasks.pop(task_id, None)

        thread = threading.Thread(target=guarded, name=f"KToolsNeo-{task_name}")
        self.active_tasks[task_id] = thread
        thread.start()

    def _handle_unexpected_task_error(self, task_name: str, error: Exception) -> None:
        self.status_progress.set(0)
        self.status_text.configure(text=f"{task_name}: erro inesperado.")
        self.show_toast("Erro inesperado", str(error), "error")

    def _on_close_request(self) -> None:
        if self.active_tasks:
            if not messagebox.askyesno(
                "Tarefas em andamento",
                "Há tarefa(s) processando arquivos. Fechar agora pode manter o processo ativo até concluir a gravação segura. Deseja fechar mesmo assim?",
            ):
                return
        self.is_closing = True
        self.destroy()

    def _configure_root_grid(self) -> None:
        self.grid_columnconfigure(0, minsize=250, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=THEME.bg_sidebar)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(10, weight=1)

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
            ("pdf_images", "🖼", "PDF/Imagens"),
            ("json_tools", "{}", "JSON"),
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
        status_box.grid(row=11, column=0, sticky="ew", padx=16, pady=(12, 18))
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
            text=f"v{APP_VERSION} hotfix",
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
        elif section_id == "pdf_images":
            if not hasattr(self, "pdf_tool"):
                self.pdf_tool = "merge"
            self._build_pdf_images_view()
            self.status_text.configure(text="PDF/Imagens pronto. Escolha uma ferramenta, revise arquivos e execute.")
        elif section_id == "json_tools":
            if not hasattr(self, "json_tool"):
                self.json_tool = "parts"
            self._build_json_view()
            self.status_text.configure(text="JSON pronto. Escolha o arquivo, defina a divisão e gere partes válidas.")
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
            ("📄", "Juntar PDFs", "Combine vários PDFs em um único arquivo final, respeitando a ordem visual.", "PDF", "pdf_images"),
            ("🧩", "Dividir documentos", "Separe MD, TXT e PDF em partes equilibradas.", "Docs", "pdf_images"),
            ("🖼", "Imagens para PDF", "Transforme imagens em um PDF com uma página por imagem.", "Imagens", "pdf_images"),
            ("🗂", "Diagnosticar pastas", "Liste arquivos, conte pastas e exporte relatórios em TXT, JSON, CSV e XLSX.", "Arquivos", "folders"),
            ("🔊", "Extrair áudio", "Extraia áudio de vídeos ou una o áudio de vários vídeos.", "Mídia", "audio"),
            ("🌐", "WebP para PNG", "Converta imagens WebP em PNG mantendo transparência quando existir.", "Imagens", "pdf_images"),
            ("{}", "Dividir JSON", "Fatie arquivos JSON grandes por partes ou por tamanho aproximado.", "Dados", "json_tools"),
            ("⚙", "Configurações", "Ajuste pasta padrão, dependências, FFmpeg e logs.", "Sistema", "settings"),
        ]
        cards_per_row = 3
        tools_start_row = 2
        tools_rows = math.ceil(len(card_data) / cards_per_row)
        status_title_row = tools_start_row + tools_rows
        status_cards_row = status_title_row + 1
        tips_row = status_cards_row + 1

        for index, (icon, title, desc, category, target) in enumerate(card_data):
            card = ToolCard(
                root,
                icon=icon,
                title=title,
                description=desc,
                category=category,
                command=lambda sid=target: self.show_section(sid),
            )
            card.grid(row=tools_start_row + index // cards_per_row, column=index % cards_per_row, sticky="nsew", padx=8, pady=8)

        ctk.CTkLabel(
            root,
            text="Status do ambiente",
            font=(THEME.font_family, 16, "bold"),
            text_color=THEME.text_primary,
            anchor="w",
        ).grid(row=status_title_row, column=0, columnspan=3, sticky="ew", pady=(22, 8))

        status_cards = ctk.CTkFrame(root, fg_color="transparent")
        status_cards.grid(row=status_cards_row, column=0, columnspan=3, sticky="ew")
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
        tips.grid(row=tips_row, column=0, columnspan=3, sticky="ew", pady=(18, 0))
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
            ("split", "✂", "Cortar em partes", "Divida um áudio em partes iguais.", "Áudio"),
            ("extract", "🔊", "Extrair de vídeo", "Extraia áudio de um vídeo.", "Mídia"),
            ("batch", "🎞", "Áudio de vídeos", "Extraia e una áudio de vários vídeos.", "Mídia"),
            ("convert", "🔁", "Converter áudio", "Converta áudios em lote para MP3, M4A, WAV ou FLAC.", "Novo"),
            ("extract_batch", "📥", "Extrair em lote", "Extraia áudio de vários vídeos sem unir.", "Novo"),
            ("cut_time", "⏱", "Cortar por tempo", "Gere um trecho a partir de início e fim.", "Novo"),
            ("cut_marks", "✂", "Múltiplos cortes", "Divida por pontos de corte informados.", "Avançado"),
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
            ).grid(row=index // 4, column=index % 4, sticky="nsew", padx=8, pady=8)

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
        elif tool == "convert":
            self._build_audio_convert_tool(self.audio_body)
        elif tool == "extract_batch":
            self._build_audio_extract_batch_tool(self.audio_body)
        elif tool == "cut_time":
            self._build_audio_cut_time_tool(self.audio_body)
        elif tool == "cut_marks":
            self._build_audio_cut_marks_tool(self.audio_body)
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
            self.after(0, lambda value=value, message=message: self.audio_join_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = join_audio_files(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_join_finish(result, error))
        self._run_background_task(worker, "Processamento")

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
        if result:
            self._open_folder_if_enabled(Path(result).parent)

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
            self.after(0, lambda value=value, message=message: self.audio_split_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = split_audio_file(input_path, output_folder, parts, fmt, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_split_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_split_finish(self, result: Optional[List[Path]], error: Optional[Exception]) -> None:
        self.audio_split_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_split_progress.stop("Erro ao cortar áudio.")
            self.show_toast("Erro ao cortar", str(error), "error")
            return
        self.audio_split_progress.complete(f"{len(result or [])} parte(s) geradas com sucesso.")
        self.show_toast("Áudio cortado", f"{len(result or [])} arquivo(s) gerados.", "success")
        if result:
            self._open_folder_if_enabled(Path(result[0]).parent)

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
            self.after(0, lambda value=value, message=message: self.audio_extract_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = extract_audio_from_video(video, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_extract_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_extract_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_extract_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_extract_progress.stop("Erro ao extrair áudio.")
            self.show_toast("Erro na extração", str(error), "error")
            return
        self.audio_extract_progress.complete(f"Áudio extraído: {result}")
        self.show_toast("Áudio extraído", f"Arquivo salvo em: {result}", "success")
        if result:
            self._open_folder_if_enabled(Path(result).parent)

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
            self.after(0, lambda value=value, message=message: self.audio_batch_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = extract_and_join_audio_from_videos(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_batch_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_batch_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_batch_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_batch_progress.stop("Erro ao extrair/unir áudio dos vídeos.")
            self.show_toast("Erro nos vídeos", str(error), "error")
            return
        self.audio_batch_progress.complete(f"Áudio dos vídeos gerado: {result}")
        self.show_toast("Áudio dos vídeos gerado", f"Arquivo salvo em: {result}", "success")
        if result:
            self._open_folder_if_enabled(Path(result).parent)


    # -------------------------- Converter áudio em lote --------------------------
    def _build_audio_convert_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="🔁 Converter áudio", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Converta vários áudios para MP3, M4A, WAV ou FLAC. Saídas com nomes únicos para evitar sobrescrita.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        for i in range(9): actions.grid_columnconfigure(i, weight=0)
        ActionButton(actions, "Adicionar áudios", "secondary", self._audio_convert_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._audio_convert_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        self.audio_convert_subfolders = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.audio_convert_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_secondary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Remover", "secondary", lambda: self._audio_remove_selected(self.audio_convert_table)).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._audio_clear_table(self.audio_convert_table)).grid(row=0, column=4, padx=4)
        self.audio_convert_sort = tk.StringVar(value="Natural")
        ctk.CTkComboBox(actions, variable=self.audio_convert_sort, values=["Natural", "Nome A-Z", "Data de modificação"], command=lambda _v: self._sort_table_paths(self.audio_convert_table, self.audio_convert_sort.get()), width=180, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt, button_hover_color=THEME.bg_surface_hover, border_color=THEME.border_medium, dropdown_fg_color=THEME.bg_surface, dropdown_hover_color=THEME.bg_surface_hover, text_color=THEME.text_primary).grid(row=0, column=5, padx=4)
        self.audio_convert_table = FileTable(panel)
        self.audio_convert_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(output, text="Formato", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")
        self.audio_convert_format = tk.StringVar(value="m4a")
        ctk.CTkComboBox(output, variable=self.audio_convert_format, values=["m4a", "mp3", "wav", "flac", "aac", "ogg"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        ctk.CTkLabel(output, text="Bitrate", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=1, padx=8, pady=(14, 6), sticky="w")
        self.audio_convert_bitrate = tk.StringVar(value="192k")
        ctk.CTkComboBox(output, variable=self.audio_convert_bitrate, values=["Automático", "96k", "128k", "192k", "256k", "320k"], width=120, fg_color=THEME.bg_input, button_color=THEME.bg_surface).grid(row=1, column=1, padx=8, pady=(0, 14), sticky="w")
        ctk.CTkLabel(output, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=3, padx=(8, 10), pady=(14, 6), sticky="w")
        self.audio_convert_folder = tk.StringVar(value="")
        ctk.CTkEntry(output, textvariable=self.audio_convert_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=1, column=3, sticky="ew", padx=(8, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._audio_convert_choose_folder).grid(row=1, column=4, padx=(0, 14), pady=(0, 14))
        self.audio_convert_progress = ProgressPanel(panel, title="Progresso")
        self.audio_convert_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.audio_convert_btn = ActionButton(panel, "Converter áudios", "primary", self._audio_convert_run, icon="▶")
        self.audio_convert_btn.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _audio_convert_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecione os áudios", filetypes=self._audio_filetypes())
        if files:
            added = self._add_unique_to_table(self.audio_convert_table, [Path(f) for f in files], is_supported_audio_file, self.audio_convert_sort.get())
            self.show_toast("Áudios adicionados", f"{added} novo(s) áudio(s) entraram na lista.", "success" if added else "warning")

    def _audio_convert_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta com áudios")
        if folder:
            root = Path(folder)
            include_subfolders = self.audio_convert_subfolders.get()
            self.audio_convert_progress.set_progress(0, "Pesquisando áudios na pasta...")
            def worker() -> None:
                try:
                    iterator = root.rglob("*") if include_subfolders else root.iterdir()
                    paths = [p for p in iterator if is_supported_audio_file(p)]
                    error = None
                except Exception as exc:
                    paths = []
                    error = exc
                self.after(0, lambda paths=paths, error=error: self._audio_convert_folder_scan_finish(paths, error))
            self._run_background_task(worker, "Processamento")

    def _audio_convert_folder_scan_finish(self, paths: List[Path], error: Optional[Exception]) -> None:
        self.audio_convert_progress.set_progress(0, "Pronto para converter.")
        if error:
            self.show_toast("Erro na varredura", str(error), "error")
            return
        added = self._add_unique_to_table(self.audio_convert_table, paths, is_supported_audio_file, self.audio_convert_sort.get())
        self.show_toast("Pasta analisada", f"{added} áudio(s) encontrados.", "success" if added else "warning")

    def _audio_convert_choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta de saída")
        if folder:
            self.audio_convert_folder.set(folder)

    def _audio_convert_run(self) -> None:
        paths = self._paths_from_table(self.audio_convert_table)
        folder_raw = self.audio_convert_folder.get().strip()
        if not paths:
            self.show_toast("Nenhum áudio", "Adicione pelo menos um arquivo de áudio.", "warning")
            return
        if not folder_raw:
            self.show_toast("Escolha a saída", "Escolha a pasta de saída.", "warning")
            return
        output_folder = Path(folder_raw)
        self.audio_convert_btn.set_loading(True, "Convertendo...")
        self.audio_convert_progress.reset_success_color()
        self.audio_convert_progress.set_progress(0, "Preparando conversão...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda value=value, message=message: self.audio_convert_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = convert_audio_files_batch(paths, output_folder, self.audio_convert_format.get(), self.audio_convert_bitrate.get(), callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_convert_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_convert_finish(self, result: Optional[Tuple[List[Path], List[str]]], error: Optional[Exception]) -> None:
        self.audio_convert_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_convert_progress.stop("Erro ao converter áudios.")
            self.show_toast("Erro na conversão", str(error), "error")
            return
        outputs, skipped = result or ([], [])
        msg = f"{len(outputs)} arquivo(s) convertido(s)."
        if skipped:
            msg += f" {len(skipped)} item(ns) ignorado(s)."
        self.audio_convert_progress.complete(msg)
        self.show_toast("Conversão concluída", msg, "success" if not skipped else "warning")
        if outputs:
            self._open_folder_if_enabled(Path(outputs[0]).parent)

    # -------------------------- Extrair áudio em lote --------------------------
    def _build_audio_extract_batch_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(panel, text="📥 Extrair áudio em lote", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Extraia um arquivo de áudio para cada vídeo selecionado, sem unir os resultados.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        ActionButton(actions, "Adicionar vídeos", "secondary", self._audio_extract_batch_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._audio_extract_batch_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        self.audio_extract_batch_subfolders = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.audio_extract_batch_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_secondary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Remover", "secondary", lambda: self._audio_remove_selected(self.audio_extract_batch_table)).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._audio_clear_table(self.audio_extract_batch_table)).grid(row=0, column=4, padx=4)
        self.audio_extract_batch_sort = tk.StringVar(value="Natural")
        ctk.CTkComboBox(actions, variable=self.audio_extract_batch_sort, values=["Natural", "Nome A-Z", "Data de modificação"], command=lambda _v: self._sort_table_paths(self.audio_extract_batch_table, self.audio_extract_batch_sort.get()), width=180, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt, button_hover_color=THEME.bg_surface_hover, border_color=THEME.border_medium, dropdown_fg_color=THEME.bg_surface, dropdown_hover_color=THEME.bg_surface_hover, text_color=THEME.text_primary).grid(row=0, column=5, padx=4)
        self.audio_extract_batch_table = FileTable(panel)
        self.audio_extract_batch_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(3, weight=1)
        ctk.CTkLabel(output, text="Formato", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, padx=14, pady=(14, 6), sticky="w")
        self.audio_extract_batch_format = tk.StringVar(value="m4a")
        ctk.CTkComboBox(output, variable=self.audio_extract_batch_format, values=["m4a", "mp3", "wav", "flac", "aac", "ogg"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        ctk.CTkLabel(output, text="Bitrate", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=1, padx=8, pady=(14, 6), sticky="w")
        self.audio_extract_batch_bitrate = tk.StringVar(value="192k")
        ctk.CTkComboBox(output, variable=self.audio_extract_batch_bitrate, values=["Automático", "96k", "128k", "192k", "256k", "320k"], width=120, fg_color=THEME.bg_input, button_color=THEME.bg_surface).grid(row=1, column=1, padx=8, pady=(0, 14), sticky="w")
        ctk.CTkLabel(output, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=3, padx=(8, 10), pady=(14, 6), sticky="w")
        self.audio_extract_batch_folder = tk.StringVar(value="")
        ctk.CTkEntry(output, textvariable=self.audio_extract_batch_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=1, column=3, sticky="ew", padx=(8, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._audio_extract_batch_choose_folder).grid(row=1, column=4, padx=(0, 14), pady=(0, 14))
        self.audio_extract_batch_progress = ProgressPanel(panel, title="Progresso")
        self.audio_extract_batch_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.audio_extract_batch_btn = ActionButton(panel, "Extrair áudios", "primary", self._audio_extract_batch_run, icon="▶")
        self.audio_extract_batch_btn.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _audio_extract_batch_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecione os vídeos", filetypes=self._video_filetypes())
        if files:
            added = self._add_unique_to_table(self.audio_extract_batch_table, [Path(f) for f in files], is_supported_video_file, self.audio_extract_batch_sort.get())
            self.show_toast("Vídeos adicionados", f"{added} novo(s) vídeo(s) entraram na lista.", "success" if added else "warning")

    def _audio_extract_batch_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione uma pasta com vídeos")
        if folder:
            root = Path(folder)
            include_subfolders = self.audio_extract_batch_subfolders.get()
            self.audio_extract_batch_progress.set_progress(0, "Pesquisando vídeos na pasta...")
            def worker() -> None:
                try:
                    iterator = root.rglob("*") if include_subfolders else root.iterdir()
                    paths = [p for p in iterator if is_supported_video_file(p)]
                    error = None
                except Exception as exc:
                    paths = []
                    error = exc
                self.after(0, lambda paths=paths, error=error: self._audio_extract_batch_folder_scan_finish(paths, error))
            self._run_background_task(worker, "Processamento")

    def _audio_extract_batch_folder_scan_finish(self, paths: List[Path], error: Optional[Exception]) -> None:
        self.audio_extract_batch_progress.set_progress(0, "Pronto para extrair.")
        if error:
            self.show_toast("Erro na varredura", str(error), "error")
            return
        added = self._add_unique_to_table(self.audio_extract_batch_table, paths, is_supported_video_file, self.audio_extract_batch_sort.get())
        self.show_toast("Pasta analisada", f"{added} vídeo(s) encontrados.", "success" if added else "warning")

    def _audio_extract_batch_choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta de saída")
        if folder:
            self.audio_extract_batch_folder.set(folder)

    def _audio_extract_batch_run(self) -> None:
        paths = self._paths_from_table(self.audio_extract_batch_table)
        folder_raw = self.audio_extract_batch_folder.get().strip()
        if not paths:
            self.show_toast("Nenhum vídeo", "Adicione pelo menos um vídeo.", "warning")
            return
        if not folder_raw:
            self.show_toast("Escolha a saída", "Escolha a pasta de saída.", "warning")
            return
        self.audio_extract_batch_btn.set_loading(True, "Extraindo...")
        self.audio_extract_batch_progress.reset_success_color()
        self.audio_extract_batch_progress.set_progress(0, "Preparando extração em lote...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda value=value, message=message: self.audio_extract_batch_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = extract_audio_batch_from_videos(paths, Path(folder_raw), self.audio_extract_batch_format.get(), self.audio_extract_batch_bitrate.get(), callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_extract_batch_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_extract_batch_finish(self, result: Optional[Tuple[List[Path], List[str]]], error: Optional[Exception]) -> None:
        self.audio_extract_batch_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_extract_batch_progress.stop("Erro ao extrair áudios.")
            self.show_toast("Erro na extração", str(error), "error")
            return
        outputs, skipped = result or ([], [])
        msg = f"{len(outputs)} arquivo(s) extraído(s)."
        if skipped:
            msg += f" {len(skipped)} vídeo(s) ignorado(s)."
        self.audio_extract_batch_progress.complete(msg)
        self.show_toast("Extração concluída", msg, "success" if not skipped else "warning")
        if outputs:
            self._open_folder_if_enabled(Path(outputs[0]).parent)

    # -------------------------- Cortar áudio por tempo --------------------------
    def _build_audio_cut_time_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text="⏱ Cortar áudio por tempo", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Informe início e fim para gerar um único trecho. Exemplos: 90, 01:30 ou 00:01:30.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 16))
        self.audio_cut_time_input = tk.StringVar(value="")
        self.audio_cut_time_start = tk.StringVar(value="00:00:00")
        self.audio_cut_time_end = tk.StringVar(value="")
        self.audio_cut_time_format = tk.StringVar(value="m4a")
        self.audio_cut_time_bitrate = tk.StringVar(value="192k")
        self.audio_cut_time_output = tk.StringVar(value="")
        ctk.CTkLabel(panel, text="Arquivo de áudio", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_cut_time_input, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Selecionar", "secondary", self._audio_cut_time_choose_input).grid(row=2, column=2, padx=18, pady=6)
        time_row = ctk.CTkFrame(panel, fg_color="transparent")
        time_row.grid(row=3, column=1, sticky="w", padx=8, pady=6)
        ctk.CTkLabel(panel, text="Tempos", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(time_row, textvariable=self.audio_cut_time_start, width=130, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkLabel(time_row, text="até", text_color=THEME.text_secondary).grid(row=0, column=1, padx=(0, 8))
        ctk.CTkEntry(time_row, textvariable=self.audio_cut_time_end, width=130, height=36, placeholder_text="fim opcional", fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=0, column=2, padx=(0, 12))
        ctk.CTkComboBox(time_row, variable=self.audio_cut_time_format, values=["m4a", "mp3", "wav", "flac", "aac", "ogg"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=0, column=3, padx=(0, 8))
        ctk.CTkComboBox(time_row, variable=self.audio_cut_time_bitrate, values=["Automático", "96k", "128k", "192k", "256k", "320k"], width=120, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=0, column=4)
        ctk.CTkLabel(panel, text="Arquivo final", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_cut_time_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=4, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._audio_cut_time_choose_output).grid(row=4, column=2, padx=18, pady=6)
        self.audio_cut_time_progress = ProgressPanel(panel, title="Progresso")
        self.audio_cut_time_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 14))
        self.audio_cut_time_btn = ActionButton(panel, "Cortar trecho", "primary", self._audio_cut_time_run, icon="▶")
        self.audio_cut_time_btn.grid(row=6, column=2, sticky="e", padx=18, pady=(0, 18))

    def _audio_cut_time_choose_input(self) -> None:
        file = filedialog.askopenfilename(title="Selecione um áudio", filetypes=self._audio_filetypes())
        if file:
            self.audio_cut_time_input.set(file)
            fmt = self.audio_cut_time_format.get().lower()
            self.audio_cut_time_output.set(str(Path(file).with_name(f"{Path(file).stem}_trecho.{fmt}")))

    def _audio_cut_time_choose_output(self) -> None:
        fmt = self.audio_cut_time_format.get().lower()
        file = filedialog.asksaveasfilename(title="Salvar trecho de áudio", defaultextension=f".{fmt}", initialfile=f"trecho_audio.{fmt}", filetypes=[("Áudio", f"*.{fmt}"), ("Todos os arquivos", "*.*")])
        if file:
            self.audio_cut_time_output.set(str(ensure_audio_extension(Path(file), fmt)))

    def _audio_cut_time_run(self) -> None:
        input_raw = self.audio_cut_time_input.get().strip()
        output_raw = self.audio_cut_time_output.get().strip()
        if not input_raw or not output_raw:
            self.show_toast("Entrada incompleta", "Selecione o áudio e o arquivo final.", "warning")
            return
        try:
            start = parse_timestamp_to_seconds(self.audio_cut_time_start.get())
            end_raw = self.audio_cut_time_end.get().strip()
            end = parse_timestamp_to_seconds(end_raw) if end_raw else None
        except Exception as exc:
            self.show_toast("Tempo inválido", str(exc), "warning")
            return
        input_path = Path(input_raw)
        output = ensure_audio_extension(Path(output_raw), self.audio_cut_time_format.get())
        if not input_path.exists() or not is_supported_audio_file(input_path):
            self.show_toast("Áudio inválido", "Selecione um arquivo de áudio compatível.", "warning")
            return
        self.audio_cut_time_output.set(str(output))
        if not self._confirm_overwrite(output):
            return
        self.audio_cut_time_btn.set_loading(True, "Cortando...")
        self.audio_cut_time_progress.reset_success_color()
        self.audio_cut_time_progress.set_progress(0, "Preparando corte por tempo...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda value=value, message=message: self.audio_cut_time_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = cut_audio_by_time_range(input_path, output, start, end, self.audio_cut_time_bitrate.get(), callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_cut_time_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_cut_time_finish(self, result: Optional[Path], error: Optional[Exception]) -> None:
        self.audio_cut_time_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_cut_time_progress.stop("Erro ao cortar trecho.")
            self.show_toast("Erro no corte", str(error), "error")
            return
        self.audio_cut_time_progress.complete(f"Trecho gerado: {result}")
        self.show_toast("Trecho gerado", f"Arquivo salvo em: {result}", "success")
        if result:
            self._open_folder_if_enabled(Path(result).parent)

    # -------------------------- Cortar áudio por múltiplos tempos --------------------------
    def _build_audio_cut_marks_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text="✂ Cortar por múltiplos tempos", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Informe pontos de corte. Exemplo: 00:10:00, 00:20:00, 00:35:30.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 16))
        self.audio_cut_marks_input = tk.StringVar(value="")
        self.audio_cut_marks_folder = tk.StringVar(value="")
        self.audio_cut_marks_points = tk.StringVar(value="")
        self.audio_cut_marks_format = tk.StringVar(value="m4a")
        self.audio_cut_marks_bitrate = tk.StringVar(value="192k")
        ctk.CTkLabel(panel, text="Arquivo de áudio", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_cut_marks_input, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Selecionar", "secondary", self._audio_cut_marks_choose_input).grid(row=2, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Pontos de corte", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.audio_cut_marks_points, height=36, placeholder_text="00:10:00, 00:20:00", fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        options = ctk.CTkFrame(panel, fg_color="transparent")
        options.grid(row=4, column=1, sticky="w", padx=8, pady=6)
        ctk.CTkLabel(panel, text="Saída", text_color=THEME.text_secondary, font=(THEME.font_family, 12, "bold")).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkComboBox(options, variable=self.audio_cut_marks_format, values=["m4a", "mp3", "wav", "flac", "aac", "ogg"], width=100, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkComboBox(options, variable=self.audio_cut_marks_bitrate, values=["Automático", "96k", "128k", "192k", "256k", "320k"], width=120, fg_color=THEME.bg_input, button_color=THEME.bg_surface_alt).grid(row=0, column=1, padx=(0, 12))
        ctk.CTkEntry(options, textvariable=self.audio_cut_marks_folder, width=420, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=0, column=2, padx=(0, 8))
        ActionButton(options, "Escolher pasta", "secondary", self._audio_cut_marks_choose_folder).grid(row=0, column=3)
        self.audio_cut_marks_progress = ProgressPanel(panel, title="Progresso")
        self.audio_cut_marks_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 14))
        self.audio_cut_marks_btn = ActionButton(panel, "Gerar trechos", "primary", self._audio_cut_marks_run, icon="▶")
        self.audio_cut_marks_btn.grid(row=6, column=2, sticky="e", padx=18, pady=(0, 18))

    def _audio_cut_marks_choose_input(self) -> None:
        file = filedialog.askopenfilename(title="Selecione um áudio", filetypes=self._audio_filetypes())
        if file:
            self.audio_cut_marks_input.set(file)
            if not self.audio_cut_marks_folder.get().strip():
                self.audio_cut_marks_folder.set(str(Path(file).parent))

    def _audio_cut_marks_choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta de saída")
        if folder:
            self.audio_cut_marks_folder.set(folder)

    def _audio_cut_marks_run(self) -> None:
        input_raw = self.audio_cut_marks_input.get().strip()
        folder_raw = self.audio_cut_marks_folder.get().strip()
        if not input_raw or not folder_raw:
            self.show_toast("Entrada incompleta", "Selecione o áudio e a pasta de saída.", "warning")
            return
        try:
            points = parse_cut_points(self.audio_cut_marks_points.get())
        except Exception as exc:
            self.show_toast("Pontos inválidos", str(exc), "warning")
            return
        input_path = Path(input_raw)
        if not input_path.exists() or not is_supported_audio_file(input_path):
            self.show_toast("Áudio inválido", "Selecione um arquivo de áudio compatível.", "warning")
            return
        self.audio_cut_marks_btn.set_loading(True, "Cortando...")
        self.audio_cut_marks_progress.reset_success_color()
        self.audio_cut_marks_progress.set_progress(0, "Preparando cortes...")
        def callback(value: float, message: str) -> None:
            self.after(0, lambda value=value, message=message: self.audio_cut_marks_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))
        def worker() -> None:
            result = None; error = None
            try:
                result = split_audio_by_cut_points(input_path, Path(folder_raw), points, self.audio_cut_marks_format.get(), self.audio_cut_marks_bitrate.get(), callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._audio_cut_marks_finish(result, error))
        self._run_background_task(worker, "Processamento")

    def _audio_cut_marks_finish(self, result: Optional[List[Path]], error: Optional[Exception]) -> None:
        self.audio_cut_marks_btn.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.audio_cut_marks_progress.stop("Erro ao gerar trechos.")
            self.show_toast("Erro nos cortes", str(error), "error")
            return
        self.audio_cut_marks_progress.complete(f"{len(result or [])} trecho(s) gerados com sucesso.")
        self.show_toast("Trechos gerados", f"{len(result or [])} arquivo(s) salvos.", "success")
        if result:
            self._open_folder_if_enabled(Path(result[0]).parent)

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
            self.after(0, lambda found=found, error=error, recursive=recursive: self._md_finish_scan(found, error, recursive))

        self._run_background_task(worker, "Processamento")

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
            self.after(0, lambda value=value, message=message: self.md_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))

        def worker() -> None:
            error: Optional[Exception] = None
            result: Optional[Path] = None
            try:
                result = merge_text_files(paths, output_path, separator, progress_callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._md_finish_join(result, error))

        self._run_background_task(worker, "Processamento")

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
        if result:
            self._open_folder_if_enabled(Path(result).parent)
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
            self.after(0, lambda value=value, message=message: self.video_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))

        def worker() -> None:
            result = None
            error = None
            try:
                result = join_video_files(paths, output, callback)
            except Exception as exc:
                error = exc
            self.after(0, lambda result=result, error=error: self._video_join_finish(result, error))

        self._run_background_task(worker, "Processamento")

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
        if result:
            self._open_folder_if_enabled(Path(result).parent)

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
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="folder_cards")
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
            icon="🔤",
            title="Exportar nomes",
            description="Exporta nomes simples ou caminhos completos com filtro por extensão.",
            category="Listagem",
            command=lambda: self._set_folders_mode("names"),
            active=getattr(self, "folders_mode", "structure") == "names",
        ).grid(row=0, column=2, sticky="nsew", padx=8)
        ToolCard(
            cards,
            icon="📊",
            title="Resumo final",
            description="Cards com totais, tamanho e erros de acesso.",
            category="Resumo",
            command=lambda: self.show_toast("Resumo", "O resumo aparece após gerar ou listar.", "info"),
        ).grid(row=0, column=3, sticky="nsew", padx=(8, 0))

        self._build_folders_panel(root)

    def _build_folders_panel(self, master) -> None:
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(4, weight=1)

        mode = getattr(self, "folders_mode", "structure")
        if mode == "structure":
            title = "🗂 Gerar estrutura de pastas"
            description = "Analise arquivos e diretórios, gere resumo e exporte relatórios completos."
        elif mode == "names":
            title = "🔤 Exportar nomes de arquivos"
            description = "Exporte nomes simples ou caminhos completos, com filtro por extensão."
        else:
            title = "📄 Listar arquivos rapidamente"
            description = "Liste arquivos com metadados e exporte uma relação simples."
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
        self.folders_ext_filter_var = getattr(self, "folders_ext_filter_var", tk.StringVar(value=""))
        self.folders_path_mode_var = getattr(self, "folders_path_mode_var", tk.StringVar(value="Nome simples"))

        if mode == "names":
            ctk.CTkLabel(options, text="Incluir", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=(14, 12), pady=(14, 4))
            ctk.CTkCheckBox(options, text="Subpastas", variable=self.folders_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=1, sticky="w", padx=6, pady=(14, 4))
            ctk.CTkCheckBox(options, text="Ocultos", variable=self.folders_include_hidden, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, sticky="w", padx=6, pady=(14, 4))

            ctk.CTkLabel(options, text="Filtro por extensão", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=3, sticky="w", padx=(18, 8), pady=(14, 4))
            ctk.CTkEntry(options, textvariable=self.folders_ext_filter_var, placeholder_text="Ex.: pdf, md, txt", width=170, height=32, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=4, columnspan=2, sticky="ew", padx=(0, 8), pady=(14, 4))

            ctk.CTkLabel(options, text="Exportar como", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=6, sticky="w", padx=(12, 8), pady=(14, 4))
            ctk.CTkOptionMenu(options, variable=self.folders_path_mode_var, values=["Nome simples", "Caminho completo"], fg_color=THEME.bg_input, button_color=THEME.primary, button_hover_color=THEME.primary_hover, dropdown_fg_color=THEME.bg_surface_alt, dropdown_hover_color=THEME.bg_surface_hover, text_color=THEME.text_primary, width=160).grid(row=0, column=7, columnspan=2, sticky="w", padx=(0, 14), pady=(14, 4))

            ctk.CTkLabel(options, text="Formatos", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=1, column=0, sticky="w", padx=(14, 12), pady=(4, 14))
            ctk.CTkCheckBox(options, text="TXT", variable=self.folders_fmt_txt, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=1, sticky="w", padx=6, pady=(4, 14))
            ctk.CTkCheckBox(options, text="CSV", variable=self.folders_fmt_csv, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=2, sticky="w", padx=6, pady=(4, 14))
            ctk.CTkCheckBox(options, text="XLSX", variable=self.folders_fmt_xlsx, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=3, sticky="w", padx=6, pady=(4, 14))
            ctk.CTkLabel(options, text="Dica: deixe o filtro vazio para listar todos os arquivos.", font=(THEME.font_family, 11), text_color=THEME.text_muted, anchor="w").grid(row=1, column=4, columnspan=5, sticky="ew", padx=(12, 14), pady=(4, 14))
        else:
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
        run_text = "Exportar nomes" if mode == "names" else ("Listar arquivos" if mode == "list" else "Gerar relatório")
        self.folders_run_btn = ActionButton(actions, run_text, "primary", self._folders_run, icon="▶")
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
        mode = getattr(self, "folders_mode", "structure")
        if self.folders_fmt_txt.get():
            formats.append("txt")
        if mode != "names" and self.folders_fmt_json.get():
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
        mode = getattr(self, "folders_mode", "structure")
        for index, entry in enumerate(entries[:limit], start=1):
            tipo = "DIR" if entry.get("tipo") == "Pasta" else str(entry.get("extensao") or "FILE").upper().lstrip(".")
            status = "Nome" if mode == "names" else ("Diretório" if entry.get("tipo") == "Pasta" else "Arquivo")
            display_name = str(entry.get("nome_exportado") or entry.get("nome", ""))
            rows.append((
                f"{index:03d}",
                display_name,
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
            mode = getattr(self, "folders_mode", "structure")
            allowed = "TXT, CSV ou XLSX" if mode == "names" else "TXT, JSON, CSV ou XLSX"
            self.show_toast("Formato obrigatório", f"Marque pelo menos {allowed}.", "warning")
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

        loading_text = "Listando..." if mode == "names" else "Analisando..."
        self.folders_run_btn.set_loading(True, loading_text)
        self.folders_progress.reset_success_color()
        self.folders_progress.set_progress(0.03, "Preparando listagem..." if mode == "names" else "Preparando análise...")
        self.status_text.configure(text="Arquivos/Pastas: listando nomes de arquivos..." if mode == "names" else "Arquivos/Pastas: analisando pasta...")
        self.status_progress.set(0.03)

        include_files = True if mode in {"list", "names"} else bool(self.folders_include_files.get())
        include_dirs = False if mode in {"list", "names"} else bool(self.folders_include_dirs.get())
        include_hidden = bool(self.folders_include_hidden.get())
        include_subfolders = bool(self.folders_include_subfolders.get())
        extension_filter = self.folders_ext_filter_var.get().strip() if mode == "names" and hasattr(self, "folders_ext_filter_var") else ""
        export_path_mode = self.folders_path_mode_var.get().strip() if mode == "names" and hasattr(self, "folders_path_mode_var") else "Nome simples"

        def callback(value: float, message: str) -> None:
            self.after(0, lambda value=value, message=message: self.folders_progress.set_progress(value, message))
            self.after(0, lambda value=value: self.status_progress.set(value))

        def worker() -> None:
            result = None
            generated = None
            error = None
            try:
                if mode == "names":
                    result = scan_simple_file_names(
                        root_path,
                        include_hidden=include_hidden,
                        include_subfolders=include_subfolders,
                        extensions=parse_extension_filter(extension_filter),
                        export_mode=export_path_mode,
                        progress_callback=callback,
                    )
                    generated = export_simple_name_reports(result, output_folder, formats, progress_callback=callback)
                else:
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
            self.after(0, lambda result=result, generated=generated, error=error: self._folders_finish(result, generated, error))

        self._run_background_task(worker, "Processamento")

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
        mode = getattr(self, "folders_mode", "structure")
        if mode == "names":
            self.folders_progress.complete(f"Nomes exportados: {generated_names}")
            self.status_text.configure(text=f"Arquivos/Pastas: {stats.get('total_arquivos', 0)} nome(s) exportado(s). Formatos: {generated_names}.")
            self.show_toast("Nomes exportados", f"{stats.get('total_arquivos', 0)} arquivo(s) listado(s).", "success")
            if generated:
                self._open_folder_if_enabled(next(iter(generated.values())).parent)
        else:
            self.folders_progress.complete(f"Relatórios gerados: {generated_names}")
            self.status_text.configure(text=f"Arquivos/Pastas: {stats.get('total_itens', 0)} item(ns) analisados. Relatórios: {generated_names}.")
            self.show_toast("Relatórios gerados", f"{stats.get('total_arquivos', 0)} arquivo(s), {stats.get('total_pastas', 0)} pasta(s).", "success")
            if generated:
                self._open_folder_if_enabled(next(iter(generated.values())).parent)

    # ------------------------------------------------------------------
    # Configurações
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # PDF/Imagens
    # ------------------------------------------------------------------
    def _build_pdf_images_view(self) -> None:
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="pdf_tools")
        tools = [
            ("merge", "📄", "Juntar PDFs", "Combine vários PDFs em um único arquivo final.", "PDF"),
            ("images", "🖼", "Imagens para PDF", "Crie um PDF com uma imagem por página.", "Imagens"),
            ("webp", "🌐", "WebP para PNG", "Converta WebP para PNG em lote.", "Imagem"),
            ("split", "✂", "Dividir PDF", "Separe um PDF em partes equilibradas.", "PDF"),
            ("docs", "🧩", "Dividir documentos", "Divida MD, TXT e PDF em partes equilibradas.", "Docs"),
        ]
        for index, (tool_id, icon, title, desc, category) in enumerate(tools):
            card = ToolCard(
                cards,
                icon=icon,
                title=title,
                description=desc,
                category=category,
                active=getattr(self, "pdf_tool", "merge") == tool_id,
                command=lambda t=tool_id: self._set_pdf_tool(t),
            )
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=(0 if index % 3 == 0 else 8, 0 if index % 3 == 2 else 8), pady=(0 if index < 3 else 12, 0))

        self.pdf_body = ctk.CTkFrame(root, fg_color="transparent")
        self.pdf_body.grid(row=1, column=0, sticky="nsew")
        self.pdf_body.grid_columnconfigure(0, weight=1)
        tool = getattr(self, "pdf_tool", "merge")
        if tool == "images":
            self._build_images_to_pdf_tool(self.pdf_body)
        elif tool == "webp":
            self._build_webp_to_png_tool(self.pdf_body)
        elif tool == "split":
            self._build_split_pdf_tool(self.pdf_body)
        elif tool == "docs":
            self._build_document_split_tool(self.pdf_body)
        else:
            self._build_merge_pdfs_tool(self.pdf_body)

    def _set_pdf_tool(self, tool_id: str) -> None:
        self.pdf_tool = tool_id
        self.clear_content()
        self._build_pdf_images_view()

    def _pdf_filetypes(self):
        return [("PDF", "*.pdf"), ("Todos os arquivos", "*.*")]

    def _image_filetypes(self):
        return [("Imagens", " ".join(f"*{ext}" for ext in sorted(IMAGE_EXTENSIONS))), ("Todos os arquivos", "*.*")]

    def _webp_filetypes(self):
        return [("WebP", "*.webp"), ("Todos os arquivos", "*.*")]

    def _default_output_folder_path(self) -> Path:
        raw = str(self.settings_config.get("default_output_folder", default_output_dir()))
        path = Path(raw).expanduser()
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            path = default_output_dir()
            path.mkdir(parents=True, exist_ok=True)
        return path

    def _confirm_multiple_overwrite(self, outputs: Sequence[Path]) -> bool:
        existing = [Path(p) for p in outputs if Path(p).exists()]
        if not existing:
            return True
        preview = "\n".join(str(p) for p in existing[:8])
        if len(existing) > 8:
            preview += f"\n... e mais {len(existing) - 8} arquivo(s)."
        return messagebox.askyesno("Arquivos já existem", f"Os arquivos abaixo já existem:\n\n{preview}\n\nDeseja substituir?")

    def _select_output_pdf(self, title: str, default_name: str) -> str:
        initialdir = self._default_output_folder_path()
        filename = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".pdf",
            initialdir=str(initialdir),
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf")],
        )
        return str(ensure_pdf_extension(Path(filename))) if filename else ""

    def _scan_files_in_folder(self, folder: Path, include_subfolders: bool, valid_func: Callable[[Path], bool]) -> List[Path]:
        """Varre uma pasta sem derrubar a interface se houver arquivo inacessível."""
        found: List[Path] = []
        try:
            iterator = folder.rglob("*") if include_subfolders else folder.iterdir()
            for item in iterator:
                try:
                    if valid_func(item):
                        found.append(item)
                except Exception:
                    continue
        except Exception as exc:
            self.show_toast("Erro na varredura", f"Não foi possível ler a pasta: {exc}", "error")
        return sort_paths(found, "natural")

    # -------------------------- Juntar PDFs --------------------------
    def _build_merge_pdfs_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(panel, text="📄 Juntar PDFs", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Adicione PDFs, revise a ordem e gere um único arquivo final.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        actions.grid_columnconfigure(12, weight=1)
        self.pdf_merge_include_subfolders = tk.BooleanVar(value=False)
        self.pdf_merge_sort = tk.StringVar(value="Natural")
        ActionButton(actions, "Adicionar PDFs", "secondary", self._pdf_merge_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._pdf_merge_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.pdf_merge_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Subir", "ghost", lambda: self.pdf_merge_table.move_selected_up()).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Descer", "ghost", lambda: self.pdf_merge_table.move_selected_down()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self.pdf_merge_table.remove_selected()).grid(row=0, column=5, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._clear_table_confirm(self.pdf_merge_table)).grid(row=0, column=6, padx=4)
        ctk.CTkComboBox(actions, variable=self.pdf_merge_sort, values=["Natural", "Nome A-Z", "Data de modificação"], width=160, fg_color=THEME.bg_input, button_color=THEME.bg_surface, button_hover_color=THEME.bg_surface_hover, command=lambda v: self._sort_table_paths(self.pdf_merge_table, v)).grid(row=0, column=7, padx=8)

        self.pdf_merge_table = FileTable(panel)
        self.pdf_merge_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))

        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(0, weight=1)
        self.pdf_merge_output = tk.StringVar(value="")
        ctk.CTkLabel(output, text="Arquivo final", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkEntry(output, textvariable=self.pdf_merge_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, sticky="ew", padx=(14, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._pdf_merge_choose_output).grid(row=1, column=1, padx=(0, 14), pady=(0, 14))

        self.pdf_merge_progress = ProgressPanel(panel, "Progresso")
        self.pdf_merge_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.pdf_merge_run_button = ActionButton(panel, "Juntar PDFs", "primary", self._pdf_merge_run, icon="📄")
        self.pdf_merge_run_button.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _pdf_merge_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecionar PDFs", filetypes=self._pdf_filetypes())
        added = self._add_unique_to_table(self.pdf_merge_table, [Path(f) for f in files], is_supported_pdf_file, self.pdf_merge_sort.get())
        if added:
            self.show_toast("PDFs adicionados", f"{added} arquivo(s) adicionado(s).", "success")

    def _pdf_merge_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecionar pasta com PDFs")
        if not folder:
            return
        paths = self._scan_files_in_folder(Path(folder), self.pdf_merge_include_subfolders.get(), is_supported_pdf_file)
        added = self._add_unique_to_table(self.pdf_merge_table, paths, is_supported_pdf_file, self.pdf_merge_sort.get())
        self.show_toast("Varredura concluída", f"{added} PDF(s) adicionado(s).", "success" if added else "warning")

    def _pdf_merge_choose_output(self) -> None:
        selected = self._select_output_pdf("Salvar PDF final", "pdf_unificado.pdf")
        if selected:
            self.pdf_merge_output.set(selected)

    def _pdf_merge_run(self) -> None:
        paths = self._paths_from_table(self.pdf_merge_table)
        output_raw = self.pdf_merge_output.get().strip()
        if not paths or not output_raw:
            self.show_toast("Dados incompletos", "Adicione PDFs e escolha o arquivo final.", "warning")
            return
        output = ensure_pdf_extension(Path(output_raw))
        self.pdf_merge_output.set(str(output))
        if not self._confirm_overwrite(output):
            return
        self.pdf_merge_run_button.set_loading(True, "Juntando PDFs...")
        self.pdf_merge_progress.start_indeterminate("Preparando PDFs...")
        def worker():
            try:
                def cb(value, msg): self.after(0, lambda value=value, msg=msg: self.pdf_merge_progress.set_progress(value, msg))
                result = merge_pdf_files(paths, output, cb)
                self.after(0, lambda result=result: self._finish_task(self.pdf_merge_run_button, self.pdf_merge_progress, "PDF gerado", f"Arquivo final: {result}", result.parent))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._fail_task(self.pdf_merge_run_button, self.pdf_merge_progress, "Erro ao juntar PDFs", str(exc)))
        self._run_background_task(worker, "Processamento")

    # -------------------------- Imagens para PDF --------------------------
    def _build_images_to_pdf_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(panel, text="🖼 Imagens para PDF", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Crie um PDF com uma imagem por página. Transparência é convertida para fundo branco.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        actions.grid_columnconfigure(12, weight=1)
        self.images_pdf_include_subfolders = tk.BooleanVar(value=False)
        self.images_pdf_sort = tk.StringVar(value="Natural")
        ActionButton(actions, "Adicionar imagens", "secondary", self._images_pdf_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._images_pdf_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.images_pdf_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Subir", "ghost", lambda: self.images_pdf_table.move_selected_up()).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Descer", "ghost", lambda: self.images_pdf_table.move_selected_down()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self.images_pdf_table.remove_selected()).grid(row=0, column=5, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._clear_table_confirm(self.images_pdf_table)).grid(row=0, column=6, padx=4)
        ctk.CTkComboBox(actions, variable=self.images_pdf_sort, values=["Natural", "Nome A-Z", "Data de modificação"], width=160, fg_color=THEME.bg_input, button_color=THEME.bg_surface, button_hover_color=THEME.bg_surface_hover, command=lambda v: self._sort_table_paths(self.images_pdf_table, v)).grid(row=0, column=7, padx=8)

        self.images_pdf_table = FileTable(panel)
        self.images_pdf_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))

        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(0, weight=1)
        self.images_pdf_output = tk.StringVar(value="")
        ctk.CTkLabel(output, text="Arquivo PDF final", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkEntry(output, textvariable=self.images_pdf_output, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, sticky="ew", padx=(14, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._images_pdf_choose_output).grid(row=1, column=1, padx=(0, 14), pady=(0, 14))

        self.images_pdf_progress = ProgressPanel(panel, "Progresso")
        self.images_pdf_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.images_pdf_run_button = ActionButton(panel, "Gerar PDF", "primary", self._images_pdf_run, icon="🖼")
        self.images_pdf_run_button.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _images_pdf_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecionar imagens", filetypes=self._image_filetypes())
        added = self._add_unique_to_table(self.images_pdf_table, [Path(f) for f in files], is_supported_image_file, self.images_pdf_sort.get())
        if added:
            self.show_toast("Imagens adicionadas", f"{added} arquivo(s) adicionado(s).", "success")

    def _images_pdf_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecionar pasta com imagens")
        if not folder:
            return
        paths = self._scan_files_in_folder(Path(folder), self.images_pdf_include_subfolders.get(), is_supported_image_file)
        added = self._add_unique_to_table(self.images_pdf_table, paths, is_supported_image_file, self.images_pdf_sort.get())
        self.show_toast("Varredura concluída", f"{added} imagem(ns) adicionada(s).", "success" if added else "warning")

    def _images_pdf_choose_output(self) -> None:
        selected = self._select_output_pdf("Salvar PDF de imagens", "imagens_unidas.pdf")
        if selected:
            self.images_pdf_output.set(selected)

    def _images_pdf_run(self) -> None:
        paths = self._paths_from_table(self.images_pdf_table)
        output_raw = self.images_pdf_output.get().strip()
        if not paths or not output_raw:
            self.show_toast("Dados incompletos", "Adicione imagens e escolha o PDF final.", "warning")
            return
        output = ensure_pdf_extension(Path(output_raw))
        self.images_pdf_output.set(str(output))
        if not self._confirm_overwrite(output):
            return
        self.images_pdf_run_button.set_loading(True, "Gerando PDF...")
        self.images_pdf_progress.start_indeterminate("Preparando imagens...")
        def worker():
            try:
                def cb(value, msg): self.after(0, lambda value=value, msg=msg: self.images_pdf_progress.set_progress(value, msg))
                result = images_to_pdf(paths, output, cb)
                self.after(0, lambda result=result: self._finish_task(self.images_pdf_run_button, self.images_pdf_progress, "PDF gerado", f"Arquivo final: {result}", result.parent))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._fail_task(self.images_pdf_run_button, self.images_pdf_progress, "Erro ao gerar PDF", str(exc)))
        self._run_background_task(worker, "Processamento")

    # -------------------------- WebP para PNG --------------------------
    def _build_webp_to_png_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(panel, text="🌐 Converter WebP para PNG", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Converta arquivos WebP para PNG em lote, preservando transparência quando possível.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        actions.grid_columnconfigure(12, weight=1)
        self.webp_include_subfolders = tk.BooleanVar(value=False)
        self.webp_sort = tk.StringVar(value="Natural")
        ActionButton(actions, "Adicionar WebP", "secondary", self._webp_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._webp_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.webp_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Remover", "secondary", lambda: self.webp_table.remove_selected()).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._clear_table_confirm(self.webp_table)).grid(row=0, column=4, padx=4)
        ctk.CTkComboBox(actions, variable=self.webp_sort, values=["Natural", "Nome A-Z", "Data de modificação"], width=160, fg_color=THEME.bg_input, button_color=THEME.bg_surface, button_hover_color=THEME.bg_surface_hover, command=lambda v: self._sort_table_paths(self.webp_table, v)).grid(row=0, column=5, padx=8)
        self.webp_table = FileTable(panel)
        self.webp_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))
        output = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        output.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        output.grid_columnconfigure(0, weight=1)
        self.webp_output_folder = tk.StringVar(value="")
        ctk.CTkLabel(output, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkEntry(output, textvariable=self.webp_output_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, sticky="ew", padx=(14, 10), pady=(0, 14))
        ActionButton(output, "Escolher", "secondary", self._webp_choose_output_folder).grid(row=1, column=1, padx=(0, 14), pady=(0, 14))
        self.webp_progress = ProgressPanel(panel, "Progresso")
        self.webp_progress.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.webp_run_button = ActionButton(panel, "Converter para PNG", "primary", self._webp_run, icon="🌐")
        self.webp_run_button.grid(row=6, column=0, sticky="e", padx=18, pady=(0, 18))

    def _webp_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecionar WebP", filetypes=self._webp_filetypes())
        added = self._add_unique_to_table(self.webp_table, [Path(f) for f in files], is_supported_webp_file, self.webp_sort.get())
        if added: self.show_toast("WebP adicionados", f"{added} arquivo(s) adicionado(s).", "success")

    def _webp_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecionar pasta com WebP")
        if not folder: return
        paths = self._scan_files_in_folder(Path(folder), self.webp_include_subfolders.get(), is_supported_webp_file)
        added = self._add_unique_to_table(self.webp_table, paths, is_supported_webp_file, self.webp_sort.get())
        self.show_toast("Varredura concluída", f"{added} WebP adicionado(s).", "success" if added else "warning")

    def _webp_choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolher pasta de saída")
        if folder: self.webp_output_folder.set(folder)

    def _webp_run(self) -> None:
        paths = self._paths_from_table(self.webp_table)
        folder_raw = self.webp_output_folder.get().strip()
        if not paths or not folder_raw:
            self.show_toast("Dados incompletos", "Adicione WebP e escolha a pasta de saída.", "warning")
            return
        output_folder = Path(folder_raw)
        planned = [output_folder / f"{p.stem}.png" for p in paths]
        if not self._confirm_multiple_overwrite(planned):
            return
        self.webp_run_button.set_loading(True, "Convertendo...")
        self.webp_progress.start_indeterminate("Convertendo WebP...")
        def worker():
            try:
                def cb(value, msg): self.after(0, lambda value=value, msg=msg: self.webp_progress.set_progress(value, msg))
                result = convert_webp_to_png(paths, output_folder, cb)
                self.after(0, lambda result=result, output_folder=output_folder: self._finish_task(self.webp_run_button, self.webp_progress, "Conversão concluída", f"{len(result)} PNG(s) gerado(s).", output_folder))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._fail_task(self.webp_run_button, self.webp_progress, "Erro na conversão", str(exc)))
        self._run_background_task(worker, "Processamento")

    # -------------------------- Dividir PDF --------------------------
    def _build_split_pdf_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="ew")
        panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text="✂ Dividir PDF em partes", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Selecione um PDF, informe o número de partes e escolha a pasta de saída.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 14))
        self.split_pdf_input = tk.StringVar(value="")
        self.split_pdf_output_folder = tk.StringVar(value="")
        self.split_pdf_parts = tk.IntVar(value=2)
        ctk.CTkLabel(panel, text="PDF de entrada", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.split_pdf_input, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._split_pdf_choose_input).grid(row=2, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.split_pdf_output_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._split_pdf_choose_output_folder).grid(row=3, column=2, padx=18, pady=6)
        ctk.CTkLabel(panel, text="Número de partes", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.split_pdf_parts, height=36, width=120, fg_color=THEME.bg_input, border_color=THEME.border_medium).grid(row=4, column=1, sticky="w", padx=8, pady=6)
        self.split_pdf_progress = ProgressPanel(panel, "Progresso")
        self.split_pdf_progress.grid(row=5, column=0, columnspan=3, sticky="ew", padx=18, pady=(14, 14))
        self.split_pdf_run_button = ActionButton(panel, "Dividir PDF", "primary", self._split_pdf_run, icon="✂")
        self.split_pdf_run_button.grid(row=6, column=2, sticky="e", padx=18, pady=(0, 18))

    def _split_pdf_choose_input(self) -> None:
        file = filedialog.askopenfilename(title="Selecionar PDF", filetypes=self._pdf_filetypes())
        if file:
            self.split_pdf_input.set(file)
            if not self.split_pdf_output_folder.get().strip():
                self.split_pdf_output_folder.set(str(Path(file).parent))

    def _split_pdf_choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolher pasta de saída")
        if folder: self.split_pdf_output_folder.set(folder)

    def _split_pdf_run(self) -> None:
        input_raw = self.split_pdf_input.get().strip()
        folder_raw = self.split_pdf_output_folder.get().strip()
        try:
            parts = int(self.split_pdf_parts.get())
        except Exception:
            parts = 0
        if not input_raw or not folder_raw or parts < 2:
            self.show_toast("Dados incompletos", "Escolha o PDF, a pasta e informe pelo menos 2 partes.", "warning")
            return
        input_pdf = Path(input_raw)
        output_folder = Path(folder_raw)
        planned = [output_folder / f"{input_pdf.stem}_parte_{i:02d}_de_{parts:02d}.pdf" for i in range(1, parts + 1)]
        if not self._confirm_multiple_overwrite(planned):
            return
        self.split_pdf_run_button.set_loading(True, "Dividindo...")
        self.split_pdf_progress.start_indeterminate("Dividindo PDF...")
        def worker():
            try:
                def cb(value, msg): self.after(0, lambda value=value, msg=msg: self.split_pdf_progress.set_progress(value, msg))
                result = split_pdf_into_parts(input_pdf, output_folder, parts, cb)
                self.after(0, lambda result=result, output_folder=output_folder: self._finish_task(self.split_pdf_run_button, self.split_pdf_progress, "PDF dividido", f"{len(result)} parte(s) gerada(s).", output_folder))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._fail_task(self.split_pdf_run_button, self.split_pdf_progress, "Erro ao dividir PDF", str(exc)))
        self._run_background_task(worker, "Processamento")


    # -------------------------- Dividir documentos --------------------------
    def _document_filetypes(self):
        return [("Documentos", "*.md *.txt *.pdf"), ("Markdown", "*.md"), ("Texto", "*.txt"), ("PDF", "*.pdf"), ("Todos os arquivos", "*.*")]

    def _build_document_split_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(panel, text="🧩 Dividir documentos em partes", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text="Divida arquivos .md, .txt e .pdf. Textos são divididos por conteúdo; PDFs são divididos por páginas.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w").grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        actions.grid_columnconfigure(12, weight=1)
        self.docsplit_include_subfolders = tk.BooleanVar(value=False)
        self.docsplit_sort = tk.StringVar(value="Natural")
        ActionButton(actions, "Adicionar arquivos", "secondary", self._docsplit_add_files, icon="＋").grid(row=0, column=0, padx=(0, 8))
        ActionButton(actions, "Selecionar pasta", "secondary", self._docsplit_select_folder, icon="📁").grid(row=0, column=1, padx=4)
        ctk.CTkCheckBox(actions, text="Incluir subpastas", variable=self.docsplit_include_subfolders, fg_color=THEME.primary, hover_color=THEME.primary_hover, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=0, column=2, padx=8)
        ActionButton(actions, "Subir", "ghost", lambda: self.docsplit_table.move_selected_up()).grid(row=0, column=3, padx=4)
        ActionButton(actions, "Descer", "ghost", lambda: self.docsplit_table.move_selected_down()).grid(row=0, column=4, padx=4)
        ActionButton(actions, "Remover", "secondary", lambda: self.docsplit_table.remove_selected()).grid(row=0, column=5, padx=4)
        ActionButton(actions, "Limpar", "ghost", lambda: self._clear_table_confirm(self.docsplit_table)).grid(row=0, column=6, padx=4)
        ctk.CTkComboBox(actions, variable=self.docsplit_sort, values=["Natural", "Nome A-Z", "Data de modificação"], width=160, fg_color=THEME.bg_input, button_color=THEME.bg_surface, button_hover_color=THEME.bg_surface_hover, command=lambda v: self._sort_table_paths(self.docsplit_table, v)).grid(row=0, column=7, padx=8)

        self.docsplit_table = FileTable(panel)
        self.docsplit_table.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 14))

        options = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, corner_radius=16)
        options.grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 14))
        options.grid_columnconfigure(1, weight=1)
        self.docsplit_output_folder = tk.StringVar(value="")
        self.docsplit_parts = tk.IntVar(value=2)
        ctk.CTkLabel(options, text="Número de partes", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkEntry(options, textvariable=self.docsplit_parts, height=36, width=120, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 14))
        ctk.CTkLabel(options, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=0, column=1, sticky="w", padx=14, pady=(14, 6))
        ctk.CTkEntry(options, textvariable=self.docsplit_output_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=1, column=1, sticky="ew", padx=(14, 10), pady=(0, 14))
        ActionButton(options, "Escolher", "secondary", self._docsplit_choose_output_folder).grid(row=1, column=2, padx=(0, 14), pady=(0, 14))

        self.docsplit_summary_card = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        self.docsplit_summary_card.grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.docsplit_summary_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.docsplit_summary_card, text="Resumo final", font=(THEME.font_family, 14, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        self.docsplit_summary_text = ctk.CTkLabel(self.docsplit_summary_card, text="Nenhum documento dividido ainda.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w", justify="left")
        self.docsplit_summary_text.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        self.docsplit_progress = ProgressPanel(panel, "Progresso")
        self.docsplit_progress.grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.docsplit_run_button = ActionButton(panel, "Dividir documentos", "primary", self._docsplit_run, icon="🧩")
        self.docsplit_run_button.grid(row=7, column=0, sticky="e", padx=18, pady=(0, 18))

    def _docsplit_add_files(self) -> None:
        files = filedialog.askopenfilenames(title="Selecionar documentos", filetypes=self._document_filetypes())
        added = self._add_unique_to_table(self.docsplit_table, [Path(f) for f in files], is_supported_document_split_file, self.docsplit_sort.get())
        if added:
            self.show_toast("Documentos adicionados", f"{added} arquivo(s) adicionado(s).", "success")
        self.status_text.configure(text=f"Dividir documentos: {len(self._paths_from_table(self.docsplit_table))} arquivo(s) na lista.")

    def _docsplit_select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecionar pasta com documentos")
        if not folder:
            return
        self.status_text.configure(text="Dividir documentos: varrendo pasta...")
        paths = self._scan_files_in_folder(Path(folder), self.docsplit_include_subfolders.get(), is_supported_document_split_file)
        added = self._add_unique_to_table(self.docsplit_table, paths, is_supported_document_split_file, self.docsplit_sort.get())
        self.show_toast("Varredura concluída", f"{added} documento(s) adicionado(s).", "success" if added else "warning")
        self.status_text.configure(text=f"Dividir documentos: {len(self._paths_from_table(self.docsplit_table))} arquivo(s) na lista.")

    def _docsplit_choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolher pasta de saída")
        if folder:
            self.docsplit_output_folder.set(folder)

    def _docsplit_run(self) -> None:
        paths = self._paths_from_table(self.docsplit_table)
        folder_raw = self.docsplit_output_folder.get().strip()
        try:
            parts = int(self.docsplit_parts.get())
        except Exception:
            parts = 0
        if not paths or not folder_raw or parts < 2:
            self.show_toast("Dados incompletos", "Adicione documentos, escolha a pasta de saída e informe pelo menos 2 partes.", "warning")
            return
        output_folder = Path(folder_raw)
        planned: List[Path] = []
        for path in paths:
            p = Path(path)
            suffix = p.suffix.lower()
            planned_parts = max(2, parts)
            # PDFs podem ter menos páginas que partes; a confirmação conservadora ainda é segura.
            for i in range(1, planned_parts + 1):
                planned.append(output_folder / f"{p.stem}_parte_{i:02d}_de_{planned_parts:02d}{suffix}")
        if not self._confirm_multiple_overwrite(planned):
            return
        self.docsplit_run_button.set_loading(True, "Dividindo...")
        self.docsplit_progress.reset_success_color()
        self.docsplit_progress.start_indeterminate("Dividindo documentos...")
        self.status_text.configure(text="Dividir documentos: processando...")

        def worker():
            try:
                def cb(value, msg):
                    self.after(0, lambda v=value, m=msg: self.docsplit_progress.set_progress(v, m))
                result = split_document_files_into_parts(paths, output_folder, parts, cb)
                self.after(0, lambda r=result: self._docsplit_finish(r))
            except Exception as exc:
                self.after(0, lambda e=exc: self._fail_task(self.docsplit_run_button, self.docsplit_progress, "Erro ao dividir documentos", str(e)))

        self._run_background_task(worker, "Processamento")

    def _docsplit_finish(self, result: Dict[str, object]) -> None:
        outputs = result.get("outputs", [])
        errors = result.get("errors", [])
        folder = Path(result.get("output_folder", self.docsplit_output_folder.get().strip() or "."))
        input_count = result.get("input_count", 0)
        output_count = result.get("output_count", len(outputs))
        summary = f"Documentos processados: {input_count}\nArquivos gerados: {output_count}\nPasta: {folder}"
        if errors:
            summary += f"\nAvisos/erros: {len(errors)} arquivo(s) não processado(s)."
        self.docsplit_summary_text.configure(text=summary, text_color="#BBF7D0" if not errors else "#FDE68A")
        self._finish_task(self.docsplit_run_button, self.docsplit_progress, "Documentos divididos", f"{output_count} arquivo(s) gerado(s).", folder)
        if errors:
            self.show_toast("Divisão concluída com avisos", f"{len(errors)} arquivo(s) não foi processado. Veja o resumo.", "warning")


    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------
    def _build_json_view(self) -> None:
        root = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        cards.grid_columnconfigure((0, 1), weight=1, uniform="json_tools")
        tools = [
            ("parts", "{}", "Dividir por partes", "Divida a lista principal em uma quantidade definida de arquivos.", "JSON"),
            ("size", "📏", "Dividir por tamanho", "Gere partes por tamanho aproximado em MB.", "JSON"),
        ]
        for index, (tool_id, icon, title, desc, category) in enumerate(tools):
            ToolCard(
                cards,
                icon=icon,
                title=title,
                description=desc,
                category=category,
                active=getattr(self, "json_tool", "parts") == tool_id,
                command=lambda t=tool_id: self._set_json_tool(t),
            ).grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0 if index == len(tools) - 1 else 8))

        self.json_body = ctk.CTkFrame(root, fg_color="transparent")
        self.json_body.grid(row=1, column=0, sticky="nsew")
        self.json_body.grid_columnconfigure(0, weight=1)
        self._build_json_split_tool(self.json_body)

    def _set_json_tool(self, tool_id: str) -> None:
        self.json_tool = tool_id
        self.clear_content()
        self._build_json_view()

    def _json_filetypes(self):
        return [("JSON", "*.json"), ("Todos os arquivos", "*.*")]

    def _build_json_split_tool(self, master) -> None:
        master.grid_columnconfigure(0, weight=1)
        panel = ctk.CTkFrame(master, fg_color=THEME.bg_surface, border_color=THEME.border_soft, border_width=1, corner_radius=20)
        panel.grid(row=0, column=0, sticky="nsew")
        panel.grid_columnconfigure(1, weight=1)

        mode = getattr(self, "json_tool", "parts")
        mode_title = "Dividir JSON por número de partes" if mode == "parts" else "Dividir JSON por tamanho aproximado"
        mode_hint = "Escolha quantas partes deseja gerar." if mode == "parts" else "Defina o tamanho aproximado máximo de cada parte em MB."
        ctk.CTkLabel(panel, text=f"{{}} {mode_title}", font=(THEME.font_family, 18, "bold"), text_color=THEME.text_primary, anchor="w").grid(row=0, column=0, columnspan=3, sticky="ew", padx=18, pady=(16, 4))
        ctk.CTkLabel(panel, text=f"O app detecta a lista principal, preserva a estrutura JSON quando possível e gera arquivos válidos. {mode_hint}", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w", wraplength=900).grid(row=1, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 14))

        self.json_input = tk.StringVar(value=getattr(self, "json_input", tk.StringVar(value="")).get() if hasattr(self, "json_input") else "")
        self.json_output_folder = tk.StringVar(value=getattr(self, "json_output_folder", tk.StringVar(value="")).get() if hasattr(self, "json_output_folder") else "")
        self.json_prefix = tk.StringVar(value=getattr(self, "json_prefix", tk.StringVar(value="json_parte")).get() if hasattr(self, "json_prefix") else "json_parte")
        self.json_parts = tk.StringVar(value=getattr(self, "json_parts", tk.StringVar(value="3")).get() if hasattr(self, "json_parts") else "3")
        self.json_size_mb = tk.StringVar(value=getattr(self, "json_size_mb", tk.StringVar(value="5")).get() if hasattr(self, "json_size_mb") else "5")

        ctk.CTkLabel(panel, text="Arquivo JSON", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=2, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.json_input, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._json_choose_input).grid(row=2, column=2, padx=18, pady=6)

        ctk.CTkLabel(panel, text="Pasta de saída", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=3, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.json_output_folder, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        ActionButton(panel, "Escolher", "secondary", self._json_choose_output_folder).grid(row=3, column=2, padx=18, pady=6)

        ctk.CTkLabel(panel, text="Prefixo dos arquivos", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=4, column=0, sticky="w", padx=18, pady=6)
        ctk.CTkEntry(panel, textvariable=self.json_prefix, height=36, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=4, column=1, sticky="ew", padx=8, pady=6)

        if mode == "parts":
            ctk.CTkLabel(panel, text="Número de partes", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=5, column=0, sticky="w", padx=18, pady=6)
            ctk.CTkEntry(panel, textvariable=self.json_parts, height=36, width=120, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=5, column=1, sticky="w", padx=8, pady=6)
        else:
            ctk.CTkLabel(panel, text="Tamanho aproximado por parte (MB)", font=(THEME.font_family, 12, "bold"), text_color=THEME.text_secondary).grid(row=5, column=0, sticky="w", padx=18, pady=6)
            ctk.CTkEntry(panel, textvariable=self.json_size_mb, height=36, width=120, fg_color=THEME.bg_input, border_color=THEME.border_medium, text_color=THEME.text_primary).grid(row=5, column=1, sticky="w", padx=8, pady=6)

        preview = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        preview.grid(row=6, column=0, columnspan=3, sticky="ew", padx=18, pady=(14, 10))
        preview.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="json_preview")
        self.json_preview_size = ctk.CTkLabel(preview, text="Tamanho\n—", font=(THEME.font_family, 12), text_color=THEME.text_secondary)
        self.json_preview_path = ctk.CTkLabel(preview, text="Lista detectada\n—", font=(THEME.font_family, 12), text_color=THEME.text_secondary)
        self.json_preview_items = ctk.CTkLabel(preview, text="Itens\n—", font=(THEME.font_family, 12), text_color=THEME.text_secondary)
        self.json_preview_parts = ctk.CTkLabel(preview, text="Partes previstas\n—", font=(THEME.font_family, 12), text_color=THEME.text_secondary)
        self.json_preview_size.grid(row=0, column=0, padx=12, pady=14, sticky="ew")
        self.json_preview_path.grid(row=0, column=1, padx=12, pady=14, sticky="ew")
        self.json_preview_items.grid(row=0, column=2, padx=12, pady=14, sticky="ew")
        self.json_preview_parts.grid(row=0, column=3, padx=12, pady=14, sticky="ew")

        self.json_progress = ProgressPanel(panel, "Progresso")
        self.json_progress.grid(row=7, column=0, columnspan=3, sticky="ew", padx=18, pady=(6, 14))

        self.json_result_card = ctk.CTkFrame(panel, fg_color=THEME.bg_surface_alt, border_color=THEME.border_soft, border_width=1, corner_radius=16)
        self.json_result_card.grid(row=8, column=0, columnspan=3, sticky="ew", padx=18, pady=(0, 14))
        self.json_result_card.grid_columnconfigure(0, weight=1)
        self.json_result_title = ctk.CTkLabel(self.json_result_card, text="Resumo final", font=(THEME.font_family, 14, "bold"), text_color=THEME.text_primary, anchor="w")
        self.json_result_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))
        self.json_result_text = ctk.CTkLabel(self.json_result_card, text="Aguardando processamento.", font=(THEME.font_family, 12), text_color=THEME.text_secondary, anchor="w", justify="left")
        self.json_result_text.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        button_bar = ctk.CTkFrame(panel, fg_color="transparent")
        button_bar.grid(row=9, column=0, columnspan=3, sticky="e", padx=18, pady=(0, 18))
        ActionButton(button_bar, "Atualizar prévia", "secondary", self._json_preview_run, icon="🔎").grid(row=0, column=0, padx=(0, 8))
        self.json_run_button = ActionButton(button_bar, "Dividir JSON", "primary", self._json_split_run, icon="{}")
        self.json_run_button.grid(row=0, column=1)

    def _json_choose_input(self) -> None:
        file = filedialog.askopenfilename(title="Selecionar JSON", filetypes=self._json_filetypes())
        if not file:
            return
        self.json_input.set(file)
        path = Path(file)
        if not self.json_output_folder.get().strip():
            self.json_output_folder.set(str(path.parent))
        if self.json_prefix.get().strip() in {"", "json_parte"}:
            self.json_prefix.set(path.stem)
        self._json_preview_run()

    def _json_choose_output_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolher pasta de saída")
        if folder:
            self.json_output_folder.set(folder)

    def _json_parse_options(self) -> Tuple[Path, Path, str, int, float]:
        input_raw = self.json_input.get().strip()
        output_raw = self.json_output_folder.get().strip()
        prefix = self.json_prefix.get().strip() or "json_parte"
        if not input_raw or not output_raw:
            raise ValueError("Escolha o arquivo JSON de entrada e a pasta de saída.")
        input_path = Path(input_raw)
        if not input_path.exists() or input_path.suffix.lower() != ".json":
            raise ValueError("Escolha um arquivo .json válido.")
        output_folder = Path(output_raw)
        try:
            parts = int(str(self.json_parts.get()).strip())
        except Exception:
            parts = 0
        try:
            target_mb = float(str(self.json_size_mb.get()).replace(",", ".").strip())
        except Exception:
            target_mb = 0
        return input_path, output_folder, prefix, parts, target_mb

    def _json_preview_run(self) -> None:
        try:
            input_path, _output_folder, _prefix, parts, target_mb = self._json_parse_options()
            mode = getattr(self, "json_tool", "parts")
            if mode == "parts" and parts < 1:
                raise ValueError("Informe um número de partes maior que zero.")
            if mode == "size" and target_mb <= 0:
                raise ValueError("Informe um tamanho maior que zero.")
        except Exception as exc:
            self.show_toast("Prévia indisponível", str(exc), "warning")
            return
        self.json_progress.start_indeterminate("Analisando JSON...")
        self.status_text.configure(text="JSON: analisando estrutura para prévia...")

        def worker() -> None:
            try:
                info = analyze_json_split(input_path, mode, parts=parts, target_mb=target_mb)
                self.after(0, lambda info=info: self._json_preview_finish(info, None))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._json_preview_finish({}, exc))

        self._run_background_task(worker, "Processamento")

    def _json_preview_finish(self, info: Dict[str, object], error: Optional[Exception]) -> None:
        if error:
            self.json_progress.stop("Falha ao analisar JSON.")
            self.show_toast("Erro na prévia", str(error), "error")
            self.status_text.configure(text="JSON: erro ao gerar prévia.")
            return
        sizes = info.get("estimated_sizes", []) or []
        avg_size = int(sum(sizes) / len(sizes)) if sizes else 0
        self.json_preview_size.configure(text=f"Tamanho\n{format_size(int(info.get('input_size', 0)))}")
        self.json_preview_path.configure(text=f"Lista detectada\n{info.get('list_path_label', '—')}")
        self.json_preview_items.configure(text=f"Itens\n{info.get('item_count', 0)}")
        self.json_preview_parts.configure(text=f"Partes previstas\n{info.get('part_count', 0)} • média {format_size(avg_size)}")
        self.json_progress.stop("Prévia atualizada.")
        self.status_text.configure(text="JSON: prévia atualizada.")
        self.show_toast("Prévia JSON pronta", f"{info.get('part_count', 0)} parte(s) previstas.", "success")

    def _json_split_run(self) -> None:
        try:
            input_path, output_folder, prefix, parts, target_mb = self._json_parse_options()
            mode = getattr(self, "json_tool", "parts")
            if mode == "parts" and parts < 1:
                raise ValueError("Informe um número de partes maior que zero.")
            if mode == "size" and target_mb <= 0:
                raise ValueError("Informe um tamanho maior que zero.")
        except Exception as exc:
            self.show_toast("Dados inválidos", str(exc), "warning")
            return

        # Arquivos grandes não podem ser analisados no callback da interface.
        # Primeiro analisamos em thread; depois voltamos ao mainloop para confirmar sobrescrita.
        self.json_run_button.set_loading(True, "Analisando...")
        self.json_progress.start_indeterminate("Analisando JSON antes da divisão...")
        self.status_text.configure(text="JSON: analisando arquivo antes de dividir...")

        def analyzer() -> None:
            try:
                info = analyze_json_split(input_path, mode, parts=parts, target_mb=target_mb)
                self.after(0, lambda info=info: self._json_split_after_analysis(input_path, output_folder, prefix, mode, parts, target_mb, info, None))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._json_split_after_analysis(input_path, output_folder, prefix, mode, parts, target_mb, {}, exc))

        self._run_background_task(analyzer, "Análise JSON")

    def _json_split_after_analysis(
        self,
        input_path: Path,
        output_folder: Path,
        prefix: str,
        mode: str,
        parts: int,
        target_mb: float,
        info: Dict[str, object],
        error: Optional[Exception],
    ) -> None:
        if error:
            self.json_run_button.set_loading(False)
            self.json_progress.stop("Erro ao analisar JSON.")
            self.status_text.configure(text="JSON: erro ao analisar arquivo.")
            self.show_toast("Erro ao analisar JSON", str(error), "error")
            return

        planned = build_json_output_paths(output_folder, prefix, int(info.get("part_count", 0)))
        if not planned:
            self.json_run_button.set_loading(False)
            self.json_progress.stop("Nenhuma parte foi planejada.")
            self.show_toast("Divisão inválida", "A divisão não gerou partes válidas.", "warning")
            return

        if not self._confirm_multiple_overwrite(planned):
            self.json_run_button.set_loading(False)
            self.json_progress.stop("Divisão cancelada pelo usuário.")
            self.status_text.configure(text="JSON: divisão cancelada.")
            return

        if info.get("large_file_warning"):
            self.show_toast(
                "Arquivo JSON grande",
                "A divisão continuará em segundo plano. O processamento pode demorar.",
                "warning",
            )

        self.json_run_button.set_loading(True, "Dividindo...")
        self.json_progress.reset_success_color()
        self.json_progress.set_progress(0, "Preparando divisão JSON...")
        self.status_text.configure(text="JSON: dividindo arquivo em partes...")

        def worker() -> None:
            try:
                def cb(value: float, msg: str) -> None:
                    self.after(0, lambda value=value, msg=msg: self.json_progress.set_progress(value, msg))
                    self.after(0, lambda value=value: self.status_progress.set(value))
                written, summary = split_json_file(input_path, output_folder, prefix, mode, parts=parts, target_mb=target_mb, progress_callback=cb)
                self.after(0, lambda written=written, summary=summary: self._json_split_finish(written, summary, None))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._json_split_finish([], {}, exc))

        self._run_background_task(worker, "Processamento")

    def _json_split_finish(self, written: List[Path], summary: Dict[str, object], error: Optional[Exception]) -> None:
        self.json_run_button.set_loading(False)
        self.status_progress.set(0)
        if error:
            self.json_progress.stop("Erro ao dividir JSON.")
            self.status_text.configure(text="JSON: erro ao dividir arquivo.")
            self.show_toast("Erro ao dividir JSON", str(error), "error")
            return
        total_size = sum(safe_stat_size(p) for p in written)
        folder = written[0].parent if written else Path(self.json_output_folder.get().strip() or ".")
        self.json_progress.complete(f"JSON dividido: {len(written)} arquivo(s) gerado(s).")
        self.json_result_title.configure(text="✓ JSON dividido com sucesso")
        self.json_result_text.configure(
            text=(
                f"Arquivos gerados: {len(written)}\n"
                f"Itens distribuídos: {summary.get('item_count', 0)}\n"
                f"Lista detectada: {summary.get('list_path_label', '—')}\n"
                f"Tamanho total gerado: {format_size(total_size)}\n"
                f"Pasta: {folder}"
            ),
            text_color="#BBF7D0",
        )
        self.status_text.configure(text="JSON: divisão concluída com sucesso.")
        self.show_toast("JSON dividido", f"{len(written)} arquivo(s) gerado(s).", "success")
        self._open_folder_if_enabled(folder)

    def _clear_table_confirm(self, table: FileTable) -> None:
        if table.get_all_values() and not messagebox.askyesno("Limpar lista", "Deseja limpar todos os arquivos da lista?"):
            return
        table.clear()
        self.status_text.configure(text="Lista limpa.")

    def _open_folder_if_enabled(self, folder: Path) -> None:
        if self.settings_config.get("open_folder_on_finish", True):
            try:
                open_path_in_os(Path(folder))
            except Exception:
                pass

    def _finish_task(self, button: ActionButton, progress: ProgressPanel, title: str, message: str, output_folder: Path) -> None:
        button.set_loading(False)
        self.status_progress.set(0)
        progress.complete(message)
        self.status_text.configure(text=title)
        self.show_toast(title, message, "success")
        self._open_folder_if_enabled(output_folder)

    def _fail_task(self, button: ActionButton, progress: ProgressPanel, title: str, message: str) -> None:
        button.set_loading(False)
        self.status_progress.set(0)
        progress.stop(title)
        self.status_text.configure(text=title)
        self.show_toast(title, message, "error")

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
                self.after(0, lambda exe=exe, version_line=version_line: self._settings_finish_ffmpeg_test(exe, version_line, None))
            except Exception as exc:
                self.after(0, lambda exc=exc: self._settings_finish_ffmpeg_test("", "", exc))

        self._run_background_task(worker, "Processamento")

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
            self.after(0, lambda ok=ok, failed=failed: self._settings_finish_dependencies(ok, failed))

        self._run_background_task(worker, "Processamento")

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
        if section_id == "json_tools":
            return [
                ("{}", "Dividir por partes", "Divide uma lista JSON em partes equilibradas.", "Dados", True),
                ("📏", "Dividir por tamanho", "Gera partes por tamanho aproximado em MB.", "Dados", True),
                ("🔎", "Prévia semântica", "Detecta a maior lista dentro do JSON.", "Análise", True),
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
