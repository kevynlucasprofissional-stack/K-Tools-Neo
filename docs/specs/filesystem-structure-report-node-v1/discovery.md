# Discovery: Filesystem Structure Report Node V1

## Context and Problem
The workspace contains `EC.py` ("Extrator Completo de Estrutura de Pastas"). While `folder.scan_files` returns a `FILE_SET` of discovered artifacts, users often need structured analytical reporting of an entire storage volume or directory tree:
1. Complete inventory with file sizes, extensions, and depths.
2. Formatted outputs in CSV (for database/spreadsheet import), TXT (visual tree structure), and JSON.
3. Excel XLSX workbook with summary and detailed inventory sheets.

## Candidate Node Definition
- Node Type: `filesystem.structure_report`
- Inputs: `folder: PortDefinition(DataType.FOLDER)`
- Outputs:
  - `csv: PortDefinition(DataType.FILE)`
  - `txt: PortDefinition(DataType.FILE)`
  - `json: PortDefinition(DataType.JSON)`
- Config:
  - `include_hidden` (bool, default False)
  - `output_dir` (optional str)
  - `base_name` (optional str, default "structure_report")

## Technical Architecture
- Module: `packages/ktools-filesystem/src/ktools_filesystem/reports.py`
- Functions:
  - `generate_structure_report(root_dir: Path, output_dir: Path, ...) -> dict[str, Any]`
- Atomic writes via `.tmp` promotion.
- Integrated into `ktools-filesystem` node registry.
