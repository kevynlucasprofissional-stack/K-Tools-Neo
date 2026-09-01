from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.artifact_registry import SQLiteArtifactRegistry, validate_artifact_record
from ktools_core.cache_store import SQLiteNodeCache
from ktools_core.engine import WorkflowEngine
from ktools_core.models import (
    Artifact,
    CachePolicy,
    DataType,
    NodeDefinition,
    PortDefinition,
    WorkflowDefinition,
    WorkflowNode,
)
from ktools_core.registry import NodeExecutionContext, NodeRegistry


class SQLiteArtifactRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "artifacts.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_artifact_occurrence_survives_reopen_with_run_node_port_provenance(self) -> None:
        path = self.root / "result.bin"
        path.write_bytes(b"artifact-content")
        artifact = Artifact.create(
            type=DataType.FILE,
            uri=path.resolve().as_uri(),
            produced_by="run-origin/node-origin",
            metadata={"kind": "fixture"},
        )

        with SQLiteArtifactRegistry(self.database) as registry:
            records = registry.observe_outputs(
                run_id="run_current",
                node_id="producer",
                outputs={"file": artifact},
                source="EXECUTED",
            )
            self.assertEqual(len(records), 1)
            self.assertTrue(validate_artifact_record(records[0]).strongly_valid)

        with SQLiteArtifactRegistry(self.database) as registry:
            records = registry.list_for_run("run_current")
            self.assertEqual(len(records), 1)
            record = records[0]
            self.assertEqual(record.artifact.id, artifact.id)
            self.assertEqual(record.run_id, "run_current")
            self.assertEqual(record.node_id, "producer")
            self.assertEqual(record.output_port, "file")
            self.assertEqual(record.value_path, "$")
            self.assertEqual(record.source, "EXECUTED")
            self.assertEqual(record.artifact.produced_by, "run-origin/node-origin")
            self.assertEqual(record.artifact.metadata["kind"], "fixture")
            self.assertIsNotNone(record.snapshot)

    def test_engine_records_executed_and_cached_occurrences_for_same_artifact(self) -> None:
        output = self.root / "engine-result.bin"
        calls = {"count": 0}
        registry = NodeRegistry()

        def handler(_inputs: dict, config: dict, context: NodeExecutionContext) -> dict:
            calls["count"] += 1
            output.write_bytes(b"stable-output")
            return {
                "file": Artifact.create(
                    type=DataType.FILE,
                    uri=output.resolve().as_uri(),
                    produced_by=f"{context.run_id}/{context.node_id}",
                    metadata={"config": config["label"]},
                )
            }

        registry.register(
            NodeDefinition(
                type_id="test.artifact-producer",
                title="Artifact producer",
                outputs={"file": PortDefinition(DataType.FILE)},
                version="1",
                cache_policy=CachePolicy.PURE,
            ),
            handler,
        )
        workflow = WorkflowDefinition(
            id="artifact-registry-cache",
            nodes=(
                WorkflowNode(
                    id="producer",
                    type="test.artifact-producer",
                    config={"label": "same"},
                ),
            ),
            edges=(),
        )

        with SQLiteArtifactRegistry(self.database) as artifact_registry:
            with SQLiteNodeCache(self.root / "cache.sqlite3") as cache:
                first = WorkflowEngine(
                    registry,
                    cache=cache,
                    artifact_registry=artifact_registry,
                ).execute(workflow)
                second = WorkflowEngine(
                    registry,
                    cache=cache,
                    artifact_registry=artifact_registry,
                ).execute(workflow)

            first_records = artifact_registry.list_for_run(first.run_id)
            second_records = artifact_registry.list_for_run(second.run_id)

        self.assertEqual(calls["count"], 1)
        self.assertEqual(len(first_records), 1)
        self.assertEqual(len(second_records), 1)
        self.assertEqual(first_records[0].source, "EXECUTED")
        self.assertEqual(second_records[0].source, "CACHED")
        self.assertEqual(first_records[0].artifact.id, second_records[0].artifact.id)
        self.assertEqual(second_records[0].node_id, "producer")
        self.assertEqual(second_records[0].output_port, "file")
        self.assertTrue(validate_artifact_record(second_records[0]).strongly_valid)

    def test_nested_artifacts_are_bound_to_output_port_and_value_path(self) -> None:
        first_path = self.root / "first.bin"
        second_path = self.root / "second.bin"
        first_path.write_bytes(b"first")
        second_path.write_bytes(b"second")
        first = Artifact.create(type=DataType.FILE, uri=first_path.resolve().as_uri())
        second = Artifact.create(type=DataType.FILE, uri=second_path.resolve().as_uri())

        with SQLiteArtifactRegistry(self.database) as registry:
            records = registry.observe_outputs(
                run_id="run",
                node_id="node",
                outputs={"parts": [{"artifact": first}, {"artifact": second}]},
                source="EXECUTED",
            )

        self.assertEqual(len(records), 2)
        self.assertEqual({record.output_port for record in records}, {"parts"})
        self.assertEqual(
            {record.value_path for record in records},
            {"$[0].artifact", "$[1].artifact"},
        )

    def test_external_file_mutation_changes_current_validity_without_erasing_history(self) -> None:
        path = self.root / "mutable.bin"
        path.write_bytes(b"before")
        artifact = Artifact.create(type=DataType.FILE, uri=path.resolve().as_uri())
        with SQLiteArtifactRegistry(self.database) as registry:
            record = registry.observe_outputs(
                run_id="run",
                node_id="node",
                outputs={"file": artifact},
                source="EXECUTED",
            )[0]
            self.assertTrue(validate_artifact_record(record).strongly_valid)
            path.write_bytes(b"after-longer")
            validation = validate_artifact_record(record)
            self.assertFalse(validation.strongly_valid)
            self.assertEqual(validation.reason, "size-changed")
            persisted = registry.list_for_artifact(artifact.id)
            self.assertEqual(len(persisted), 1)
            self.assertEqual(persisted[0].snapshot.sha256, record.snapshot.sha256)

    def test_unsupported_artifact_is_recorded_without_claiming_strong_validity(self) -> None:
        artifact = Artifact(
            id="remote-artifact",
            type=DataType.FILE,
            uri="https://example.test/file.bin",
        )
        with SQLiteArtifactRegistry(self.database) as registry:
            record = registry.observe_outputs(
                run_id="run",
                node_id="node",
                outputs={"file": artifact},
                source="EXECUTED",
            )[0]

        self.assertIsNone(record.snapshot)
        validation = validate_artifact_record(record)
        self.assertIsNone(validation.strongly_valid)
        self.assertIn("UnsupportedArtifactError", validation.reason)


if __name__ == "__main__":
    unittest.main()
