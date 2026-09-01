"""Headless workflow execution with the official JSON node pack."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ktools_core import DiagnosticsSession, RunJournal, SQLiteRunJournal
from ktools_core.builtin import register_builtin_nodes
from ktools_core.engine import WorkflowEngine, WorkflowExecutionError, WorkflowValidationError
from ktools_core.models import Artifact, WorkflowDefinition
from ktools_core.registry import NodeRegistry

from .node import register_nodes


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
) -> WorkflowEngine:
    registry = NodeRegistry()
    register_builtin_nodes(registry)
    register_nodes(registry)
    return WorkflowEngine(registry, journal=journal, diagnostics=diagnostics)


def _latest_correlation(diagnostics: DiagnosticsSession | None) -> tuple[str | None, str | None]:
    if diagnostics is None:
        return None, None
    for event in reversed(diagnostics.events):
        if event.run_id or event.workflow_id:
            return event.run_id, event.workflow_id
    return None, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute a K-Tools Neo workflow JSON file with the JSON node pack"
    )
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--journal", type=Path, metavar="SQLITE_DB")
    parser.add_argument(
        "--diagnostics-dir",
        type=Path,
        default=Path.cwd() / "ktools-diagnostics",
        help="Parent directory for automatic diagnostic reports/support bundles",
    )
    parser.add_argument("--no-diagnostics", action="store_true")
    args = parser.parse_args(argv)

    diagnostics = None if args.no_diagnostics else DiagnosticsSession(
        args.diagnostics_dir, component="ktools-json.cli", product_version="0.1.0"
    )
    journal = SQLiteRunJournal(args.journal) if args.journal is not None else None
    result = None
    bundle: Path | None = None

    try:
        try:
            raw = json.loads(args.workflow.read_text(encoding="utf-8"))
            workflow = WorkflowDefinition.from_dict(raw)
            if diagnostics is not None:
                diagnostics.log(
                    "JSON Node Pack workflow document loaded",
                    category="cli.input",
                    context={"workflowFile": str(args.workflow), "workflowId": workflow.id},
                )
            result = build_engine(journal=journal, diagnostics=diagnostics).execute(workflow)
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
                    status="FAILED", run_id=run_id, workflow_id=workflow_id, journal_events=journal_events
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
