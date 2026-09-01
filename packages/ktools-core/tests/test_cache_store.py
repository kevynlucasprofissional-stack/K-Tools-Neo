from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.cache_store import (
    CacheError,
    CacheSerializationUnsupported,
    SQLiteNodeCache,
    validate_cache_entry,
)
from ktools_core.models import Artifact, DataType


class SQLiteNodeCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.database = self.root / "cache.sqlite3"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_entry_survives_close_reopen_and_preserves_provenance(self) -> None:
        with SQLiteNodeCache(self.database) as cache:
            cache.put(
                signature="abc123",
                node_type="text.concat",
                node_version="1",
                origin_run_id="run_original",
                origin_node_id="join",
                outputs={"text": "K-Tools Neo", "meta": {"count": 2}},
            )

        with SQLiteNodeCache(self.database) as cache:
            entry = cache.get("abc123")
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.node_type, "text.concat")
            self.assertEqual(entry.node_version, "1")
            self.assertEqual(entry.origin_run_id, "run_original")
            self.assertEqual(entry.origin_node_id, "join")
            self.assertEqual(entry.outputs["text"], "K-Tools Neo")
            self.assertEqual(entry.outputs["meta"], {"count": 2})
            self.assertTrue(validate_cache_entry(entry).valid)

            self.assertIsNone(entry.last_used_at)
            cache.mark_used("abc123")
            used = cache.get("abc123")
            self.assertIsNotNone(used)
            assert used is not None
            self.assertIsNotNone(used.last_used_at)

    def test_user_json_cannot_collide_with_internal_cache_envelopes(self) -> None:
        payload = {
            "__ktoolsCacheEnvelope__": "artifact",
            "value": {
                "id": "this-is-user-json-not-an-artifact",
                "type": "file",
            },
        }
        with SQLiteNodeCache(self.database) as cache:
            cache.put(
                signature="marker-collision",
                node_type="test.json",
                node_version="1",
                origin_run_id="run",
                origin_node_id="node",
                outputs={"payload": payload},
            )
            entry = cache.get("marker-collision")
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry.outputs["payload"], payload)
            self.assertNotIsInstance(entry.outputs["payload"], Artifact)

    def test_file_artifact_output_is_rehydrated_and_strongly_revalidated(self) -> None:
        output = self.root / "result.bin"
        output.write_bytes(b"artifact-result")
        artifact = Artifact.create(
            type=DataType.FILE,
            uri=output.resolve().as_uri(),
            produced_by="run_original/node_original",
        )

        with SQLiteNodeCache(self.database) as cache:
            cache.put(
                signature="artifact-signature",
                node_type="test.file-transform",
                node_version="1",
                origin_run_id="run_original",
                origin_node_id="node_original",
                outputs={"file": artifact},
            )

        with SQLiteNodeCache(self.database) as cache:
            entry = cache.get("artifact-signature")
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertIsInstance(entry.outputs["file"], Artifact)
            self.assertEqual(entry.outputs["file"].uri, artifact.uri)
            self.assertEqual(len(entry.artifact_snapshots), 1)
            self.assertTrue(validate_cache_entry(entry).valid)

            output.unlink()
            validation = validate_cache_entry(entry)
            self.assertFalse(validation.valid)
            self.assertEqual(validation.reason, "artifact-invalid")
            self.assertEqual(validation.artifact_reason, "missing")

    def test_modified_artifact_invalidates_candidate(self) -> None:
        output = self.root / "modified.bin"
        output.write_bytes(b"before")
        artifact = Artifact.create(type=DataType.FILE, uri=output.resolve().as_uri())

        with SQLiteNodeCache(self.database) as cache:
            cache.put(
                signature="modified-signature",
                node_type="test.file-transform",
                node_version="1",
                origin_run_id="run_original",
                origin_node_id="node_original",
                outputs={"file": artifact},
            )
            entry = cache.get("modified-signature")
            assert entry is not None
            output.write_bytes(b"after-longer")
            validation = validate_cache_entry(entry)
            self.assertFalse(validation.valid)
            self.assertEqual(validation.artifact_reason, "size-changed")

    def test_opaque_and_raw_path_outputs_fail_closed(self) -> None:
        class Opaque:
            pass

        with SQLiteNodeCache(self.database) as cache:
            with self.assertRaises(CacheSerializationUnsupported):
                cache.put(
                    signature="opaque",
                    node_type="test.pure",
                    node_version="1",
                    origin_run_id="run",
                    origin_node_id="node",
                    outputs={"value": Opaque()},
                )

            with self.assertRaises(CacheSerializationUnsupported):
                cache.put(
                    signature="path",
                    node_type="test.pure",
                    node_version="1",
                    origin_run_id="run",
                    origin_node_id="node",
                    outputs={"value": self.root / "file.bin"},
                )

    def test_sqlite_runtime_error_is_wrapped_as_cache_error(self) -> None:
        cache = SQLiteNodeCache(self.database)
        cache.close()
        with self.assertRaises(CacheError):
            cache.get("anything")

    def test_invalidate_removes_entry(self) -> None:
        with SQLiteNodeCache(self.database) as cache:
            cache.put(
                signature="remove-me",
                node_type="text.literal",
                node_version="1",
                origin_run_id="run",
                origin_node_id="node",
                outputs={"text": "hello"},
            )
            self.assertIsNotNone(cache.get("remove-me"))
            cache.invalidate("remove-me")
            self.assertIsNone(cache.get("remove-me"))


if __name__ == "__main__":
    unittest.main()
