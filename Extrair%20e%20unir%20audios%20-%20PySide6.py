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
instalar_biblioteca("PySide6")
instalar_biblioteca("imageio-ffmpeg", "imageio_ffmpeg")


# Agora podemos importar normalmente
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
    QProgressBar,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
)
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
# INTERFACE PYSIDE6
# ============================================================

class App(QMainWindow):

    # Sinais usados para atualizar a interface com segurança
    # a partir da thread de processamento.
    sinal_log = Signal(str)
    sinal_progresso = Signal(int, str)
    sinal_contagem = Signal(int)
    sinal_sucesso = Signal(str, str)
    sinal_erro = Signal(str)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Extrator e Unificador de Áudio")
        self.resize(900, 720)
        self.setMinimumSize(780, 650)

        self.pasta = None
        self.processando = False

        self.criar_interface()
        self.conectar_sinais()

    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout_raiz = QVBoxLayout(central)
        layout_raiz.setContentsMargins(25, 22, 25, 25)
        layout_raiz.setSpacing(8)

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        titulo = QLabel("Extrator e Unificador de Áudio")
        fonte_titulo = QFont()
        fonte_titulo.setPointSize(20)
        fonte_titulo.setBold(True)
        titulo.setFont(fonte_titulo)
        titulo.setAlignment(Qt.AlignHCenter)
        layout_raiz.addWidget(titulo)

        subtitulo = QLabel(
            "Localiza vídeos, extrai os áudios e gera um único arquivo M4A."
        )
        subtitulo.setAlignment(Qt.AlignHCenter)
        subtitulo.setStyleSheet("color: #777777;")
        layout_raiz.addWidget(subtitulo)
        layout_raiz.addSpacing(12)

        # ----------------------------------------------------
        # FRAME PRINCIPAL
        # ----------------------------------------------------

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        layout_frame = QVBoxLayout(frame)
        layout_frame.setContentsMargins(20, 20, 20, 20)
        layout_frame.setSpacing(10)

        layout_raiz.addWidget(frame, 1)

        # ----------------------------------------------------
        # SELEÇÃO DE PASTA
        # ----------------------------------------------------

        pasta_label = QLabel("Pasta principal:")
        fonte_label = QFont()
        fonte_label.setBold(True)
        pasta_label.setFont(fonte_label)
        layout_frame.addWidget(pasta_label)

        pasta_layout = QHBoxLayout()
        pasta_layout.setSpacing(10)

        self.entry_pasta = QLineEdit()
        self.entry_pasta.setPlaceholderText(
            "Selecione a pasta dos vídeos..."
        )
        pasta_layout.addWidget(self.entry_pasta, 1)

        self.botao_pasta = QPushButton("Selecionar pasta")
        self.botao_pasta.setMinimumWidth(150)
        self.botao_pasta.clicked.connect(
            self.selecionar_pasta
        )
        pasta_layout.addWidget(self.botao_pasta)

        layout_frame.addLayout(pasta_layout)
        layout_frame.addSpacing(8)

        # ----------------------------------------------------
        # CONFIGURAÇÕES
        # ----------------------------------------------------

        configuracoes = QHBoxLayout()
        configuracoes.setSpacing(12)

        nome_layout = QVBoxLayout()
        nome_layout.setSpacing(5)

        nome_label = QLabel("Nome do arquivo:")
        nome_layout.addWidget(nome_label)

        self.entry_nome = QLineEdit("audio_unificado.m4a")
        nome_layout.addWidget(self.entry_nome)

        configuracoes.addLayout(nome_layout, 1)

        bitrate_layout = QVBoxLayout()
        bitrate_layout.setSpacing(5)

        bitrate_label = QLabel("Qualidade AAC:")
        bitrate_layout.addWidget(bitrate_label)

        self.combo_bitrate = QComboBox()
        self.combo_bitrate.addItems([
            "128k",
            "160k",
            "192k",
            "256k",
            "320k"
        ])
        self.combo_bitrate.setCurrentText("192k")
        self.combo_bitrate.setMinimumWidth(130)
        bitrate_layout.addWidget(self.combo_bitrate)

        configuracoes.addLayout(bitrate_layout)

        layout_frame.addLayout(configuracoes)
        layout_frame.addSpacing(8)

        # ----------------------------------------------------
        # INFORMAÇÕES
        # ----------------------------------------------------

        self.label_status = QLabel("Nenhuma pasta selecionada.")
        layout_frame.addWidget(self.label_status)

        self.label_contagem = QLabel("Vídeos encontrados: 0")
        layout_frame.addWidget(self.label_contagem)
        layout_frame.addSpacing(4)

        # ----------------------------------------------------
        # BARRA DE PROGRESSO
        # ----------------------------------------------------

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout_frame.addWidget(self.progress_bar)

        self.label_progresso = QLabel("0%")
        self.label_progresso.setAlignment(Qt.AlignHCenter)
        layout_frame.addWidget(self.label_progresso)
        layout_frame.addSpacing(4)

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        log_label = QLabel("Processamento:")
        log_label.setFont(fonte_label)
        layout_frame.addWidget(log_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(230)
        layout_frame.addWidget(self.log_box, 1)

        # ----------------------------------------------------
        # BOTÕES
        # ----------------------------------------------------

        botoes = QHBoxLayout()
        botoes.setSpacing(10)

        self.botao_iniciar = QPushButton("Iniciar processamento")
        self.botao_iniciar.setMinimumHeight(42)
        fonte_botao = self.botao_iniciar.font()
        fonte_botao.setBold(True)
        self.botao_iniciar.setFont(fonte_botao)
        self.botao_iniciar.clicked.connect(
            self.iniciar
        )
        botoes.addWidget(self.botao_iniciar, 1)

        self.botao_abrir = QPushButton("Abrir pasta")
        self.botao_abrir.setMinimumHeight(42)
        self.botao_abrir.setMinimumWidth(130)
        self.botao_abrir.setEnabled(False)
        self.botao_abrir.clicked.connect(
            self.abrir_pasta
        )
        botoes.addWidget(self.botao_abrir)

        layout_frame.addLayout(botoes)

    def conectar_sinais(self):
        """
        Conecta os sinais emitidos pela thread de processamento
        às funções que alteram os widgets na thread principal do Qt.
        """

        self.sinal_log.connect(self._inserir_log)
        self.sinal_progresso.connect(
            self._atualizar_progresso_ui
        )
        self.sinal_contagem.connect(
            self._atualizar_contagem_ui
        )
        self.sinal_sucesso.connect(
            self.finalizar_sucesso
        )
        self.sinal_erro.connect(
            self.finalizar_erro
        )

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

        percentual = max(
            0,
            min(100, round(progresso * 100))
        )

        self.sinal_progresso.emit(
            percentual,
            texto or ""
        )

    def _atualizar_progresso_ui(
        self,
        percentual,
        texto
    ):

        self.progress_bar.setValue(percentual)
        self.label_progresso.setText(
            f"{percentual}%"
        )

        if texto:
            self.label_status.setText(texto)

    def _atualizar_contagem_ui(self, total):
        self.label_contagem.setText(
            f"Vídeos encontrados: {total}"
        )

    # ========================================================
    # PASTA
    # ========================================================

    def selecionar_pasta(self):

        if self.processando:
            return

        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta principal",
            str(self.pasta) if self.pasta else ""
        )

        if not pasta:
            return

        self.pasta = Path(pasta)
        self.entry_pasta.setText(
            str(self.pasta)
        )

        self.analisar_pasta()

    def analisar_pasta(self):

        if not self.pasta:
            return

        videos = localizar_videos(
            self.pasta
        )

        self.label_contagem.setText(
            f"Vídeos encontrados: {len(videos)}"
        )

        self.label_status.setText(
            "Pasta analisada."
        )

        linhas = []

        if videos:
            linhas.append("ORDEM DOS VÍDEOS:\n")

            for numero, video in enumerate(
                videos,
                start=1
            ):

                relativo = video.relative_to(
                    self.pasta
                )

                linhas.append(
                    f"{numero:04d} - {relativo}"
                )

        else:
            linhas.append(
                "Nenhum vídeo encontrado."
            )

        self.log_box.setPlainText(
            "\n".join(linhas)
        )

    # ========================================================
    # PROCESSAMENTO
    # ========================================================

    def iniciar(self):

        if self.processando:
            return

        pasta_texto = self.entry_pasta.text().strip()

        if not pasta_texto:

            QMessageBox.warning(
                self,
                "Pasta não selecionada",
                "Selecione uma pasta primeiro."
            )

            return

        pasta = Path(pasta_texto)

        if not pasta.exists() or not pasta.is_dir():

            QMessageBox.critical(
                self,
                "Erro",
                "A pasta informada não existe."
            )

            return

        nome_saida = self.entry_nome.text().strip()

        if not nome_saida:
            nome_saida = "audio_unificado.m4a"

        if not nome_saida.lower().endswith(".m4a"):
            nome_saida += ".m4a"

        self.pasta = pasta
        self.processando = True

        self.botao_iniciar.setEnabled(False)
        self.botao_iniciar.setText("Processando...")
        self.botao_pasta.setEnabled(False)
        self.botao_abrir.setEnabled(False)

        self.progress_bar.setValue(0)
        self.label_progresso.setText("0%")

        thread = threading.Thread(
            target=self.processar,
            args=(
                pasta,
                nome_saida,
                self.combo_bitrate.currentText()
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
            self.sinal_contagem.emit(total)

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
                            f"Preparando áudio "
                            f"{indice} de {total}..."
                        )
                    )

                    # Já codifica cada trecho diretamente em AAC/M4A.
                    # Assim, a etapa final só precisa concatenar os fluxos,
                    # sem recodificar horas de áudio novamente.
                    temporario = (
                        pasta_temp
                        / f"{indice:06d}.m4a"
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
                        "aac",

                        "-b:a",
                        bitrate,

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
                        "    ✓ Áudio preparado."
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
                    "Unindo os áudios sem recodificar..."
                )

                self.log(
                    "\nUnindo todos os áudios "
                    "(cópia rápida, sem recodificação)..."
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

                    # Os segmentos já estão em AAC com os mesmos
                    # parâmetros. Apenas copia os pacotes para o M4A final.
                    "-c:a",
                    "copy",

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

            self.sinal_sucesso.emit(
                str(arquivo_final),
                tamanho
            )

        except Exception as erro:

            self.log(
                f"\nERRO:\n{erro}"
            )

            self.sinal_erro.emit(
                str(erro)
            )

    # ========================================================
    # FINALIZAÇÃO
    # ========================================================

    def finalizar_sucesso(
        self,
        caminho_arquivo,
        tamanho
    ):

        arquivo_final = Path(caminho_arquivo)

        self.processando = False

        self.botao_iniciar.setEnabled(True)
        self.botao_iniciar.setText(
            "Iniciar processamento"
        )
        self.botao_pasta.setEnabled(True)
        self.botao_abrir.setEnabled(True)

        QMessageBox.information(
            self,
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

        self.botao_iniciar.setEnabled(True)
        self.botao_iniciar.setText(
            "Iniciar processamento"
        )
        self.botao_pasta.setEnabled(True)

        QMessageBox.critical(
            self,
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

            QMessageBox.critical(
                self,
                "Erro",
                str(erro)
            )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app_qt = QApplication(sys.argv)

    janela = App()
    janela.show()

    sys.exit(app_qt.exec())
