#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import ctypes
import hashlib
import importlib
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path


def install_and_import(package: str, import_name: str | None = None):
    module_name = import_name or package
    try:
        return importlib.import_module(module_name)
    except ImportError:
        pass

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])

    subprocess.check_call([
        sys.executable, "-m", "pip", "install",
        "--disable-pip-version-check", "--upgrade", package
    ])
    importlib.invalidate_caches()
    return importlib.import_module(module_name)


def get_ffmpeg() -> str:
    system = shutil.which("ffmpeg")
    if system:
        return system
    imageio_ffmpeg = install_and_import("imageio-ffmpeg", "imageio_ffmpeg")
    return imageio_ffmpeg.get_ffmpeg_exe()


try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    print(
        "Tkinter não está disponível.\n"
        "Reinstale/repare o Python oficial para Windows e habilite Tcl/Tk."
    )
    raise SystemExit(1)


def creation_flags() -> int:
    if os.name == "nt":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def prevent_windows_sleep(enable: bool) -> None:
    if os.name != "nt":
        return
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    try:
        if enable:
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            )
        else:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    except Exception:
        pass


class Logger:
    def __init__(self, path: Path):
        self.path = path
        self.lock = threading.Lock()

    def write(self, message: str) -> None:
        line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n"
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)


def human_size(n: int) -> str:
    value = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{n} B"


def format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}min {s}s"
    if m:
        return f"{m}min {s}s"
    return f"{s}s"


def probe_input(ffmpeg: str, source: Path) -> tuple[float, str]:
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(source)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creation_flags(),
    )
    text = proc.stderr.decode("utf-8", errors="replace")

    duration = 0.0
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", text)
    if match:
        h, m, s = match.groups()
        duration = int(h) * 3600 + int(m) * 60 + float(s)

    audio_line = ""
    for line in text.splitlines():
        if "Audio:" in line:
            audio_line = line.strip()
            break

    if not audio_line:
        raise RuntimeError("Não foi possível identificar uma faixa de áudio válida.")

    low = audio_line.lower()
    float_markers = ("pcm_f32", "pcm_f64", "32-bit float", "64-bit float")
    if any(marker in low for marker in float_markers):
        raise RuntimeError(
            "Este WAV usa PCM em ponto flutuante.\n\n"
            "Para não prometer preservação matemática indevida, esta versão "
            "não converte WAV float para ALAC automaticamente."
        )

    return duration, audio_line


def parse_ffmpeg_time(value: str) -> float:
    try:
        h, m, s = value.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return 0.0


def convert_alac(ffmpeg: str, source: Path, temp_output: Path,
                 duration: float, progress_cb, logger: Logger) -> None:
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", str(source),
        "-map", "0:a:0",
        "-vn", "-sn", "-dn",
        "-map_metadata", "0",
        "-c:a", "alac",
        "-threads", "0",
        "-progress", "pipe:1",
        "-nostats",
        str(temp_output),
    ]

    logger.write("Iniciando FFmpeg: conversão ALAC.")
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        creationflags=creation_flags(),
    )

    assert proc.stdout is not None
    last_progress = 0.0

    for raw_line in proc.stdout:
        line = raw_line.strip()
        seconds = None

        if line.startswith("out_time="):
            seconds = parse_ffmpeg_time(line.split("=", 1)[1])
        elif line.startswith("out_time_us="):
            try:
                seconds = int(line.split("=", 1)[1]) / 1_000_000
            except Exception:
                pass
        elif line.startswith("out_time_ms="):
            try:
                seconds = int(line.split("=", 1)[1]) / 1_000_000
            except Exception:
                pass

        if seconds is not None and duration > 0:
            pct = min(99.5, max(last_progress, seconds / duration * 100))
            last_progress = pct
            progress_cb(pct, seconds, duration)

    stderr = proc.stderr.read() if proc.stderr else ""
    rc = proc.wait()

    if rc != 0:
        logger.write(f"FFmpeg falhou (código {rc}).")
        if stderr.strip():
            logger.write("FFmpeg stderr: " + stderr.strip())
        raise RuntimeError(
            "O FFmpeg não conseguiu concluir a conversão.\n\n"
            + (stderr.strip() or f"Código de saída: {rc}")
        )

    progress_cb(100.0, duration, duration)
    logger.write("Conversão ALAC concluída pelo FFmpeg.")


def decoded_pcm_sha256(ffmpeg: str, path: Path) -> str:
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-i", str(path),
        "-map", "0:a:0",
        "-vn", "-sn", "-dn",
        "-c:a", "pcm_s32le",
        "-f", "s32le",
        "-",
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=creation_flags(),
    )
    assert proc.stdout is not None
    digest = hashlib.sha256()

    while True:
        chunk = proc.stdout.read(1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)

    stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError("Falha na verificação SHA-256 do PCM.\n\n" + stderr.strip())

    return digest.hexdigest()


def verify_bit_exact(ffmpeg: str, source: Path, output: Path, logger: Logger) -> None:
    logger.write("Iniciando verificação rigorosa: hash PCM do WAV.")
    h1 = decoded_pcm_sha256(ffmpeg, source)
    logger.write("Calculando hash PCM do M4A.")
    h2 = decoded_pcm_sha256(ffmpeg, output)
    if h1 != h2:
        logger.write("ERRO: hashes PCM diferentes.")
        raise RuntimeError("A verificação rigorosa falhou: os hashes PCM são diferentes.")
    logger.write("Verificação rigorosa concluída: hashes PCM idênticos.")


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WAV → M4A Lossless")
        self.root.geometry("640x410")
        self.root.minsize(580, 370)

        self.source: Path | None = None
        self.output: Path | None = None
        self.log_path: Path | None = None
        self.running = False
        self.verify_var = tk.BooleanVar(value=False)

        self.build_ui()
        self.root.after(150, self.select_file)

    def build_ui(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Conversor WAV → M4A / ALAC",
            font=("", 14, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            frame,
            text=(
                "Modo rápido por padrão: uma única passagem pelo áudio. "
                "ALAC é lossless, então não descarta informação do áudio."
            ),
            wraplength=590,
        ).pack(anchor="w", pady=(5, 14))

        self.file_label = ttk.Label(frame, text="Nenhum arquivo selecionado.", wraplength=590)
        self.file_label.pack(anchor="w")

        ttk.Checkbutton(
            frame,
            text=(
                "Verificação rigorosa bit-a-bit após converter "
                "(mais lenta: acrescenta 2 passagens completas)"
            ),
            variable=self.verify_var,
        ).pack(anchor="w", pady=(14, 10))

        self.status_title = ttk.Label(
            frame,
            text="Selecione um arquivo WAV",
            font=("", 11, "bold"),
        )
        self.status_title.pack(anchor="w", pady=(8, 4))

        self.status_label = ttk.Label(frame, text="", wraplength=590, justify="left")
        self.status_label.pack(anchor="w")

        self.progress = ttk.Progressbar(
            frame, orient="horizontal", mode="determinate", maximum=100
        )
        self.progress.pack(fill="x", pady=(14, 5))

        self.percent_label = ttk.Label(frame, text="0%")
        self.percent_label.pack(anchor="e")

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(18, 0))

        self.select_button = ttk.Button(buttons, text="Selecionar WAV", command=self.select_file)
        self.select_button.pack(side="left")

        self.open_button = ttk.Button(
            buttons, text="Abrir pasta", command=self.open_folder, state="disabled"
        )
        self.open_button.pack(side="left", padx=(8, 0))

        ttk.Button(buttons, text="Fechar", command=self.close).pack(side="right")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def ui(self, func):
        self.root.after(0, func)

    def set_status(self, title: str, text: str):
        self.ui(lambda: (
            self.status_title.config(text=title),
            self.status_label.config(text=text),
        ))

    def set_progress(self, pct: float, seconds: float = 0, duration: float = 0):
        pct = min(100.0, max(0.0, pct))

        def update():
            self.progress["value"] = pct
            if duration > 0 and seconds >= 0:
                remaining = max(0, duration - seconds)
                self.percent_label.config(
                    text=f"{pct:.1f}% — áudio restante: ~{format_duration(remaining)}"
                )
            else:
                self.percent_label.config(text=f"{pct:.1f}%")

        self.ui(update)

    def select_file(self):
        if self.running:
            return

        selected = filedialog.askopenfilename(
            title="Selecione o arquivo WAV",
            filetypes=[("Arquivos WAV", "*.wav"), ("Todos os arquivos", "*.*")],
        )
        if not selected:
            return

        source = Path(selected).resolve()
        if source.suffix.lower() != ".wav":
            messagebox.showerror("Arquivo inválido", "Selecione um arquivo .wav.")
            return

        output = source.with_suffix(".m4a")
        temp_output = source.with_name(source.stem + ".converting.m4a")
        log_path = source.with_name(source.stem + ".wav_to_m4a.log")

        if output.exists():
            replace = messagebox.askyesno(
                "Arquivo já existe",
                f"Já existe:\n\n{output}\n\nDeseja substituir?",
            )
            if not replace:
                return

        try:
            if temp_output.exists():
                temp_output.unlink()
        except OSError:
            pass

        self.source = source
        self.output = output
        self.log_path = log_path

        self.file_label.config(text=f"Entrada: {source}")
        self.progress["value"] = 0
        self.percent_label.config(text="0%")
        self.open_button.config(state="disabled")

        self.running = True
        self.select_button.config(state="disabled")

        thread = threading.Thread(
            target=self.worker,
            args=(source, output, temp_output, log_path),
            daemon=False,
        )
        thread.start()

    def worker(self, source: Path, output: Path, temp_output: Path, log_path: Path):
        logger = Logger(log_path)
        logger.write("=" * 70)
        logger.write(f"Entrada: {source}")
        logger.write(f"Saída final: {output}")
        logger.write(f"Saída temporária: {temp_output}")
        logger.write(f"Verificação rigorosa: {self.verify_var.get()}")

        prevent_windows_sleep(True)

        try:
            self.set_status(
                "Preparando FFmpeg",
                "Localizando o FFmpeg. Na primeira execução pode haver instalação automática.",
            )
            ffmpeg = get_ffmpeg()
            logger.write(f"FFmpeg: {ffmpeg}")

            self.set_status("Analisando WAV", source.name)
            duration, audio_info = probe_input(ffmpeg, source)
            logger.write(f"Áudio: {audio_info}")
            logger.write(f"Duração detectada: {duration:.3f} s")

            self.set_status(
                "Convertendo para ALAC",
                "Uma única passagem. O arquivo final só é criado após o FFmpeg terminar com sucesso.",
            )

            started = time.time()
            convert_alac(
                ffmpeg, source, temp_output, duration, self.set_progress, logger
            )

            if not temp_output.exists() or temp_output.stat().st_size == 0:
                raise RuntimeError("O FFmpeg terminou sem produzir um arquivo válido.")

            if output.exists():
                output.unlink()
            os.replace(temp_output, output)
            logger.write("Arquivo temporário promovido para o nome final.")

            if self.verify_var.get():
                self.set_status(
                    "Verificação rigorosa",
                    "Comparando o PCM do WAV e do M4A. Esta etapa lê os dois arquivos inteiros.",
                )
                verify_bit_exact(ffmpeg, source, output, logger)

            elapsed = time.time() - started
            before = source.stat().st_size
            after = output.stat().st_size
            delta = before - after
            pct_saved = (delta / before * 100) if before else 0

            logger.write(f"Concluído em {elapsed:.1f} segundos.")
            logger.write(f"WAV: {human_size(before)}")
            logger.write(f"M4A: {human_size(after)}")
            if delta >= 0:
                logger.write(f"Economia: {human_size(delta)} ({pct_saved:.2f}%)")
            else:
                logger.write(f"Aumento: {human_size(-delta)} ({-pct_saved:.2f}%)")

            verification_text = (
                "Verificação rigorosa: OK."
                if self.verify_var.get()
                else "Modo rápido: ALAC lossless, sem hash PCM adicional."
            )

            result_text = (
                f"Arquivo criado:\n{output}\n\n"
                f"WAV: {human_size(before)}\n"
                f"M4A: {human_size(after)}\n"
            )
            if delta >= 0:
                result_text += f"Economia: {human_size(delta)} ({pct_saved:.2f}%)\n"
            else:
                result_text += f"Tamanho aumentou: {human_size(-delta)}\n"

            result_text += (
                f"Tempo de conversão: {format_duration(elapsed)}\n"
                f"{verification_text}\n\n"
                f"Log: {log_path}"
            )

            self.set_progress(100, duration, duration)
            self.set_status("Conversão concluída", result_text)
            self.ui(lambda: self.open_button.config(state="normal"))
            logger.write("SUCESSO.")

        except Exception as exc:
            logger.write("FALHA: " + repr(exc))
            try:
                if temp_output.exists():
                    temp_output.unlink()
            except OSError:
                pass

            self.set_status(
                "Falha na conversão",
                f"{exc}\n\nO log completo ficou salvo em:\n{log_path}",
            )
            self.ui(lambda: self.open_button.config(state="normal"))

        finally:
            prevent_windows_sleep(False)
            self.running = False
            self.ui(lambda: self.select_button.config(state="normal"))

    def open_folder(self):
        target = self.output.parent if self.output else (
            self.source.parent if self.source else None
        )
        if not target:
            return

        try:
            if os.name == "nt":
                os.startfile(str(target))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(target)])
            else:
                subprocess.Popen(["xdg-open", str(target)])
        except Exception as exc:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{exc}")

    def close(self):
        if self.running:
            leave = messagebox.askyesno(
                "Conversão em andamento",
                "A conversão ainda está em andamento.\n\n"
                "Fechar agora interromperá o processo.\n"
                "Deseja realmente fechar?",
            )
            if not leave:
                return
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
