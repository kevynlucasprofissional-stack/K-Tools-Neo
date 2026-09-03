from ktools_core.models import DataType, Artifact
from ktools_core.registry import NodeExecutionContext
from ktools_core.local_files import path_from_file_uri
from pathlib import Path
from typing import Any

PDF_NODES = '''

def _merge_pdfs_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    pdfs = inputs.get("pdfs")
    if not pdfs:
        raise ValueError("pdf.merge requires 'pdfs' input.")

    artifacts = pdfs if isinstance(pdfs, list) else [pdfs]
    artifacts = sorted(artifacts, key=lambda a: a.metadata.get("name", a.uri) if a.metadata else a.uri)

    input_paths = [path_from_file_uri(a.uri) for a in artifacts]

    output_dir = input_paths[0].parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    output_name = config.get("output_name", "merged.pdf")
    output_path = output_dir / output_name

    counter = 1
    while output_path.exists():
        output_path = output_dir / f"merged_{counter}.pdf"
        counter += 1

    final_path = merge_pdfs(
        input_paths=input_paths,
        output_path=output_path,
    )

    from ktools_core.models import Artifact

    out_artifact = Artifact.create(
        type=DataType.FILE,
        uri=final_path.as_uri(),
        metadata={
            "name": final_path.name,
            "size_bytes": final_path.stat().st_size,
        },
    )
    return {"pdf": out_artifact}


def _split_pdf_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    pdf_artifact = inputs["pdf"]
    if pdf_artifact.type not in (DataType.FILE,):
        raise TypeError("pdf.split requires a FILE artifact")

    input_path = path_from_file_uri(pdf_artifact.uri)

    parts = config.get("parts")
    if not isinstance(parts, int) or parts < 2:
        raise ValueError("pdf.split config 'parts' must be an integer >= 2")

    output_dir = input_path.parent
    if "output_dir" in config:
        output_dir = Path(config["output_dir"])

    part_paths = split_pdf(
        input_path=input_path,
        output_dir=output_dir,
        parts=parts,
    )

    from ktools_core.models import Artifact

    part_artifacts = []
    for p_path in part_paths:
        part_artifacts.append(
            Artifact.create(
                type=DataType.FILE,
                uri=p_path.as_uri(),
                metadata={
                    "name": p_path.name,
                    "size_bytes": p_path.stat().st_size,
                },
            )
        )

    return {"parts": part_artifacts}
'''

p = __import__('pathlib').Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
p.write_text(code + PDF_NODES, 'utf-8')
print("Done")
