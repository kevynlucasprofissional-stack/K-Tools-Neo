# Spec: Media De-ess Audio Node V1

## Functional Contract
Module: `ktools_media.audio.deesser`
Function:
```python
def deess_audio(
    input_path: Path,
    output_path: Path,
    intensity: float = 0.5,
    frequency: float = 0.5,
    noise_reduction: bool = False,
    output_format: str = "wav",
) -> Path:
    ...
```

Node Contract:
- `type_id`: `media.deess_audio`
- `title`: `De-ess Audio`
- `category`: `Media`
- `inputs`:
  - `audio`: `PortDefinition(DataType.FILE)`
- `outputs`:
  - `audio`: `PortDefinition(DataType.AUDIO)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Input file missing -> `FileNotFoundError`
- Invalid intensity (<0.0 or >1.0) -> `ValueError`
- Invalid frequency (<0.0 or >1.0) -> `ValueError`
- FFmpeg execution failure -> `RuntimeError`
- Atomic replacement -> `.tmp` promoted via `os.replace`
