from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from ktools_core.cache_identity import (
    ArtifactSnapshotError,
    CacheSignatureUnsupported,
    UnsupportedArtifactError,
    build_cache_signature,
    snapshot_artifact,
    validate_artifact_snapshot,
)
from ktools_core.models import Artifact, CachePolicy, DataType, NodeDefinition


class ArtifactSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _artifact(self, path: Path, *, artifact_id: str = "artifact_random") -> Artifact:
        return Artifact(
            id=artifact_id,
            type=DataType.FILE,
            uri=path.resolve().as_uri(),
            produced_by="run_random/node_random",
        )

    def test_file_artifact_snapshot_hashes_and_validates_unchanged_content(self) -> None:
        path = self.root / "payload.bin"
        path.write_bytes(b"k-tools-cache")
        snapshot = snapshot_artifact(self._artifact(path))

        self.assertEqual(snapshot.size_bytes, len(b"k-tools-cache"))
        self.assertEqual(len(snapshot.sha256), 64)
        self.assertEqual(snapshot.content_identity["type"], "file")
        self.assertNotIn("artifact_random", str(snapshot.content_identity))
        self.assertNotIn("run_random", str(snapshot.content_identity))

        validation = validate_artifact_snapshot(snapshot)
        self.assertTrue(validation.valid)
        self.assertEqual(validation.reason, "valid")
        self.assertEqual(validation.current_sha256, snapshot.sha256)

    def test_deleted_file_invalidates_snapshot(self) -> None:
        path = self.root / "deleted.bin"
        path.write_bytes(b"abc")
        snapshot = snapshot_artifact(self._artifact(path))
        path.unlink()

        validation = validate_artifact_snapshot(snapshot)
        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "missing")

    def test_same_size_content_change_is_detected_even_when_mtime_is_restored(self) -> None:
        path = self.root / "same-size.bin"
        path.write_bytes(b"AAAA")
        snapshot = snapshot_artifact(self._artifact(path))

        path.write_bytes(b"BBBB")
        os.utime(path, ns=(snapshot.mtime_ns, snapshot.mtime_ns))
        self.assertEqual(path.stat().st_size, snapshot.size_bytes)
        self.assertEqual(path.stat().st_mtime_ns, snapshot.mtime_ns)

        validation = validate_artifact_snapshot(snapshot)
        self.assertFalse(validation.valid)
        self.assertEqual(validation.reason, "content-changed")
        self.assertNotEqual(validation.current_sha256, snapshot.sha256)

    def test_unsupported_uri_and_directory_fail_closed(self) -> None:
        with self.assertRaises(UnsupportedArtifactError):
            snapshot_artifact(
                Artifact(id="remote", type=DataType.FILE, uri="https://example.test/file.bin")
            )

        folder = self.root / "folder"
        folder.mkdir()
        with self.assertRaises(UnsupportedArtifactError):
            snapshot_artifact(
                Artifact(id="folder", type=DataType.FOLDER, uri=folder.resolve().as_uri())
            )

    def test_missing_file_cannot_be_snapshotted(self) -> None:
        with self.assertRaises(ArtifactSnapshotError):
            snapshot_artifact(self._artifact(self.root / "missing.bin"))


class CacheSignatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.definition = NodeDefinition(
            type_id="test.pure",
            title="Pure",
            version="1",
            cache_policy=CachePolicy.PURE,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _signature(self, *, definition: NodeDefinition | None = None, config=None, inputs=None) -> str:
        return build_cache_signature(
            definition or self.definition,
            config={} if config is None else config,
            inputs={} if inputs is None else inputs,
        )

    def test_node_definition_default_cache_policy_is_never(self) -> None:
        definition = NodeDefinition(type_id="test.default", title="Default")
        self.assertIs(definition.cache_policy, CachePolicy.NEVER)

    def test_signature_is_stable_for_equivalent_scalar_and_json_values(self) -> None:
        first = self._signature(
            config={"b": 2, "a": 1},
            inputs={"payload": {"z": [3, 2, 1], "ok": True}},
        )
        second = self._signature(
            config={"a": 1, "b": 2},
            inputs={"payload": {"ok": True, "z": [3, 2, 1]}},
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)

    def test_config_input_and_node_version_changes_change_signature(self) -> None:
        baseline = self._signature(config={"mode": "a"}, inputs={"value": 1})
        changed_config = self._signature(config={"mode": "b"}, inputs={"value": 1})
        changed_input = self._signature(config={"mode": "a"}, inputs={"value": 2})
        changed_version = self._signature(
            definition=NodeDefinition(
                type_id="test.pure",
                title="Pure",
                version="2",
                cache_policy=CachePolicy.PURE,
            ),
            config={"mode": "a"},
            inputs={"value": 1},
        )

        self.assertNotEqual(baseline, changed_config)
        self.assertNotEqual(baseline, changed_input)
        self.assertNotEqual(baseline, changed_version)

    def test_artifact_signature_uses_content_identity_not_random_artifact_id(self) -> None:
        path = self.root / "artifact.bin"
        path.write_bytes(b"same-content")
        first = Artifact(
            id="artifact_first_random",
            type=DataType.FILE,
            uri=path.resolve().as_uri(),
            produced_by="run_one/node_a",
        )
        second = Artifact(
            id="artifact_second_random",
            type=DataType.FILE,
            uri=path.resolve().as_uri(),
            produced_by="run_two/node_b",
        )

        before_first = self._signature(inputs={"file": first})
        before_second = self._signature(inputs={"file": second})
        self.assertEqual(before_first, before_second)

        path.write_bytes(b"different-content")
        after_change = self._signature(inputs={"file": second})
        self.assertNotEqual(before_first, after_change)

    def test_never_policy_and_opaque_values_fail_closed(self) -> None:
        with self.assertRaises(CacheSignatureUnsupported):
            build_cache_signature(
                NodeDefinition(type_id="test.never", title="Never"),
                config={},
                inputs={},
            )

        class Opaque:
            pass

        with self.assertRaises(CacheSignatureUnsupported):
            self._signature(inputs={"opaque": Opaque()})


if __name__ == "__main__":
    unittest.main()
