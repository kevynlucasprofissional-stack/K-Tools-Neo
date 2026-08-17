import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { StateStore } from '../src/state.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-fail-soft-'));}

async function blocker(root,name='blocked'){
  const file=path.join(root,name);await fs.writeFile(file,'not-a-directory');return file;
}

test('diagnostic logger filesystem failure is fail-soft and remains observable in memory/fallback sink',async()=>{
  const root=await tmp();const blocked=await blocker(root);const fallback=[];
  const logger=new RunnerLogger({
    logFile:path.join(blocked,'runner.log'),
    eventFile:path.join(blocked,'events.jsonl'),
    runId:'fail-soft-run',
    diagnosticFailureSink:entry=>fallback.push(entry),
  });
  await assert.doesNotReject(()=>logger.log('DOWNLOAD','healthy work should continue',{position:1}));
  const health=logger.diagnosticHealth();
  assert.equal(health.degraded,true);
  assert.ok(health.failures.length>=1);
  assert.ok(fallback.length>=1);
  assert.ok(health.failures.every(x=>x.code));
});

test('RunDiagnostics falls back when the configured diagnostic output root cannot be written',async()=>{
  const root=await tmp();const blocked=await blocker(root,'output-is-file');
  const diag=new RunDiagnostics({outputRoot:blocked,command:'download',runId:'fallback-run',env:{}});
  await assert.doesNotReject(()=>diag.start({logger:new RunnerLogger()}));
  const report=await diag.finalize({status:'COMPLETE',ok:true,exitCode:0,result:{status:'COMPLETE'}});
  assert.equal(report.outcome.status,'COMPLETE');
  assert.equal(report.diagnosticHealth.degraded,true);
  assert.equal(report.diagnosticHealth.primaryStorageAvailable,false);
  assert.ok(report.diagnosticHealth.fallbackStorageUsed || report.diagnosticHealth.memoryOnly);
});

test('functional state persistence remains fail-hard when its filesystem path is invalid',async()=>{
  const root=await tmp();const blocked=await blocker(root,'functional-output-is-file');
  const store=new StateStore({outputRoot:blocked,courseName:'Course',totalPositions:1});
  await assert.rejects(()=>store.initialize({resume:false,workPageUrl:'https://www.xcursos.com/curso/test/aula/1'}));
});
