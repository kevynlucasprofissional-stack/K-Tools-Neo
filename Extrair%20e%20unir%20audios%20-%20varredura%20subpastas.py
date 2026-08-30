import sys
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path


# ============================================================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ============================================================

def instalar_biblioteca(pacote, modulo=None):
    """
    Instala automaticamente uma biblioteca caso ela
    ainda não esteja instalada.
    """

    modulo = modulo or pacote

    try:
        __import__(modulo)
    except ImportError:
        print(f"Instalando {pacote}...")

        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            pacote
        ])


# Instala dependências necessárias
instalar_biblioteca("customtkinter")
instalar_biblioteca("imageio-ffmpeg", "imageio_ffmpeg")


# Agora podemos importar normalmente
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import imageio_ffmpeg


# ============================================================
# CONFIGURAÇÕES
# ============================================================

EXTENSOES_VIDEO = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".wmv",
    ".flv",
    ".m4v",
    ".mpeg",
    ".mpg",
    ".ts",
    ".mts",
    ".m2ts",
    ".3gp",
    ".3g2",
    ".ogv",
    ".vob",
    ".asf",
    ".rm",
    ".rmvb",
}


SAMPLE_RATE = 48000
CANAIS = 2


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_ffmpeg():
    """
    Retorna o caminho do executável FFmpeg fornecido
    pelo imageio-ffmpeg.
    """

    return imageio_ffmpeg.get_ffmpeg_exe()


def chave_natural(texto):
    """
    Ordenação natural.

    Exemplo:

    video1
    video2
    video10

    em vez de:

    video1
    video10
    video2
    """

    return [
        int(parte) if parte.isdigit() else parte.lower()
        for parte in re.split(r"(\d+)", str(texto))
    ]


def localizar_videos(pasta):
    """
    Faz uma varredura recursiva automática na pasta principal
    e em todas as suas subpastas, localizando arquivos de vídeo.

    A ordenação considera o caminho relativo completo para preservar
    a sequência natural das pastas e, dentro delas, dos arquivos.
    """

    pasta = Path(pasta)
    videos = []

    # rglob percorre automaticamente todos os níveis de subpastas.
    for arquivo in pasta.rglob("*"):

        if (
            arquivo.is_file()
            and arquivo.suffix.lower() in EXTENSOES_VIDEO
        ):
            videos.append(arquivo)

    # Ordena pela estrutura completa:
    # Módulo 1/Aula 1 -> Módulo 1/Aula 2 -> Módulo 2/Aula 1 ...
    videos.sort(
        key=lambda arquivo: chave_natural(
            str(arquivo.relative_to(pasta))
        )
    )

    return videos


def formatar_tamanho(bytes_total):

    mb = bytes_total / 1024 / 1024

    if mb < 1024:
        return f"{mb:.2f} MB"

    gb = mb / 1024

    return f"{gb:.2f} GB"


# ============================================================
# INTERFACE
# ============================================================

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Extrator e Unificador de Áudio")
        self.geometry("900x720")
        self.minsize(780, 650)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.pasta = None
        self.processando = False

        self.criar_interface()

    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        titulo = ctk.CTkLabel(
            self,
            text="Extrator e Unificador de Áudio",
            font=ctk.CTkFont(
                size=26,
                weight="bold"
            )
        )

        titulo.pack(
            pady=(25, 5)
        )

        subtitulo = ctk.CTkLabel(
            self,
            text=(
                "Localiza vídeos, extrai os áudios "
                "e gera um único arquivo M4A."
            ),
            text_color="gray"
        )

        subtitulo.pack(
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # FRAME PRINCIPAL
        # ----------------------------------------------------

        frame = ctk.CTkFrame(self)

        frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25)
        )

        # ----------------------------------------------------
        # SELEÇÃO DE PASTA
        # ----------------------------------------------------

        pasta_label = ctk.CTkLabel(
            frame,
            text="Pasta principal:",
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            )
        )

        pasta_label.pack(
            anchor="w",
            padx=20,
            pady=(20, 5)
        )

        pasta_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        pasta_frame.pack(
            fill="x",
            padx=20
        )

        self.entry_pasta = ctk.CTkEntry(
            pasta_frame,
            placeholder_text="Selecione a pasta dos vídeos..."
        )

        self.entry_pasta.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        botao_pasta = ctk.CTkButton(
            pasta_frame,
            text="Selecionar pasta",
            width=150,
            command=self.selecionar_pasta
        )

        botao_pasta.pack(
            side="right"
        )

        # ----------------------------------------------------
        # CONFIGURAÇÕES
        # ----------------------------------------------------

        configuracoes = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        configuracoes.pack(
            fill="x",
            padx=20,
            pady=20
        )

        # Nome
        nome_frame = ctk.CTkFrame(
            configuracoes,
            fg_color="transparent"
        )

        nome_frame.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )

        nome_label = ctk.CTkLabel(
            nome_frame,
            text="Nome do arquivo:"
        )

        nome_label.pack(
            anchor="w"
        )

        self.entry_nome = ctk.CTkEntry(
            nome_frame
        )

        self.entry_nome.insert(
            0,
            "audio_unificado.m4a"
        )

        self.entry_nome.pack(
            fill="x",
            pady=(5, 0)
        )

        # Bitrate
        bitrate_frame = ctk.CTkFrame(
            configuracoes,
            fg_color="transparent"
        )

        bitrate_frame.pack(
            side="right"
        )

        bitrate_label = ctk.CTkLabel(
            bitrate_frame,
            text="Qualidade AAC:"
        )

        bitrate_label.pack(
            anchor="w"
        )

        self.combo_bitrate = ctk.CTkComboBox(
            bitrate_frame,
            values=[
                "128k",
                "160k",
                "192k",
                "256k",
                "320k"
            ],
            width=130
        )

        self.combo_bitrate.set("192k")

        self.combo_bitrate.pack(
            pady=(5, 0)
        )

        # ----------------------------------------------------
        # INFORMAÇÕES
        # ----------------------------------------------------

        self.label_status = ctk.CTkLabel(
            frame,
            text="Nenhuma pasta selecionada.",
            anchor="w"
        )

        self.label_status.pack(
            fill="x",
            padx=20,
            pady=(0, 5)
        )

        self.label_contagem = ctk.CTkLabel(
            frame,
            text="Vídeos encontrados: 0",
            anchor="w"
        )

        self.label_contagem.pack(
            fill="x",
            padx=20,
            pady=(0, 15)
        )

        # ----------------------------------------------------
        # BARRA DE PROGRESSO
        # ----------------------------------------------------

        self.progress_bar = ctk.CTkProgressBar(
            frame
        )

        self.progress_bar.pack(
            fill="x",
            padx=20
        )

        self.progress_bar.set(0)

        self.label_progresso = ctk.CTkLabel(
            frame,
            text="0%"
        )

        self.label_progresso.pack(
            pady=(4, 10)
        )

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        log_label = ctk.CTkLabel(
            frame,
            text="Processamento:",
            font=ctk.CTkFont(
                weight="bold"
            )
        )

        log_label.pack(
            anchor="w",
            padx=20
        )

        self.log_box = ctk.CTkTextbox(
            frame,
            height=230
        )

        self.log_box.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(5, 15)
        )

        self.log_box.configure(
            state="disabled"
        )

        # ----------------------------------------------------
        # BOTÕES
        # ----------------------------------------------------

        botoes = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        botoes.pack(
            fill="x",
            padx=20,
            pady=(0, 20)
        )

        self.botao_iniciar = ctk.CTkButton(
            botoes,
            text="Iniciar processamento",
            height=42,
            font=ctk.CTkFont(
                size=15,
                weight="bold"
            ),
            command=self.iniciar
        )

        self.botao_iniciar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5)
        )

        self.botao_abrir = ctk.CTkButton(
            botoes,
            text="Abrir pasta",
            height=42,
            width=130,
            command=self.abrir_pasta,
            state="disabled"
        )

        self.botao_abrir.pack(
            side="right",
            padx=(5, 0)
        )

    # ========================================================
    # LOG
    # ========================================================

    def log(self, texto):

        def inserir():

            self.log_box.configure(
                state="normal"
            )

            self.log_box.insert(
                "end",
                texto + "\n"
            )

            self.log_box.see("end")

            self.log_box.configure(
                state="disabled"
            )

        self.after(
            0,
            inserir
        )

    # ========================================================
    # STATUS
    # ========================================================

    def atualizar_progresso(
        self,
        atual,
        total,
        texto=None
    ):

        if total <= 0:
            progresso = 0
        else:
            progresso = atual / total

        def atualizar():

            self.progress_bar.set(
                progresso
            )

            self.label_progresso.configure(
                text=f"{progresso * 100:.0f}%"
            )

            if texto:
                self.label_status.configure(
                    text=texto
                )

        self.after(
            0,
            atualizar
        )

    # ========================================================
    # PASTA
    # ========================================================

    def selecionar_pasta(self):

        if self.processando:
            return

        pasta = filedialog.askdirectory(
            title="Selecione a pasta principal"
        )

        if not pasta:
            return

        self.pasta = Path(pasta)

        self.entry_pasta.delete(
            0,
            "end"
        )

        self.entry_pasta.insert(
            0,
            str(self.pasta)
        )

        self.analisar_pasta()

    def analisar_pasta(self):

        if not self.pasta:
            return

        videos = localizar_videos(
            self.pasta
        )

        self.label_contagem.configure(
            text=(
                f"Vídeos encontrados: "
                f"{len(videos)}"
            )
        )

        self.label_status.configure(
            text="Pasta analisada."
        )

        self.log_box.configure(
            state="normal"
        )

        self.log_box.delete(
            "1.0",
            "end"
        )

        if videos:

            self.log_box.insert(
                "end",
                "ORDEM DOS VÍDEOS:\n\n"
            )

            for numero, video in enumerate(
                videos,
                start=1
            ):

                relativo = video.relative_to(
                    self.pasta
                )

                self.log_box.insert(
                    "end",
                    f"{numero:04d} - {relativo}\n"
                )

        else:

            self.log_box.insert(
                "end",
                "Nenhum vídeo encontrado."
            )

        self.log_box.configure(
            state="disabled"
        )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    def iniciar(self):

        if self.processando:
            return

        pasta_texto = self.entry_pasta.get().strip()

        if not pasta_texto:

            messagebox.showwarning(
                "Pasta não selecionada",
                "Selecione uma pasta primeiro."
            )

            return

        pasta = Path(pasta_texto)

        if not pasta.exists():

            messagebox.showerror(
                "Erro",
                "A pasta informada não existe."
            )

            return

        nome_saida = self.entry_nome.get().strip()

        if not nome_saida:

            nome_saida = "audio_unificado.m4a"

        if not nome_saida.lower().endswith(".m4a"):

            nome_saida += ".m4a"

        self.pasta = pasta

        self.processando = True

        self.botao_iniciar.configure(
            state="disabled",
            text="Processando..."
        )

        self.botao_abrir.configure(
            state="disabled"
        )

        self.progress_bar.set(0)

        self.label_progresso.configure(
            text="0%"
        )

        thread = threading.Thread(
            target=self.processar,
            args=(
                pasta,
                nome_saida,
                self.combo_bitrate.get()
            ),
            daemon=True
        )

        thread.start()

    # ========================================================
    # EXECUTAR FFMPEG
    # ========================================================

    def executar_ffmpeg(self, comando):

        processo = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if os.name == "nt"
                else 0
            )
        )

        return (
            processo.returncode,
            processo.stderr
        )

    # ========================================================
    # PROCESSAR
    # ========================================================

    def processar(
        self,
        pasta,
        nome_saida,
        bitrate
    ):

        try:

            ffmpeg = obter_ffmpeg()

            self.log(
                "\n======================================"
            )
            self.log(
                "INICIANDO PROCESSAMENTO"
            )
            self.log(
                "======================================\n"
            )

            videos = localizar_videos(
                pasta
            )

            if not videos:

                raise RuntimeError(
                    "Nenhum vídeo encontrado na pasta."
                )

            total = len(videos)

            self.after(
                0,
                lambda: self.label_contagem.configure(
                    text=f"Vídeos encontrados: {total}"
                )
            )

            arquivo_final = (
                pasta / nome_saida
            )

            with tempfile.TemporaryDirectory(
                prefix="audio_unificador_"
            ) as pasta_temp:

                pasta_temp = Path(
                    pasta_temp
                )

                segmentos = []

                # ============================================
                # EXTRAÇÃO
                # ============================================

                for indice, video in enumerate(
                    videos,
                    start=1
                ):

                    relativo = video.relative_to(
                        pasta
                    )

                    self.log(
                        f"[{indice}/{total}] {relativo}"
                    )

                    self.atualizar_progresso(
                        indice - 1,
                        total + 1,
                        (
                            f"Extraindo áudio "
                            f"{indice} de {total}..."
                        )
                    )

                    temporario = (
                        pasta_temp
                        / f"{indice:06d}.flac"
                    )

                    comando = [
                        ffmpeg,

                        "-hide_banner",
                        "-loglevel",
                        "error",

                        "-y",

                        "-i",
                        str(video),

                        "-vn",

                        "-map",
                        "0:a:0?",

                        "-map_metadata",
                        "-1",

                        "-ar",
                        str(SAMPLE_RATE),

                        "-ac",
                        str(CANAIS),

                        "-c:a",
                        "flac",

                        "-compression_level",
                        "5",

                        str(temporario)
                    ]

                    codigo, erro = (
                        self.executar_ffmpeg(
                            comando
                        )
                    )

                    if (
                        codigo != 0
                        or not temporario.exists()
                        or temporario.stat().st_size == 0
                    ):

                        self.log(
                            "    ⚠ Sem áudio ou erro. Ignorado."
                        )

                        if erro.strip():

                            ultima_linha = (
                                erro
                                .strip()
                                .splitlines()[-1]
                            )

                            self.log(
                                f"    {ultima_linha}"
                            )

                        continue

                    segmentos.append(
                        temporario
                    )

                    self.log(
                        "    ✓ Áudio extraído."
                    )

                if not segmentos:

                    raise RuntimeError(
                        "Nenhum vídeo possui áudio utilizável."
                    )

                # ============================================
                # LISTA DE CONCATENAÇÃO
                # ============================================

                arquivo_lista = (
                    pasta_temp
                    / "concat.txt"
                )

                with open(
                    arquivo_lista,
                    "w",
                    encoding="utf-8"
                ) as arquivo:

                    for segmento in segmentos:

                        arquivo.write(
                            f"file '{segmento.name}'\n"
                        )

                # ============================================
                # CONCATENAÇÃO FINAL
                # ============================================

                self.atualizar_progresso(
                    total,
                    total + 1,
                    "Unindo os áudios..."
                )

                self.log(
                    "\nUnindo todos os áudios..."
                )

                comando_final = [
                    ffmpeg,

                    "-hide_banner",
                    "-loglevel",
                    "error",

                    "-y",

                    "-f",
                    "concat",

                    "-safe",
                    "0",

                    "-i",
                    str(arquivo_lista),

                    "-vn",

                    "-c:a",
                    "aac",

                    "-b:a",
                    bitrate,

                    "-ar",
                    str(SAMPLE_RATE),

                    "-ac",
                    str(CANAIS),

                    "-movflags",
                    "+faststart",

                    str(arquivo_final)
                ]

                codigo, erro = (
                    self.executar_ffmpeg(
                        comando_final
                    )
                )

                if codigo != 0:

                    raise RuntimeError(
                        "Erro durante a criação "
                        "do arquivo final:\n\n"
                        + erro
                    )

            # ================================================
            # FINALIZAÇÃO
            # ================================================

            tamanho = formatar_tamanho(
                arquivo_final.stat().st_size
            )

            self.atualizar_progresso(
                total + 1,
                total + 1,
                "Concluído."
            )

            self.log(
                "\n======================================"
            )
            self.log(
                "CONCLUÍDO"
            )
            self.log(
                "======================================"
            )

            self.log(
                f"\nArquivo:\n{arquivo_final}"
            )

            self.log(
                f"\nTamanho final: {tamanho}"
            )

            self.log(
                f"Qualidade: AAC {bitrate}"
            )

            self.log(
                f"Vídeos encontrados: {total}"
            )

            self.log(
                f"Áudios utilizados: {len(segmentos)}"
            )

            self.after(
                0,
                lambda: self.finalizar_sucesso(
                    arquivo_final,
                    tamanho
                )
            )

        except Exception as erro:

            self.log(
                f"\nERRO:\n{erro}"
            )

            self.after(
                0,
                lambda e=str(erro): (
                    self.finalizar_erro(e)
                )
            )

    # ========================================================
    # FINALIZAÇÃO
    # ========================================================

    def finalizar_sucesso(
        self,
        arquivo_final,
        tamanho
    ):

        self.processando = False

        self.botao_iniciar.configure(
            state="normal",
            text="Iniciar processamento"
        )

        self.botao_abrir.configure(
            state="normal"
        )

        messagebox.showinfo(
            "Concluído",
            (
                "Áudio criado com sucesso!\n\n"
                f"{arquivo_final.name}\n\n"
                f"Tamanho: {tamanho}"
            )
        )

    def finalizar_erro(
        self,
        erro
    ):

        self.processando = False

        self.botao_iniciar.configure(
            state="normal",
            text="Iniciar processamento"
        )

        messagebox.showerror(
            "Erro",
            erro
        )

    # ========================================================
    # ABRIR PASTA
    # ========================================================

    def abrir_pasta(self):

        if not self.pasta:
            return

        try:

            if os.name == "nt":

                os.startfile(
                    self.pasta
                )

            elif sys.platform == "darwin":

                subprocess.Popen([
                    "open",
                    str(self.pasta)
                ])

            else:

                subprocess.Popen([
                    "xdg-open",
                    str(self.pasta)
                ])

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                str(erro)
            )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app = App()

    app.mainloop()