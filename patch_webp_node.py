from ktools_core.models import DataType, Artifact
from ktools_core.registry import NodeExecutionContext
from ktools_core.local_files import path_from_file_uri
from pathlib import Path
from typing import Any

FUNC = '''

def _webp_to_png_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    image_artifact = inputs["image"]
    if image_artifact.type not in (DataType.FILE, DataType.IMAGE):
        raise TypeError("media.webp_to_png requires an IMAGE or FILE artifact")

    input_path = path_from_file_uri(image_artifact.uri)
    
    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])
        
    output_path = output_dir / f"{input_path.stem}.png"
    
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{input_path.stem}_{counter}.png"
        counter += 1
        
    final_path = webp_to_png(
        input_path=input_path,
        output_path=output_path,
    )
    
    from ktools_core.models import Artifact
    
    out_artifact = Artifact.create(
        type=DataType.IMAGE,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "format": "png",
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"image": out_artifact}
'''

p = __import__('pathlib').Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
p.write_text(code + FUNC, 'utf-8')
print("Done")
