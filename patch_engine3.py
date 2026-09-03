import pathlib
p = pathlib.Path('packages/ktools-core/src/ktools_core/engine.py')
code = p.read_text('utf-8')
lines = code.splitlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith('    def _execute_inner'):
        new_lines.append(line)
        skip = True
        continue
    if skip:
        if 'order = self.validate' in line:
            skip = False
            new_lines.append(line)
        continue
    new_lines.append(line)

p.write_text('\n'.join(new_lines) + '\n', 'utf-8')
