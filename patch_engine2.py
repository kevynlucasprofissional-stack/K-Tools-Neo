import pathlib
p = pathlib.Path('packages/ktools-core/src/ktools_core/engine.py')
code = p.read_text('utf-8')

original_def = "    def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:"
new_def = """    def execute(self, workflow: WorkflowDefinition) -> WorkflowResult:
        from .diagnostics import _ACTIVE_SESSION
        token = _ACTIVE_SESSION.set(self.diagnostics) if self.diagnostics else None
        try:
            return self._execute_inner(workflow)
        finally:
            if token:
                _ACTIVE_SESSION.reset(token)

    def _execute_inner(self, workflow: WorkflowDefinition) -> WorkflowResult:"""
    
code = code.replace(original_def, new_def)
p.write_text(code, 'utf-8')
