import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');

test('xcursos-all records a PowerShell transcript and exposes it to child diagnostic reports',async()=>{
  const script=await fs.readFile(path.join(root,'download-all.ps1'),'utf8');
  assert.match(script,/Start-Transcript\s+-Path\s+\$transcriptPath/);assert.match(script,/\$env:XCURSOS_POWERSHELL_TRANSCRIPT\s*=\s*\$transcriptPath/);assert.match(script,/Stop-Transcript/);assert.match(script,/Child diagnostic report:/);
  assert.equal([...script].every(ch=>ch.charCodeAt(0)<128),true,'download-all.ps1 must remain ASCII-only for Windows PowerShell 5.1');
});

test('xcursos-all transcript path is unique per process and stored outside course files',async()=>{
  const script=await fs.readFile(path.join(root,'download-all.ps1'),'utf8');
  assert.match(script,/XCursosRunner\\logs/);assert.match(script,/xcursos-all-\$transcriptStamp-\$PID\.log/);
});
