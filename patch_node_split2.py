import pathlib
p = pathlib.Path('packages/ktools-media/src/ktools_media/node.py')
code = p.read_text('utf-8')
lines = code.splitlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('    out_artifact = Artifact.create('):
        skip = True
    if skip:
        if line.startswith('    pass'):
            skip = False
            new_lines.append('    return {"pieces": pieces_artifacts}')
        continue
    new_lines.append(line)

p.write_text('\n'.join(new_lines) + '\n', 'utf-8')
