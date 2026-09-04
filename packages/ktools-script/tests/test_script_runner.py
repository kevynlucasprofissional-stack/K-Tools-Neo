import unittest
import tempfile
from pathlib import Path
from ktools_script.runner import run_python_script


class ScriptRunnerTests(unittest.TestCase):
    def test_run_inline_code_success(self):
        code = """
print("Executando dentro do K-Tools!")
result = data * 2
outputs["result"] = result
"""
        res = run_python_script(code=code, inputs={"data": 21})
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(res.result, 42)
        self.assertIn("Executando dentro do K-Tools!", res.stdout)
        self.assertEqual(res.stderr, "")

    def test_run_inline_code_syntax_error(self):
        code = "def syntax_error(:"
        res = run_python_script(code=code)
        self.assertEqual(res.exit_code, 1)
        self.assertIn("SyntaxError", res.stderr)

    def test_run_external_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            script_file = Path(tmp_dir) / "custom_tool.py"
            script_file.write_text(
                "print('Hello from file')\nresult = 'file_ok'\noutputs['result'] = result\n",
                encoding="utf-8",
            )
            res = run_python_script(file_path=script_file)
            self.assertEqual(res.exit_code, 0)
            self.assertEqual(res.result, "file_ok")
            self.assertIn("Hello from file", res.stdout)


if __name__ == "__main__":
    unittest.main()
