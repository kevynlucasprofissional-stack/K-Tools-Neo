import sys
import os
import re
import subprocess
import tempfile
import threading
import hashlib
import json
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# ============================================================
# INSTALAÇÃO AUTOMÁTICA DE BIBLIOTECAS
# ============================================================

def instalar_biblioteca(pacote, modulo=None):
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


instalar_biblioteca("PySide6")
instalar_biblioteca("imageio-ffmpeg", "imageio_ffmpeg")


from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
)
import imageio_ffmpeg


# ============================================================
# CONFIGURAÇÕES
# ============================================================

EXTENSOES_VIDEO = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv", ".flv",
    ".m4v", ".mpeg", ".mpg", ".ts", ".mts", ".m2ts", ".3gp",
    ".3g2", ".ogv", ".vob", ".asf", ".rm", ".rmvb",
}

SAMPLE_RATE = 48000
CANAIS = 2


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def obter_ffmpeg():
    return imageio_ffmpeg.get_ffmpeg_exe()


def chave_natural(texto):
    return [
        int(parte) if parte.isdigit() else parte.lower()
        for parte in re.split(r"(\d+)", str(texto))
    ]


def localizar_videos(pasta):
    """
    Varredura recursiva automática, preservando a ordem natural da
    estrutura de subpastas e dos arquivos.
    """
    pasta = Path(pasta)
    videos = []

    for arquivo in pasta.rglob("*"):
        if arquivo.is_file() and arquivo.suffix.lower() in EXTENSOES_VIDEO:
            videos.append(arquivo)

    videos.sort(
        key=lambda arquivo: chave_natural(
            str(arquivo.relative_to(pasta))
        )
    )

    return videos


def obter_info_audio(ffmpeg, arquivo):
    """Lê metadados básicos do primeiro stream de áudio usando o próprio FFmpeg."""
    processo = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", str(arquivo)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0),
    )
    texto = processo.stderr or ""
    linha_audio = next(
        (linha.strip() for linha in texto.splitlines() if "Audio:" in linha),
        "",
    )

    codec = None
    sample_rate = None
    canais = None
    duracao = None

    if linha_audio:
        match_codec = re.search(r"Audio:\s*([^,\s]+)", linha_audio, re.I)
        match_rate = re.search(r"(\d+)\s*Hz", linha_audio, re.I)
        if match_codec:
            codec = match_codec.group(1).lower()
        if match_rate:
            sample_rate = int(match_rate.group(1))

        lower = linha_audio.lower()
        if "stereo" in lower:
            canais = 2
        elif "mono" in lower:
            canais = 1
        else:
            match_channels = re.search(r"(\d+)\s+channels?", lower)
            if match_channels:
                canais = int(match_channels.group(1))

    match_duration = re.search(
        r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", texto
    )
    if match_duration:
        horas, minutos, segundos = match_duration.groups()
        duracao = int(horas) * 3600 + int(minutos) * 60 + float(segundos)

    return {
        "codec": codec,
        "sample_rate": sample_rate,
        "channels": canais,
        "duration": duracao,
        "raw": linha_audio,
    }


def audio_compativel_com_saida(info):
    return (
        info.get("codec") == "aac"
        and info.get("sample_rate") == SAMPLE_RATE
        and info.get("channels") == CANAIS
    )


def chave_cache_audio(video, bitrate, info, trecho=None):
    stat = video.stat()
    dados = {
        "path": str(video.resolve()),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "bitrate": bitrate,
        "sample_rate": SAMPLE_RATE,
        "channels": CANAIS,
        "source_codec": info.get("codec"),
        "source_rate": info.get("sample_rate"),
        "source_channels": info.get("channels"),
        "trecho": trecho,
        "pipeline": 7,
    }
    bruto = json.dumps(dados, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(bruto).hexdigest()


def escapar_concat(caminho):
    return str(Path(caminho).resolve()).replace("\\", "/").replace("'", "'\\''")


def formatar_tamanho(bytes_total):
    mb = bytes_total / 1024 / 1024
    if mb < 1024:
        return f"{mb:.2f} MB"
    return f"{mb / 1024:.2f} GB"


# ============================================================
# COMPONENTES VISUAIS
# ============================================================

class DropZone(QFrame):
    pasta_soltra = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setProperty("dragActive", False)
        self.setMinimumHeight(118)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(5)

        self.titulo = QLabel("Arraste uma pasta para cá")
        self.titulo.setObjectName("dropTitle")
        self.titulo.setAlignment(Qt.AlignCenter)

        self.subtitulo = QLabel(
            "ou selecione manualmente. As subpastas serão varridas automaticamente."
        )
        self.subtitulo.setObjectName("dropSubtitle")
        self.subtitulo.setAlignment(Qt.AlignCenter)
        self.subtitulo.setWordWrap(True)

        layout.addStretch()
        layout.addWidget(self.titulo)
        layout.addWidget(self.subtitulo)
        layout.addStretch()

    def _set_drag_state(self, ativo):
        self.setProperty("dragActive", ativo)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def dragEnterEvent(self, event):
        urls = event.mimeData().urls()
        if urls and Path(urls[0].toLocalFile()).is_dir():
            event.acceptProposedAction()
            self._set_drag_state(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_drag_state(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._set_drag_state(False)
        urls = event.mimeData().urls()
        if not urls:
            return

        pasta = Path(urls[0].toLocalFile())
        if pasta.is_dir():
            self.pasta_soltra.emit(str(pasta))
            event.acceptProposedAction()


class StatCard(QFrame):
    def __init__(self, titulo, valor="—", detalhe="", parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(92)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(3)

        label_titulo = QLabel(titulo.upper())
        label_titulo.setObjectName("statTitle")

        self.label_valor = QLabel(valor)
        self.label_valor.setObjectName("statValue")

        self.label_detalhe = QLabel(detalhe)
        self.label_detalhe.setObjectName("statDetail")

        layout.addWidget(label_titulo)
        layout.addWidget(self.label_valor)
        layout.addWidget(self.label_detalhe)

    def atualizar(self, valor, detalhe=""):
        self.label_valor.setText(str(valor))
        self.label_detalhe.setText(detalhe)


# ============================================================
# APLICAÇÃO
# ============================================================

class App(QMainWindow):
    sinal_log = Signal(str)
    sinal_progresso = Signal(int, str)
    sinal_contagem = Signal(int)
    sinal_sucesso = Signal(str, str)
    sinal_erro = Signal(str)
    sinal_varredura = Signal(object)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AudioMerge Studio")
        self.resize(1180, 800)
        self.setMinimumSize(980, 700)

        self.pasta = None
        self.processando = False
        self.varrendo = False
        self.videos_detectados = []
        self.ultimo_arquivo = None
        self.scan_id = 0

        self.criar_interface()
        self.conectar_sinais()
        self.aplicar_estilo()
        self.atualizar_estado_pronto(False)

    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):
        central = QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(28, 24, 28, 24)
        raiz.setSpacing(18)

        # ---------------- HEADER ----------------
        header = QHBoxLayout()
        header.setSpacing(14)

        marca = QLabel("AM")
        marca.setObjectName("brandMark")
        marca.setFixedSize(48, 48)
        marca.setAlignment(Qt.AlignCenter)

        bloco_titulo = QVBoxLayout()
        bloco_titulo.setSpacing(1)

        titulo = QLabel("AudioMerge Studio")
        titulo.setObjectName("appTitle")

        subtitulo = QLabel(
            "Transforme uma coleção de vídeos em um único áudio, mantendo a ordem das pastas."
        )
        subtitulo.setObjectName("appSubtitle")

        bloco_titulo.addWidget(titulo)
        bloco_titulo.addWidget(subtitulo)

        header.addWidget(marca)
        header.addLayout(bloco_titulo)
        header.addStretch()

        self.status_chip = QLabel("Aguardando pasta")
        self.status_chip.setObjectName("statusChip")
        self.status_chip.setProperty("state", "idle")
        self.status_chip.setAlignment(Qt.AlignCenter)
        self.status_chip.setMinimumWidth(140)
        self.status_chip.setFixedHeight(34)
        header.addWidget(self.status_chip)

        raiz.addLayout(header)

        # ---------------- ÁREA CENTRAL ----------------
        corpo = QHBoxLayout()
        corpo.setSpacing(18)
        raiz.addLayout(corpo, 1)

        # COLUNA PRINCIPAL
        esquerda = QVBoxLayout()
        esquerda.setSpacing(14)
        corpo.addLayout(esquerda, 3)

        # Card fonte
        fonte_card = QFrame()
        fonte_card.setObjectName("panel")
        fonte_layout = QVBoxLayout(fonte_card)
        fonte_layout.setContentsMargins(20, 18, 20, 18)
        fonte_layout.setSpacing(12)

        secao_topo = QHBoxLayout()
        secao_titulo = QLabel("1. Escolha a fonte")
        secao_titulo.setObjectName("sectionTitle")
        secao_topo.addWidget(secao_titulo)
        secao_topo.addStretch()

        self.botao_atualizar = QPushButton("↻  Revarrer")
        self.botao_atualizar.setObjectName("ghostButton")
        self.botao_atualizar.setEnabled(False)
        self.botao_atualizar.clicked.connect(self.analisar_pasta)
        secao_topo.addWidget(self.botao_atualizar)

        fonte_layout.addLayout(secao_topo)

        self.drop_zone = DropZone()
        self.drop_zone.pasta_soltra.connect(self.definir_pasta)
        fonte_layout.addWidget(self.drop_zone)

        pasta_linha = QHBoxLayout()
        pasta_linha.setSpacing(10)

        self.entry_pasta = QLineEdit()
        self.entry_pasta.setPlaceholderText("Caminho da pasta principal")
        self.entry_pasta.returnPressed.connect(self.usar_caminho_digitado)
        pasta_linha.addWidget(self.entry_pasta, 1)

        self.botao_pasta = QPushButton("Escolher pasta")
        self.botao_pasta.setObjectName("secondaryButton")
        self.botao_pasta.clicked.connect(self.selecionar_pasta)
        pasta_linha.addWidget(self.botao_pasta)

        fonte_layout.addLayout(pasta_linha)
        esquerda.addWidget(fonte_card)

        # Cards de resumo
        stats = QGridLayout()
        stats.setHorizontalSpacing(10)
        stats.setVerticalSpacing(10)

        self.card_videos = StatCard("Vídeos", "0", "nenhum detectado")
        self.card_pastas = StatCard("Subpastas", "0", "na seleção atual")
        self.card_tamanho = StatCard("Fonte", "0 MB", "tamanho dos vídeos")

        stats.addWidget(self.card_videos, 0, 0)
        stats.addWidget(self.card_pastas, 0, 1)
        stats.addWidget(self.card_tamanho, 0, 2)
        esquerda.addLayout(stats)

        # Lista de arquivos
        lista_card = QFrame()
        lista_card.setObjectName("panel")
        lista_layout = QVBoxLayout(lista_card)
        lista_layout.setContentsMargins(20, 18, 20, 18)
        lista_layout.setSpacing(10)

        lista_header = QHBoxLayout()
        lista_titulo = QLabel("2. Revise a ordem detectada")
        lista_titulo.setObjectName("sectionTitle")
        lista_header.addWidget(lista_titulo)
        lista_header.addStretch()

        self.entry_filtro = QLineEdit()
        self.entry_filtro.setPlaceholderText("Filtrar vídeos...")
        self.entry_filtro.setMaximumWidth(230)
        self.entry_filtro.textChanged.connect(self.filtrar_lista)
        lista_header.addWidget(self.entry_filtro)

        lista_layout.addLayout(lista_header)

        self.lista_videos = QListWidget()
        self.lista_videos.setObjectName("videoList")
        self.lista_videos.setAlternatingRowColors(False)
        self.lista_videos.hide()
        lista_layout.addWidget(self.lista_videos, 1)

        self.label_lista_vazia = QLabel(
            "Selecione uma pasta para visualizar a sequência dos vídeos."
        )
        self.label_lista_vazia.setObjectName("emptyHint")
        self.label_lista_vazia.setAlignment(Qt.AlignCenter)
        lista_layout.addWidget(self.label_lista_vazia)

        esquerda.addWidget(lista_card, 1)

        # COLUNA DIREITA
        direita = QVBoxLayout()
        direita.setSpacing(14)
        corpo.addLayout(direita, 2)

        # Configurações
        config_card = QFrame()
        config_card.setObjectName("panel")
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(20, 18, 20, 20)
        config_layout.setSpacing(12)

        config_titulo = QLabel("3. Configure a saída")
        config_titulo.setObjectName("sectionTitle")
        config_layout.addWidget(config_titulo)

        nome_label = QLabel("Nome do arquivo")
        nome_label.setObjectName("fieldLabel")
        config_layout.addWidget(nome_label)

        self.entry_nome = QLineEdit("audio_unificado.m4a")
        self.entry_nome.textChanged.connect(self.atualizar_preview_saida)
        config_layout.addWidget(self.entry_nome)

        bitrate_linha = QHBoxLayout()
        bitrate_bloco = QVBoxLayout()
        bitrate_bloco.setSpacing(5)

        bitrate_label = QLabel("Qualidade AAC")
        bitrate_label.setObjectName("fieldLabel")
        bitrate_bloco.addWidget(bitrate_label)

        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems(["128k", "160k", "192k", "256k", "320k"])
        self.combo_bitrate.setCurrentText("192k")
        bitrate_bloco.addWidget(self.combo_bitrate)

        bitrate_linha.addLayout(bitrate_bloco, 1)

        modo_box = QFrame()
        modo_box.setObjectName("fastMode")
        modo_layout = QVBoxLayout(modo_box)
        modo_layout.setContentsMargins(12, 8, 12, 8)
        modo_layout.setSpacing(1)
        modo_tag = QLabel("MODO RÁPIDO")
        modo_tag.setObjectName("fastTag")
        modo_desc = QLabel("União final sem recodificar")
        modo_desc.setObjectName("fastDesc")
        modo_desc.setWordWrap(True)
        modo_layout.addWidget(modo_tag)
        modo_layout.addWidget(modo_desc)
        bitrate_linha.addWidget(modo_box, 1)

        config_layout.addLayout(bitrate_linha)

        motor_label = QLabel("Motor de processamento")
        motor_label.setObjectName("fieldLabel")
        config_layout.addWidget(motor_label)

        self.combo_motor = QComboBox()
        self.combo_motor.addItems([
            "Turbo adaptativo",
            "Paralelo + Smart Copy",
            "Single-pass sem temporários",
        ])
        self.combo_motor.setCurrentText("Turbo adaptativo")
        config_layout.addWidget(self.combo_motor)

        self.check_cache = QCheckBox("Reutilizar cache de áudios já processados")
        self.check_cache.setChecked(True)
        self.check_cache.setToolTip(
            "Acelera novas execuções quando os vídeos e as configurações não mudaram."
        )
        config_layout.addWidget(self.check_cache)

        self.check_dividir_longos = QCheckBox(
            "Dividir vídeos longos para processar trechos em paralelo"
        )
        self.check_dividir_longos.setChecked(True)
        self.check_dividir_longos.setToolTip(
            "Vídeos com mais de 45 minutos que precisem de recodificação "
            "são divididos em blocos de 15 minutos."
        )
        config_layout.addWidget(self.check_dividir_longos)

        saida_label = QLabel("Arquivo final")
        saida_label.setObjectName("fieldLabel")
        config_layout.addWidget(saida_label)

        self.label_saida = QLabel("Escolha uma pasta para definir o destino.")
        self.label_saida.setObjectName("outputPreview")
        self.label_saida.setWordWrap(True)
        config_layout.addWidget(self.label_saida)

        direita.addWidget(config_card)

        # Processamento
        processo_card = QFrame()
        processo_card.setObjectName("panelAccent")
        processo_layout = QVBoxLayout(processo_card)
        processo_layout.setContentsMargins(20, 18, 20, 20)
        processo_layout.setSpacing(10)

        processo_titulo = QLabel("4. Criar áudio")
        processo_titulo.setObjectName("sectionTitle")
        processo_layout.addWidget(processo_titulo)

        self.label_status = QLabel("Escolha uma pasta para começar.")
        self.label_status.setObjectName("processStatus")
        self.label_status.setWordWrap(True)
        processo_layout.addWidget(self.label_status)

        progresso_linha = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        progresso_linha.addWidget(self.progress_bar, 1)

        self.label_progresso = QLabel("0%")
        self.label_progresso.setObjectName("progressValue")
        self.label_progresso.setFixedWidth(44)
        self.label_progresso.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        progresso_linha.addWidget(self.label_progresso)
        processo_layout.addLayout(progresso_linha)

        self.botao_iniciar = QPushButton("▶  Criar áudio unificado")
        self.botao_iniciar.setObjectName("primaryButton")
        self.botao_iniciar.setMinimumHeight(48)
        self.botao_iniciar.clicked.connect(self.iniciar)
        processo_layout.addWidget(self.botao_iniciar)

        self.botao_abrir = QPushButton("Abrir pasta do resultado")
        self.botao_abrir.setObjectName("secondaryButton")
        self.botao_abrir.setEnabled(False)
        self.botao_abrir.clicked.connect(self.abrir_pasta)
        processo_layout.addWidget(self.botao_abrir)

        self.label_resultado = QLabel("")
        self.label_resultado.setObjectName("resultHint")
        self.label_resultado.setWordWrap(True)
        self.label_resultado.hide()
        processo_layout.addWidget(self.label_resultado)

        direita.addWidget(processo_card)

        # Log expansível
        log_card = QFrame()
        log_card.setObjectName("panel")
        log_layout = QVBoxLayout(log_card)
        log_layout.setContentsMargins(16, 12, 16, 12)
        log_layout.setSpacing(8)

        log_topo = QHBoxLayout()
        self.botao_detalhes = QPushButton("Detalhes técnicos  ›")
        self.botao_detalhes.setObjectName("linkButton")
        self.botao_detalhes.clicked.connect(self.alternar_log)
        log_topo.addWidget(self.botao_detalhes)
        log_topo.addStretch()

        self.botao_limpar_log = QPushButton("Limpar")
        self.botao_limpar_log.setObjectName("linkButton")
        self.botao_limpar_log.clicked.connect(lambda: self.log_box.clear())
        log_topo.addWidget(self.botao_limpar_log)

        log_layout.addLayout(log_topo)

        self.log_box = QTextEdit()
        self.log_box.setObjectName("logBox")
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(180)
        self.log_box.hide()
        log_layout.addWidget(self.log_box)

        direita.addWidget(log_card, 1)

        # Rodapé
        rodape = QLabel(
            "AAC • 48 kHz • estéreo • união rápida por stream copy"
        )
        rodape.setObjectName("footer")
        rodape.setAlignment(Qt.AlignCenter)
        raiz.addWidget(rodape)

    def aplicar_estilo(self):
        self.setStyleSheet("""
            QWidget#root {
                background: #0B0D12;
                color: #EDEFF5;
                font-family: "Segoe UI", "Inter", Arial;
                font-size: 13px;
            }

            QLabel#brandMark {
                background: #7C5CFC;
                color: white;
                border-radius: 15px;
                font-size: 16px;
                font-weight: 800;
            }

            QLabel#appTitle {
                color: #F7F8FC;
                font-size: 24px;
                font-weight: 750;
            }

            QLabel#appSubtitle {
                color: #8F96A8;
                font-size: 12px;
            }

            QLabel#statusChip {
                border-radius: 17px;
                padding: 0 14px;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#statusChip[state="idle"] {
                background: #171A22;
                color: #A1A8B8;
                border: 1px solid #252A36;
            }
            QLabel#statusChip[state="scan"] {
                background: #282134;
                color: #CDBDFF;
                border: 1px solid #59489A;
            }
            QLabel#statusChip[state="ready"] {
                background: #13271E;
                color: #80E0AA;
                border: 1px solid #24573A;
            }
            QLabel#statusChip[state="work"] {
                background: #272316;
                color: #F3D778;
                border: 1px solid #65572A;
            }
            QLabel#statusChip[state="done"] {
                background: #13271E;
                color: #80E0AA;
                border: 1px solid #24573A;
            }
            QLabel#statusChip[state="error"] {
                background: #2A1719;
                color: #FF9B9B;
                border: 1px solid #6F2C33;
            }

            QFrame#panel, QFrame#panelAccent {
                background: #11141B;
                border: 1px solid #1F2430;
                border-radius: 16px;
            }

            QFrame#panelAccent {
                border: 1px solid #302A52;
                background: #12141D;
            }

            QLabel#sectionTitle {
                color: #F2F4F8;
                font-size: 15px;
                font-weight: 700;
            }

            QFrame#dropZone {
                background: #0D1016;
                border: 1px dashed #343A49;
                border-radius: 14px;
            }
            QFrame#dropZone:hover {
                background: #10131B;
                border: 1px dashed #6552C9;
            }
            QFrame#dropZone[dragActive="true"] {
                background: #17142A;
                border: 2px dashed #8A72FF;
            }
            QLabel#dropTitle {
                color: #E9EAF0;
                font-size: 15px;
                font-weight: 700;
            }
            QLabel#dropSubtitle {
                color: #737B8E;
                font-size: 11px;
            }

            QLineEdit, QComboBox {
                background: #0D1016;
                color: #EEF0F5;
                border: 1px solid #282D3A;
                border-radius: 10px;
                padding: 9px 11px;
                min-height: 18px;
                selection-background-color: #7C5CFC;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #7C5CFC;
            }
            QLineEdit::placeholder {
                color: #606879;
            }
            QComboBox::drop-down {
                border: none;
                width: 28px;
            }
            QComboBox QAbstractItemView {
                background: #151923;
                color: #EEF0F5;
                selection-background-color: #30285C;
                border: 1px solid #2A3040;
                outline: none;
            }

            QPushButton {
                border-radius: 10px;
                padding: 9px 14px;
                font-weight: 650;
            }
            QPushButton#primaryButton {
                background: #7C5CFC;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton#primaryButton:hover {
                background: #8A6AFF;
            }
            QPushButton#primaryButton:pressed {
                background: #6C4DE8;
            }
            QPushButton#primaryButton:disabled {
                background: #292C35;
                color: #666D7B;
            }
            QPushButton#secondaryButton {
                background: #191D27;
                color: #DDE0E8;
                border: 1px solid #2C3240;
            }
            QPushButton#secondaryButton:hover {
                background: #202532;
                border-color: #41495B;
            }
            QPushButton#secondaryButton:disabled {
                color: #5E6573;
                background: #151820;
                border-color: #232833;
            }
            QPushButton#ghostButton, QPushButton#linkButton {
                background: transparent;
                color: #AFA5E9;
                border: none;
                padding: 5px 8px;
            }
            QPushButton#ghostButton:hover, QPushButton#linkButton:hover {
                color: #D6D0FF;
                background: #19172A;
            }
            QPushButton#ghostButton:disabled {
                color: #555B68;
            }

            QFrame#statCard {
                background: #0F1218;
                border: 1px solid #1D222D;
                border-radius: 13px;
            }
            QLabel#statTitle {
                color: #687184;
                font-size: 9px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QLabel#statValue {
                color: #F1F3F7;
                font-size: 22px;
                font-weight: 750;
            }
            QLabel#statDetail {
                color: #6F7787;
                font-size: 10px;
            }

            QListWidget#videoList {
                background: #0C0F14;
                border: 1px solid #1D222D;
                border-radius: 11px;
                padding: 6px;
                outline: none;
            }
            QListWidget#videoList::item {
                color: #C9CEDA;
                padding: 8px 10px;
                margin: 1px 0;
                border-radius: 7px;
            }
            QListWidget#videoList::item:hover {
                background: #171B24;
            }
            QListWidget#videoList::item:selected {
                background: #282343;
                color: #F0EDFF;
            }
            QLabel#emptyHint {
                color: #626A79;
                padding: 12px;
            }

            QLabel#fieldLabel {
                color: #9097A8;
                font-size: 11px;
                font-weight: 650;
            }
            QFrame#fastMode {
                background: #151927;
                border: 1px solid #292F42;
                border-radius: 10px;
            }
            QLabel#fastTag {
                color: #9B89FF;
                font-size: 9px;
                font-weight: 800;
            }
            QLabel#fastDesc {
                color: #8990A0;
                font-size: 10px;
            }
            QLabel#outputPreview {
                color: #B7BDCA;
                background: #0D1016;
                border: 1px solid #222733;
                border-radius: 9px;
                padding: 9px 10px;
            }
            QLabel#processStatus {
                color: #A8AFBD;
                font-size: 12px;
            }
            QLabel#progressValue {
                color: #C9CED8;
                font-weight: 700;
            }
            QProgressBar {
                background: #232731;
                border: none;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background: #7C5CFC;
                border-radius: 4px;
            }
            QLabel#resultHint {
                background: #10231A;
                color: #88D9AA;
                border: 1px solid #244B36;
                border-radius: 9px;
                padding: 9px 10px;
            }
            QTextEdit#logBox {
                background: #090B0F;
                color: #AEB5C2;
                border: 1px solid #1B202A;
                border-radius: 10px;
                padding: 8px;
                font-family: Consolas, "Cascadia Mono", monospace;
                font-size: 11px;
            }
            QLabel#footer {
                color: #505868;
                font-size: 10px;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #2E3441;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #444B5B;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

    def conectar_sinais(self):
        self.sinal_log.connect(self._inserir_log)
        self.sinal_progresso.connect(self._atualizar_progresso_ui)
        self.sinal_contagem.connect(self._atualizar_contagem_ui)
        self.sinal_sucesso.connect(self.finalizar_sucesso)
        self.sinal_erro.connect(self.finalizar_erro)
        self.sinal_varredura.connect(self.finalizar_varredura)

    # ========================================================
    # ESTADOS E UX
    # ========================================================

    def definir_status_chip(self, texto, estado):
        self.status_chip.setText(texto)
        self.status_chip.setProperty("state", estado)
        self.status_chip.style().unpolish(self.status_chip)
        self.status_chip.style().polish(self.status_chip)
        self.status_chip.update()

    def atualizar_estado_pronto(self, pronto):
        pode_iniciar = pronto and not self.processando and not self.varrendo
        self.botao_iniciar.setEnabled(pode_iniciar)
        self.entry_nome.setEnabled(not self.processando)
        self.combo_bitrate.setEnabled(not self.processando)
        self.combo_motor.setEnabled(not self.processando)
        self.check_cache.setEnabled(not self.processando)
        self.check_dividir_longos.setEnabled(not self.processando)

    def atualizar_preview_saida(self):
        if not self.pasta:
            self.label_saida.setText("Escolha uma pasta para definir o destino.")
            return

        nome = self.entry_nome.text().strip() or "audio_unificado.m4a"
        if not nome.lower().endswith(".m4a"):
            nome += ".m4a"

        self.label_saida.setText(str(self.pasta / nome))

    def alternar_log(self):
        mostrar = self.log_box.isHidden()
        self.log_box.setVisible(mostrar)
        self.botao_detalhes.setText(
            "Detalhes técnicos  ⌄" if mostrar else "Detalhes técnicos  ›"
        )

    def filtrar_lista(self, texto):
        filtro = texto.strip().lower()
        for i in range(self.lista_videos.count()):
            item = self.lista_videos.item(i)
            item.setHidden(filtro not in item.text().lower())

    # ========================================================
    # LOG
    # ========================================================

    def log(self, texto):
        self.sinal_log.emit(texto)

    def _inserir_log(self, texto):
        self.log_box.moveCursor(QTextCursor.End)
        self.log_box.insertPlainText(texto + "\n")
        self.log_box.moveCursor(QTextCursor.End)

    # ========================================================
    # STATUS / PROGRESSO
    # ========================================================

    def atualizar_progresso(self, atual, total, texto=None):
        progresso = 0 if total <= 0 else atual / total
        percentual = max(0, min(100, round(progresso * 100)))
        self.sinal_progresso.emit(percentual, texto or "")

    def _atualizar_progresso_ui(self, percentual, texto):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)

        self.progress_bar.setValue(percentual)
        self.label_progresso.setText(f"{percentual}%")

        if texto:
            self.label_status.setText(texto)

    def _atualizar_contagem_ui(self, total):
        self.card_videos.atualizar(total, "vídeos na sequência")

    # ========================================================
    # PASTA / VARREDURA
    # ========================================================

    def selecionar_pasta(self):
        if self.processando:
            return

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta principal",
            str(self.pasta) if self.pasta else ""
        )

        if pasta:
            self.definir_pasta(pasta)

    def usar_caminho_digitado(self):
        caminho = self.entry_pasta.text().strip().strip('"')
        if caminho:
            self.definir_pasta(caminho)

    def definir_pasta(self, pasta):
        if self.processando:
            return

        pasta = Path(pasta)
        if not pasta.exists() or not pasta.is_dir():
            QMessageBox.warning(
                self,
                "Pasta inválida",
                "O caminho informado não corresponde a uma pasta válida."
            )
            return

        self.pasta = pasta
        self.entry_pasta.setText(str(pasta))
        self.botao_atualizar.setEnabled(True)
        self.botao_abrir.setEnabled(False)
        self.label_resultado.hide()
        self.ultimo_arquivo = None
        self.atualizar_preview_saida()
        self.analisar_pasta()

    def analisar_pasta(self):
        if not self.pasta or self.processando:
            return

        self.scan_id += 1
        scan_id_atual = self.scan_id
        self.varrendo = True
        self.videos_detectados = []
        self.lista_videos.clear()
        self.label_lista_vazia.setText("Varrendo pasta e subpastas...")
        self.label_lista_vazia.show()

        self.card_videos.atualizar("…", "procurando vídeos")
        self.card_pastas.atualizar("…", "analisando estrutura")
        self.card_tamanho.atualizar("…", "calculando tamanho")

        self.progress_bar.setRange(0, 0)
        self.label_progresso.setText("…")
        self.label_status.setText("Varrendo pasta e subpastas...")
        self.definir_status_chip("Analisando", "scan")
        self.atualizar_estado_pronto(False)
        self.botao_atualizar.setEnabled(False)

        pasta_atual = self.pasta

        def tarefa():
            try:
                videos = localizar_videos(pasta_atual)
                tamanho_total = sum(
                    video.stat().st_size
                    for video in videos
                    if video.exists()
                )

                pastas_relativas = {
                    str(video.parent.relative_to(pasta_atual))
                    for video in videos
                    if video.parent != pasta_atual
                }

                self.sinal_varredura.emit({
                    "pasta": str(pasta_atual),
                    "scan_id": scan_id_atual,
                    "videos": videos,
                    "tamanho": tamanho_total,
                    "subpastas": len(pastas_relativas),
                    "erro": None,
                })
            except Exception as erro:
                self.sinal_varredura.emit({
                    "pasta": str(pasta_atual),
                    "scan_id": scan_id_atual,
                    "videos": [],
                    "tamanho": 0,
                    "subpastas": 0,
                    "erro": str(erro),
                })

        threading.Thread(target=tarefa, daemon=True).start()

    def finalizar_varredura(self, dados):
        # Ignora resultados de varreduras anteriores.
        if (
            not self.pasta
            or Path(dados["pasta"]) != self.pasta
            or dados.get("scan_id") != self.scan_id
        ):
            return

        self.varrendo = False
        self.botao_atualizar.setEnabled(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.label_progresso.setText("0%")

        if dados["erro"]:
            self.definir_status_chip("Erro na varredura", "error")
            self.label_status.setText("Não foi possível analisar a pasta.")
            self.atualizar_estado_pronto(False)
            QMessageBox.critical(self, "Erro", dados["erro"])
            return

        videos = dados["videos"]
        self.videos_detectados = videos

        self.card_videos.atualizar(
            len(videos),
            "vídeos na sequência" if videos else "nenhum detectado"
        )
        self.card_pastas.atualizar(
            dados["subpastas"],
            "subpastas com vídeos"
        )
        self.card_tamanho.atualizar(
            formatar_tamanho(dados["tamanho"]),
            "tamanho dos vídeos"
        )

        self.lista_videos.clear()
        for numero, video in enumerate(videos, start=1):
            relativo = video.relative_to(self.pasta)
            item = QListWidgetItem(f"{numero:04d}    {relativo}")
            item.setToolTip(str(video))
            self.lista_videos.addItem(item)

        tem_videos = bool(videos)
        self.lista_videos.setVisible(tem_videos)
        self.label_lista_vazia.setVisible(not tem_videos)

        if tem_videos:
            self.definir_status_chip("Pronto para criar", "ready")
            self.label_status.setText(
                f"{len(videos)} vídeos prontos. Revise a ordem e clique em criar áudio."
            )
            self.label_lista_vazia.setText("")

            self.log_box.clear()
            self.log_box.append("ORDEM DOS VÍDEOS:\n")
            for numero, video in enumerate(videos, start=1):
                self.log_box.append(
                    f"{numero:04d} - {video.relative_to(self.pasta)}"
                )
        else:
            self.definir_status_chip("Nenhum vídeo", "idle")
            self.label_status.setText(
                "Nenhum arquivo de vídeo compatível foi encontrado."
            )
            self.label_lista_vazia.setText(
                "Nenhum vídeo compatível foi encontrado nesta pasta."
            )

        self.atualizar_estado_pronto(tem_videos)

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    def iniciar(self):
        if self.processando or self.varrendo:
            return

        if not self.pasta or not self.videos_detectados:
            QMessageBox.warning(
                self,
                "Nada para processar",
                "Selecione uma pasta que contenha vídeos primeiro."
            )
            return

        nome_saida = self.entry_nome.text().strip() or "audio_unificado.m4a"
        if not nome_saida.lower().endswith(".m4a"):
            nome_saida += ".m4a"

        self.processando = True
        self.label_resultado.hide()
        self.botao_iniciar.setEnabled(False)
        self.botao_iniciar.setText("Processando áudio...")
        self.botao_pasta.setEnabled(False)
        self.botao_atualizar.setEnabled(False)
        self.entry_pasta.setEnabled(False)
        self.botao_abrir.setEnabled(False)
        self.entry_nome.setEnabled(False)
        self.combo_bitrate.setEnabled(False)
        self.combo_motor.setEnabled(False)
        self.check_cache.setEnabled(False)
        self.check_dividir_longos.setEnabled(False)

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.label_progresso.setText("0%")
        self.label_status.setText("Preparando processamento...")
        self.definir_status_chip("Processando", "work")

        threading.Thread(
            target=self.processar,
            args=(
                self.pasta,
                nome_saida,
                self.combo_bitrate.currentText(),
                self.combo_motor.currentText(),
                self.check_cache.isChecked(),
                self.check_dividir_longos.isChecked(),
            ),
            daemon=True
        ).start()

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

        return processo.returncode, processo.stderr

    # ========================================================
    # PIPELINE DE ÁUDIO — MANTIDO
    # ========================================================

    # ========================================================
    # MOTOR SINGLE-PASS — SEM ARQUIVOS TEMPORÁRIOS
    # ========================================================

    def processar_single_pass(self, ffmpeg, videos, arquivo_final, bitrate):
        validos = []
        for video in videos:
            info = obter_info_audio(ffmpeg, video)
            if info.get("codec"):
                validos.append(video)

        if not validos:
            raise RuntimeError("Nenhum vídeo possui áudio utilizável.")

        comando = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        for video in validos:
            comando += ["-i", str(video)]

        filtros = []
        rotulos = []
        for i in range(len(validos)):
            rotulo = f"a{i}"
            filtros.append(
                f"[{i}:a:0]aresample={SAMPLE_RATE},"
                f"aformat=channel_layouts=stereo,"
                f"asetpts=PTS-STARTPTS[{rotulo}]"
            )
            rotulos.append(f"[{rotulo}]")

        if len(validos) == 1:
            filtros.append(f"{rotulos[0]}anull[outa]")
        else:
            filtros.append(
                "".join(rotulos) + f"concat=n={len(validos)}:v=0:a=1[outa]"
            )

        comando += [
            "-filter_complex", ";".join(filtros),
            "-map", "[outa]",
            "-c:a", "aac",
            "-aac_coder", "fast",
            "-b:a", bitrate,
            str(arquivo_final),
        ]

        self.log(
            f"Single-pass: {len(validos)} fontes → arquivo final, sem segmentos temporários."
        )
        codigo, erro = self.executar_ffmpeg(comando)
        if codigo != 0:
            raise RuntimeError("Erro no motor single-pass:\n\n" + erro)
        return len(validos)

    def processar(self, pasta, nome_saida, bitrate, motor, usar_cache, dividir_longos):
        try:
            ffmpeg = obter_ffmpeg()

            self.log("\n======================================")
            self.log("INICIANDO PROCESSAMENTO TURBO")
            self.log("======================================\n")

            videos = localizar_videos(pasta)
            if not videos:
                raise RuntimeError("Nenhum vídeo encontrado na pasta.")

            total_videos = len(videos)
            self.sinal_contagem.emit(total_videos)
            arquivo_final = pasta / nome_saida

            # O motor sem temporários permanece disponível como alternativa
            # explícita. O Turbo adaptativo prioriza paralelismo, Smart Copy,
            # cache e divisão de vídeos longos.
            if motor == "Single-pass sem temporários":
                self.atualizar_progresso(0, 1, "Processando em single-pass...")
                usados = self.processar_single_pass(
                    ffmpeg, videos, arquivo_final, bitrate
                )
                tamanho = formatar_tamanho(arquivo_final.stat().st_size)
                self.atualizar_progresso(1, 1, "Áudio criado com sucesso.")
                self.log(f"\nTamanho final: {tamanho}")
                self.log(f"Áudios utilizados: {usados}")
                self.sinal_sucesso.emit(str(arquivo_final), tamanho)
                return

            workers = min(6, max(2, (os.cpu_count() or 4) // 2))
            workers = min(workers, max(1, total_videos * 2))
            self.log(f"Processamento paralelo: {workers} workers")

            # Pré-análise também é paralela, para não transformar o probe
            # de metadados em um novo gargalo sequencial.
            self.atualizar_progresso(0, 100, "Analisando streams de áudio...")
            infos = {}
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futuros_info = {
                    executor.submit(obter_info_audio, ffmpeg, video): indice
                    for indice, video in enumerate(videos, start=1)
                }
                analisados = 0
                for futuro in as_completed(futuros_info):
                    indice = futuros_info[futuro]
                    infos[indice] = futuro.result()
                    analisados += 1
                    percentual_probe = int((analisados / total_videos) * 8)
                    self.sinal_progresso.emit(
                        percentual_probe,
                        f"Analisando áudio: {analisados} de {total_videos}..."
                    )

            cache_dir = Path.home() / ".audiomerge_studio_cache"
            if usar_cache:
                cache_dir.mkdir(parents=True, exist_ok=True)
                self.log(f"Cache persistente: {cache_dir}")

            LIMITE_VIDEO_LONGO = 45 * 60
            TAMANHO_TRECHO = 15 * 60
            trabalhos = []
            videos_divididos = 0

            for indice, video in enumerate(videos, start=1):
                info = infos.get(indice, {})
                if not info.get("codec"):
                    self.log(f"[{indice}/{total_videos}] ⚠ Sem stream de áudio: {video.name}")
                    continue

                duracao = info.get("duration") or 0
                pode_copiar = audio_compativel_com_saida(info)
                deve_dividir = (
                    dividir_longos
                    and not pode_copiar
                    and duracao >= LIMITE_VIDEO_LONGO
                )

                if deve_dividir:
                    quantidade = math.ceil(duracao / TAMANHO_TRECHO)
                    videos_divididos += 1
                    self.log(
                        f"[{indice}/{total_videos}] vídeo longo: "
                        f"{duracao / 60:.1f} min → {quantidade} trechos"
                    )
                    for trecho_indice in range(quantidade):
                        inicio = trecho_indice * TAMANHO_TRECHO
                        duracao_trecho = min(TAMANHO_TRECHO, duracao - inicio)
                        trabalhos.append({
                            "ordem": (indice, trecho_indice),
                            "video_index": indice,
                            "video": video,
                            "info": info,
                            "inicio": inicio,
                            "duracao": duracao_trecho,
                            "trecho_numero": trecho_indice + 1,
                            "trechos_total": quantidade,
                        })
                else:
                    trabalhos.append({
                        "ordem": (indice, 0),
                        "video_index": indice,
                        "video": video,
                        "info": info,
                        "inicio": None,
                        "duracao": None,
                        "trecho_numero": None,
                        "trechos_total": None,
                    })

            if not trabalhos:
                raise RuntimeError("Nenhum vídeo possui áudio utilizável.")

            if videos_divididos:
                self.log(
                    f"Divisão paralela ativada em {videos_divididos} vídeo(s) longo(s)."
                )

            with tempfile.TemporaryDirectory(prefix="audio_unificador_") as pasta_temp:
                pasta_temp = Path(pasta_temp)
                resultados = {}
                concluidos = 0
                falhas_trechos = []
                total_trabalhos = len(trabalhos)

                def preparar(trabalho):
                    ordem = trabalho["ordem"]
                    indice, trecho_idx = ordem
                    video = trabalho["video"]
                    info = trabalho["info"]
                    inicio = trabalho["inicio"]
                    duracao_trecho = trabalho["duracao"]
                    eh_trecho = inicio is not None
                    trecho_cache = None
                    if eh_trecho:
                        trecho_cache = [round(inicio, 3), round(duracao_trecho, 3)]

                    cache_final = None
                    if usar_cache:
                        chave = chave_cache_audio(
                            video, bitrate, info, trecho=trecho_cache
                        )
                        cache_final = cache_dir / f"{chave}.m4a"
                        if cache_final.exists() and cache_final.stat().st_size > 0:
                            return trabalho, cache_final, True, "", "cache"
                        destino = cache_dir / (
                            f"{chave}.{threading.get_ident()}.part.m4a"
                        )
                    else:
                        destino = pasta_temp / f"{indice:06d}_{trecho_idx:04d}.m4a"

                    destino.unlink(missing_ok=True)

                    # Smart Copy só é usado em um arquivo inteiro. Um trecho
                    # longo que entrou nesta fila precisa ser recodificado.
                    if not eh_trecho and audio_compativel_com_saida(info):
                        comando = [
                            ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                            "-i", str(video), "-vn", "-map", "0:a:0?",
                            "-map_metadata", "-1", "-c:a", "copy", str(destino)
                        ]
                        codigo, erro = self.executar_ffmpeg(comando)
                        if codigo == 0 and destino.exists() and destino.stat().st_size > 0:
                            if cache_final:
                                os.replace(destino, cache_final)
                                destino = cache_final
                            return trabalho, destino, True, erro, "copy"
                        destino.unlink(missing_ok=True)

                    comando = [
                        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    ]
                    if eh_trecho:
                        comando += ["-ss", f"{inicio:.3f}"]
                    comando += [
                        "-i", str(video),
                    ]
                    if eh_trecho:
                        comando += ["-t", f"{duracao_trecho:.3f}"]
                    comando += [
                        "-vn", "-map", "0:a:0?", "-map_metadata", "-1",
                    ]
                    if info.get("sample_rate") != SAMPLE_RATE:
                        comando += ["-ar", str(SAMPLE_RATE)]
                    if info.get("channels") != CANAIS:
                        comando += ["-ac", str(CANAIS)]
                    comando += [
                        "-c:a", "aac", "-aac_coder", "fast",
                        "-b:a", bitrate, str(destino)
                    ]

                    codigo, erro = self.executar_ffmpeg(comando)
                    ok = (
                        codigo == 0
                        and destino.exists()
                        and destino.stat().st_size > 0
                    )
                    if ok and cache_final:
                        os.replace(destino, cache_final)
                        destino = cache_final
                    elif not ok:
                        destino.unlink(missing_ok=True)
                    return trabalho, destino, ok, erro, "encode"

                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futuros = {
                        executor.submit(preparar, trabalho): trabalho
                        for trabalho in trabalhos
                    }

                    for futuro in as_completed(futuros):
                        trabalho, segmento, ok, erro, modo = futuro.result()
                        concluidos += 1
                        ordem = trabalho["ordem"]
                        indice = trabalho["video_index"]
                        video = trabalho["video"]
                        relativo = video.relative_to(pasta)

                        if trabalho["trecho_numero"]:
                            sufixo = (
                                f" — trecho {trabalho['trecho_numero']}/"
                                f"{trabalho['trechos_total']}"
                            )
                        else:
                            sufixo = ""

                        if ok:
                            resultados[ordem] = segmento
                            if modo == "cache":
                                icone = "♻ CACHE"
                            elif modo == "copy":
                                icone = "⚡ COPY"
                            else:
                                icone = "⚙ ENCODE"
                            self.log(
                                f"[{indice}/{total_videos}] ✓ {relativo}{sufixo} [{icone}]"
                            )
                        else:
                            self.log(
                                f"[{indice}/{total_videos}] ⚠ {relativo}{sufixo} — falhou"
                            )
                            if trabalho["trecho_numero"]:
                                falhas_trechos.append((relativo, sufixo))
                            if erro.strip():
                                self.log(f"    {erro.strip().splitlines()[-1]}")

                        # 8% fica reservado ao probe; 91% ao preparo; 1% concat.
                        percentual = 8 + int((concluidos / total_trabalhos) * 91)
                        self.sinal_progresso.emit(
                            min(percentual, 99),
                            f"Processando: {concluidos} de {total_trabalhos} tarefas..."
                        )

                if falhas_trechos:
                    raise RuntimeError(
                        "Um ou mais trechos de vídeos longos falharam. "
                        "O arquivo final não foi criado para evitar lacunas no áudio."
                    )

                segmentos = [resultados[chave] for chave in sorted(resultados)]
                if not segmentos:
                    raise RuntimeError("Nenhum vídeo possui áudio utilizável.")

                arquivo_lista = pasta_temp / "concat.txt"
                with open(arquivo_lista, "w", encoding="utf-8") as arquivo:
                    for segmento in segmentos:
                        arquivo.write(f"file '{escapar_concat(segmento)}'\n")

                self.sinal_progresso.emit(99, "Finalizando sem recodificar...")
                self.log(
                    "\nUnindo todos os segmentos (cópia rápida, sem recodificação)..."
                )
                comando_final = [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "concat", "-safe", "0", "-i", str(arquivo_lista),
                    "-vn", "-c:a", "copy", str(arquivo_final)
                ]
                codigo, erro = self.executar_ffmpeg(comando_final)
                if codigo != 0:
                    raise RuntimeError(
                        "Erro durante a criação do arquivo final:\n\n" + erro
                    )

            tamanho = formatar_tamanho(arquivo_final.stat().st_size)
            self.sinal_progresso.emit(100, "Áudio criado com sucesso.")
            self.log("\n======================================")
            self.log("CONCLUÍDO")
            self.log("======================================")
            self.log(f"\nArquivo:\n{arquivo_final}")
            self.log(f"\nTamanho final: {tamanho}")
            self.log(f"Qualidade: AAC {bitrate}")
            self.log(f"Vídeos encontrados: {total_videos}")
            self.log(f"Segmentos utilizados: {len(segmentos)}")
            self.sinal_sucesso.emit(str(arquivo_final), tamanho)

        except Exception as erro:
            self.log(f"\nERRO:\n{erro}")
            self.sinal_erro.emit(str(erro))

    # ========================================================
    # FINALIZAÇÃO
    # ========================================================

    def finalizar_sucesso(self, caminho_arquivo, tamanho):
        arquivo_final = Path(caminho_arquivo)
        self.ultimo_arquivo = arquivo_final
        self.processando = False

        self.botao_iniciar.setText("▶  Criar áudio novamente")
        self.botao_pasta.setEnabled(True)
        self.botao_atualizar.setEnabled(True)
        self.entry_pasta.setEnabled(True)
        self.entry_nome.setEnabled(True)
        self.combo_bitrate.setEnabled(True)
        self.combo_motor.setEnabled(True)
        self.check_cache.setEnabled(True)
        self.check_dividir_longos.setEnabled(True)
        self.botao_abrir.setEnabled(True)
        self.atualizar_estado_pronto(bool(self.videos_detectados))

        self.progress_bar.setValue(100)
        self.label_progresso.setText("100%")
        self.label_status.setText("Concluído. O arquivo final está pronto para uso.")
        self.definir_status_chip("Concluído", "done")

        self.label_resultado.setText(
            f"✓ {arquivo_final.name}  •  {tamanho}"
        )
        self.label_resultado.show()

    def finalizar_erro(self, erro):
        self.processando = False

        self.botao_iniciar.setText("▶  Tentar novamente")
        self.botao_pasta.setEnabled(True)
        self.botao_atualizar.setEnabled(bool(self.pasta))
        self.entry_pasta.setEnabled(True)
        self.entry_nome.setEnabled(True)
        self.combo_bitrate.setEnabled(True)
        self.combo_motor.setEnabled(True)
        self.check_cache.setEnabled(True)
        self.check_dividir_longos.setEnabled(True)
        self.atualizar_estado_pronto(bool(self.videos_detectados))

        self.label_status.setText("O processamento foi interrompido por um erro.")
        self.definir_status_chip("Erro", "error")

        QMessageBox.critical(self, "Erro no processamento", erro)

    # ========================================================
    # ABRIR PASTA
    # ========================================================

    def abrir_pasta(self):
        pasta = self.pasta
        if not pasta:
            return

        try:
            if os.name == "nt":
                os.startfile(pasta)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(pasta)])
            else:
                subprocess.Popen(["xdg-open", str(pasta)])

        except Exception as erro:
            QMessageBox.critical(self, "Erro", str(erro))


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    app_qt = QApplication(sys.argv)
    app_qt.setApplicationName("AudioMerge Studio")

    janela = App()
    janela.show()

    sys.exit(app_qt.exec())
