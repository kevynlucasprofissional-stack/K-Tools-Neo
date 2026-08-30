# -*- coding: utf-8 -*-
r"""
Importador de Logomarcas ACIRV — HD Externo
============================================

Objetivo:
- Ler arquivos previamente identificados no HD externo da ACIRV (padrão F:\).
- Copiar somente ativos de marca relevantes para a biblioteca:
  C:\Users\Kevyn Lucas\Downloads\LOGOMARCAS - ACIRV E PROJETOS
- Manter a organização por projeto e por tipo de arquivo.
- Não apagar, mover ou modificar nenhum arquivo de origem.
- Evitar redundâncias usando SHA-256: conteúdo idêntico não é copiado novamente.
- Preservar versões realmente diferentes, mesmo quando têm nomes parecidos.
- Interface gráfica em PySide6 com instalação automática da dependência.

Autoteste:
    python importar_logomarcas_hd_acirv.py --self-test
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional


APP_NAME = "Importador de Logomarcas ACIRV — HD Externo"
DEFAULT_SOURCE_ROOT = Path("F:\\")
DEFAULT_DEST_ROOT = Path(
    r"C:\Users\Kevyn Lucas\Downloads\LOGOMARCAS - ACIRV E PROJETOS"
)

PROJECTS = [
    "00 - ACIRV",
    "01 - ACIRV MULHER",
    "02 - CAM ACIRV",
    "03 - CONECTA ACIRV",
    "04 - CONECTA SAÚDE",
    "05 - CAFÉ ENTRE AMIGOS",
    "06 - EMPREGA ACIRV",
    "07 - ALERVE",
    "08 - SUDOEXPO",
    "09 - CONQUISTA",
    "10 - QUEM INDICA FORTALECE",
    "11 - FÓRUM",
    "12 - EMPREENDELAS",
    "13 - OBSERVATÓRIO RIO VERDE",
    "14 - BARZINHO E VIOLÃO",
    "15 - COMITÊ DE MARKETING",
    "16 - PIRULITO E VIOLÃO",
    "17 - CAFÉ COM O PRESIDENTE",
    "18 - ACIRV NOTÍCIAS",
    "99 - A IDENTIFICAR",
]

SUBFOLDERS = ["PNG", "PDF - VETOR", "EDITÁVEIS"]

RASTER_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"
}
EDITABLE_EXTENSIONS = {
    ".ai", ".psd", ".psb", ".svg", ".eps", ".cdr", ".indd",
    ".otf", ".ttf"
}


@dataclass(frozen=True)
class Asset:
    project: str
    relative_path: str
    note: str = ""


# ---------------------------------------------------------------------------
# ATIVOS IDENTIFICADOS NO HD EXTERNO
#
# Critério de inclusão:
# - logo/logomarca/logotipo em arquivo final;
# - arquivo vetorial/editável útil;
# - versão histórica claramente identificada;
# - variante de cor/fundo ou export em alta qualidade.
#
# Critério de exclusão:
# - proposta de criação de logo;
# - mídia kit;
# - arte/post que apenas contém a marca;
# - logo de patrocinador/expositor/fornecedor;
# - cópia de backup óbvia quando já há uma fonte canônica equivalente.
# ---------------------------------------------------------------------------

HD_ASSETS = [
    # =======================================================================
    # 00 - ACIRV
    # =======================================================================
    Asset(
        "00 - ACIRV",
        r"ACIRV\ACIRV - CARTA\Acirv_Nova_Logo.ai",
        "Arquivo vetorial/editável da marca ACIRV."
    ),
    Asset(
        "00 - ACIRV",
        r"ACIRV\Logo Acirv.jpg",
        "Versão raster encontrada na raiz institucional."
    ),
    Asset(
        "00 - ACIRV",
        r"ACIRV\@Revista-ACIRV\Revista-ACIRV-2025 Folder\Links\Logo ACIRV - Associação.pdf",
        "PDF alternativo da assinatura institucional."
    ),
    Asset(
        "00 - ACIRV",
        r"KEVYN\Identidade Visual\LOGO ACIRV - ALTA - SEM FUNDO - SEM FRASE.png",
        "Export de alta resolução sem fundo e sem frase."
    ),
    Asset(
        "00 - ACIRV",
        r"ACIRV\Selo Acirv + Rio Verde.ai",
        "Selo/co-brand institucional em formato editável."
    ),

    # =======================================================================
    # 01 - ACIRV MULHER
    # =======================================================================
    Asset(
        "01 - ACIRV MULHER",
        r"ACIRV\Logos ACIRV\ACIRV Mulher.pdf",
        "Versão histórica/vetorial da marca."
    ),
    Asset(
        "01 - ACIRV MULHER",
        r"ACIRV\Logos ACIRV\ACIRV Mulher.png",
        "Export raster da versão histórica."
    ),
    Asset(
        "01 - ACIRV MULHER",
        r"ACIRV\Logos ACIRV\LogoACIRV Mulher.pdf",
        "Outra versão PDF encontrada no acervo oficial."
    ),
    Asset(
        "01 - ACIRV MULHER",
        r"KEVYN\Criativos\2026\ACIRV MULHER\230626 - Telão Congresso\Logo ACIRV Mulher.png",
        "Export PNG de uso recente."
    ),

    # =======================================================================
    # 02 - CAM ACIRV
    # =======================================================================
    Asset(
        "02 - CAM ACIRV",
        r"ACIRV\LOGO CAM ACIRV.ai",
        "Arquivo Illustrator da CAM ACIRV."
    ),
    Asset(
        "02 - CAM ACIRV",
        r"ACIRV\Logos ACIRV\CAM-ACIRV Logo.pdf",
        "PDF vetorial da CAM ACIRV."
    ),
    Asset(
        "02 - CAM ACIRV",
        r"BACKUP Notebook VAIO\Downloads\08-09-25 - Nova Logo CAM.pdf",
        "PDF da nova identidade CAM, útil como vetor/arquivo mestre."
    ),
    Asset(
        "02 - CAM ACIRV",
        r"KEVYN\Identidade Visual\CAM ACIRV - BRANCO.png",
        "Variação branca da marca."
    ),
    Asset(
        "02 - CAM ACIRV",
        r"KEVYN\Identidade Visual\Cam - Foto de perfil.png",
        "Versão preparada para avatar/foto de perfil."
    ),

    # =======================================================================
    # 03 - CONECTA ACIRV
    # =======================================================================
    Asset(
        "03 - CONECTA ACIRV",
        r"ACIRV\Logos ACIRV\Conecta-ACIRV.pdf",
        "PDF vetorial do Conecta ACIRV."
    ),
    Asset(
        "03 - CONECTA ACIRV",
        r"KEVYN\Identidade Visual\Logo Conecta.png",
        "Fallback do PNG atual; será ignorado se já existir idêntico."
    ),
    Asset(
        "03 - CONECTA ACIRV",
        r"KEVYN\Identidade Visual\LOGO CONECTA.psd",
        "Fallback do PSD atual; será ignorado se já existir idêntico."
    ),

    # =======================================================================
    # 04 - CONECTA SAÚDE
    # =======================================================================
    Asset(
        "04 - CONECTA SAÚDE",
        r"Backup Samsung\2026 Maio\Outros\Download\LOGO CONECTA SAÚDE.pdf",
        "PDF vetorial encontrado apenas no HD."
    ),
    Asset(
        "04 - CONECTA SAÚDE",
        r"KEVYN\Identidade Visual\LOGO CONECTA SAÚDE - HQ COLOR.png",
        "Fallback do PNG HQ atual."
    ),
    Asset(
        "04 - CONECTA SAÚDE",
        r"KEVYN\Identidade Visual\Logo Conecta Saúde - HQ.png",
        "Fallback do PNG HQ."
    ),
    Asset(
        "04 - CONECTA SAÚDE",
        r"KEVYN\Identidade Visual\Logo Conecta Saúde.png",
        "Fallback do PNG padrão."
    ),
    Asset(
        "04 - CONECTA SAÚDE",
        r"KEVYN\Identidade Visual\LOGO CONECTA SAÚDE.psd",
        "Fallback do PSD atual."
    ),

    # =======================================================================
    # 05 - CAFÉ ENTRE AMIGOS
    # =======================================================================
    Asset(
        "05 - CAFÉ ENTRE AMIGOS",
        r"ACIRV\Logos ACIRV\Cafe-entre-amigos.pdf",
        "PDF vetorial do Café Entre Amigos."
    ),
    Asset(
        "05 - CAFÉ ENTRE AMIGOS",
        r"ACIRV\Logos ACIRV\Cafe-entre-amigos1.pdf",
        "Segunda versão PDF, mantida somente se o conteúdo for diferente."
    ),

    # =======================================================================
    # 06 - EMPREGA ACIRV
    # =======================================================================
    Asset(
        "06 - EMPREGA ACIRV",
        r"ACIRV\Logos ACIRV\Emprega-ACIRV.pdf",
        "PDF vetorial/final do Emprega ACIRV."
    ),

    # =======================================================================
    # 07 - ALERVE
    # =======================================================================
    Asset(
        "07 - ALERVE",
        r"Backup Samsung\2026 Maio\Outros\Download\Logo ALERVE.pdf",
        "Fallback encontrado no HD; hash evita duplicação."
    ),

    # =======================================================================
    # 08 - SUDOEXPO
    # =======================================================================
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\Logo ACIRV e SudoExpo.ai",
        "Lockup ACIRV + SudoExpo em Illustrator."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\Logo ACIRV e SudoExpo.pdf",
        "Lockup ACIRV + SudoExpo em PDF."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Identidade SudoExpo 24.ai",
        "Arquivo mestre da identidade SudoExpo 2024."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Identidade SudoExpo 24.pdf",
        "PDF da identidade SudoExpo 2024."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo Sudoexpo 24 Avatar prov.ai",
        "Arquivo de avatar 2024; mantido como versão histórica."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo Sudoexpo 2022 com data.pdf",
        "Versão histórica 2022 com data."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo Sudoexpo 2022 sem data.pdf",
        "Versão histórica 2022 sem data."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo Sudoexpo 2022.pdf",
        "Outra versão histórica 2022."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo Sudoexpo.pdf",
        "Versão adicional encontrada no acervo SUDOEXPO."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\logo-evento.png",
        "Export raster histórico."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\logo-sudoexpo-3.png",
        "Export raster histórico."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\Logo-Sudoexpo-2022-sem-data.png",
        "Export PNG 2022 sem data."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\LOGOS SUDOEXPO.ai",
        "Arquivo Illustrator com versões da SudoExpo."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"ACIRV\SUDOEXPO\LOGOS SUDOEXPO.pdf",
        "PDF com versões da SudoExpo."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"KEVYN\DADOS ACIRV\Outros\LOGO SUDOEXPO (1).png",
        "Export de alta resolução encontrado no HD."
    ),
    Asset(
        "08 - SUDOEXPO",
        r"KEVYN\DADOS ACIRV\Outros\LOGO SUDOEXPO.psd",
        "PSD da marca SudoExpo encontrado no HD."
    ),

    # =======================================================================
    # 09 - CONQUISTA
    # =======================================================================
    Asset(
        "09 - CONQUISTA",
        r"BACKUP Notebook VAIO\Downloads\LOGOMARCA CONQUISTA VETOR OK-02.png",
        "Variação OK-02, diferente da OK-01 já mapeada anteriormente."
    ),
    Asset(
        "09 - CONQUISTA",
        r"BACKUP Notebook VAIO\Downloads\LOGOMARCA CONQUISTA VETOR sem bandeira desde 1992.pdf",
        "Versão vetorial/PDF sem bandeira."
    ),

    # =======================================================================
    # 10 - QUEM INDICA FORTALECE
    # =======================================================================
    Asset(
        "10 - QUEM INDICA FORTALECE",
        r"KEVYN\Identidade Visual\Reunião de apresentação de Métricas 15.01\Quem indica fortalece\LOGO REVEAL\Quem Indica Fortalece - Acirv.png",
        "Export em resolução superior ao arquivo pequeno já encontrado."
    ),

    # =======================================================================
    # 11 - FÓRUM
    # =======================================================================
    Asset(
        "11 - FÓRUM",
        r"ACIRV\Logos ACIRV\Fórum de RH - Branca.png",
        "Versão branca identificada explicitamente como Fórum de RH."
    ),
    Asset(
        "11 - FÓRUM",
        r"ACIRV\Logos ACIRV\Fórum de RH - Colorida.png",
        "Versão colorida identificada explicitamente como Fórum de RH."
    ),
    Asset(
        "11 - FÓRUM",
        r"KEVYN\Identidade Visual\Logo_Forum\Logo_Forum\Logo_Forum.ai",
        "Fallback do arquivo mestre do Fórum."
    ),
    Asset(
        "11 - FÓRUM",
        r"KEVYN\Identidade Visual\Logo_Forum\Logo_Forum\PNGs\Logo_Preta.png",
        "Variação preta do Fórum."
    ),

    # =======================================================================
    # NOVOS PROJETOS/MARCAS ACIRV ENCONTRADOS NO HD
    # =======================================================================
    Asset(
        "12 - EMPREENDELAS",
        r"ACIRV\LOGO EMPREENDELAS.pdf",
        "Marca de projeto encontrada diretamente na raiz ACIRV."
    ),
    Asset(
        "13 - OBSERVATÓRIO RIO VERDE",
        r"ACIRV\Logo OBSERVATÓRIO RIO VERDE.pdf",
        "Marca de projeto encontrada diretamente na raiz ACIRV."
    ),
    Asset(
        "14 - BARZINHO E VIOLÃO",
        r"ACIRV\Logos ACIRV\Logo Barzinho e Violão.pdf",
        "Marca histórica presente na pasta oficial Logos ACIRV."
    ),
    Asset(
        "15 - COMITÊ DE MARKETING",
        r"ACIRV\Logos ACIRV\Logo Comitê de Mkt - ACIRV - Comitê de Marketing.pdf",
        "Marca histórica presente na pasta oficial Logos ACIRV."
    ),
    Asset(
        "16 - PIRULITO E VIOLÃO",
        r"ACIRV\Logos ACIRV\Logo Pirulito e Violão.pdf",
        "Marca histórica presente na pasta oficial Logos ACIRV."
    ),
    Asset(
        "17 - CAFÉ COM O PRESIDENTE",
        r"KEVYN\Identidade Visual\CAFÉ COM O PRESIDENTE\LOGO CAFÉ COM O PRESIDENTE.png",
        "Logo principal do projeto/série."
    ),
    Asset(
        "17 - CAFÉ COM O PRESIDENTE",
        r"KEVYN\Identidade Visual\CAFÉ COM O PRESIDENTE\LOGO CAFÉ COM O PRESIDENTE - fundo verde.png",
        "Variação para fundo verde."
    ),
    Asset(
        "18 - ACIRV NOTÍCIAS",
        r"KEVYN\Identidade Visual\ACIRV NOTÍCIAS.png",
        "Export PNG da identidade ACIRV Notícias."
    ),
    Asset(
        "18 - ACIRV NOTÍCIAS",
        r"KEVYN\Identidade Visual\ACIRV NOTÍCIAS.psd",
        "Arquivo editável da identidade ACIRV Notícias."
    ),
]



def resolve_source_path(source_root: Path, relative_path: str) -> Path:
    """Resolve caminhos Windows mapeados mesmo durante testes em outros SOs."""
    parts = [part for part in relative_path.replace("/", "\\").split("\\") if part]
    return source_root.joinpath(*parts)

def type_folder(path: Path) -> str:
    """Retorna a subpasta de destino mantendo a estrutura existente."""
    ext = path.suffix.lower()
    if ext == ".pdf":
        return "PDF - VETOR"
    if ext in RASTER_EXTENSIONS:
        return "PNG"
    if ext in EDITABLE_EXTENSIONS:
        return "EDITÁVEIS"
    # Arquivos sem extensão ou formatos de design não previstos:
    return "EDITÁVEIS"


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Calcula SHA-256 sem carregar o arquivo inteiro na memória."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def iter_destination_files(dest_root: Path, project: Optional[str] = None) -> Iterable[Path]:
    root = dest_root / project if project else dest_root
    if not root.exists():
        return []
    return (p for p in root.rglob("*") if p.is_file())


def build_hash_index(dest_root: Path) -> dict[str, Path]:
    """
    Índice global dos arquivos já existentes na biblioteca.

    O hash global impede que o MESMO arquivo físico seja importado repetidamente
    a partir de backups diferentes. Se um mesmo conteúdo já está na biblioteca,
    ele é considerado redundante.
    """
    index: dict[str, Path] = {}
    if not dest_root.exists():
        return index

    for path in dest_root.rglob("*"):
        if not path.is_file():
            continue
        try:
            index.setdefault(sha256_file(path), path)
        except OSError:
            # Um arquivo inacessível não deve impedir o restante da importação.
            continue
    return index


def unique_name(target: Path) -> Path:
    """Gera um nome alternativo somente quando o mesmo nome tem outro conteúdo."""
    if not target.exists():
        return target

    stem = target.stem
    suffix = target.suffix
    number = 2
    while True:
        candidate = target.with_name(f"{stem} ({number}){suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def ensure_structure(dest_root: Path) -> None:
    dest_root.mkdir(parents=True, exist_ok=True)
    for project in PROJECTS:
        for subfolder in SUBFOLDERS:
            (dest_root / project / subfolder).mkdir(parents=True, exist_ok=True)


@dataclass
class OperationResult:
    copied: int = 0
    skipped_duplicate: int = 0
    missing: int = 0
    errors: int = 0
    total: int = 0


def verify_assets(source_root: Path) -> tuple[int, int, list[Asset]]:
    found = 0
    missing_assets: list[Asset] = []
    for asset in HD_ASSETS:
        source = resolve_source_path(source_root, asset.relative_path)
        if source.is_file():
            found += 1
        else:
            missing_assets.append(asset)
    return found, len(missing_assets), missing_assets


def import_assets(
    source_root: Path,
    dest_root: Path,
    log: Callable[[str], None] = print,
    progress: Optional[Callable[[int, int], None]] = None,
    dry_run: bool = False,
) -> OperationResult:
    """Importa os ativos do HD com deduplicação global por SHA-256."""
    result = OperationResult(total=len(HD_ASSETS))

    if not dry_run:
        ensure_structure(dest_root)

    log("Indexando arquivos já existentes para evitar redundâncias...")
    hash_index = build_hash_index(dest_root) if dest_root.exists() else {}

    for position, asset in enumerate(HD_ASSETS, start=1):
        if progress:
            progress(position, len(HD_ASSETS))

        source = resolve_source_path(source_root, asset.relative_path)
        if not source.is_file():
            result.missing += 1
            log(f"⚠ NÃO ENCONTRADO | {source}")
            continue

        try:
            source_hash = sha256_file(source)

            if source_hash in hash_index:
                result.skipped_duplicate += 1
                existing = hash_index[source_hash]
                log(
                    f"↷ REDUNDANTE — ignorado | {source.name} "
                    f"| já existe em: {existing}"
                )
                continue

            target_dir = dest_root / asset.project / type_folder(source)
            target = unique_name(target_dir / source.name)

            if dry_run:
                result.copied += 1
                hash_index[source_hash] = target
                log(f"✓ SIMULAÇÃO | {source} -> {target}")
                continue

            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

            # Validação pós-cópia.
            copied_hash = sha256_file(target)
            if copied_hash != source_hash:
                try:
                    target.unlink(missing_ok=True)
                finally:
                    raise IOError("Falha de integridade: SHA-256 da cópia não confere.")

            hash_index[source_hash] = target
            result.copied += 1
            log(f"✓ COPIADO | {source.name} -> {asset.project}\\{type_folder(source)}")
            if asset.note:
                log(f"  └ {asset.note}")

        except Exception as exc:
            result.errors += 1
            log(f"✗ ERRO | {source} | {exc}")

    return result


# =============================================================================
# AUTOTESTES
# =============================================================================

def self_test() -> int:
    print(f"Executando autotestes — {APP_NAME}")

    assert type_folder(Path("x.png")) == "PNG"
    assert type_folder(Path("x.jpg")) == "PNG"
    assert type_folder(Path("x.pdf")) == "PDF - VETOR"
    assert type_folder(Path("x.ai")) == "EDITÁVEIS"
    assert type_folder(Path("x.psd")) == "EDITÁVEIS"
    assert len({a.relative_path for a in HD_ASSETS}) == len(HD_ASSETS), \
        "Há caminhos duplicados no mapeamento."

    projects_set = set(PROJECTS)
    assert all(a.project in projects_set for a in HD_ASSETS), \
        "Existe ativo apontando para projeto inexistente."

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source_root = root / "source"
        dest_root = root / "dest"

        # Usa dois ativos sintéticos para testar cópia e deduplicação.
        synthetic_assets = [
            Asset("00 - ACIRV", r"A\logo.png"),
            Asset("00 - ACIRV", r"B\logo-copia.png"),
        ]

        original_assets = list(HD_ASSETS)
        try:
            globals()["HD_ASSETS"] = synthetic_assets

            (source_root / "A").mkdir(parents=True)
            (source_root / "B").mkdir(parents=True)
            payload = b"conteudo-identico-para-testar-deduplicacao"
            (source_root / "A" / "logo.png").write_bytes(payload)
            (source_root / "B" / "logo-copia.png").write_bytes(payload)

            logs: list[str] = []
            result = import_assets(
                source_root,
                dest_root,
                log=logs.append,
                dry_run=False,
            )

            assert result.copied == 1, result
            assert result.skipped_duplicate == 1, result
            assert result.missing == 0, result
            assert result.errors == 0, result

            copied_files = [
                p for p in dest_root.rglob("*")
                if p.is_file()
            ]
            assert len(copied_files) == 1, copied_files
            assert copied_files[0].read_bytes() == payload

            # Segunda execução: nada deve ser duplicado.
            result2 = import_assets(
                source_root,
                dest_root,
                log=lambda _: None,
                dry_run=False,
            )
            assert result2.copied == 0, result2
            assert result2.skipped_duplicate == 2, result2

        finally:
            globals()["HD_ASSETS"] = original_assets

    print("AUTOTESTES: OK")
    print(f"Ativos HD mapeados: {len(HD_ASSETS)}")
    print(f"Projetos/pastas: {len(PROJECTS)}")
    return 0


# =============================================================================
# INSTALAÇÃO AUTOMÁTICA DO PYSIDE6
# =============================================================================

def install_pyside6() -> bool:
    try:
        import PySide6  # noqa: F401
        return True
    except ImportError:
        pass

    print("PySide6 não encontrado. Tentando instalar automaticamente...")

    # Garante pip quando possível.
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        try:
            subprocess.run(
                [sys.executable, "-m", "ensurepip", "--upgrade"],
                check=True,
            )
        except Exception:
            pass

    commands = [
        [sys.executable, "-m", "pip", "install", "PySide6"],
        [sys.executable, "-m", "pip", "install", "--user", "PySide6"],
    ]

    for command in commands:
        try:
            subprocess.run(command, check=True)
            import PySide6  # noqa: F401
            return True
        except Exception:
            continue

    return False


def show_bootstrap_error() -> None:
    message = (
        "Não foi possível instalar o PySide6 automaticamente.\n\n"
        "Verifique sua conexão com a internet e execute:\n"
        "python -m pip install PySide6"
    )
    print(message)

    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
        except Exception:
            pass


# =============================================================================
# GUI
# =============================================================================

def run_gui() -> int:
    if not install_pyside6():
        show_bootstrap_error()
        return 1

    from PySide6.QtCore import QObject, QThread, Signal, Qt
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QPlainTextEdit,
        QScrollArea,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )

    class ImportWorker(QObject):
        progress = Signal(int)
        log_line = Signal(str)
        finished = Signal(object)

        def __init__(self, source_root: Path, dest_root: Path):
            super().__init__()
            self.source_root = source_root
            self.dest_root = dest_root

        def run(self):
            try:
                result = import_assets(
                    self.source_root,
                    self.dest_root,
                    log=self.log_line.emit,
                    progress=lambda current, total: self.progress.emit(
                        int(current * 100 / max(total, 1))
                    ),
                )
            except Exception as exc:
                result = OperationResult(errors=1, total=len(HD_ASSETS))
                self.log_line.emit(f"✗ ERRO GERAL | {exc}")
            self.finished.emit(result)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.thread: Optional[QThread] = None
            self.worker: Optional[ImportWorker] = None

            self.setWindowTitle(APP_NAME)
            self.resize(1050, 760)
            self.setMinimumSize(850, 650)

            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setContentsMargins(28, 24, 28, 24)
            layout.setSpacing(16)

            title = QLabel("Logomarcas ACIRV · HD Externo")
            title_font = QFont()
            title_font.setPointSize(22)
            title_font.setBold(True)
            title.setFont(title_font)

            subtitle = QLabel(
                "Importa apenas ativos de marca selecionados do HD, "
                "preserva versões diferentes e elimina cópias idênticas por SHA-256."
            )
            subtitle.setWordWrap(True)
            subtitle.setStyleSheet("color: #777; font-size: 13px;")

            layout.addWidget(title)
            layout.addWidget(subtitle)

            info = QLabel(
                f"{len(HD_ASSETS)} ativos mapeados · "
                f"{len(PROJECTS) - 1} categorias de marca/projeto · "
                "nenhum arquivo de origem será movido ou apagado"
            )
            info.setStyleSheet(
                "padding: 10px 12px; border-radius: 8px; "
                "background: rgba(127,127,127,0.10);"
            )
            layout.addWidget(info)

            source_frame = self.path_row(
                "HD externo",
                str(DEFAULT_SOURCE_ROOT),
                self.choose_source,
            )
            self.source_edit = source_frame[0]
            layout.addWidget(source_frame[1])

            dest_frame = self.path_row(
                "Biblioteca final",
                str(DEFAULT_DEST_ROOT),
                self.choose_dest,
            )
            self.dest_edit = dest_frame[0]
            layout.addWidget(dest_frame[1])

            buttons = QHBoxLayout()
            self.verify_button = QPushButton("Verificar arquivos")
            self.verify_button.clicked.connect(self.verify)
            self.copy_button = QPushButton("Importar sem redundâncias")
            self.copy_button.clicked.connect(self.start_import)
            self.open_button = QPushButton("Abrir pasta final")
            self.open_button.clicked.connect(self.open_dest)

            for button in (self.verify_button, self.copy_button, self.open_button):
                button.setMinimumHeight(42)

            buttons.addWidget(self.verify_button)
            buttons.addWidget(self.copy_button)
            buttons.addWidget(self.open_button)
            layout.addLayout(buttons)

            self.status = QLabel("Pronto para verificar o HD.")
            self.status.setWordWrap(True)
            layout.addWidget(self.status)

            self.progress = QProgressBar()
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setTextVisible(True)
            layout.addWidget(self.progress)

            log_title = QLabel("Relatório")
            log_title.setStyleSheet("font-weight: 600;")
            layout.addWidget(log_title)

            self.log = QPlainTextEdit()
            self.log.setReadOnly(True)
            self.log.setPlaceholderText(
                "Aqui serão exibidos os arquivos encontrados, copiados, "
                "redundantes, ausentes e eventuais erros."
            )
            layout.addWidget(self.log, 1)

        def path_row(self, label_text, default_value, callback):
            frame = QFrame()
            row = QHBoxLayout(frame)
            row.setContentsMargins(0, 0, 0, 0)

            label = QLabel(label_text)
            label.setMinimumWidth(110)

            edit = QLineEdit(default_value)
            edit.setMinimumHeight(38)

            browse = QPushButton("Selecionar…")
            browse.setMinimumHeight(38)
            browse.clicked.connect(callback)

            row.addWidget(label)
            row.addWidget(edit, 1)
            row.addWidget(browse)
            return edit, frame

        def choose_source(self):
            directory = QFileDialog.getExistingDirectory(
                self,
                "Selecione a raiz do HD externo",
                self.source_edit.text() or str(DEFAULT_SOURCE_ROOT),
            )
            if directory:
                self.source_edit.setText(directory)

        def choose_dest(self):
            directory = QFileDialog.getExistingDirectory(
                self,
                "Selecione a biblioteca final",
                self.dest_edit.text() or str(DEFAULT_DEST_ROOT.parent),
            )
            if directory:
                self.dest_edit.setText(directory)

        def verify(self):
            source = Path(self.source_edit.text().strip())
            self.log.clear()

            if not source.exists():
                self.status.setText(
                    f"HD não encontrado em: {source}. "
                    "Selecione a letra/pasta correta do HD externo."
                )
                self.log.appendPlainText(f"✗ Origem inexistente: {source}")
                return

            found, missing, missing_assets = verify_assets(source)
            self.status.setText(
                f"Verificação concluída: {found} encontrados · "
                f"{missing} ausentes · {len(HD_ASSETS)} mapeados."
            )
            self.log.appendPlainText(
                f"✓ Encontrados: {found}\n"
                f"⚠ Ausentes: {missing}\n"
                f"Total mapeado: {len(HD_ASSETS)}\n"
            )

            if missing_assets:
                self.log.appendPlainText("ARQUIVOS AUSENTES:")
                for asset in missing_assets:
                    self.log.appendPlainText(
                        f"• [{asset.project}] {asset.relative_path}"
                    )

        def start_import(self):
            source = Path(self.source_edit.text().strip())
            dest = Path(self.dest_edit.text().strip())

            if not source.exists():
                QMessageBox.warning(
                    self,
                    "HD não encontrado",
                    f"A pasta de origem não existe:\n{source}",
                )
                return

            self.set_busy(True)
            self.progress.setValue(0)
            self.log.clear()
            self.status.setText("Indexando e importando ativos...")

            self.thread = QThread(self)
            self.worker = ImportWorker(source, dest)
            self.worker.moveToThread(self.thread)

            self.thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.progress.setValue)
            self.worker.log_line.connect(self.log.appendPlainText)
            self.worker.finished.connect(self.import_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        def import_finished(self, result: OperationResult):
            self.set_busy(False)
            self.progress.setValue(100)

            summary = (
                f"Concluído: {result.copied} copiados · "
                f"{result.skipped_duplicate} redundantes ignorados · "
                f"{result.missing} ausentes · "
                f"{result.errors} erros."
            )
            self.status.setText(summary)
            self.log.appendPlainText("\n" + "=" * 70)
            self.log.appendPlainText(summary)

            if result.errors:
                QMessageBox.warning(self, "Importação concluída com erros", summary)
            else:
                QMessageBox.information(self, "Importação concluída", summary)

        def set_busy(self, busy: bool):
            self.verify_button.setEnabled(not busy)
            self.copy_button.setEnabled(not busy)
            self.open_button.setEnabled(not busy)
            self.source_edit.setEnabled(not busy)
            self.dest_edit.setEnabled(not busy)

        def open_dest(self):
            dest = Path(self.dest_edit.text().strip())
            dest.mkdir(parents=True, exist_ok=True)

            try:
                if os.name == "nt":
                    os.startfile(dest)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(dest)])
                else:
                    subprocess.Popen(["xdg-open", str(dest)])
            except Exception as exc:
                QMessageBox.warning(
                    self,
                    "Não foi possível abrir a pasta",
                    str(exc),
                )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    return app.exec()


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
