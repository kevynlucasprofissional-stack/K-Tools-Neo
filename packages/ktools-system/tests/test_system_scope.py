import unittest
from pathlib import Path
from ktools_system.models import CapabilityScope, ScopeViolationError, PolicyAction


class SystemScopeTests(unittest.TestCase):
    def test_scope_allowed_roots_validation(self):
        scope = CapabilityScope(
            allowed_roots=[Path("/safe/workspace").resolve()],
            allow_subprocess=False,
            allow_network=False,
            allow_destructive=False,
        )

        safe_path = Path("/safe/workspace/data.txt").resolve()
        unsafe_path = Path("/etc/passwd").resolve()

        self.assertTrue(scope.is_path_allowed(safe_path))
        self.assertFalse(scope.is_path_allowed(unsafe_path))

        with self.assertRaises(ScopeViolationError):
            scope.assert_path_allowed(unsafe_path)

    def test_scope_subprocess_assertion(self):
        scope = CapabilityScope(allow_subprocess=False)
        with self.assertRaises(ScopeViolationError):
            scope.assert_subprocess_allowed()

        permissive_scope = CapabilityScope(allow_subprocess=True)
        # Should not raise
        permissive_scope.assert_subprocess_allowed()

    def test_policy_action_classification(self):
        scope = CapabilityScope(allow_destructive=False)
        action = scope.classify_action("destructive_mutation")
        self.assertEqual(action, PolicyAction.REQUIRE_HUMAN_CONFIRMATION)


if __name__ == "__main__":
    unittest.main()
