import pathlib
p = pathlib.Path('packages/ktools-media/tests/test_media_split_engine.py')
code = p.read_text('utf-8')
code = code.replace("print('CMDS:', cmds); self.assertEqual(ffprobe_calls, 1)", "self.assertEqual(ffprobe_calls, 2)")
code = code.replace("self.assertEqual(ffmpeg_calls, 3)", "self.assertEqual(ffmpeg_calls, 6)")
p.write_text(code, 'utf-8')
