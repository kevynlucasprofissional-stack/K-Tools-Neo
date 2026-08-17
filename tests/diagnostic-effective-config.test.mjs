import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as cliDiagnostics from '../src/cli-diagnostics.mjs';
import { DEFAULT_LIMITS } from '../src/constants.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-config-'));}

test('effective diagnostic configuration contains actual safe runtime and limit overrides only',()=>{
  assert.equal(typeof cliDiagnostics.buildEffectiveDiagnosticConfig,'function');
  const root='C:\\Users\\Pessoa\\Downloads\\Cursos';
  const snapshot=cliDiagnostics.buildEffectiveDiagnosticConfig({
    runtime:{resume:false,cdpEndpoint:'http://127.0.0.1:9333',outputRoot:root,profileDir:'C:\\Profile',chromePath:'C:\\Chrome\\chrome.exe',startUrl:'https://www.xcursos.com/aula/1?token=SECRET',lastLessonUrl:'https://www.xcursos.com/aula/2?token=SECRET'},
    limits:{...DEFAULT_LIMITS,downloadRetries:7,mediaReadyTimeoutMs:9999,authorization:'Bearer SECRET',token:'SECRET'},
  });
  assert.equal(snapshot.runtime.resume,false);assert.equal(snapshot.runtime.cdpEndpoint,'http://127.0.0.1:9333');assert.equal(snapshot.runtime.outputRoot,root);
  assert.equal(snapshot.limits.downloadRetries,7);assert.equal(snapshot.limits.mediaReadyTimeoutMs,9999);
  assert.equal('startUrl' in snapshot.runtime,false);assert.equal('lastLessonUrl' in snapshot.runtime,false);assert.equal('authorization' in snapshot.limits,false);assert.equal('token' in snapshot.limits,false);
  assert.doesNotMatch(JSON.stringify(snapshot),/SECRET/);
});

test('diagnostic report and metadata persist one sanitized effective configuration snapshot',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'download',runId:'effective-config',env:{}});await diag.start({logger:new RunnerLogger()});
  assert.equal(typeof diag.setConfiguration,'function');
  diag.setConfiguration({runtime:{resume:true,cdpEndpoint:'http://127.0.0.1:9222',outputRoot:root},limits:{downloadRetries:4,navigationRetries:2,secret:'do-not-store'}});
  await diag.phase('COMMAND','START');await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});
  const report=JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8'));const meta=JSON.parse(await fs.readFile(diag.metaPath,'utf8'));
  assert.deepEqual(meta.effectiveConfig,report.effectiveConfig);assert.equal(report.effectiveConfig.limits.downloadRetries,4);assert.equal(report.effectiveConfig.runtime.resume,true);
  assert.doesNotMatch(JSON.stringify(report.effectiveConfig),/do-not-store/);
});
