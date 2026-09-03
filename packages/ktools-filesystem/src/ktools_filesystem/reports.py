from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4


def _build_ascii_tree(dir_path: Path, prefix: str = "", include_hidden: bool = False) -> list[str]:
    lines: list[str] = []
    try:
        entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except (PermissionError, OSError):
        return [f"{prefix}[Acesso negado]"]

    if not include_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]

    total = len(entries)
    for index, entry in enumerate(entries):
        is_last = index == (total - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(_build_ascii_tree(entry, prefix + extension, include_hidden))
    return lines


def generate_structure_report(
    root_dir: Path,
    output_dir: Path,
    base_name: str = "structure_report",
    include_hidden: bool = False,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Generates a full filesystem structure report (CSV inventory, ASCII tree TXT, and JSON metrics).
    Writes atomically via temporary files.
    """
    root = Path(root_dir)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Root directory not found: {root_dir}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / f"{base_name}.csv"
    txt_path = out_dir / f"{base_name}.txt"

    tmp_csv = csv_path.with_name(f"{csv_path.name}.{uuid4().hex}.tmp")
    tmp_txt = txt_path.with_name(f"{txt_path.name}.{uuid4().hex}.tmp")

    total_files = 0
    total_dirs = 0
    total_bytes = 0
    extension_counts: Counter[str] = Counter()

    rows: list[list[Any]] = [
        ["relative_path", "name", "type", "size_bytes", "extension", "depth"]
    ]

    for current_root, dirs, files in os.walk(root):
        cur = Path(current_root)
        # Exclude output_dir from traversal if it is a distinct subfolder inside root
        if out_dir.resolve() != root.resolve():
            if out_dir.resolve() in cur.parents or cur.resolve() == out_dir.resolve():
                dirs[:] = []
                continue
            if out_dir.name in dirs and cur.resolve() == out_dir.parent.resolve():
                dirs.remove(out_dir.name)

        if not include_hidden:
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            files = [f for f in files if not f.startswith(".")]

        # Ignore generated report files if writing into root directly
        files = [
            f for f in files
            if f not in (csv_path.name, txt_path.name, tmp_csv.name, tmp_txt.name)
        ]

        rel_dir = cur.relative_to(root)
        depth = len(rel_dir.parts)

        if cur != root:
            total_dirs += 1
            rows.append([
                str(rel_dir).replace("\\", "/"),
                cur.name,
                "directory",
                0,
                "",
                depth,
            ])

        for f in sorted(files, key=str.lower):
            file_path = cur / f
            total_files += 1
            size = 0
            try:
                size = file_path.stat().st_size
                total_bytes += size
            except OSError:
                pass

            ext = file_path.suffix.lower()
            extension_counts[ext] += 1
            rel_file = file_path.relative_to(root)

            rows.append([
                str(rel_file).replace("\\", "/"),
                f,
                "file",
                size,
                ext,
                depth + 1,
            ])

    # Write CSV
    with open(tmp_csv, "w", newline="", encoding="utf-8") as f_csv:
        writer = csv.writer(f_csv)
        writer.writerows(rows)

    # Build and write ASCII Tree
    tree_lines = [f"{root.name}/"] + _build_ascii_tree(root, include_hidden=include_hidden)
    tmp_txt.write_text("\n".join(tree_lines), encoding="utf-8")

    try:
        os.replace(tmp_csv, csv_path)
        os.replace(tmp_txt, txt_path)
    finally:
        for t in (tmp_csv, tmp_txt):
            if t.exists():
                try:
                    t.unlink()
                except OSError:
                    pass

    summary_json: dict[str, Any] = {
        "root_directory": str(root.resolve()),
        "total_files": total_files,
        "total_directories": total_dirs,
        "total_bytes": total_bytes,
        "extension_counts": dict(extension_counts),
    }

    return csv_path, txt_path, summary_json
