import pathlib
p = pathlib.Path('packages/ktools-media/tests/test_media_split_engine.py')
code = p.read_text('utf-8')
code = code.replace("from ktools_core.local_files import file_uri_from_path", "")
p.write_text(code, 'utf-8')
