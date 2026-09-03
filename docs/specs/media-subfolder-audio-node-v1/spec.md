# Spec: Media Extract and Join by Subfolder Node V1

## Functional Contract
Module: `ktools_media.orchestrators.subfolder_audio`
Function:
```python
def extract_and_join_by_subfolder(
    root_dir: Path,
    output_dir: Optional[Path] = None,
    output_format: str = "m4a",
    bitrate: str = "192k",
) -> tuple[list[Path], dict[str, Any]]:
    ...
```

Node Contract:
- `type_id`: `media.extract_and_join_by_subfolder`
- `title`: `Extract and Join Audio by Subfolder`
- `category`: `Media`
- `inputs`:
  - `folder`: `PortDefinition(DataType.FOLDER)`
- `outputs`:
  - `audios`: `PortDefinition(DataType.FILE_SET)`
  - `report`: `PortDefinition(DataType.JSON)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Root directory not found -> `FileNotFoundError`
- Empty or zero video files found -> Returns empty list and report indicating 0 folders
- Atomic publication -> Per-folder outputs written to `.tmp` and promoted
