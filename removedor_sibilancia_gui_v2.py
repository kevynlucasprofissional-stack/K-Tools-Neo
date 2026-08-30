#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Removedor de Sibilância e Chiado V2 com interface CustomTkinter.

Recursos:
- Instala automaticamente as bibliotecas Python ausentes.
- De-esser dinâmico para reduzir "S", "X", "CH" e "SH" agressivos.
- Redução opcional de chiado por spectral gating.
- Presets para diferentes tipos de voz.
- Processamento em segundo plano para não travar a interface.
- Entrada em M4A, AAC, MP3, MP4, WAV, FLAC, OGG, AIFF e outros formatos.
- Conversão automática com FFmpeg quando o SoundFile não reconhecer o arquivo.
- Processamento em blocos para áudios longos, reduzindo o consumo de memória.
- Saída em WAV/RF64 ou FLAC de 24 bits.
- Botão para copiar todo o log para a área de transferência.

Execute:
    py removedor_sibilancia_gui_v2.py
"""

from __future__ import annotations

import importlib.util
import os
import platform
import subprocess
import sys
import threading
import tempfile
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Instalação automática de dependências
# ---------------------------------------------------------------------------

REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter>=5.2",
    "numpy": "numpy>=1.24",
    "scipy": "scipy>=1.10",
    "soundfile": "soundfile>=0.12",
    "noisereduce": "noisereduce>=3.0",
    "imageio_ffmpeg": "imageio-ffmpeg>=0.6",
}


def install_missing_packages() -> None:
    """Instala com pip apenas os módulos que ainda não estão disponíveis."""
    missing = [
        pip_name
        for import_name, pip_name in REQUIRED_PACKAGES.items()
        if importlib.util.find_spec(import_name) is None
    ]

    if not missing:
        return

    status_window = None
    status_label = None

    try:
        import tkinter as bootstrap_tk

        status_window = bootstrap_tk.Tk()
        status_window.title("Preparando o aplicativo")
        status_window.geometry("470x150")
        status_window.resizable(False, False)

        bootstrap_tk.Label(
            status_window,
            text="Instalando bibliotecas necessárias",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(24, 8))

        status_label = bootstrap_tk.Label(
            status_window,
            text="Aguarde...",
            font=("Segoe UI", 10),
        )
        status_label.pack(pady=5)
        status_window.update()
    except Exception:
        status_window = None

    try:
        for package in missing:
            if status_label is not None and status_window is not None:
                status_label.configure(text=f"Instalando: {package}")
                status_window.update()

            print(f"[Dependências] Instalando {package}...")
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    package,
                ]
            )
    except Exception as exc:
        message = (
            "Não foi possível instalar automaticamente as bibliotecas.\n\n"
            f"Detalhes: {exc}\n\n"
            "Tente abrir o terminal como administrador ou executar:\n"
            f"{sys.executable} -m pip install "
            + " ".join(REQUIRED_PACKAGES.values())
        )

        if status_window is not None:
            try:
                from tkinter import messagebox

                messagebox.showerror("Erro na instalação", message)
            except Exception:
                pass

        print(message, file=sys.stderr)
        raise
    finally:
        if status_window is not None:
            try:
                status_window.destroy()
            except Exception:
                pass


install_missing_packages()


# Imports realizados somente depois do instalador automático.
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import imageio_ffmpeg
import noisereduce as nr
import numpy as np
import soundfile as sf
from scipy.ndimage import uniform_filter1d
from scipy.signal import butter, sosfiltfilt


# ---------------------------------------------------------------------------
# Configurações e processamento de áudio
# ---------------------------------------------------------------------------

@dataclass
class AudioSettings:
    use_deesser: bool = True
    use_noise_reduction: bool = False
    normalize: bool = True

    low_freq: float = 5000.0
    high_freq: float = 10000.0
    threshold_db: float = -32.0
    max_reduction_db: float = 8.0
    ratio: float = 6.0
    attack_ms: float = 2.0
    release_ms: float = 80.0

    noise_strength: float = 0.55


class ProcessingCancelled(Exception):
    """Exceção interna para cancelamento solicitado pelo usuário."""


def smooth_gain(
    target_gain: np.ndarray,
    sample_rate: int,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    """
    Suaviza a atuação do de-esser.

    Ataque rápido: reduz rapidamente a sibilância.
    Release mais lento: devolve o brilho da voz sem criar bombeamento.
    """
    if target_gain.size == 0:
        return target_gain

    attack_samples = max(sample_rate * attack_ms / 1000.0, 1.0)
    release_samples = max(sample_rate * release_ms / 1000.0, 1.0)

    attack_coefficient = np.exp(-1.0 / attack_samples)
    release_coefficient = np.exp(-1.0 / release_samples)

    smoothed = np.empty_like(target_gain, dtype=np.float32)
    smoothed[0] = target_gain[0]

    for index in range(1, target_gain.size):
        coefficient = (
            attack_coefficient
            if target_gain[index] < smoothed[index - 1]
            else release_coefficient
        )
        smoothed[index] = (
            coefficient * smoothed[index - 1]
            + (1.0 - coefficient) * target_gain[index]
        )

    return smoothed


def apply_deesser(
    audio: np.ndarray,
    sample_rate: int,
    settings: AudioSettings,
    cancel_event: threading.Event,
    channel_progress: Optional[Callable[[float], None]] = None,
) -> np.ndarray:
    """
    De-esser dinâmico split-band.

    A faixa sibilante é isolada por um filtro passa-faixa. Quando o envelope
    dessa faixa ultrapassa o limiar, somente ela é atenuada.
    """
    if audio.ndim == 1:
        audio = audio[:, np.newaxis]

    nyquist = sample_rate / 2.0
    low_freq = max(100.0, settings.low_freq)
    high_freq = min(settings.high_freq, nyquist - 100.0)

    if low_freq >= high_freq:
        raise ValueError(
            "A faixa do de-esser é incompatível com a taxa de amostragem "
            f"de {sample_rate} Hz. Diminua a frequência final."
        )

    sos = butter(
        N=4,
        Wn=[low_freq, high_freq],
        btype="bandpass",
        fs=sample_rate,
        output="sos",
    )

    result = np.empty_like(audio, dtype=np.float32)
    number_of_channels = audio.shape[1]

    for channel in range(number_of_channels):
        if cancel_event.is_set():
            raise ProcessingCancelled()

        signal = audio[:, channel].astype(np.float32, copy=False)
        sibilant_band = sosfiltfilt(sos, signal).astype(np.float32)

        # Janela curta para reagir aos fonemas sibilantes.
        window_size = max(3, int(sample_rate * 0.008))
        if window_size % 2 == 0:
            window_size += 1

        envelope = np.sqrt(
            uniform_filter1d(
                np.square(sibilant_band, dtype=np.float32),
                size=window_size,
                mode="nearest",
            )
            + 1e-12
        )

        envelope_db = 20.0 * np.log10(envelope + 1e-12)
        excess_db = np.maximum(envelope_db - settings.threshold_db, 0.0)

        ratio = max(settings.ratio, 1.01)
        reduction_db = excess_db * (1.0 - 1.0 / ratio)
        reduction_db = np.minimum(reduction_db, settings.max_reduction_db)

        target_gain = np.power(10.0, -reduction_db / 20.0).astype(np.float32)
        gain = smooth_gain(
            target_gain,
            sample_rate,
            settings.attack_ms,
            settings.release_ms,
        )

        # Split-band: preserva todo o espectro e substitui apenas a faixa
        # sibilante por uma versão dinamicamente atenuada.
        result[:, channel] = signal - sibilant_band + (sibilant_band * gain)

        if channel_progress:
            channel_progress((channel + 1) / number_of_channels)

    return result


def apply_noise_reduction(
    audio: np.ndarray,
    sample_rate: int,
    settings: AudioSettings,
    cancel_event: threading.Event,
    channel_progress: Optional[Callable[[float], None]] = None,
) -> np.ndarray:
    """Reduz chiado estacionário em cada canal usando spectral gating."""
    if audio.ndim == 1:
        audio = audio[:, np.newaxis]

    result = np.empty_like(audio, dtype=np.float32)
    number_of_channels = audio.shape[1]

    # FFT adaptada à taxa de amostragem.
    if sample_rate >= 44100:
        n_fft = 2048
    elif sample_rate >= 22050:
        n_fft = 1024
    else:
        n_fft = 512

    for channel in range(number_of_channels):
        if cancel_event.is_set():
            raise ProcessingCancelled()

        result[:, channel] = nr.reduce_noise(
            y=audio[:, channel],
            sr=sample_rate,
            stationary=True,
            prop_decrease=float(np.clip(settings.noise_strength, 0.0, 1.0)),
            n_fft=n_fft,
            use_tqdm=False,
        ).astype(np.float32)

        if channel_progress:
            channel_progress((channel + 1) / number_of_channels)

    return result


def normalize_peak(audio: np.ndarray, target_peak: float = 0.98) -> np.ndarray:
    """Normaliza o maior pico sem alterar a relação entre os canais."""
    peak = float(np.max(np.abs(audio)))

    if peak <= 1e-12:
        return audio

    return audio * (target_peak / peak)


def prevent_clipping(audio: np.ndarray, limit: float = 0.999) -> np.ndarray:
    """Atenua somente quando o processamento ultrapassa o limite digital."""
    peak = float(np.max(np.abs(audio)))

    if peak > limit:
        return audio * (limit / peak)

    return audio


def _ffmpeg_creation_flags() -> int:
    """Evita que o FFmpeg abra uma janela de terminal extra no Windows."""
    return getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def convert_to_temporary_wav(
    input_path: Path,
    temporary_wav: Path,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
    log_callback: Callable[[str], None],
) -> None:
    """Converte qualquer formato reconhecido pelo FFmpeg para WAV float32."""
    ffmpeg_executable = imageio_ffmpeg.get_ffmpeg_exe()
    log_callback("O formato será convertido automaticamente com FFmpeg.")
    log_callback(f"FFmpeg: {ffmpeg_executable}")
    progress_callback(0.06, "Convertendo o áudio para um formato de trabalho...")

    command = [
        ffmpeg_executable,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-map_metadata",
        "-1",
        "-c:a",
        "pcm_f32le",
        str(temporary_wav),
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=_ffmpeg_creation_flags(),
    )

    while process.poll() is None:
        if cancel_event.is_set():
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            raise ProcessingCancelled()
        time.sleep(0.10)

    _, stderr = process.communicate()

    if process.returncode != 0 or not temporary_wav.is_file():
        details = (stderr or "Erro desconhecido do FFmpeg.").strip()
        raise RuntimeError(
            "O FFmpeg não conseguiu decodificar o arquivo de entrada.\n"
            f"Detalhes: {details}"
        )

    progress_callback(0.14, "Conversão concluída.")
    log_callback("Conversão temporária concluída com sucesso.")


def prepare_readable_audio(
    input_path: Path,
    temporary_directory: Path,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
    log_callback: Callable[[str], None],
) -> Path:
    """Usa o arquivo diretamente ou cria um WAV temporário via FFmpeg."""
    progress_callback(0.03, "Analisando o arquivo de entrada...")

    try:
        with sf.SoundFile(str(input_path), mode="r") as audio_file:
            if audio_file.frames <= 0:
                raise ValueError("O arquivo de áudio está vazio.")
        log_callback("O arquivo é compatível diretamente com o SoundFile.")
        return input_path
    except (sf.LibsndfileError, RuntimeError, ValueError) as direct_error:
        log_callback(
            "Leitura direta indisponível: "
            f"{type(direct_error).__name__}: {direct_error}"
        )

    temporary_wav = temporary_directory / "entrada_convertida.wav"
    convert_to_temporary_wav(
        input_path,
        temporary_wav,
        cancel_event,
        progress_callback,
        log_callback,
    )
    return temporary_wav


def process_audio_chunk(
    audio: np.ndarray,
    sample_rate: int,
    settings: AudioSettings,
    cancel_event: threading.Event,
) -> np.ndarray:
    """Aplica os tratamentos em um bloco de áudio."""
    processed = audio.astype(np.float32, copy=False)

    # Blocos muito curtos não possuem amostras suficientes para filtros FFT.
    can_filter = len(processed) >= max(256, int(sample_rate * 0.10))

    if settings.use_noise_reduction and can_filter:
        processed = apply_noise_reduction(
            processed,
            sample_rate,
            settings,
            cancel_event,
        )

    if settings.use_deesser and can_filter:
        processed = apply_deesser(
            processed,
            sample_rate,
            settings,
            cancel_event,
        )

    return np.nan_to_num(
        processed,
        nan=0.0,
        posinf=0.999,
        neginf=-0.999,
    ).astype(np.float32, copy=False)


def process_in_chunks(
    readable_input: Path,
    temporary_processed: Path,
    settings: AudioSettings,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
    log_callback: Callable[[str], None],
) -> tuple[int, int, int]:
    """
    Processa o áudio em blocos sobrepostos e faz crossfade nas emendas.

    Isso permite tratar audiobooks longos sem carregar o arquivo inteiro na RAM.
    """
    with sf.SoundFile(str(readable_input), mode="r") as source:
        sample_rate = int(source.samplerate)
        channels = int(source.channels)
        total_frames = int(source.frames)

        if total_frames <= 0:
            raise ValueError("O arquivo de áudio está vazio.")

        duration = total_frames / sample_rate
        log_callback(f"Taxa de amostragem: {sample_rate} Hz")
        log_callback(f"Canais: {channels}")
        log_callback(f"Duração: {duration / 60:.2f} minutos")
        log_callback("Modo de processamento: blocos de 30 segundos.")

        if settings.use_noise_reduction:
            log_callback(
                f"Redução de chiado: {settings.noise_strength * 100:.0f}%"
            )
        else:
            log_callback("Redução de chiado: desativada.")

        if settings.use_deesser:
            log_callback(
                "De-esser: "
                f"{settings.low_freq:.0f}–{settings.high_freq:.0f} Hz | "
                f"limiar {settings.threshold_db:.1f} dB | "
                f"redução máxima {settings.max_reduction_db:.1f} dB"
            )
        else:
            log_callback("De-esser: desativado.")

        chunk_frames = max(sample_rate * 30, 4096)
        overlap_frames = min(max(int(sample_rate * 0.25), 512), chunk_frames // 4)
        step_frames = chunk_frames - overlap_frames
        estimated_chunks = max(1, int(np.ceil(max(total_frames - overlap_frames, 1) / step_frames)))

        previous_tail: Optional[np.ndarray] = None
        position = 0
        chunk_index = 0

        with sf.SoundFile(
            str(temporary_processed),
            mode="w",
            samplerate=sample_rate,
            channels=channels,
            format="WAV",
            subtype="FLOAT",
        ) as destination:
            while position < total_frames:
                if cancel_event.is_set():
                    raise ProcessingCancelled()

                source.seek(position)
                chunk = source.read(
                    frames=chunk_frames,
                    dtype="float32",
                    always_2d=True,
                )

                if len(chunk) == 0:
                    break

                processed = process_audio_chunk(
                    chunk,
                    sample_rate,
                    settings,
                    cancel_event,
                )

                is_last = position + len(chunk) >= total_frames

                if previous_tail is None:
                    if is_last or len(processed) <= overlap_frames:
                        destination.write(processed)
                    else:
                        destination.write(processed[:-overlap_frames])
                        previous_tail = processed[-overlap_frames:].copy()
                else:
                    overlap = min(overlap_frames, len(previous_tail), len(processed))

                    if overlap > 0:
                        fade_in = np.linspace(
                            0.0,
                            1.0,
                            overlap,
                            endpoint=True,
                            dtype=np.float32,
                        )[:, np.newaxis]
                        blended = (
                            previous_tail[-overlap:] * (1.0 - fade_in)
                            + processed[:overlap] * fade_in
                        )
                        destination.write(blended)

                    body = processed[overlap:]

                    if is_last:
                        destination.write(body)
                        previous_tail = None
                    elif len(body) > overlap_frames:
                        destination.write(body[:-overlap_frames])
                        previous_tail = body[-overlap_frames:].copy()
                    else:
                        previous_tail = body.copy()

                chunk_index += 1
                position += step_frames
                fraction = min(chunk_index / estimated_chunks, 1.0)
                progress_callback(
                    0.16 + fraction * 0.66,
                    f"Processando bloco {chunk_index} de {estimated_chunks}...",
                )

            if previous_tail is not None and len(previous_tail):
                destination.write(previous_tail)

    return sample_rate, channels, total_frames


def scan_peak_streaming(
    processed_path: Path,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
) -> float:
    """Encontra o maior pico sem carregar o áudio inteiro na memória."""
    peak = 0.0

    with sf.SoundFile(str(processed_path), mode="r") as source:
        total_frames = max(int(source.frames), 1)
        scanned = 0
        block_frames = max(source.samplerate * 60, 65536)

        while True:
            if cancel_event.is_set():
                raise ProcessingCancelled()

            block = source.read(block_frames, dtype="float32", always_2d=True)
            if len(block) == 0:
                break

            peak = max(peak, float(np.max(np.abs(block))))
            scanned += len(block)
            progress_callback(
                0.82 + min(scanned / total_frames, 1.0) * 0.05,
                "Analisando os picos do resultado...",
            )

    return peak


def export_streaming(
    processed_path: Path,
    output_path: Path,
    gain: float,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
    log_callback: Callable[[str], None],
) -> None:
    """Exporta o arquivo final em WAV/RF64 ou FLAC de 24 bits."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = output_path.suffix.lower()

    if suffix not in {".wav", ".flac"}:
        output_path = output_path.with_suffix(".wav")
        log_callback("Extensão de saída ajustada automaticamente para .wav.")

    with sf.SoundFile(str(processed_path), mode="r") as source:
        sample_rate = int(source.samplerate)
        channels = int(source.channels)
        total_frames = max(int(source.frames), 1)

        if output_path.suffix.lower() == ".flac":
            output_format = "FLAC"
            log_callback("Formato de saída: FLAC PCM 24 bits.")
        else:
            estimated_bytes = total_frames * channels * 3
            output_format = "RF64" if estimated_bytes >= 3_800_000_000 else "WAV"
            if output_format == "RF64":
                log_callback(
                    "Arquivo muito longo: usando RF64 para superar o limite de 4 GB do WAV comum."
                )
            else:
                log_callback("Formato de saída: WAV PCM 24 bits.")

        with sf.SoundFile(
            str(output_path),
            mode="w",
            samplerate=sample_rate,
            channels=channels,
            format=output_format,
            subtype="PCM_24",
        ) as destination:
            written = 0
            block_frames = max(sample_rate * 60, 65536)

            while True:
                if cancel_event.is_set():
                    raise ProcessingCancelled()

                block = source.read(block_frames, dtype="float32", always_2d=True)
                if len(block) == 0:
                    break

                block = np.clip(block * gain, -0.999, 0.999).astype(np.float32)
                destination.write(block)
                written += len(block)
                progress_callback(
                    0.87 + min(written / total_frames, 1.0) * 0.13,
                    "Gravando o arquivo final...",
                )


def process_audio_file(
    input_path: Path,
    output_path: Path,
    settings: AudioSettings,
    cancel_event: threading.Event,
    progress_callback: Callable[[float, str], None],
    log_callback: Callable[[str], None],
) -> None:
    """Executa a conversão, o tratamento em blocos e a exportação final."""
    log_callback(f"Entrada: {input_path}")
    log_callback("Versão do motor: V2 com FFmpeg e processamento em blocos.")

    with tempfile.TemporaryDirectory(prefix="removedor_sibilancia_v2_") as directory:
        temporary_directory = Path(directory)
        readable_input = prepare_readable_audio(
            input_path,
            temporary_directory,
            cancel_event,
            progress_callback,
            log_callback,
        )

        if cancel_event.is_set():
            raise ProcessingCancelled()

        temporary_processed = temporary_directory / "audio_processado_float.wav"
        process_in_chunks(
            readable_input,
            temporary_processed,
            settings,
            cancel_event,
            progress_callback,
            log_callback,
        )

        peak = scan_peak_streaming(
            temporary_processed,
            cancel_event,
            progress_callback,
        )

        if peak <= 1e-12:
            gain = 1.0
            log_callback("O áudio processado está silencioso; normalização ignorada.")
        elif settings.normalize:
            gain = 0.98 / peak
            log_callback(
                f"Normalização de pico: ganho {20 * np.log10(gain):+.2f} dB."
            )
        elif peak > 0.999:
            gain = 0.999 / peak
            log_callback(
                "Atenuação preventiva aplicada para evitar clipping no arquivo final."
            )
        else:
            gain = 1.0
            log_callback("Normalização desativada; nível original preservado.")

        export_streaming(
            temporary_processed,
            output_path,
            gain,
            cancel_event,
            progress_callback,
            log_callback,
        )

    progress_callback(1.0, "Processamento concluído.")
    log_callback(f"Saída: {output_path}")


# ---------------------------------------------------------------------------
# Interface gráfica
# ---------------------------------------------------------------------------

class AudioCleanerApp(ctk.CTk):
    PRESETS = {
        "Voz masculina": {
            "low_freq": 4500,
            "high_freq": 8500,
            "threshold_db": -32,
            "max_reduction_db": 7,
            "ratio": 5,
            "attack_ms": 2,
            "release_ms": 90,
        },
        "Voz feminina": {
            "low_freq": 5500,
            "high_freq": 11000,
            "threshold_db": -33,
            "max_reduction_db": 8,
            "ratio": 6,
            "attack_ms": 2,
            "release_ms": 80,
        },
        "Suave": {
            "low_freq": 5000,
            "high_freq": 10000,
            "threshold_db": -28,
            "max_reduction_db": 4,
            "ratio": 4,
            "attack_ms": 3,
            "release_ms": 110,
        },
        "Forte": {
            "low_freq": 4500,
            "high_freq": 11500,
            "threshold_db": -38,
            "max_reduction_db": 12,
            "ratio": 8,
            "attack_ms": 1.5,
            "release_ms": 70,
        },
    }

    def __init__(self) -> None:
        super().__init__()

        self.title("Removedor de Sibilância e Chiado V2")
        self.geometry("980x760")
        self.minsize(900, 680)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.processing_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.last_output_path: Optional[Path] = None

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()

        self.use_deesser_var = tk.BooleanVar(value=True)
        self.use_noise_var = tk.BooleanVar(value=False)
        self.normalize_var = tk.BooleanVar(value=True)

        self.preset_var = tk.StringVar(value="Voz masculina")
        self.appearance_var = tk.StringVar(value="Sistema")

        self.low_freq_var = tk.DoubleVar(value=4500)
        self.high_freq_var = tk.DoubleVar(value=8500)
        self.threshold_var = tk.DoubleVar(value=-32)
        self.reduction_var = tk.DoubleVar(value=7)
        self.ratio_var = tk.DoubleVar(value=5)
        self.attack_var = tk.DoubleVar(value=2)
        self.release_var = tk.DoubleVar(value=90)
        self.noise_strength_var = tk.DoubleVar(value=0.55)

        self.value_labels: dict[str, ctk.CTkLabel] = {}

        self._build_layout()
        self._update_control_states()
        self._update_all_value_labels()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------------------- Construção da UI -------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Removedor de Sibilância e Chiado V2",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.grid(row=0, column=0, padx=24, pady=(18, 2), sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text=(
                "Reduza os “S” agressivos e o ruído constante sem destruir "
                "o brilho natural da voz."
            ),
            text_color=("gray35", "gray70"),
        )
        subtitle.grid(row=1, column=0, padx=24, pady=(0, 16), sticky="w")

        appearance_menu = ctk.CTkOptionMenu(
            header,
            width=130,
            values=["Sistema", "Claro", "Escuro"],
            variable=self.appearance_var,
            command=self._change_appearance,
        )
        appearance_menu.grid(row=0, column=1, rowspan=2, padx=24, pady=20)

        content = ctk.CTkScrollableFrame(self, corner_radius=0)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        self._build_file_section(content)
        self._build_processing_section(content)
        self._build_deesser_section(content)
        self._build_noise_section(content)
        self._build_status_section(content)

    def _build_file_section(self, parent: ctk.CTkBaseClass) -> None:
        frame = ctk.CTkFrame(parent)
        frame.grid(
            row=0,
            column=0,
            columnspan=2,
            padx=16,
            pady=(12, 8),
            sticky="ew",
        )
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            frame,
            text="Arquivos",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=18, pady=(15, 10), sticky="w")

        ctk.CTkLabel(frame, text="Áudio de entrada").grid(
            row=1, column=0, padx=(18, 10), pady=8, sticky="w"
        )
        input_entry = ctk.CTkEntry(
            frame,
            textvariable=self.input_var,
            placeholder_text="Selecione o áudio que será tratado",
        )
        input_entry.grid(row=1, column=1, padx=0, pady=8, sticky="ew")

        ctk.CTkButton(
            frame,
            text="Selecionar",
            width=110,
            command=self._select_input,
        ).grid(row=1, column=2, padx=12, pady=8)

        ctk.CTkLabel(frame, text="Arquivo de saída").grid(
            row=2, column=0, padx=(18, 10), pady=(8, 16), sticky="w"
        )
        output_entry = ctk.CTkEntry(
            frame,
            textvariable=self.output_var,
            placeholder_text="O resultado será salvo em WAV",
        )
        output_entry.grid(row=2, column=1, padx=0, pady=(8, 16), sticky="ew")

        ctk.CTkButton(
            frame,
            text="Escolher local",
            width=110,
            command=self._select_output,
        ).grid(row=2, column=2, padx=12, pady=(8, 16))

    def _build_processing_section(self, parent: ctk.CTkBaseClass) -> None:
        frame = ctk.CTkFrame(parent)
        frame.grid(row=1, column=0, padx=(16, 8), pady=8, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Processamento",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(15, 8), sticky="w")

        self.deesser_switch = ctk.CTkSwitch(
            frame,
            text="Ativar de-esser",
            variable=self.use_deesser_var,
            command=self._update_control_states,
        )
        self.deesser_switch.grid(row=1, column=0, padx=18, pady=8, sticky="w")

        self.noise_switch = ctk.CTkSwitch(
            frame,
            text="Reduzir chiado constante",
            variable=self.use_noise_var,
            command=self._update_control_states,
        )
        self.noise_switch.grid(row=2, column=0, padx=18, pady=8, sticky="w")

        ctk.CTkSwitch(
            frame,
            text="Normalizar volume ao final",
            variable=self.normalize_var,
        ).grid(row=3, column=0, padx=18, pady=8, sticky="w")

        ctk.CTkLabel(
            frame,
            text="Preset do de-esser",
            text_color=("gray35", "gray70"),
        ).grid(row=4, column=0, padx=18, pady=(12, 4), sticky="w")

        self.preset_menu = ctk.CTkOptionMenu(
            frame,
            values=list(self.PRESETS.keys()) + ["Personalizado"],
            variable=self.preset_var,
            command=self._apply_preset,
        )
        self.preset_menu.grid(
            row=5, column=0, padx=18, pady=(0, 17), sticky="ew"
        )

    def _build_deesser_section(self, parent: ctk.CTkBaseClass) -> None:
        self.deesser_frame = ctk.CTkFrame(parent)
        self.deesser_frame.grid(
            row=1,
            column=1,
            padx=(8, 16),
            pady=8,
            sticky="nsew",
        )
        self.deesser_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.deesser_frame,
            text="Controles do de-esser",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(15, 6), sticky="w")

        self._add_slider(
            self.deesser_frame,
            row=1,
            key="low",
            title="Frequência inicial",
            variable=self.low_freq_var,
            start=3000,
            end=8000,
            steps=100,
            formatter=lambda value: f"{value:.0f} Hz",
        )
        self._add_slider(
            self.deesser_frame,
            row=2,
            key="high",
            title="Frequência final",
            variable=self.high_freq_var,
            start=7000,
            end=15000,
            steps=160,
            formatter=lambda value: f"{value:.0f} Hz",
        )
        self._add_slider(
            self.deesser_frame,
            row=3,
            key="threshold",
            title="Limiar de ativação",
            variable=self.threshold_var,
            start=-50,
            end=-15,
            steps=140,
            formatter=lambda value: f"{value:.1f} dB",
        )
        self._add_slider(
            self.deesser_frame,
            row=4,
            key="reduction",
            title="Redução máxima",
            variable=self.reduction_var,
            start=2,
            end=18,
            steps=64,
            formatter=lambda value: f"{value:.1f} dB",
        )
        self._add_slider(
            self.deesser_frame,
            row=5,
            key="ratio",
            title="Proporção de compressão",
            variable=self.ratio_var,
            start=2,
            end=12,
            steps=40,
            formatter=lambda value: f"{value:.1f}:1",
        )
        self._add_slider(
            self.deesser_frame,
            row=6,
            key="attack",
            title="Ataque",
            variable=self.attack_var,
            start=0.5,
            end=20,
            steps=78,
            formatter=lambda value: f"{value:.1f} ms",
        )
        self._add_slider(
            self.deesser_frame,
            row=7,
            key="release",
            title="Release",
            variable=self.release_var,
            start=20,
            end=250,
            steps=92,
            formatter=lambda value: f"{value:.0f} ms",
        )

    def _build_noise_section(self, parent: ctk.CTkBaseClass) -> None:
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=0, padx=(16, 8), pady=8, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Redução de chiado",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(15, 5), sticky="w")

        self.noise_controls = ctk.CTkFrame(frame, fg_color="transparent")
        self.noise_controls.grid(row=1, column=0, sticky="ew")
        self.noise_controls.grid_columnconfigure(0, weight=1)

        self._add_slider(
            self.noise_controls,
            row=0,
            key="noise",
            title="Intensidade",
            variable=self.noise_strength_var,
            start=0.10,
            end=1.0,
            steps=90,
            formatter=lambda value: f"{value * 100:.0f}%",
        )

        note = ctk.CTkLabel(
            frame,
            text=(
                "Valores altos removem mais ruído, mas podem criar voz "
                "metálica. Comece entre 45% e 60%."
            ),
            wraplength=380,
            justify="left",
            text_color=("gray35", "gray70"),
        )
        note.grid(row=2, column=0, padx=18, pady=(2, 15), sticky="w")

    def _build_status_section(self, parent: ctk.CTkBaseClass) -> None:
        frame = ctk.CTkFrame(parent)
        frame.grid(row=2, column=1, padx=(8, 16), pady=8, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame,
            text="Execução",
            font=ctk.CTkFont(size=17, weight="bold"),
        ).grid(row=0, column=0, columnspan=3, padx=18, pady=(15, 5), sticky="w")

        self.status_label = ctk.CTkLabel(
            frame,
            text="Selecione um áudio para começar.",
            anchor="w",
        )
        self.status_label.grid(
            row=1, column=0, columnspan=3, padx=18, pady=(4, 8), sticky="ew"
        )

        self.progress_bar = ctk.CTkProgressBar(frame)
        self.progress_bar.set(0)
        self.progress_bar.grid(
            row=2, column=0, columnspan=3, padx=18, pady=(0, 12), sticky="ew"
        )

        self.process_button = ctk.CTkButton(
            frame,
            text="Processar áudio",
            height=42,
            command=self._start_processing,
        )
        self.process_button.grid(
            row=3, column=0, padx=(18, 6), pady=(0, 12), sticky="ew"
        )

        self.cancel_button = ctk.CTkButton(
            frame,
            text="Cancelar",
            width=100,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            state="disabled",
            command=self._request_cancel,
        )
        self.cancel_button.grid(row=3, column=1, padx=6, pady=(0, 12))

        self.open_folder_button = ctk.CTkButton(
            frame,
            text="Abrir pasta",
            width=105,
            state="disabled",
            command=self._open_output_folder,
        )
        self.open_folder_button.grid(
            row=3, column=2, padx=(6, 18), pady=(0, 8)
        )

        self.copy_log_button = ctk.CTkButton(
            frame,
            text="Copiar log",
            height=32,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray40"),
            command=self._copy_log,
        )
        self.copy_log_button.grid(
            row=4,
            column=0,
            columnspan=3,
            padx=18,
            pady=(0, 14),
            sticky="ew",
        )

        self.log_box = ctk.CTkTextbox(parent, height=170)
        self.log_box.grid(
            row=3,
            column=0,
            columnspan=2,
            padx=16,
            pady=(8, 18),
            sticky="ew",
        )
        self.log_box.insert(
            "end",
            "Pronto. V2 carregada; M4A e arquivos longos são suportados.\n"
            "O arquivo original não será alterado.\n",
        )
        self.log_box.configure(state="disabled")

    def _add_slider(
        self,
        parent: ctk.CTkBaseClass,
        row: int,
        key: str,
        title: str,
        variable: tk.DoubleVar,
        start: float,
        end: float,
        steps: int,
        formatter: Callable[[float], str],
    ) -> None:
        container = ctk.CTkFrame(parent, fg_color="transparent")
        container.grid(row=row, column=0, padx=18, pady=5, sticky="ew")
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(container, text=title).grid(
            row=0, column=0, sticky="w"
        )

        value_label = ctk.CTkLabel(
            container,
            text=formatter(variable.get()),
            width=90,
            anchor="e",
            text_color=("gray35", "gray70"),
        )
        value_label.grid(row=0, column=1, sticky="e")
        self.value_labels[key] = value_label

        def on_change(value: float) -> None:
            variable.set(float(value))
            value_label.configure(text=formatter(float(value)))
            if key != "noise":
                self.preset_var.set("Personalizado")

        slider = ctk.CTkSlider(
            container,
            from_=start,
            to=end,
            number_of_steps=steps,
            variable=variable,
            command=on_change,
        )
        slider.grid(row=1, column=0, columnspan=2, pady=(4, 0), sticky="ew")

        if key == "noise":
            self.noise_slider = slider
        else:
            if not hasattr(self, "deesser_sliders"):
                self.deesser_sliders: list[ctk.CTkSlider] = []
            self.deesser_sliders.append(slider)

    # --------------------------- Eventos da interface ----------------------

    def _select_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o áudio",
            filetypes=[
                (
                    "Arquivos de áudio",
                    "*.m4a *.aac *.mp3 *.mp4 *.wav *.flac *.ogg *.opus *.aiff *.aif *.wma",
                ),
                ("M4A/AAC", "*.m4a *.aac *.mp4"),
                ("MP3", "*.mp3"),
                ("WAV", "*.wav"),
                ("FLAC", "*.flac"),
                ("OGG", "*.ogg"),
                ("AIFF", "*.aiff *.aif"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if not path:
            return

        self.input_var.set(path)
        input_path = Path(path)
        suggested_output = input_path.with_name(
            f"{input_path.stem}_tratado.wav"
        )
        self.output_var.set(str(suggested_output))
        self.status_label.configure(text="Arquivo selecionado. Pronto para processar.")

    def _select_output(self) -> None:
        initial_name = "audio_tratado.wav"

        if self.input_var.get().strip():
            input_path = Path(self.input_var.get().strip())
            initial_name = f"{input_path.stem}_tratado.wav"

        path = filedialog.asksaveasfilename(
            title="Escolha onde salvar o resultado",
            defaultextension=".wav",
            initialfile=initial_name,
            filetypes=[("Áudio WAV", "*.wav"), ("Áudio FLAC", "*.flac")],
        )

        if path:
            output_path = Path(path)
            if output_path.suffix.lower() not in {".wav", ".flac"}:
                output_path = output_path.with_suffix(".wav")
            self.output_var.set(str(output_path))

    def _apply_preset(self, selected: str) -> None:
        if selected == "Personalizado":
            return

        values = self.PRESETS[selected]
        self.low_freq_var.set(values["low_freq"])
        self.high_freq_var.set(values["high_freq"])
        self.threshold_var.set(values["threshold_db"])
        self.reduction_var.set(values["max_reduction_db"])
        self.ratio_var.set(values["ratio"])
        self.attack_var.set(values["attack_ms"])
        self.release_var.set(values["release_ms"])
        self._update_all_value_labels()

    def _change_appearance(self, selected: str) -> None:
        modes = {
            "Sistema": "System",
            "Claro": "Light",
            "Escuro": "Dark",
        }
        ctk.set_appearance_mode(modes.get(selected, "System"))

    def _update_control_states(self) -> None:
        deesser_state = "normal" if self.use_deesser_var.get() else "disabled"
        noise_state = "normal" if self.use_noise_var.get() else "disabled"

        if hasattr(self, "preset_menu"):
            self.preset_menu.configure(state=deesser_state)

        for slider in getattr(self, "deesser_sliders", []):
            slider.configure(state=deesser_state)

        if hasattr(self, "noise_slider"):
            self.noise_slider.configure(state=noise_state)

    def _update_all_value_labels(self) -> None:
        formats = {
            "low": f"{self.low_freq_var.get():.0f} Hz",
            "high": f"{self.high_freq_var.get():.0f} Hz",
            "threshold": f"{self.threshold_var.get():.1f} dB",
            "reduction": f"{self.reduction_var.get():.1f} dB",
            "ratio": f"{self.ratio_var.get():.1f}:1",
            "attack": f"{self.attack_var.get():.1f} ms",
            "release": f"{self.release_var.get():.0f} ms",
            "noise": f"{self.noise_strength_var.get() * 100:.0f}%",
        }

        for key, text in formats.items():
            if key in self.value_labels:
                self.value_labels[key].configure(text=text)

    def _collect_settings(self) -> AudioSettings:
        low_freq = float(self.low_freq_var.get())
        high_freq = float(self.high_freq_var.get())

        if low_freq >= high_freq:
            raise ValueError(
                "A frequência inicial deve ser menor que a frequência final."
            )

        return AudioSettings(
            use_deesser=self.use_deesser_var.get(),
            use_noise_reduction=self.use_noise_var.get(),
            normalize=self.normalize_var.get(),
            low_freq=low_freq,
            high_freq=high_freq,
            threshold_db=float(self.threshold_var.get()),
            max_reduction_db=float(self.reduction_var.get()),
            ratio=float(self.ratio_var.get()),
            attack_ms=float(self.attack_var.get()),
            release_ms=float(self.release_var.get()),
            noise_strength=float(self.noise_strength_var.get()),
        )

    def _start_processing(self) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            return

        input_text = self.input_var.get().strip()
        output_text = self.output_var.get().strip()

        if not input_text:
            messagebox.showwarning(
                "Arquivo não selecionado",
                "Selecione um arquivo de áudio para processar.",
            )
            return

        input_path = Path(input_text)

        if not input_path.is_file():
            messagebox.showerror(
                "Arquivo inválido",
                "O arquivo de entrada não existe ou não pode ser acessado.",
            )
            return

        if not output_text:
            output_path = input_path.with_name(f"{input_path.stem}_tratado.wav")
            self.output_var.set(str(output_path))
        else:
            output_path = Path(output_text)

        if output_path.suffix.lower() not in {".wav", ".flac"}:
            output_path = output_path.with_suffix(".wav")
            self.output_var.set(str(output_path))

        try:
            if input_path.resolve() == output_path.resolve():
                messagebox.showerror(
                    "Saída inválida",
                    "O arquivo de saída não pode substituir o original.",
                )
                return
        except OSError:
            pass

        try:
            settings = self._collect_settings()
        except ValueError as exc:
            messagebox.showerror("Configuração inválida", str(exc))
            return

        self.cancel_event.clear()
        self.last_output_path = None
        self.progress_bar.set(0)
        self.open_folder_button.configure(state="disabled")
        self.process_button.configure(state="disabled", text="Processando...")
        self.cancel_button.configure(state="normal")
        self.status_label.configure(text="Iniciando o processamento...")
        self._append_log("")
        self._append_log("─" * 64)
        self._append_log("Novo processamento iniciado.")

        self.processing_thread = threading.Thread(
            target=self._processing_worker,
            args=(input_path, output_path, settings),
            daemon=True,
        )
        self.processing_thread.start()

    def _processing_worker(
        self,
        input_path: Path,
        output_path: Path,
        settings: AudioSettings,
    ) -> None:
        try:
            process_audio_file(
                input_path=input_path,
                output_path=output_path,
                settings=settings,
                cancel_event=self.cancel_event,
                progress_callback=self._threadsafe_progress,
                log_callback=self._threadsafe_log,
            )
        except ProcessingCancelled:
            self.after(0, self._processing_cancelled)
        except Exception as exc:
            details = traceback.format_exc()
            self._threadsafe_log(details)
            self.after(0, lambda: self._processing_failed(str(exc)))
        else:
            self.after(0, lambda: self._processing_succeeded(output_path))

    def _threadsafe_progress(self, value: float, status: str) -> None:
        self.after(0, lambda: self._set_progress(value, status))

    def _threadsafe_log(self, message: str) -> None:
        self.after(0, lambda: self._append_log(message))

    def _set_progress(self, value: float, status: str) -> None:
        self.progress_bar.set(float(np.clip(value, 0.0, 1.0)))
        self.status_label.configure(text=status)

    def _append_log(self, message: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _copy_log(self) -> None:
        """Copia integralmente o conteúdo visível do log."""
        log_text = self.log_box.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(log_text)
        # Mantém o conteúdo disponível depois do retorno do callback no Windows.
        self.update_idletasks()
        self.status_label.configure(text="Log copiado para a área de transferência.")

    def _request_cancel(self) -> None:
        self.cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.status_label.configure(
            text="Cancelamento solicitado. Finalizando a etapa atual..."
        )
        self._append_log("Cancelamento solicitado pelo usuário.")

    def _processing_succeeded(self, output_path: Path) -> None:
        self.last_output_path = output_path
        self.progress_bar.set(1.0)
        self.status_label.configure(text="Áudio processado com sucesso.")
        self.process_button.configure(state="normal", text="Processar áudio")
        self.cancel_button.configure(state="disabled")
        self.open_folder_button.configure(state="normal")

        messagebox.showinfo(
            "Processamento concluído",
            f"O áudio tratado foi salvo em:\n\n{output_path}",
        )

    def _processing_failed(self, error_message: str) -> None:
        self.progress_bar.set(0)
        self.status_label.configure(text="O processamento encontrou um erro.")
        self.process_button.configure(state="normal", text="Processar áudio")
        self.cancel_button.configure(state="disabled")

        messagebox.showerror(
            "Erro no processamento",
            f"{error_message}\n\n"
            "O erro completo está no log. Use o botão ‘Copiar log’ para copiá-lo.",
        )

    def _processing_cancelled(self) -> None:
        self.progress_bar.set(0)
        self.status_label.configure(text="Processamento cancelado.")
        self.process_button.configure(state="normal", text="Processar áudio")
        self.cancel_button.configure(state="disabled")

    def _open_output_folder(self) -> None:
        if self.last_output_path is None:
            return

        folder = self.last_output_path.parent

        try:
            if platform.system() == "Windows":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
        except Exception as exc:
            messagebox.showerror(
                "Não foi possível abrir a pasta",
                str(exc),
            )

    def _on_close(self) -> None:
        if self.processing_thread and self.processing_thread.is_alive():
            should_close = messagebox.askyesno(
                "Processamento em andamento",
                "Deseja cancelar o processamento e fechar o aplicativo?",
            )
            if not should_close:
                return
            self.cancel_event.set()

        self.destroy()


def main() -> None:
    app = AudioCleanerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
