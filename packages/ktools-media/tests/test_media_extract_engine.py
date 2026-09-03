from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ktools_core.artifact_registry import SQLiteArtifactRegistry
from ktools_core.engine import WorkflowEngine
from ktools_core.models import DataType, WorkflowDefinition, WorkflowNode, WorkflowEdge, Artifact
from ktools_core.registry import NodeRegistry
from ktools_core.sqlite_journal import SQLiteRunJournal
from ktools_core.builtin import register_builtin_nodes

from ktools_media.node import register_nodes
from ktools_media.ffmpeg import get_ffmpeg_exe


class MediaExtractEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.db_path = self.root / "cache.sqlite"
        self.registry = NodeRegistry()
        register_builtin_nodes(self.registry)
        register_nodes(self.registry)
        
        self.run_journal = SQLiteRunJournal(str(self.db_path))
        self.artifact_registry = SQLiteArtifactRegistry(str(self.db_path))
        from ktools_core.diagnostics import DiagnosticsSession
        self.diagnostics = DiagnosticsSession(root=str(self.root / "diag"))
        
        self.engine = WorkflowEngine(
            registry=self.registry,
            journal=self.run_journal,
            artifact_registry=self.artifact_registry,
            diagnostics=self.diagnostics
        )

        self.video_path = self.root / "synthetic_test_video.mp4"
        self._create_synthetic_video()

    def tearDown(self) -> None:
        self.artifact_registry.close()
        self.run_journal.close()
        self.temp.cleanup()

    def _create_synthetic_video(self) -> None:
        import subprocess
        exe = get_ffmpeg_exe()
        cmd = [
            exe,
            "-y",
            "-f", "lavfi", "-i", "color=c=black:s=128x128:d=1",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(self.video_path)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def test_workflow_execution_and_diagnostics(self) -> None:
        video_artifact = Artifact.create(
            type=DataType.FILE,
            uri=self.video_path.as_uri()
        )

        workflow = WorkflowDefinition(
            id="test-media-workflow",
            nodes=(
                WorkflowNode(id="n0", type="file.literal", config={"path": str(self.video_path)}),
                WorkflowNode(id="n1", type="media.extract_audio", config={"format": "wav"}),
            ),
            edges=(
                WorkflowEdge(source_node="n0", source_port="file", target_node="n1", target_port="video"),
            )
        )
        
        result = self.engine.execute(workflow)
        
        self.assertIn("n1", result.node_outputs)
        audio_out = result.node_outputs["n1"]["audio"]
        self.assertEqual(audio_out.type, DataType.AUDIO)
        
        # Verify artifact is snapshotted
        records = self.artifact_registry.list_for_artifact(audio_out.id)
        self.assertGreater(len(records), 0)
        self.assertIsNotNone(records[0].snapshot)

        # Verify subprocess diagnostics exist
        events = self.diagnostics.events
        subproc_events = [e for e in events if e.kind == "SUBPROCESS"]
        self.assertGreater(len(subproc_events), 0, "No subprocess diagnostic events recorded")
        
        # Should have at least one ffprobe (detect stream) and one ffmpeg (extract)
        cmds = [e.context.get("command", []) for e in subproc_events]
        has_ffprobe = any("ffprobe" in c[0] for c in cmds if c)
        has_ffmpeg = any("ffmpeg" in c[0] for c in cmds if c)
        
        self.assertTrue(has_ffprobe, "Did not record ffprobe execution")
        self.assertTrue(has_ffmpeg, "Did not record ffmpeg execution")


if __name__ == "__main__":
    unittest.main()
