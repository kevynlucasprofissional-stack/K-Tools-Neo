from __future__ import annotations

import inspect
import unittest

from ktools_core import builtin


class FileLiteralOwnershipTests(unittest.TestCase):
    def test_single_and_multi_file_literals_share_local_artifact_owner(self) -> None:
        single = inspect.getsource(builtin._file_literal)
        multiple = inspect.getsource(builtin._files_literal)

        self.assertIn("_local_file_artifact", single)
        self.assertIn("_local_file_artifact", multiple)
        self.assertNotIn("Artifact.create", single)
        self.assertNotIn("Artifact.create", multiple)


if __name__ == "__main__":
    unittest.main()
