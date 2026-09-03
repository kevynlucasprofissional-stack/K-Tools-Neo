from __future__ import annotations

from typing import Any

from ktools_core.local_files import path_from_file_uri
from ktools_core.models import CachePolicy, DataType, NodeDefinition, PortDefinition
from ktools_core.registry import NodeExecutionContext, NodeRegistry

from .scanner import scan_files
from .reports import generate_structure_report
from .drive_scanner import stream_scan_directory


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
    registry.register(
        NodeDefinition(
            type_id="filesystem.structure_report",
            title="Export Structure Report",
            category="Filesystem",
            inputs={
                "folder": PortDefinition(DataType.FOLDER),
            },
            outputs={
                "csv": PortDefinition(DataType.FILE),
                "txt": PortDefinition(DataType.FILE),
                "json": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _structure_report_node,
    )
    registry.register(
        NodeDefinition(
            type_id="filesystem.drive_stream_scan",
            title="Drive Streaming Scanner",
            category="Filesystem",
            inputs={
                "folder": PortDefinition(DataType.FOLDER),
            },
            outputs={
                "database": PortDefinition(DataType.FILE),
                "csv": PortDefinition(DataType.FILE),
                "report": PortDefinition(DataType.JSON),
            },
            version="1",
            cache_policy=CachePolicy.NEVER,
        ),
        _drive_stream_scan_node,
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


def _structure_report_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    folder_artifact = inputs.get("folder")
    if not folder_artifact or folder_artifact.type != DataType.FOLDER:
        raise TypeError("filesystem.structure_report requires a FOLDER artifact")

    root_path = path_from_file_uri(folder_artifact.uri)

    output_dir = root_path
    if "output_dir" in config and config["output_dir"]:
        output_dir = Path(config["output_dir"])

    base_name = config.get("base_name", f"{root_path.name}_structure")
    include_hidden = bool(config.get("include_hidden", False))

    csv_path, txt_path, summary_json = generate_structure_report(
        root_dir=root_path,
        output_dir=output_dir,
        base_name=base_name,
        include_hidden=include_hidden,
    )

    from ktools_core.models import Artifact

    csv_artifact = Artifact.create(
        type=DataType.FILE,
        uri=csv_path.as_uri(),
        metadata={
            "name": csv_path.name,
            "format": "csv",
            "size_bytes": csv_path.stat().st_size,
        },
    )
    txt_artifact = Artifact.create(
        type=DataType.FILE,
        uri=txt_path.as_uri(),
        metadata={
            "name": txt_path.name,
            "format": "txt",
            "size_bytes": txt_path.stat().st_size,
        },
    )
    json_artifact = Artifact.create(
        type=DataType.JSON,
        uri=root_path.as_uri(),
        metadata=summary_json,
    )

    return {
        "csv": csv_artifact,
        "txt": txt_artifact,
        "json": json_artifact,
    }


def _drive_stream_scan_node(
    inputs: dict[str, Any], config: dict[str, Any], context: NodeExecutionContext
) -> dict[str, Any]:
    folder_artifact = inputs.get("folder")
    if not folder_artifact or folder_artifact.type != DataType.FOLDER:
        raise TypeError("filesystem.drive_stream_scan requires a FOLDER artifact")

    root_path = path_from_file_uri(folder_artifact.uri)

    output_dir = root_path
    if "output_dir" in config and config["output_dir"]:
        output_dir = Path(config["output_dir"])

    base_name = config.get("base_name", f"{root_path.name}_drive_scan")
    include_files = bool(config.get("include_files", True))
    include_hidden = bool(config.get("include_hidden", False))
    verify_stability = bool(config.get("verify_stability", False))

    db_path, csv_path, summary_report = stream_scan_directory(
        root_dir=root_path,
        output_dir=output_dir,
        base_name=base_name,
        include_files=include_files,
        include_hidden=include_hidden,
        verify_stability=verify_stability,
    )

    from ktools_core.models import Artifact

    db_artifact = Artifact.create(
        type=DataType.FILE,
        uri=db_path.as_uri(),
        metadata={
            "name": db_path.name,
            "format": "sqlite3",
            "size_bytes": db_path.stat().st_size,
        },
    )
    csv_artifact = Artifact.create(
        type=DataType.FILE,
        uri=csv_path.as_uri(),
        metadata={
            "name": csv_path.name,
            "format": "csv",
            "size_bytes": csv_path.stat().st_size,
        },
    )
    json_artifact = Artifact.create(
        type=DataType.JSON,
        uri=root_path.as_uri(),
        metadata=summary_report,
    )

    return {
        "database": db_artifact,
        "csv": csv_artifact,
        "report": json_artifact,
    }


