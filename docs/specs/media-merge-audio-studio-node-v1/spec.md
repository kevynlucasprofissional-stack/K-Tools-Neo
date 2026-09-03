# Spec: Media Merge Audio Studio Node V1

## Functional Contract
Module: `ktools_media.audio.studio_merge`
Function:
```python
def merge_audio_studio(
    input_paths: Sequence[Path],
    output_path: Path,
    output_format: str = "m4a",
    bitrate: str = "192k",
    normalize_volume: bool = False,
    natural_sort: bool = True,
) -> tuple[Path, dict[str, Any]]:
    ...
```

Node Contract:
- `type_id`: `media.merge_audio_studio`
- `title`: `Merge Audio Studio`
- `category`: `Media`
- `inputs`:
  - `sources`: `PortDefinition(DataType.FILE_SET)`
- `outputs`:
  - `audio`: `PortDefinition(DataType.AUDIO)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Input list empty or < 2 items -> `ValueError`
- Missing file -> `FileNotFoundError`
- FFmpeg failure -> `RuntimeError`
- Atomic replacement -> `.tmp` promoted via `os.replace`
