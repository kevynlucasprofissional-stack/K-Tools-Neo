from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .artifact_registry import ArtifactRegistry, SQLiteArtifactRegistry
from .builtin import register_builtin_nodes
from .cache_store import NodeCache, SQLiteNodeCache
from .diagnostics import DiagnosticsSession
from .engine import WorkflowEngine, WorkflowExecutionError, WorkflowValidationError
from .invoker import CapabilityInvoker
from .journal import RunJournal
from .manifest import generate_capability_manifest
from .mcp_server import KToolsMCPServer
from .models import Artifact, WorkflowDefinition
from .registry import NodeRegistry, load_all_installed_node_packs
from .sqlite_journal import SQLiteRunJournal


def _handle_capability_cli(argv: list[str]) -> int:
    registry = load_all_installed_node_packs()
    invoker = CapabilityInvoker(registry)

    if not argv:
        print("Usage: ktools [capabilities | mcp | <workflow.json>]")
        return 1

    cmd = argv[0]

    if cmd == "mcp":
        server = KToolsMCPServer(registry, invoker)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                res = server.handle_request(req)
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
            except Exception as exc:
                err_res = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()
        return 0

    subcmd = argv[1] if len(argv) > 1 else "list"

    if subcmd == "list":
        manifest = generate_capability_manifest(registry)
        if "--json" in argv:
            print(manifest.to_json())
        else:
            print(f"K-Tools Neo — Available Capabilities ({len(manifest.capabilities)}):")
            for cap_id, cap in sorted(manifest.capabilities.items()):
                print(f"  • {cap_id:36} [{cap.category:12}] {cap.title} ({cap.side_effect_class.value})")
        return 0

    if subcmd == "describe":
        if len(argv) < 3:
            print("Error: specify capability ID. Example: ktools capabilities describe text.concat")
            return 1
        cap_id = argv[2]
        manifest = generate_capability_manifest(registry)
        if cap_id not in manifest.capabilities:
            print(f"Error: Unknown capability '{cap_id}'")
            return 1
        cap = manifest.capabilities[cap_id]
        print(json.dumps(cap.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if subcmd == "invoke":
        if len(argv) < 3:
            print("Error: specify capability ID. Example: ktools capabilities invoke text.concat --input a=1 --input b=2")
            return 1
        cap_id = argv[2]
        inputs = {}
        idx = 3
        while idx < len(argv):
            arg = argv[idx]
            if arg in ("--input", "-i") and idx + 1 < len(argv):
                val = argv[idx + 1]
                if "=" in val:
                    k, v = val.split("=", 1)
                    inputs[k] = v
                idx += 2
            elif arg == "--input-json" and idx + 1 < len(argv):
                try:
                    inputs.update(json.loads(argv[idx + 1]))
                except Exception as exc:
                    print(f"Error parsing --input-json: {exc}")
                    return 1
                idx += 2
            else:
                idx += 1

        receipt = invoker.invoke(cap_id, inputs=inputs)
        print(receipt.to_json())
        return 0 if receipt.status.value == "SUCCESS" else 1

    print(f"Error: Unknown subcommand '{subcmd}'. Available: list, describe, invoke")
    return 1


def _jsonable(value: Any) -> Any:
    if isinstance(value, Artifact):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def build_engine(
    journal: RunJournal | None = None,
    diagnostics: DiagnosticsSession | None = None,
    cache: NodeCache | None = None,
    artifact_registry: ArtifactRegistry | None = None,
) -> WorkflowEngine:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    return WorkflowEngine(
        registry,
        journal=journal,
        diagnostics=diagnostics,
        cache=cache,
        artifact_registry=artifact_registry,
    )


def _latest_correlation(diagnostics: DiagnosticsSession | None) -> tuple[str | None, str | None]:
    if diagnostics is None:
        return None, None
    for event in reversed(diagnostics.events):
        if event.run_id or event.workflow_id:
            return event.run_id, event.workflow_id
    return None, None


def main(argv: list[str] | None = None) -> int:
    raw_args = list(sys.argv[1:]) if argv is None else list(argv)
    if raw_args and raw_args[0] in ("capabilities", "capability", "mcp"):
        return _handle_capability_cli(raw_args)

    parser = argparse.ArgumentParser(description="Execute a K-Tools Neo workflow JSON file")
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--journal",
        type=Path,
        metavar="SQLITE_DB",
        help="Persist run/node lifecycle and output metadata to a SQLite journal",
    )
    parser.add_argument(
        "--cache",
        type=Path,
        metavar="SQLITE_DB",
        help="Enable persistent semantic node cache using a SQLite database",
    )
    parser.add_argument(
        "--artifact-registry",
        type=Path,
        metavar="SQLITE_DB",
        help="Persist Artifact provenance/validity observations using SQLite",
    )
    parser.add_argument(
        "--diagnostics-dir",
        type=Path,
        default=Path.cwd() / "ktools-diagnostics",
        help="Parent directory for automatic diagnostic reports/support bundles",
    )
    parser.add_argument(
        "--no-diagnostics",
        action="store_true",
        help="Disable automatic diagnostic report generation",
    )
    args = parser.parse_args(argv)

    diagnostics = None if args.no_diagnostics else DiagnosticsSession(
        args.diagnostics_dir,
        component="ktools-core.cli",
        product_version="0.1.0",
    )
    journal = SQLiteRunJournal(args.journal) if args.journal is not None else None
    cache = SQLiteNodeCache(args.cache) if args.cache is not None else None
    artifact_registry = (
        SQLiteArtifactRegistry(args.artifact_registry)
        if args.artifact_registry is not None
        else None
    )
    result = None
    bundle: Path | None = None

    try:
        try:
            raw = json.loads(args.workflow.read_text(encoding="utf-8"))
            workflow = WorkflowDefinition.from_dict(raw)
            if diagnostics is not None:
                diagnostics.log(
                    "Workflow document loaded",
                    category="cli.input",
                    context={"workflowFile": str(args.workflow), "workflowId": workflow.id},
                )
            result = build_engine(
                journal=journal,
                diagnostics=diagnostics,
                cache=cache,
                artifact_registry=artifact_registry,
            ).execute(workflow)
        except WorkflowValidationError as exc:
            if diagnostics is not None:
                diagnostics.capture_exception(exc, "Workflow validation failed", category="cli.validation")
                run_id, workflow_id = _latest_correlation(diagnostics)
                bundle = diagnostics.finalize(status="VALIDATION_ERROR", run_id=run_id, workflow_id=workflow_id)
            print(f"VALIDATION_ERROR: {exc}")
            if bundle is not None:
                print(f"DIAGNOSTICS: {bundle}")
            return 2
        except WorkflowExecutionError as exc:
            if diagnostics is not None:
                diagnostics.capture_exception(exc, "Workflow execution returned failure", category="cli.execution")
                run_id, workflow_id = _latest_correlation(diagnostics)
                journal_events = () if journal is None or run_id is None else journal.get_events(run_id)
                bundle = diagnostics.finalize(
                    status="FAILED",
                    run_id=run_id,
                    workflow_id=workflow_id,
                    journal_events=journal_events,
                )
            print(f"EXECUTION_ERROR: {exc}")
            if bundle is not None:
                print(f"DIAGNOSTICS: {bundle}")
            return 3
        except KeyboardInterrupt as exc:
            if diagnostics is not None:
                diagnostics.capture_exception(
                    exc,
                    "Execution interrupted by user",
                    category="cli.interruption",
                )
                run_id, workflow_id = _latest_correlation(diagnostics)
                journal_events = () if journal is None or run_id is None else journal.get_events(run_id)
                bundle = diagnostics.finalize(
                    status="INTERRUPTED",
                    run_id=run_id,
                    workflow_id=workflow_id,
                    journal_events=journal_events,
                )
            print("INTERRUPTED: execution cancelled by user")
            if bundle is not None:
                print(f"DIAGNOSTICS: {bundle}")
            return 130
        except Exception as exc:
            if diagnostics is not None:
                diagnostics.capture_exception(exc, "CLI failed before workflow completion", category="cli.unexpected")
                run_id, workflow_id = _latest_correlation(diagnostics)
                bundle = diagnostics.finalize(status="FAILED", run_id=run_id, workflow_id=workflow_id)
            print(f"UNEXPECTED_ERROR: {exc}")
            if bundle is not None:
                print(f"DIAGNOSTICS: {bundle}")
            return 4

        payload = {
            "runId": result.run_id,
            "workflowId": result.workflow_id,
            "nodeOutputs": _jsonable(result.node_outputs),
        }
        if args.journal is not None:
            payload["journal"] = str(args.journal)
        if args.cache is not None:
            payload["cache"] = str(args.cache)
        if args.artifact_registry is not None:
            payload["artifactRegistry"] = str(args.artifact_registry)
        if diagnostics is not None:
            journal_events = () if journal is None else journal.get_events(result.run_id)
            bundle = diagnostics.finalize(
                status="SUCCEEDED",
                run_id=result.run_id,
                workflow_id=result.workflow_id,
                result_summary={"nodeOutputs": payload["nodeOutputs"]},
                journal_events=journal_events,
            )
            payload["diagnosticBundle"] = str(bundle)

        if args.json_output:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"Workflow {result.workflow_id} completed: {result.run_id}")
            if bundle is not None:
                print(f"Diagnostics: {bundle}")
        return 0
    finally:
        if journal is not None:
            journal.close()
        if cache is not None:
            cache.close()
        if artifact_registry is not None:
            artifact_registry.close()


if __name__ == "__main__":
    raise SystemExit(main())
