import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
# Clean out anything that is missing or broken. Let's just append it if not exists.
if "def _split_audio_node" not in code:
    code += """
def _split_audio_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    audio_artifact = inputs["audio"]
    if audio_artifact.type not in (DataType.FILE, DataType.AUDIO):
        raise TypeError("media.split_audio requires an AUDIO or FILE artifact")

    input_path = path_from_file_uri(audio_artifact.uri)
    
    parts = config.get("parts")
    if not isinstance(parts, int) or parts < 2:
        raise ValueError("media.split_audio config 'parts' must be an integer >= 2")

    out_format = config.get("format")
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    pieces_paths = split_audio(
        input_path=input_path,
        output_dir=output_dir,
        parts=parts,
        output_format=out_format,
    )

    from ktools_core.models import Artifact
    
    pieces_artifacts = []
    for p_path in pieces_paths:
        pieces_artifacts.append(
            Artifact.create(
                type=DataType.AUDIO,
                uri=p_path.as_uri(),
                metadata={
                    "name": p_path.name,
                    "format": p_path.suffix.strip("."),
                    "size_bytes": p_path.stat().st_size,
                },
            )
        )
        
    return {"pieces": pieces_artifacts}
"""
    p.write_text(code, 'utf-8')
