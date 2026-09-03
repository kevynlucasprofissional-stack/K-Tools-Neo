import pathlib
p = pathlib.Path('packages/ktools-media/tests/test_media_convert_behavior.py')
code = p.read_text('utf-8')
code = code.replace("            tmp_out.write_bytes(b\"converted\")", "            tmp_out.write_bytes(b\"converted\")\n            import subprocess\n            return subprocess.CompletedProcess(cmd, 0, \"\", \"\")")
p.write_text(code, 'utf-8')

p2 = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code2 = p2.read_text('utf-8')
code2 = code2.replace("out_artifact = Artifact(", "out_artifact = Artifact.create(")
p2.write_text(code2, 'utf-8')
