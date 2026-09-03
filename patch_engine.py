import pathlib
p = pathlib.Path('packages/ktools-core/src/ktools_core/engine.py')
code = p.read_text('utf-8')
lines = code.splitlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.startswith('    def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:'):
        start_idx = i
        break

new_lines = lines[:start_idx + 1]
new_lines.extend([
    '        from .diagnostics import _ACTIVE_SESSION',
    '        token = _ACTIVE_SESSION.set(self.diagnostics) if self.diagnostics else None',
    '        try:'
])

found_return = False
for i in range(start_idx+1, len(lines)):
    line = lines[i]
    if line.startswith('        from .diagnostics import _ACTIVE_SESSION'):
        continue
    if line.startswith('        _ACTIVE_SESSION.set(self.diagnostics)'):
        continue
        
    if not found_return:
        if line == '        return WorkflowResult(':
            new_lines.append('            return WorkflowResult(')
        elif line == '            run_id=run_id,':
            new_lines.append('                run_id=run_id,')
        elif line == '            workflow_id=workflow.id,':
            new_lines.append('                workflow_id=workflow.id,')
        elif line == '            node_outputs=outputs_by_node,':
            new_lines.append('                node_outputs=outputs_by_node,')
        elif line == '        )':
            new_lines.append('            )')
            new_lines.append('        finally:')
            new_lines.append('            if token:')
            new_lines.append('                _ACTIVE_SESSION.reset(token)')
            found_return = True
        else:
            new_lines.append('    ' + line if line else '')
    else:
        new_lines.append(line)

p.write_text('\n'.join(new_lines) + '\n', 'utf-8')
