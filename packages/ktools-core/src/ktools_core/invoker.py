from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from ktools_core.diagnostics import DiagnosticsSession
from ktools_core.journal import RunJournal, RunEvent, RunEventType
from ktools_core.models import Artifact
from ktools_core.receipt import ArtifactRecord, ExecutionReceipt, ReceiptStatus
from ktools_core.registry import NodeExecutionContext, NodeRegistry


class CapabilityInvoker:
    def __init__(
        self,
        registry: NodeRegistry,
        journal: Optional[RunJournal] = None,
        diagnostics: Optional[DiagnosticsSession] = None,
    ) -> None:
        self.registry = registry
        self.journal = journal
        self.diagnostics = diagnostics

    def invoke(
        self,
        capability_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ExecutionReceipt:
        inputs = inputs or {}
        config = config or {}
        run_id = f"run_{uuid4().hex[:12]}"
        workflow_id = f"direct_{capability_id}"
        node_id = "target_node"
        started_dt = datetime.now(timezone.utc)
        start_time = time.perf_counter()

        # Check if capability exists
        try:
            node_def = self.registry.definition(capability_id)
        except KeyError:
            duration = time.perf_counter() - start_time
            completed_dt = datetime.now(timezone.utc)
            return ExecutionReceipt(
                capability_id=capability_id,
                status=ReceiptStatus.FAILED,
                started_at=started_dt.isoformat(),
                completed_at=completed_dt.isoformat(),
                duration_seconds=round(duration, 4),
                inputs=inputs,
                error={
                    "type": "UnknownCapabilityError",
                    "message": f"Unknown capability '{capability_id}'",
                },
                run_id=run_id,
                diagnostics_session_id=self.diagnostics.session_id if self.diagnostics else None,
            )

        # Validate required inputs
        missing_inputs = [
            p_name
            for p_name, port in node_def.inputs.items()
            if port.required and p_name not in inputs
        ]
        if missing_inputs:
            duration = time.perf_counter() - start_time
            completed_dt = datetime.now(timezone.utc)
            return ExecutionReceipt(
                capability_id=capability_id,
                status=ReceiptStatus.FAILED,
                version=getattr(node_def, "version", "1.0.0"),
                started_at=started_dt.isoformat(),
                completed_at=completed_dt.isoformat(),
                duration_seconds=round(duration, 4),
                inputs=inputs,
                error={
                    "type": "ValidationError",
                    "message": f"Missing required inputs: {', '.join(missing_inputs)}",
                    "missing_ports": missing_inputs,
                },
                run_id=run_id,
                diagnostics_session_id=self.diagnostics.session_id if self.diagnostics else None,
            )

        # Journal run start
        context = NodeExecutionContext(run_id=run_id, workflow_id=workflow_id, node_id=node_id)
        if self.journal:
            try:
                self.journal.record(
                    RunEvent.create(
                        run_id=run_id,
                        workflow_id=workflow_id,
                        event_type=RunEventType.RUN_STARTED,
                    )
                )
                self.journal.record(
                    RunEvent.create(
                        run_id=run_id,
                        workflow_id=workflow_id,
                        event_type=RunEventType.NODE_STARTED,
                        node_id=node_id,
                        node_type=capability_id,
                        payload={"inputs": inputs, "config": config},
                    )
                )
            except Exception:
                pass

        # Execute handler
        try:
            raw_outputs = self.registry.execute(capability_id, inputs, config, context)
            if not isinstance(raw_outputs, dict):
                raw_outputs = {"output": raw_outputs}

            duration = time.perf_counter() - start_time
            completed_dt = datetime.now(timezone.utc)

            # Extract Artifacts
            artifacts = []
            normalized_outputs = {}
            for out_key, out_val in raw_outputs.items():
                if isinstance(out_val, Artifact):
                    art_rec = ArtifactRecord(
                        artifact_id=out_val.id,
                        uri=out_val.uri,
                        mime_type=out_val.mime_type,
                        sha256=getattr(out_val, "sha256", None),
                        size_bytes=getattr(out_val, "size_bytes", None),
                        metadata=dict(out_val.metadata) if hasattr(out_val, "metadata") else {},
                    )
                    artifacts.append(art_rec)
                    normalized_outputs[out_key] = out_val.uri
                else:
                    normalized_outputs[out_key] = out_val

            if self.journal:
                try:
                    self.journal.record(
                        RunEvent.create(
                            run_id=run_id,
                            workflow_id=workflow_id,
                            event_type=RunEventType.NODE_SUCCEEDED,
                            node_id=node_id,
                            node_type=capability_id,
                            payload={"outputs": normalized_outputs},
                        )
                    )
                    self.journal.record(
                        RunEvent.create(
                            run_id=run_id,
                            workflow_id=workflow_id,
                            event_type=RunEventType.RUN_SUCCEEDED,
                            payload={"outputs": normalized_outputs},
                        )
                    )
                except Exception:
                    pass

            return ExecutionReceipt(
                capability_id=capability_id,
                status=ReceiptStatus.SUCCESS,
                version=getattr(node_def, "version", "1.0.0"),
                started_at=started_dt.isoformat(),
                completed_at=completed_dt.isoformat(),
                duration_seconds=round(duration, 4),
                inputs=inputs,
                outputs=normalized_outputs,
                artifacts=artifacts,
                run_id=run_id,
                diagnostics_session_id=self.diagnostics.session_id if self.diagnostics else None,
            )

        except Exception as exc:
            duration = time.perf_counter() - start_time
            completed_dt = datetime.now(timezone.utc)
            err_dict = {
                "type": type(exc).__name__,
                "message": str(exc),
            }

            if self.journal:
                try:
                    self.journal.record(
                        RunEvent.create(
                            run_id=run_id,
                            workflow_id=workflow_id,
                            event_type=RunEventType.NODE_FAILED,
                            node_id=node_id,
                            node_type=capability_id,
                            payload={"error": str(exc)},
                        )
                    )
                    self.journal.record(
                        RunEvent.create(
                            run_id=run_id,
                            workflow_id=workflow_id,
                            event_type=RunEventType.RUN_FAILED,
                            payload={"error": str(exc)},
                        )
                    )
                except Exception:
                    pass

            return ExecutionReceipt(
                capability_id=capability_id,
                status=ReceiptStatus.FAILED,
                version=getattr(node_def, "version", "1.0.0"),
                started_at=started_dt.isoformat(),
                completed_at=completed_dt.isoformat(),
                duration_seconds=round(duration, 4),
                inputs=inputs,
                error=err_dict,
                run_id=run_id,
                diagnostics_session_id=self.diagnostics.session_id if self.diagnostics else None,
            )
