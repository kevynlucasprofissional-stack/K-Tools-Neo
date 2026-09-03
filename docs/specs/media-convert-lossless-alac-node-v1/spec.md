# Spec: Media Convert Lossless ALAC Node V1

## Functional Contract
Module: `ktools_media.audio.alac`
Function: `convert_to_alac(input_path: Path, output_path: Path, verify: bool = True) -> tuple[Path, str | None]`

Node Contract:
- `type_id`: `media.convert_lossless_alac`
- `title`: `Convert to Lossless ALAC`
- `category`: `Media`
- `inputs`:
  - `audio`: `PortDefinition(DataType.FILE)`
- `outputs`:
  - `audio`: `PortDefinition(DataType.AUDIO)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Input file missing -> `FileNotFoundError`
- FFmpeg conversion failure -> `RuntimeError`
- Bit-exact verification mismatch -> `RuntimeError("Lossless verification failed: PCM hashes do not match")`
- Atomic replacement -> `.tmp` intermediate promoted via `os.replace`
