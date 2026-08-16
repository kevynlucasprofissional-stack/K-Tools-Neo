import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');

test('V4.2.4 RED: download-all detects repeated no-progress fingerprints and surfaces failure causes',async()=>{
  const ps=await fs.readFile(path.join(root,'download-all.ps1'),'utf8');
  assert.match(ps,/NoProgressLimit/);assert.match(ps,/stagnant|noProgress/i);assert.match(ps,/failureSummary/);assert.match(ps,/NO_PROGRESS|sem progresso/i);
});
