from __future__ import annotations

from typing import Any

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .scanner import scan_files


def register_nodes(registry: NodeRegistry) -> None:
    registry.register(
        NodeDefinition(
            type_id="folder.scan_files",
            title="Scan Folder Files",
            category="Files",
            inputs={
                "folder": PortDefinition(DataType.FOLDER),
            },
            outputs={
                "files": PortDefinition(DataType.FILE_SET),
                "report": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _scan_files_node,
    )


def _scan_files_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    folder_artifact = inputs["folder"]
    if folder_artifact.type != DataType.FOLDER:
        raise TypeError("folder.scan_files requires a FOLDER artifact")

    root_path = path_from_file_uri(folder_artifact.uri)

    recursive = config.get("recursive", True)
    include_hidden = config.get("include_hidden", False)
    
    extensions_raw = config.get("extensions")
    extensions = None
    if extensions_raw:
        if isinstance(extensions_raw, (list, tuple)):
            extensions = set(extensions_raw)
        elif isinstance(extensions_raw, str):
            extensions = {e.strip() for e in extensions_raw.split(",")}
        elif isinstance(extensions_raw, set):
            extensions = extensions_raw

    result = scan_files(
        root_path=root_path,
        recursive=recursive,
        include_hidden=include_hidden,
        extensions=extensions,
        context=context,
    )

    return {
        "files": result.files,
        "report": result.report,
    }
