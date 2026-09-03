import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')

code = code.replace(
    "from .audio.join import join_audios",
    "from .audio.join import join_audios\nfrom .video.compress import compress_video"
)

register_call = """,
    )
    registry.register(
        NodeDefinition(
            type_id="media.compress_video",
            title="Compress Video",
            category="Media",
            inputs={
                "video": PortDefinition(DataType.FILE),
            },
            outputs={
                "video": PortDefinition(DataType.VIDEO),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _compress_video_node,
    )"""

code = code.replace(",\n    )", register_call, 1)

new_func = """

def _compress_video_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    video_artifact = inputs["video"]
    if video_artifact.type not in (DataType.FILE, DataType.VIDEO):
        raise TypeError("media.compress_video requires a VIDEO or FILE artifact")

    input_path = path_from_file_uri(video_artifact.uri)
    
    crf = config.get("crf", 28)
    preset = config.get("preset", "medium")
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        
    output_path = output_dir / f"{input_path.stem}_compressed{input_path.suffix}"
    
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_compressed_{counter}{input_path.suffix}"
        counter += 1
        
    final_path = compress_video(
        input_path=input_path,
        output_path=output_path,
        crf=int(crf),
        preset=str(preset),
    )
    
    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.VIDEO,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"video": out_artifact}
"""
code += new_func
p.write_text(code, 'utf-8')
