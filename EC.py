# ============================================================
# EXTRATOR COMPLETO DE ESTRUTURA DE PASTAS
# ============================================================
# O que este script faz:
# - Permite escolher a pasta raiz por interface gráfica
# - Permite escolher a pasta de saída por interface gráfica
# - Percorre pastas e subpastas
# - Lista pastas e arquivos
# - Inclui extensão dos arquivos
# - Conta quantos arquivos existem em cada pasta
# - Gera relatórios em TXT, JSON, CSV e XLSX
# - NÃO copia nenhum arquivo
# - Pula pastas sem permissão de acesso
# - Gera log de erros de acesso
# python EC.py
# Compatível com Windows, Linux e macOS
# ============================================================

# ============================================================
# ZONA DE CONFIGURAÇÃO
# ============================================================

CONFIG = {
    # Se True, abre janela para escolher a pasta raiz
    "USE_GUI_TO_SELECT_ROOT_FOLDER": True,

    # Caminho da pasta raiz, caso não use interface
    "ROOT_FOLDER": r"D:\ARQUIVOS\CLIENTES E OUTROS\ACIRV",

    # Se True, abre janela para escolher a pasta de saída
    "USE_GUI_TO_SELECT_OUTPUT_FOLDER": True,

    # Caminho da pasta de saída, caso não use interface
    "OUTPUT_FOLDER": r"C:\Users\Kevyn Lucas\Documents\Códigos Python\Saidas",

    # Nome base dos arquivos gerados
    "OUTPUT_BASENAME": "estrutura_pastas",

    # Formatos de saída:
    # opções: "txt", "json", "csv", "xlsx"
    "OUTPUT_FORMATS": ["txt", "json", "csv", "xlsx"],

    # Se True, gera TXT com árvore visual
    "GENERATE_TREE_TXT": True,

    # Se True, gera arquivo TXT com resumo
    "GENERATE_SUMMARY_FILE": True,

    # Se True, gera log de erros
    "GENERATE_ERROR_LOG": True,

    # Se True, inclui arquivos
    "INCLUDE_FILES": True,

    # Se True, inclui diretórios
    "INCLUDE_DIRECTORIES": True,

    # Se True, inclui arquivos ocultos
    "INCLUDE_HIDDEN_FILES": False,

    # Se True, inclui pastas ocultas
    "INCLUDE_HIDDEN_DIRECTORIES": False,

    # Se True, pula pastas/itens inacessíveis
    "SKIP_INACCESSIBLE_FOLDERS": True,

    # Profundidade máxima:
    # None = sem limite
    # 0 = somente pasta raiz
    # 1 = raiz + 1 nível
    "MAX_DEPTH": None,

    # Ordenação ignorando maiúsculas/minúsculas
    "CASE_INSENSITIVE_SORT": True,

    # Pastas ignoradas pelo nome
    "EXCLUDED_DIRECTORY_NAMES": {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv"
    },

    # Extensões de arquivo a ignorar
    # Ex.: {".tmp", ".log"}
    "EXCLUDED_FILE_EXTENSIONS": set(),

    # Arquivos ignorados pelo nome exato
    "EXCLUDED_FILE_NAMES": set(),

    # Rótulo para arquivo sem extensão
    "LABEL_NO_EXTENSION": "[sem extensão]",

    # Auto-instalar bibliotecas opcionais
    "AUTO_INSTALL_OPTIONAL_LIBS": True,
}

# ============================================================
# IMPORTS
# ============================================================

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None


# ============================================================
# INSTALAÇÃO DE PACOTES OPCIONAIS
# ============================================================

def install_package(package_name: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])


def ensure_optional_dependencies(output_formats: List[str], auto_install: bool) -> None:
    """
    Garante dependências opcionais.
    Hoje, XLSX precisa de pandas + openpyxl.
    """
    if "xlsx" in output_formats:
        try:
            import pandas  # noqa: F401
            import openpyxl  # noqa: F401
        except ImportError:
            if not auto_install:
                raise RuntimeError(
                    "Para gerar XLSX, instale manualmente: pandas openpyxl"
                )
            print("Instalando dependências opcionais para XLSX...")
            install_package("pandas")
            install_package("openpyxl")


# ============================================================
# INTERFACE DE ESCOLHA DE PASTA
# ============================================================

def choose_directory_gui(title: str) -> Optional[Path]:
    if tk is None or filedialog is None:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(title=title)
    root.destroy()

    if not selected:
        return None

    return Path(selected).expanduser().resolve()


def resolve_paths_from_config(config: Dict[str, Any]) -> Tuple[Path, Path]:
    # Pasta raiz
    if config["USE_GUI_TO_SELECT_ROOT_FOLDER"]:
        selected_root = choose_directory_gui("Escolha a pasta raiz para analisar")
        if selected_root is None:
            raise RuntimeError("Nenhuma pasta raiz foi selecionada.")
        root_folder = selected_root
    else:
        root_folder = Path(config["ROOT_FOLDER"]).expanduser().resolve()

    # Pasta de saída
    if config["USE_GUI_TO_SELECT_OUTPUT_FOLDER"]:
        selected_output = choose_directory_gui("Escolha a pasta onde salvar os resultados")
        if selected_output is None:
            raise RuntimeError("Nenhuma pasta de saída foi selecionada.")
        output_folder = selected_output
    else:
        output_folder = Path(config["OUTPUT_FOLDER"]).expanduser().resolve()

    return root_folder, output_folder


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def is_hidden(path: Path) -> bool:
    return path.name.startswith(".")


def get_extension_label(path: Path, label_no_extension: str) -> str:
    ext = path.suffix.lower().strip()
    return ext if ext else label_no_extension


def sort_paths(paths: List[Path], case_insensitive: bool) -> List[Path]:
    if case_insensitive:
        return sorted(paths, key=lambda p: p.name.lower())
    return sorted(paths, key=lambda p: p.name)


def should_include_directory(path: Path, config: Dict[str, Any]) -> bool:
    if path.name in config["EXCLUDED_DIRECTORY_NAMES"]:
        return False
    if is_hidden(path) and not config["INCLUDE_HIDDEN_DIRECTORIES"]:
        return False
    return True


def should_include_file(path: Path, config: Dict[str, Any]) -> bool:
    if path.name in config["EXCLUDED_FILE_NAMES"]:
        return False
    if path.suffix.lower() in config["EXCLUDED_FILE_EXTENSIONS"]:
        return False
    if is_hidden(path) and not config["INCLUDE_HIDDEN_FILES"]:
        return False
    return True


def safe_iterdir(directory: Path, config: Dict[str, Any], error_log: List[Dict[str, str]]) -> List[Path]:
    """
    Tenta listar o conteúdo da pasta.
    Se houver erro de acesso, registra no log e retorna lista vazia.
    """
    try:
        return list(directory.iterdir())
    except PermissionError as e:
        error_log.append({
            "path": str(directory),
            "error_type": "PermissionError",
            "message": str(e),
        })
        if config.get("SKIP_INACCESSIBLE_FOLDERS", True):
            return []
        raise
    except OSError as e:
        error_log.append({
            "path": str(directory),
            "error_type": type(e).__name__,
            "message": str(e),
        })
        if config.get("SKIP_INACCESSIBLE_FOLDERS", True):
            return []
        raise


def safe_is_dir(path: Path, error_log: List[Dict[str, str]]) -> bool:
    try:
        return path.is_dir()
    except OSError as e:
        error_log.append({
            "path": str(path),
            "error_type": type(e).__name__,
            "message": str(e),
        })
        return False


def safe_is_file(path: Path, error_log: List[Dict[str, str]]) -> bool:
    try:
        return path.is_file()
    except OSError as e:
        error_log.append({
            "path": str(path),
            "error_type": type(e).__name__,
            "message": str(e),
        })
        return False


# ============================================================
# LEITURA DA ESTRUTURA
# ============================================================

def scan_structure(
    root: Path,
    config: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any], List[Dict[str, str]]]:
    """
    Retorna:
    - items: lista completa de diretórios e arquivos
    - folder_stats: estatísticas por pasta
    - summary: resumo geral
    - error_log: lista de erros de acesso
    """
    if not root.exists():
        raise FileNotFoundError(f"A pasta raiz não existe: {root}")

    if not root.is_dir():
        raise NotADirectoryError(f"O caminho não é uma pasta: {root}")

    items: List[Dict[str, Any]] = []
    folder_stats: List[Dict[str, Any]] = []
    error_log: List[Dict[str, str]] = []
    max_depth: Optional[int] = config["MAX_DEPTH"]

    total_directories = 0
    total_files = 0

    def walk_directory(current_dir: Path, depth: int) -> int:
        nonlocal total_directories, total_files

        relative_dir = current_dir.relative_to(root)
        relative_dir_str = "." if str(relative_dir) == "." else str(relative_dir)

        children = safe_iterdir(current_dir, config, error_log)

        directories: List[Path] = []
        files: List[Path] = []

        for child in children:
            if safe_is_dir(child, error_log):
                if should_include_directory(child, config):
                    directories.append(child)
            elif safe_is_file(child, error_log):
                if should_include_file(child, config):
                    files.append(child)

        directories = sort_paths(directories, config["CASE_INSENSITIVE_SORT"])
        files = sort_paths(files, config["CASE_INSENSITIVE_SORT"])

        direct_file_count = len(files)
        recursive_file_count = direct_file_count

        if config["INCLUDE_DIRECTORIES"]:
            items.append({
                "type": "directory",
                "name": current_dir.name if current_dir != root else root.name,
                "extension": "",
                "relative_path": relative_dir_str,
                "parent_relative_path": str(relative_dir.parent) if str(relative_dir) != "." else "",
                "depth": depth,
            })
            total_directories += 1

        if config["INCLUDE_FILES"]:
            for file_path in files:
                rel_path = file_path.relative_to(root)
                items.append({
                    "type": "file",
                    "name": file_path.name,
                    "extension": get_extension_label(file_path, config["LABEL_NO_EXTENSION"]),
                    "relative_path": str(rel_path),
                    "parent_relative_path": str(rel_path.parent),
                    "depth": depth + 1,
                })
                total_files += 1

        if max_depth is None or depth < max_depth:
            for dir_path in directories:
                recursive_file_count += walk_directory(dir_path, depth + 1)

        folder_stats.append({
            "folder_name": current_dir.name if current_dir != root else root.name,
            "relative_path": relative_dir_str,
            "depth": depth,
            "direct_file_count": direct_file_count,
            "total_file_count_recursive": recursive_file_count,
            "direct_subfolder_count": len(directories),
        })

        return recursive_file_count

    total_recursive_files = walk_directory(root, depth=0)

    summary = {
        "root_folder": str(root),
        "total_directories": total_directories,
        "total_files": total_files,
        "total_recursive_files_from_root": total_recursive_files,
        "total_access_errors": len(error_log),
    }

    folder_stats = sorted(folder_stats, key=lambda x: x["relative_path"].lower())
    return items, folder_stats, summary, error_log


# ============================================================
# GERAÇÃO DA ÁRVORE EM TEXTO
# ============================================================

def build_tree_text(
    root: Path,
    config: Dict[str, Any],
    folder_stats_map: Dict[str, Dict[str, Any]],
    error_log: List[Dict[str, str]]
) -> str:
    max_depth: Optional[int] = config["MAX_DEPTH"]
    root_stat = folder_stats_map.get(".", {})
    root_total = root_stat.get("total_file_count_recursive", 0)

    inaccessible_paths = sorted({entry["path"] for entry in error_log})

    lines: List[str] = [f"{root.name}/  [arquivos totais: {root_total}]"]

    def walk(current_dir: Path, prefix: str = "", depth: int = 0) -> None:
        if max_depth is not None and depth >= max_depth:
            return

        children = safe_iterdir(current_dir, config, error_log)

        directories: List[Path] = []
        files: List[Path] = []

        for child in children:
            if safe_is_dir(child, error_log):
                if should_include_directory(child, config):
                    directories.append(child)
            elif safe_is_file(child, error_log):
                if should_include_file(child, config):
                    files.append(child)

        directories = sort_paths(directories, config["CASE_INSENSITIVE_SORT"])
        files = sort_paths(files, config["CASE_INSENSITIVE_SORT"])

        entries: List[Path] = []
        if config["INCLUDE_DIRECTORIES"]:
            entries.extend(directories)
        if config["INCLUDE_FILES"]:
            entries.extend(files)

        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                rel = entry.relative_to(root)
                rel_str = str(rel)
                stat = folder_stats_map.get(rel_str, {})
                direct_count = stat.get("direct_file_count", 0)
                total_count = stat.get("total_file_count_recursive", 0)
                lines.append(
                    f"{prefix}{connector}{entry.name}/  [diretos: {direct_count} | totais: {total_count}]"
                )
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension, depth + 1)
            else:
                ext_label = get_extension_label(entry, config["LABEL_NO_EXTENSION"])
                lines.append(f"{prefix}{connector}{entry.name}  ({ext_label})")

    walk(root)

    if inaccessible_paths:
        lines.append("")
        lines.append("")
        lines.append("PASTAS/ITENS COM ERRO DE ACESSO")
        lines.append("================================")
        for path in inaccessible_paths:
            lines.append(path)

    return "\n".join(lines)


# ============================================================
# EXPORTAÇÕES
# ============================================================

def export_txt(output_path: Path, text: str) -> None:
    output_path.write_text(text, encoding="utf-8")


def export_json(output_path: Path, data: Any) -> None:
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def export_csv(output_path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    headers = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def export_xlsx(
    output_path: Path,
    items: List[Dict[str, Any]],
    folder_stats: List[Dict[str, Any]],
    summary: Dict[str, Any],
    error_log: List[Dict[str, str]]
) -> None:
    import pandas as pd

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        pd.DataFrame(items).to_excel(writer, sheet_name="estrutura", index=False)
        pd.DataFrame(folder_stats).to_excel(writer, sheet_name="estatisticas_pastas", index=False)
        pd.DataFrame([summary]).to_excel(writer, sheet_name="resumo", index=False)

        if error_log:
            pd.DataFrame(error_log).to_excel(writer, sheet_name="erros_acesso", index=False)


# ============================================================
# RESUMO
# ============================================================

def build_summary_text(summary: Dict[str, Any]) -> str:
    return (
        "RESUMO GERAL\n"
        "========================\n"
        f"Pasta raiz analisada: {summary['root_folder']}\n"
        f"Total de diretórios: {summary['total_directories']}\n"
        f"Total de arquivos: {summary['total_files']}\n"
        f"Total de arquivos a partir da raiz: {summary['total_recursive_files_from_root']}\n"
        f"Total de erros de acesso: {summary['total_access_errors']}\n"
    )


# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

def main() -> None:
    config = CONFIG.copy()
    output_formats = [fmt.lower().strip() for fmt in config["OUTPUT_FORMATS"]]

    ensure_optional_dependencies(
        output_formats=output_formats,
        auto_install=config["AUTO_INSTALL_OPTIONAL_LIBS"]
    )

    root_folder, output_folder = resolve_paths_from_config(config)
    output_folder.mkdir(parents=True, exist_ok=True)

    print(f"Analisando: {root_folder}")

    items, folder_stats, summary, error_log = scan_structure(root_folder, config)

    folder_stats_map = {row["relative_path"]: row for row in folder_stats}
    tree_text = build_tree_text(root_folder, config, folder_stats_map, error_log)
    summary_text = build_summary_text(summary)

    base = config["OUTPUT_BASENAME"]

    # TXT da árvore
    if "txt" in output_formats and config["GENERATE_TREE_TXT"]:
        txt_path = output_folder / f"{base}_arvore.txt"
        export_txt(txt_path, tree_text)
        print(f"[OK] TXT da árvore salvo em: {txt_path}")

    # TXT do resumo
    if config["GENERATE_SUMMARY_FILE"]:
        summary_txt_path = output_folder / f"{base}_resumo.txt"
        export_txt(summary_txt_path, summary_text)
        print(f"[OK] Resumo salvo em: {summary_txt_path}")

    # JSON principal
    if "json" in output_formats:
        json_path = output_folder / f"{base}.json"
        export_json(json_path, {
            "summary": summary,
            "folder_stats": folder_stats,
            "items": items,
            "error_log": error_log,
        })
        print(f"[OK] JSON salvo em: {json_path}")

    # JSON apenas de erros
    if config.get("GENERATE_ERROR_LOG", True) and error_log:
        error_log_path = output_folder / f"{base}_erros_acesso.json"
        export_json(error_log_path, error_log)
        print(f"[OK] Log de erros salvo em: {error_log_path}")

    # CSV
    if "csv" in output_formats:
        csv_items_path = output_folder / f"{base}_estrutura.csv"
        export_csv(csv_items_path, items)
        print(f"[OK] CSV da estrutura salvo em: {csv_items_path}")

        csv_stats_path = output_folder / f"{base}_estatisticas_pastas.csv"
        export_csv(csv_stats_path, folder_stats)
        print(f"[OK] CSV das estatísticas salvo em: {csv_stats_path}")

        if error_log:
            csv_errors_path = output_folder / f"{base}_erros_acesso.csv"
            export_csv(csv_errors_path, error_log)
            print(f"[OK] CSV dos erros salvo em: {csv_errors_path}")

    # XLSX
    if "xlsx" in output_formats:
        xlsx_path = output_folder / f"{base}.xlsx"
        export_xlsx(xlsx_path, items, folder_stats, summary, error_log)
        print(f"[OK] XLSX salvo em: {xlsx_path}")

    print("\nConcluído com sucesso.")
    print("Nenhum arquivo foi copiado. Apenas a estrutura foi lida e exportada.")

    if error_log:
        print(f"Foram encontrados {len(error_log)} erro(s) de acesso, mas a varredura continuou normalmente.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERRO] {e}")
        sys.exit(1)