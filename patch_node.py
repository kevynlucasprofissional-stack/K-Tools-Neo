import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')

code = code.replace(
    "from .audio.extract import extract_audio_from_video",
    "from .audio.extract import extract_audio_from_video\nfrom .audio.convert import convert_audio"
)

register_call = """,
    )
    registry.register(
        NodeDefinition(
            type_id="media.convert_audio",
            title="Convert Audio",
            category="Media",
            inputs={
                "audio": PortDefinition(DataType.AUDIO),
                "format": PortDefinition(DataType.STRING),
            },
            outputs={
                "audio": PortDefinition(DataType.AUDIO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _convert_audio_node,
    )"""

code = code.replace(",\n    )", register_call, 1)

new_func = """
def _convert_audio_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    audio_artifact = inputs["audio"]
    if audio_artifact.type not in (DataType.FILE, DataType.AUDIO):
        raise TypeError("media.convert_audio requires an AUDIO or FILE artifact")

    input_path = path_from_file_uri(audio_artifact.uri)
    out_format = inputs.get("format", config.get("format", "m4a")).lower().strip(".")
    bitrate = config.get("bitrate")

    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    output_path = output_dir / f"{input_path.stem}.{out_format}"

    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_{counter}.{out_format}"
        counter += 1

    final_path = convert_audio(
        input_path=input_path,
        output_path=output_path,
        output_format=out_format,
        bitrate=bitrate,
    )

    from ktools_core.local_files import file_uri_from_path
    from ktools_core.models import Artifact
    
    out_artifact = Artifact(
        uri=file_uri_from_path(final_path),
        type=DataType.AUDIO,
        metadata={
            "name": final_path.name,
            "format": out_format,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"audio": out_artifact}
"""

code += new_func
p.write_text(code, 'utf-8')
