import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
old_bad = """    from ktools_core.models import Artifact
    
    return {"pieces": pieces_artifacts}

def _split_audio_node("""

new_good = """    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.AUDIO,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "format": out_format,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"audio": out_artifact}

def _split_audio_node("""

code = code.replace(old_bad, new_good)
p.write_text(code, 'utf-8')
