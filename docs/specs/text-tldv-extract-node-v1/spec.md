# Spec: Text tl;dv Extract Node V1

## Functional Contract
Module: `ktools_text.tldv`
Function:
```python
def extract_tldv_transcript(html_content: str) -> list[TranscriptBlock]:
    ...

def export_transcript_outputs(
    blocks: list[TranscriptBlock],
    output_dir: Path,
    base_name: str,
    title: Optional[str] = None,
) -> tuple[Path, Path, dict[str, Any]]:
    """Returns (markdown_path, srt_path, json_data)"""
```

Node Contract:
- `type_id`: `text.tldv_extract`
- `title`: `Extract tl;dv Transcript`
- `category`: `Text`
- `inputs`:
  - `html`: `PortDefinition(DataType.FILE)`
- `outputs`:
  - `markdown`: `PortDefinition(DataType.FILE)`
  - `srt`: `PortDefinition(DataType.FILE)`
  - `json`: `PortDefinition(DataType.JSON)`
- `cache_policy`: `CachePolicy.NEVER`

## Error Boundaries
- Input file not found -> `FileNotFoundError`
- Missing `#transcript-container` -> `ValueError("No transcript-container found in HTML")`
- Empty transcript -> Valid empty outputs produced gracefully
- Atomic writing -> `.tmp` intermediate files promoted via `os.replace`
