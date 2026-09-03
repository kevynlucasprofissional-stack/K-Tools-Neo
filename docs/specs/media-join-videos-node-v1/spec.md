# Spec: Media Join Videos Node V1

## Functional Contract
Module: ktools_media.video.join
Function: join_videos(input_paths: Sequence[Path], output_path: Path, fast_copy: bool = True) -> Path

Node Contract:
- 	ype_id: media.join_videos
- 	itle: Join Videos
- category: Media
- inputs:
  - ideos: PortDefinition(DataType.FILE_SET)
- outputs:
  - ideo: PortDefinition(DataType.VIDEO)
- cache_policy: CachePolicy.NEVER

## Error Handling & Boundaries
- Missing files -> FileNotFoundError
- Empty or < 2 inputs -> ValueError
- Non-video inputs -> Checked by extension or probe
- Output collision -> Resolved by numeric suffix unless explicit output_path
- Atomic replacement -> .tmp intermediate file promoted with os.replace
