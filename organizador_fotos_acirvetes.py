# -*- coding: utf-8 -*-
"""
Organizador de Fotos ACIRVETES
--------------------------------
Copia e organiza os principais acervos de fotos das funcionárias da ACIRV
a partir do Google Drive montado/sincronizado no Windows.

Estrutura final criada:
Imagens ACIRVETES/
├── 01_Retratos_Individuais/
├── 02_Uniforme_Copa/
├── 03_Banco_de_Imagens_ACIRVETES/
├── 04_Acervo_Equipe_ACIRV/
│   ├── Geral/
│   ├── Setembro_Amarelo_2025/
│   └── CAM/
└── 05_Adria_Rocha_Conecta_Saude/

O programa:
- instala PySide6 automaticamente, se necessário;
- permite escolher a raiz do Drive e a pasta de destino;
- verifica quais pastas/arquivos de origem existem;
- permite marcar/desmarcar grupos;
- copia sem apagar ou mover os arquivos originais;
- preserva subpastas;
- não sobrescreve arquivos diferentes com o mesmo nome;
- pula arquivos já copiados quando tamanho e data indicam que são iguais;
- mostra progresso e log em tempo real.
"""

import os
import sys
import shutil
import subprocess
import importlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Auto-instalação do PySide6
# ---------------------------------------------------------------------------

def ensure_package(import_name: str, pip_name: Optional[str] = None) -> None:
    try:
        importlib.import_module(import_name)
    except ImportError:
        package = pip_name or import_name
        print(f"[INFO] Instalando dependência: {package}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", package]
        )
        importlib.invalidate_caches()

ensure_package("PySide6")

from PySide6.QtCore import Qt, QObject, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

DEFAULT_SOURCE_ROOT = Path(r"H:\Meu Drive")
DEFAULT_DESTINATION = Path(r"C:\Users\Kevyn Lucas\Documents\Imagens ACIRVETES")

@dataclass
class CopyGroup:
    key: str
    title: str
    description: str
    source_relative: Optional[Path]
    destination_relative: Path
    source_is_file: bool = False
    exclude_relative_dirs: Tuple[Path, ...] = ()


GROUPS: List[CopyGroup] = [
    CopyGroup(
        key="retratos",
        title="01 · Retratos individuais",
        description=(
            "Fotos nomeadas individualmente das ACIRVETES, como Janaine, "
            "Maria Eduarda, Mônica, Naiara, Osileia, Rahuany, Rakilandia e Tereza."
        ),
        source_relative=Path(r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Fotos ACIRVETES"),
        destination_relative=Path("01_Retratos_Individuais"),
        exclude_relative_dirs=(Path(r"Fotos ACIRVERTES c  uniforme da copa"),),
    ),
    CopyGroup(
        key="uniforme_copa",
        title="02 · Uniforme da Copa",
        description=(
            "Fotos específicas das ACIRVETES com o uniforme da Copa. "
            "Ficam separadas para facilitar campanhas e peças temáticas."
        ),
        source_relative=Path(
            r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Fotos ACIRVETES"
            r"\Fotos ACIRVERTES c  uniforme da copa"
        ),
        destination_relative=Path("02_Uniforme_Copa"),
    ),
    CopyGroup(
        key="banco_acirvetes",
        title="03 · Banco de Imagens — ACIRVETES",
        description=(
            "Banco de imagens já separado pela ACIRV. É mantido como fonte própria "
            "mesmo quando algumas fotos também aparecem em outras pastas."
        ),
        source_relative=Path(
            r"GESTÃO 2025 2028\PLANEJAMENTO VCOM"
            r"\Banco de Imagens da ACIRV\ACIRVETES"
        ),
        destination_relative=Path("03_Banco_de_Imagens_ACIRVETES"),
    ),
    CopyGroup(
        key="equipe_geral",
        title="04A · Acervo geral da equipe ACIRV",
        description=(
            "Grande acervo bruto de fotos da equipe. Mantém as subpastas originais "
            "e concentra o material histórico."
        ),
        source_relative=Path(r"GESTÃO 2025 2028\FOTOS - EQUIPE ACIRV"),
        destination_relative=Path(r"04_Acervo_Equipe_ACIRV\Geral"),
        exclude_relative_dirs=(
            Path(r"17_09_2025_SETEMBRO AMARELO"),
            Path(r"CAM"),
        ),
    ),
    CopyGroup(
        key="setembro_amarelo",
        title="04B · Setembro Amarelo 2025",
        description=(
            "Subpasta temática encontrada dentro do acervo da equipe. "
            "É copiada também para um acesso direto e organizado."
        ),
        source_relative=Path(
            r"GESTÃO 2025 2028\FOTOS - EQUIPE ACIRV"
            r"\17_09_2025_SETEMBRO AMARELO"
        ),
        destination_relative=Path(r"04_Acervo_Equipe_ACIRV\Setembro_Amarelo_2025"),
    ),
    CopyGroup(
        key="cam",
        title="04C · CAM",
        description=(
            "Subpasta CAM encontrada dentro do acervo da equipe, separada "
            "para facilitar a localização posterior."
        ),
        source_relative=Path(r"GESTÃO 2025 2028\FOTOS - EQUIPE ACIRV\CAM"),
        destination_relative=Path(r"04_Acervo_Equipe_ACIRV\CAM"),
    ),
]

# Arquivos específicos da Ádria encontrados no material do Conecta Saúde.
ADRIA_FILES = [
    Path(
        r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV"
        r"\Materiais\CONECTA\Saúde 2º ed\Capa Chamada Ádria Rocha.png"
    ),
    Path(
        r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV"
        r"\Materiais\CONECTA\Saúde 2º ed\Capa Chamada Ádria Rocha.psd"
    ),
    Path(
        r"GESTÃO 2025 2028\PLANEJAMENTO VCOM\Conecta ACIRV"
        r"\Materiais\CONECTA\Saúde 2º ed\Chamada Ádria.mp4"
    ),
]

# Extensões consideradas relevantes. Outros arquivos (ex.: desktop.ini) não são copiados.
ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".jfif",
    ".bmp", ".tif", ".tiff", ".gif",
    ".mp4", ".mov", ".avi", ".mkv", ".m4v",
    ".psd"
}

# ---------------------------------------------------------------------------
# Funções utilitárias
# ---------------------------------------------------------------------------

def is_relevant_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS


def list_relevant_files(source: Path, exclude_relative_dirs: Tuple[Path, ...] = ()) -> List[Path]:
    if not source.exists():
        return []
    if source.is_file():
        return [source] if is_relevant_file(source) else []

    files: List[Path] = []
    excluded_abs = {(source / rel).resolve() for rel in exclude_relative_dirs}

    for root, dirs, filenames in os.walk(source):
        root_path = Path(root)
        # Impede a descida em subpastas que terão categoria própria no destino.
        dirs[:] = [
            d for d in dirs
            if (root_path / d).resolve() not in excluded_abs
        ]
        for filename in filenames:
            p = root_path / filename
            if is_relevant_file(p):
                files.append(p)
    return files


def same_file_quick(src: Path, dst: Path) -> bool:
    """Comparação rápida: tamanho e timestamp com pequena tolerância."""
    if not dst.exists() or not dst.is_file():
        return False
    try:
        s1 = src.stat()
        s2 = dst.stat()
        return s1.st_size == s2.st_size and abs(s1.st_mtime - s2.st_mtime) < 2
    except OSError:
        return False


def collision_safe_destination(src: Path, desired_dst: Path) -> Tuple[Path, bool]:
    """
    Retorna:
      (destino, True)  -> arquivo já existe e parece ser o mesmo; pode pular
      (destino, False) -> usar este destino

    Se existir outro arquivo diferente com o mesmo nome, cria:
    nome__copia_2.ext, nome__copia_3.ext...
    """
    if not desired_dst.exists():
        return desired_dst, False

    if same_file_quick(src, desired_dst):
        return desired_dst, True

    stem = desired_dst.stem
    suffix = desired_dst.suffix
    parent = desired_dst.parent
    counter = 2

    while True:
        candidate = parent / f"{stem}__copia_{counter}{suffix}"
        if not candidate.exists():
            return candidate, False
        if same_file_quick(src, candidate):
            return candidate, True
        counter += 1


# ---------------------------------------------------------------------------
# Worker de cópia
# ---------------------------------------------------------------------------

class CopyWorker(QObject):
    progress = Signal(int, int)
    log = Signal(str)
    finished = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        source_root: Path,
        destination_root: Path,
        selected_keys: List[str],
        include_adria: bool,
    ):
        super().__init__()
        self.source_root = source_root
        self.destination_root = destination_root
        self.selected_keys = selected_keys
        self.include_adria = include_adria
        self.cancel_requested = False

    def request_cancel(self):
        self.cancel_requested = True

    def _build_jobs(self):
        jobs = []

        for group in GROUPS:
            if group.key not in self.selected_keys:
                continue

            source = self.source_root / group.source_relative
            if not source.exists():
                self.log.emit(f"⚠ Origem não encontrada: {source}")
                continue

            files = list_relevant_files(source, group.exclude_relative_dirs)
            for src in files:
                rel = src.relative_to(source) if source.is_dir() else Path(src.name)
                dst = self.destination_root / group.destination_relative / rel
                jobs.append((src, dst, group.title))

        if self.include_adria:
            for rel_file in ADRIA_FILES:
                src = self.source_root / rel_file
                if src.exists() and is_relevant_file(src):
                    dst = (
                        self.destination_root
                        / "05_Adria_Rocha_Conecta_Saude"
                        / src.name
                    )
                    jobs.append((src, dst, "05 · Ádria Rocha — Conecta Saúde"))
                else:
                    self.log.emit(f"⚠ Arquivo da Ádria não encontrado: {src}")

        return jobs

    def run(self):
        try:
            self.destination_root.mkdir(parents=True, exist_ok=True)

            self.log.emit("🔎 Analisando arquivos selecionados...")
            jobs = self._build_jobs()
            total = len(jobs)

            if total == 0:
                self.finished.emit(
                    {
                        "total": 0,
                        "copied": 0,
                        "skipped": 0,
                        "errors": 0,
                        "cancelled": False,
                    }
                )
                return

            self.log.emit(f"📦 {total} arquivo(s) relevante(s) encontrados.")

            copied = 0
            skipped = 0
            errors = 0

            for index, (src, desired_dst, group_title) in enumerate(jobs, start=1):
                if self.cancel_requested:
                    self.log.emit("⛔ Operação cancelada pelo usuário.")
                    self.finished.emit(
                        {
                            "total": total,
                            "copied": copied,
                            "skipped": skipped,
                            "errors": errors,
                            "cancelled": True,
                        }
                    )
                    return

                try:
                    desired_dst.parent.mkdir(parents=True, exist_ok=True)
                    final_dst, should_skip = collision_safe_destination(
                        src, desired_dst
                    )

                    if should_skip:
                        skipped += 1
                        self.log.emit(f"↷ Já existe: {final_dst}")
                    else:
                        shutil.copy2(src, final_dst)
                        copied += 1
                        self.log.emit(
                            f"✓ [{group_title}] {src.name} → {final_dst}"
                        )
                except Exception as exc:
                    errors += 1
                    self.log.emit(f"✗ Erro ao copiar {src}: {exc}")

                self.progress.emit(index, total)

            self.finished.emit(
                {
                    "total": total,
                    "copied": copied,
                    "skipped": skipped,
                    "errors": errors,
                    "cancelled": False,
                }
            )

        except Exception as exc:
            self.failed.emit(str(exc))


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizador de Fotos ACIRVETES")
        self.resize(1040, 760)

        self.worker = None
        self.thread = None
        self.group_checkboxes = {}

        root = QWidget()
        self.setCentralWidget(root)

        main = QVBoxLayout(root)
        main.setContentsMargins(24, 20, 24, 20)
        main.setSpacing(14)

        title = QLabel("Organizador de Fotos ACIRVETES")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel(
            "Copia os principais acervos da equipe para uma estrutura organizada, "
            "sem alterar os arquivos originais."
        )
        subtitle.setWordWrap(True)

        main.addWidget(title)
        main.addWidget(subtitle)

        # Caminhos
        paths_frame = QFrame()
        paths_frame.setFrameShape(QFrame.StyledPanel)
        paths_layout = QGridLayout(paths_frame)

        paths_layout.addWidget(QLabel("Raiz do Google Drive:"), 0, 0)
        self.source_edit = QLineEdit(str(DEFAULT_SOURCE_ROOT))
        self.source_button = QPushButton("Escolher...")
        self.source_button.clicked.connect(self.choose_source)
        paths_layout.addWidget(self.source_edit, 0, 1)
        paths_layout.addWidget(self.source_button, 0, 2)

        paths_layout.addWidget(QLabel("Pasta final:"), 1, 0)
        self.dest_edit = QLineEdit(str(DEFAULT_DESTINATION))
        self.dest_button = QPushButton("Escolher...")
        self.dest_button.clicked.connect(self.choose_destination)
        paths_layout.addWidget(self.dest_edit, 1, 1)
        paths_layout.addWidget(self.dest_button, 1, 2)

        main.addWidget(paths_frame)

        # Seleção de grupos
        section_label = QLabel("O que será copiado")
        font = section_label.font()
        font.setBold(True)
        section_label.setFont(font)
        main.addWidget(section_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        for group in GROUPS:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card_layout = QVBoxLayout(card)

            checkbox = QCheckBox(group.title)
            checkbox.setChecked(True)
            checkbox_font = checkbox.font()
            checkbox_font.setBold(True)
            checkbox.setFont(checkbox_font)
            self.group_checkboxes[group.key] = checkbox

            desc = QLabel(group.description)
            desc.setWordWrap(True)
            desc.setStyleSheet("color: #666;")

            path_label = QLabel(f"Origem: {group.source_relative}")
            path_label.setWordWrap(True)
            path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            path_label.setStyleSheet("font-size: 11px; color: #777;")

            card_layout.addWidget(checkbox)
            card_layout.addWidget(desc)
            card_layout.addWidget(path_label)
            scroll_layout.addWidget(card)

        self.adria_checkbox = QCheckBox("05 · Ádria Rocha — Conecta Saúde")
        self.adria_checkbox.setChecked(True)
        adria_desc = QLabel(
            "Inclui a capa PNG, o arquivo PSD e o vídeo 'Chamada Ádria' encontrados "
            "na pasta do Conecta Saúde."
        )
        adria_desc.setWordWrap(True)
        adria_desc.setStyleSheet("color: #666;")
        scroll_layout.addWidget(self.adria_checkbox)
        scroll_layout.addWidget(adria_desc)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main.addWidget(scroll, 1)

        # Botões
        buttons = QHBoxLayout()

        self.verify_button = QPushButton("Verificar origens")
        self.verify_button.clicked.connect(self.verify_sources)

        self.start_button = QPushButton("Copiar e organizar")
        self.start_button.clicked.connect(self.start_copy)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_copy)

        buttons.addWidget(self.verify_button)
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.start_button)
        main.addLayout(buttons)

        # Progresso e log
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Aguardando...")
        main.addWidget(self.progress)

        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumBlockCount(5000)
        self.log_box.setPlaceholderText("O log da operação aparecerá aqui.")
        main.addWidget(self.log_box, 1)

        self.statusBar().showMessage("Pronto.")

    def choose_source(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "Selecione a raiz do Google Drive",
            self.source_edit.text(),
        )
        if selected:
            self.source_edit.setText(selected)

    def choose_destination(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta de destino",
            self.dest_edit.text(),
        )
        if selected:
            self.dest_edit.setText(selected)

    def append_log(self, text: str):
        self.log_box.appendPlainText(text)

    def verify_sources(self):
        source_root = Path(self.source_edit.text().strip())
        self.log_box.clear()

        if not source_root.exists():
            QMessageBox.warning(
                self,
                "Drive não encontrado",
                f"A raiz informada não existe:\n{source_root}",
            )
            return

        found = 0
        missing = 0

        self.append_log(f"Raiz verificada: {source_root}")
        self.append_log("")

        for group in GROUPS:
            source = source_root / group.source_relative
            if source.exists():
                count = len(list_relevant_files(source, group.exclude_relative_dirs))
                self.append_log(
                    f"✓ {group.title}: encontrada ({count} arquivo(s) relevante(s))"
                )
                found += 1
            else:
                self.append_log(f"✗ {group.title}: NÃO encontrada")
                self.append_log(f"  {source}")
                missing += 1

        adria_found = 0
        for rel_file in ADRIA_FILES:
            if (source_root / rel_file).exists():
                adria_found += 1

        self.append_log(
            f"✓/⚠ Ádria Rocha: {adria_found}/{len(ADRIA_FILES)} arquivo(s) encontrados"
        )

        self.append_log("")
        self.append_log(f"Resumo: {found} grupo(s) encontrado(s), {missing} ausente(s).")

        self.statusBar().showMessage("Verificação concluída.")

    def start_copy(self):
        source_root = Path(self.source_edit.text().strip())
        destination_root = Path(self.dest_edit.text().strip())

        if not source_root.exists():
            QMessageBox.warning(
                self,
                "Origem inválida",
                f"A raiz do Drive não existe:\n{source_root}",
            )
            return

        if source_root == destination_root:
            QMessageBox.warning(
                self,
                "Destino inválido",
                "A pasta de origem e a pasta de destino não podem ser iguais.",
            )
            return

        selected_keys = [
            key
            for key, checkbox in self.group_checkboxes.items()
            if checkbox.isChecked()
        ]

        if not selected_keys and not self.adria_checkbox.isChecked():
            QMessageBox.information(
                self,
                "Nada selecionado",
                "Selecione pelo menos um grupo para copiar.",
            )
            return

        self.log_box.clear()
        self.progress.setValue(0)
        self.progress.setFormat("Preparando...")

        self.set_busy(True)

        self.thread = QThread()
        self.worker = CopyWorker(
            source_root=source_root,
            destination_root=destination_root,
            selected_keys=selected_keys,
            include_adria=self.adria_checkbox.isChecked(),
        )
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.on_progress)
        self.worker.log.connect(self.append_log)
        self.worker.finished.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)

        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.cleanup_thread)

        self.thread.start()
        self.statusBar().showMessage("Copiando arquivos...")

    def cancel_copy(self):
        if self.worker:
            self.worker.request_cancel()
            self.cancel_button.setEnabled(False)
            self.statusBar().showMessage("Cancelamento solicitado...")

    def on_progress(self, current: int, total: int):
        percent = int((current / total) * 100) if total else 0
        self.progress.setValue(percent)
        self.progress.setFormat(f"{current}/{total} arquivos — {percent}%")

    def on_finished(self, stats: dict):
        self.set_busy(False)

        if stats.get("total", 0) == 0:
            self.progress.setValue(0)
            self.progress.setFormat("Nenhum arquivo encontrado")
            QMessageBox.information(
                self,
                "Nenhum arquivo",
                "Nenhum arquivo relevante foi encontrado nas origens selecionadas.",
            )
            return

        cancelled = stats.get("cancelled", False)
        if not cancelled:
            self.progress.setValue(100)
            self.progress.setFormat("Concluído")

        message = (
            f"Total analisado: {stats['total']}\n"
            f"Copiados: {stats['copied']}\n"
            f"Já existentes/pulados: {stats['skipped']}\n"
            f"Erros: {stats['errors']}"
        )

        if cancelled:
            QMessageBox.information(self, "Operação cancelada", message)
            self.statusBar().showMessage("Operação cancelada.")
        else:
            QMessageBox.information(self, "Organização concluída", message)
            self.statusBar().showMessage("Concluído.")

    def on_failed(self, error: str):
        self.set_busy(False)
        self.progress.setFormat("Erro")
        self.append_log(f"ERRO FATAL: {error}")
        QMessageBox.critical(
            self,
            "Erro",
            f"Ocorreu um erro durante a operação:\n\n{error}",
        )
        self.statusBar().showMessage("Erro.")

    def cleanup_thread(self):
        if self.worker:
            self.worker.deleteLater()
        if self.thread:
            self.thread.deleteLater()
        self.worker = None
        self.thread = None

    def set_busy(self, busy: bool):
        self.source_edit.setEnabled(not busy)
        self.dest_edit.setEnabled(not busy)
        self.source_button.setEnabled(not busy)
        self.dest_button.setEnabled(not busy)
        self.verify_button.setEnabled(not busy)
        self.start_button.setEnabled(not busy)
        self.cancel_button.setEnabled(busy)

        for checkbox in self.group_checkboxes.values():
            checkbox.setEnabled(not busy)
        self.adria_checkbox.setEnabled(not busy)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Organizador de Fotos ACIRVETES")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
