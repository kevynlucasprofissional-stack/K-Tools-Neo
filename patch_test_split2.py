import pathlib
p = pathlib.Path('packages/ktools-media/tests/test_media_split_engine.py')
code = p.read_text('utf-8')
code = code.replace("self.assertEqual(ffprobe_calls, 1)", "print('CMDS:', cmds); self.assertEqual(ffprobe_calls, 1)")
p.write_text(code, 'utf-8')
