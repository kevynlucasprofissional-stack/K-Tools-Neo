import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { EventEmitter } from 'node:events';
import { RunnerLogger } from '../src/logger.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { IntegratedRunDiagnostics, installFatalDiagnosticHandlers } from '../src/integrated-diagnostics.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-final-consistency-'));}
async function events(file){return (await fs.readFile(file,'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);}

async function assertReportMatchesTimeline(diag){
  const report=JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8'));
  const timeline=await events(diag.eventPath);
  assert.equal(report.eventSummary.count,timeline.length);
  assert.deepEqual(report.eventSummary.byEvent, timeline.reduce((out,e)=>{const key=String(e.event||'UNKNOWN');out[key]=(out[key]||0)+1;return out;},{}));
  assert.equal(timeline.at(-1)?.event,'RUN_FINALIZED');
  assert.equal(report.eventSummary.byEvent.RUN_FINALIZED,1);
  return {report,timeline};
}

test('normal finalization report exactly matches the completed event timeline',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'probe',runId:'normal-final'});await diag.start({logger:new RunnerLogger()});
  await diag.phase('COMMAND','PASS');await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});await assertReportMatchesTimeline(diag);
});

test('error finalization report exactly matches the completed event timeline',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'download',runId:'error-final'});await diag.start({logger:new RunnerLogger()});
  const error=Object.assign(new Error('boom'),{code:'TEST_FAILURE'});await diag.finalize({status:'ERROR',ok:false,exitCode:2,error});
  const {report}=await assertReportMatchesTimeline(diag);assert.equal(report.errors.at(-1).error.code,'TEST_FAILURE');
});

test('fatal handler finalization report exactly matches the completed event timeline before exit',async()=>{
  const root=await tmp();const fake=new EventEmitter();fake.pid=1234;fake.version='v24-test';fake.platform='win32';fake.arch='x64';fake.cwd=()=>root;
  const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'range',runId:'fatal-final',processRef:fake,env:{}});await diag.start({logger:new RunnerLogger()});
  let resolveExit;const exited=new Promise(resolve=>{resolveExit=resolve;});const uninstall=installFatalDiagnosticHandlers({diagnostics:diag,processRef:fake,exitFn:()=>resolveExit()});
  fake.emit('uncaughtException',Object.assign(new Error('fatal'),{code:'FATAL_TEST'}));await exited;uninstall();
  const {report}=await assertReportMatchesTimeline(diag);assert.equal(report.outcome.status,'UNCAUGHT_EXCEPTION');
});

test('idempotent finalization adds one and only one RUN_FINALIZED event',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'status',runId:'idempotent-final'});await diag.start({logger:new RunnerLogger()});
  await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});await diag.finalize({status:'ERROR',ok:false,exitCode:2});
  const {report,timeline}=await assertReportMatchesTimeline(diag);assert.equal(report.outcome.status,'COMPLETE');assert.equal(timeline.filter(e=>e.event==='RUN_FINALIZED').length,1);
});
