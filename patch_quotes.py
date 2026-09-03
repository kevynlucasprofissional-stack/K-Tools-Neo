import pathlib
def fix_file(p_str):
    p = pathlib.Path(p_str)
    code = p.read_text('utf-8')
    code = code.replace('""\"', "'''")
    p.write_text(code, 'utf-8')

fix_file('packages/ktools-media/src/ktools_media/media_info.py')
fix_file('packages/ktools-media/src/ktools_media/audio/split.py')
