import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')

code = code.replace(
    "from .audio.convert import convert_audio",
    "from .audio.convert import convert_audio\nfrom .audio.split import split_audio"
)

register_call = """,
    )
    registry.register(
        NodeDefinition(
            type_id="media.split_audio",
            title="Split Audio",
            category="Media",
            inputs={
                "audio": PortDefinition(DataType.FILE),
            },
            outputs={
                "pieces": PortDefinition(DataType.FILE_SET),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _split_audio_node,
    )"""

code = code.replace(",\n    )", register_call, 1)

new_func = """
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

    from ktools_core.local_files import file_uri_from_path
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
        
    out_artifact = Artifact.create(
        type=DataType.FILE_SET,
        uri=output_dir.as_uri(),
        metadata={"count": len(pieces_artifacts)},
    )
    # FileSet outputs often include the list of files directly in some custom way?
    # K-Tools core currently doesn't formally define FileSet internals beyond the artifact itself? 
    # Wait, ktools-filesystem folder.scan_files returns a dictionary for report, but the file set is just an Artifact.
    # To pass the individual files in FILE_SET, typically it's returned as a list of artifacts attached to the node output?
    # No, we return a single FILE_SET artifact. But what contains the files?
    pass
"""

code += new_func
p.write_text(code, 'utf-8')
