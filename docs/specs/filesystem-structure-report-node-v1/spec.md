# Spec: Filesystem Structure Report Node V1

## Functional Contract
Module: `ktools_filesystem.reports`
Function:
```python
def generate_structure_report(
    root_dir: Path,
    output_dir: Path,
    base_name: str = "structure_report",
    include_hidden: bool = False,
) -> tuple[Path, Path, dict[str, Any]]:
    """Generates (csv_path, txt_tree_path, summary_json)"""
```

Node Contract:
- `type_id`: `filesystem.structure_report`
- `title`: `Export Structure Report`
- `category`: `Filesystem`
- `inputs`:
  - `folder`: `PortDefinition(DataType.FOLDER)`
- `outputs`:
  - `csv`: `PortDefinition(DataType.FILE)`
  - `txt`: `PortDefinition(DataType.FILE)`
  - `json`: `PortDefinition(DataType.JSON)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Root directory not found -> `FileNotFoundError`
- Permission errors during directory iteration are logged into summary error list without crashing the report.
- Atomic writing -> `.tmp` intermediate files promoted via `os.replace`.
