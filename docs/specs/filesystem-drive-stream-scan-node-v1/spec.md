# Spec: Filesystem Drive Streaming Scanner Node V1

## Functional Contract
Module: `ktools_filesystem.drive_scanner`
Function:
```python
def stream_scan_directory(
    root_dir: Path,
    output_dir: Path,
    base_name: str = "drive_scan",
    include_files: bool = True,
    include_hidden: bool = False,
    verify_stability: bool = False,
) -> tuple[Path, Path, dict[str, Any]]:
    """Returns (db_path, csv_path, summary_json)"""
```

Node Contract:
- `type_id`: `filesystem.drive_stream_scan`
- `title`: `Drive Streaming Scanner`
- `category`: `Filesystem`
- `inputs`:
  - `folder`: `PortDefinition(DataType.FOLDER)`
- `outputs`:
  - `database`: `PortDefinition(DataType.FILE)`
  - `csv`: `PortDefinition(DataType.FILE)`
  - `report`: `PortDefinition(DataType.JSON)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Root not found -> `FileNotFoundError`
- Access denied on specific subfolders -> Logged to SQLite `errors` table and summary JSON without crashing the scan.
- Atomic file publication for exported CSV and DB checkpoints.
