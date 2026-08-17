import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';

async function text(file){try{return await fs.readFile(file,'utf8');}catch{return'';}}

test('CI preserves Linux and adds a real Windows diagnostic validation lane',async()=>{
  const yaml=await text('.github/workflows/ci.yml');
  assert.match(yaml,/ubuntu-latest/);
  assert.match(yaml,/windows-latest/);
  assert.match(yaml,/node-version:\s*24/);
  assert.match(yaml,/npm\s+(?:run\s+check|test)/);
  assert.match(yaml,/shell:\s*powershell/i);
  assert.match(yaml,/PSVersionTable\.PSVersion\.Major/);
  assert.match(yaml,/diagnostics-check/);
  assert.match(yaml,/LOCALAPPDATA/);
  assert.match(yaml,/Start-Transcript/);
  assert.match(yaml,/Área Diagnóstico com espaços/);
  assert.match(yaml,/ConvertFrom-Json/);
});

test('Windows operational smoke-test procedure is versioned and separates CI from authenticated smoke',async()=>{
  const doc=await text('docs/diagnostics-smoke-test-windows.md');
  assert.match(doc,/Validação automatizada/i);
  assert.match(doc,/Smoke test operacional/i);
  for(const command of ['xcursos diagnostics-check','xcursos doctor','xcursos login','xcursos probe --json','xcursos current --json'])assert.ok(doc.includes(command),command);
  assert.match(doc,/diagnostic-report\.json/);
  assert.match(doc,/events\.jsonl/);
  assert.match(doc,/run-meta\.json/);
  assert.match(doc,/liveness\.json/);
  assert.match(doc,/xcursos-all-.*\.log/);
  assert.match(doc,/não.*credenciais|sem.*credenciais/i);
});
