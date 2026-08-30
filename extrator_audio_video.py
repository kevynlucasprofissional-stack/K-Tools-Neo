import sys
import os
import subprocess
import importlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Acho qu esse script serve para extrair audio de vídeos com interface gráfica
# python extrator_audio_video.py
# ============================================================
# ÁREA DE CONFIGURAÇÃO
# ============================================================

FORMATO_PADRAO = "mp3"

FORMATOS_SUPORTADOS = [
    "mp3",
    "wav",
    "m4a",
    "aac",
    "ogg",
    "flac"
]

# Configurações de codec para cada formato de saída
CONFIG_FORMATOS = {
    "mp3": ["-codec:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-codec:a", "pcm_s16le"],
    "m4a": ["-codec:a", "aac", "-b:a", "192k"],
    "aac": ["-codec:a", "aac", "-b:a", "192k"],
    "ogg": ["-codec:a", "libvorbis", "-q:a", "5"],
    "flac": ["-codec:a", "flac"]
}


# ============================================================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ============================================================

def instalar_e_importar(pacote, nome_importacao=None):
    """
    Tenta importar uma biblioteca.
    Se ela não estiver instalada, instala automaticamente via pip.
    """
    nome_importacao = nome_importacao or pacote

    try:
        return importlib.import_module(nome_importacao)
    except ImportError:
        try:
            subprocess.check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                pacote
            ])
            return importlib.import_module(nome_importacao)
        except Exception as erro:
            messagebox.showerror(
                "Erro ao instalar dependência",
                f"Não foi possível instalar a biblioteca necessária:\n\n{pacote}\n\nErro:\n{erro}"
            )
            sys.exit(1)


imageio_ffmpeg = instalar_e_importar("imageio-ffmpeg", "imageio_ffmpeg")


# ============================================================
# FUNÇÕES PRINCIPAIS
# ============================================================

def criar_nome_saida(pasta_saida, arquivo_video, formato):
    """
    Cria automaticamente o nome do arquivo de áudio de saída.
    Se já existir um arquivo com o mesmo nome, cria outro com numeração.
    """
    nome_base = os.path.splitext(os.path.basename(arquivo_video))[0]
    caminho_saida = os.path.join(pasta_saida, f"{nome_base}_audio.{formato}")

    contador = 1
    while os.path.exists(caminho_saida):
        caminho_saida = os.path.join(
            pasta_saida,
            f"{nome_base}_audio_{contador}.{formato}"
        )
        contador += 1

    return caminho_saida


def extrair_audio():
    arquivo_video = entrada_video.get().strip()
    pasta_saida = entrada_pasta.get().strip()
    formato = combo_formato.get().strip().lower()

    if not arquivo_video:
        messagebox.showwarning("Atenção", "Selecione um arquivo de vídeo.")
        return

    if not os.path.isfile(arquivo_video):
        messagebox.showerror("Erro", "O arquivo de vídeo selecionado não existe.")
        return

    if not pasta_saida:
        messagebox.showwarning("Atenção", "Selecione a pasta onde o áudio será salvo.")
        return

    if not os.path.isdir(pasta_saida):
        messagebox.showerror("Erro", "A pasta de saída selecionada não existe.")
        return

    if formato not in FORMATOS_SUPORTADOS:
        messagebox.showerror("Erro", "Formato de áudio não suportado.")
        return

    botao_extrair.config(state="disabled")
    status_var.set("Extraindo áudio... Aguarde.")

    thread = threading.Thread(
        target=executar_extracao,
        args=(arquivo_video, pasta_saida, formato),
        daemon=True
    )
    thread.start()


def executar_extracao(arquivo_video, pasta_saida, formato):
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        arquivo_saida = criar_nome_saida(pasta_saida, arquivo_video, formato)

        comando = [
            ffmpeg_exe,
            "-y",
            "-i", arquivo_video,
            "-vn",
            *CONFIG_FORMATOS[formato],
            arquivo_saida
        ]

        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )

        if resultado.returncode != 0:
            erro_ffmpeg = resultado.stderr[-3000:]
            janela.after(0, lambda: finalizar_com_erro(erro_ffmpeg))
            return

        janela.after(0, lambda: finalizar_com_sucesso(arquivo_saida))

    except Exception as erro:
        janela.after(0, lambda: finalizar_com_erro(str(erro)))


def finalizar_com_sucesso(arquivo_saida):
    botao_extrair.config(state="normal")
    status_var.set("Áudio extraído com sucesso!")

    messagebox.showinfo(
        "Concluído",
        f"Áudio extraído com sucesso!\n\nArquivo salvo em:\n{arquivo_saida}"
    )


def finalizar_com_erro(mensagem_erro):
    botao_extrair.config(state="normal")
    status_var.set("Erro ao extrair áudio.")

    messagebox.showerror(
        "Erro na extração",
        f"Não foi possível extrair o áudio.\n\nDetalhes:\n{mensagem_erro}"
    )


# ============================================================
# FUNÇÕES DA INTERFACE
# ============================================================

def selecionar_video():
    arquivo = filedialog.askopenfilename(
        title="Selecione um arquivo de vídeo",
        filetypes=[
            ("Arquivos de vídeo", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.mpeg *.mpg *.m4v"),
            ("Todos os arquivos", "*.*")
        ]
    )

    if arquivo:
        entrada_video.delete(0, tk.END)
        entrada_video.insert(0, arquivo)


def selecionar_pasta():
    pasta = filedialog.askdirectory(
        title="Selecione a pasta onde o áudio será salvo"
    )

    if pasta:
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, pasta)


# ============================================================
# INTERFACE GRÁFICA
# ============================================================

janela = tk.Tk()
janela.title("Extrator de Áudio de Vídeo")
janela.geometry("650x330")
janela.resizable(False, False)

frame_principal = ttk.Frame(janela, padding=20)
frame_principal.pack(fill="both", expand=True)

titulo = ttk.Label(
    frame_principal,
    text="Extrator de áudio de vídeo",
    font=("Segoe UI", 16, "bold")
)
titulo.pack(anchor="w", pady=(0, 15))

# Seleção de vídeo
label_video = ttk.Label(frame_principal, text="Arquivo de vídeo:")
label_video.pack(anchor="w")

frame_video = ttk.Frame(frame_principal)
frame_video.pack(fill="x", pady=(5, 12))

entrada_video = ttk.Entry(frame_video)
entrada_video.pack(side="left", fill="x", expand=True)

botao_video = ttk.Button(
    frame_video,
    text="Selecionar vídeo",
    command=selecionar_video
)
botao_video.pack(side="left", padx=(8, 0))

# Seleção de pasta
label_pasta = ttk.Label(frame_principal, text="Pasta onde o áudio será salvo:")
label_pasta.pack(anchor="w")

frame_pasta = ttk.Frame(frame_principal)
frame_pasta.pack(fill="x", pady=(5, 12))

entrada_pasta = ttk.Entry(frame_pasta)
entrada_pasta.pack(side="left", fill="x", expand=True)

botao_pasta = ttk.Button(
    frame_pasta,
    text="Selecionar pasta",
    command=selecionar_pasta
)
botao_pasta.pack(side="left", padx=(8, 0))

# Formato de saída
label_formato = ttk.Label(frame_principal, text="Formato de saída do áudio:")
label_formato.pack(anchor="w")

combo_formato = ttk.Combobox(
    frame_principal,
    values=FORMATOS_SUPORTADOS,
    state="readonly"
)
combo_formato.set(FORMATO_PADRAO)
combo_formato.pack(fill="x", pady=(5, 18))

# Botão principal
botao_extrair = ttk.Button(
    frame_principal,
    text="Extrair áudio",
    command=extrair_audio
)
botao_extrair.pack(fill="x", ipady=6)

# Status
status_var = tk.StringVar(value="Pronto para extrair áudio.")
label_status = ttk.Label(
    frame_principal,
    textvariable=status_var,
    foreground="#555"
)
label_status.pack(anchor="w", pady=(15, 0))

janela.mainloop()