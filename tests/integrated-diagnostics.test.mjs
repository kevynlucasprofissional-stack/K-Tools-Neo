import test from 'node:test';
import assert from 'node:assert/strict';
import { EventEmitter } from 'node:events';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { IntegratedRunDiagnostics, installFatalDiagnosticHandlers } from '../src/integrated-diagnostics.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-int-diag-'));}

test('IntegratedRunDiagnostics reconstructs work items and persisted errors created during this run only',async()=>{
  const root=await tmp();let now=Date.parse('2026-08-16T21:00:00Z');const logger=new RunnerLogger();const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'download',runId:'int-run',nowFn:()=>now,env:{}});await diag.start({logger});
  const meta=path.join(root,'Course','_xcursos-runner');await fs.mkdir(meta,{recursive:true});
  const manifest=path.join(meta,'manifest.jsonl'),errors=path.join(meta,'errors.jsonl');
  await fs.writeFile(manifest,`${JSON.stringify({position:1,status:'DOWNLOADED',attempts:1,lessonTitle:'Old',moduleName:'M',timestamp:'2026-08-16T20:59:00Z'})}\n${JSON.stringify({position:2,status:'DOWNLOADED',attempts:2,lessonTitle:'New',moduleName:'M',timestamp:'2026-08-16T21:00:01Z',validation:{duration:60,codec:'h264',size:10,downloadMethod:'XCURSOS_NATIVE'}})}\n`);
  await fs.writeFile(errors,`${JSON.stringify({scope:'DOWNLOAD',position:2,status:'RETRY_LATER',failureCode:'NETWORK_RESET',message:'temporary',timestamp:'2026-08-16T21:00:00.500Z'})}\n`);
  diag.attachCourseArtifacts({courseName:'Course',metaDir:meta,manifestPath:manifest,errorsPath:errors});now+=2000;
  const report=await diag.finalize({status:'RANGE_COMPLETE',ok:true,exitCode:0,result:{status:'RANGE_COMPLETE',audit:{total:2,processed:2,downloaded:2,missingPositions:[],invalidFilePositions:[]}}});
  assert.equal(report.summary.currentRunWorkItemCount,1);assert.equal(report.summary.currentRunWorkItems[0].position,2);assert.equal(report.summary.currentRunWorkItems[0].validation.downloadMethod,'XCURSOS_NATIVE');
  assert.equal(report.summary.persistedErrorCount,1);assert.equal(report.summary.persistedErrors[0].code,'NETWORK_RESET');
  const md=await fs.readFile(diag.reportMarkdownPath,'utf8');assert.match(md,/Reconstrução desta execução/);assert.match(md,/\| 2 \| DOWNLOADED \| 2 \| New \| M \|/);
});

test('fatal diagnostic handlers flush uncaught exception report before requesting process exit',async()=>{
  const root=await tmp();const fakeProcess=new EventEmitter();fakeProcess.pid=123;fakeProcess.version='v24-test';fakeProcess.platform='win32';fakeProcess.arch='x64';fakeProcess.cwd=()=>root;
  const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'download',runId:'fatal-run',processRef:fakeProcess,env:{}});await diag.start({logger:new RunnerLogger()});
  let exitCode=null;let resolveExit;const exited=new Promise(resolve=>{resolveExit=resolve;});const uninstall=installFatalDiagnosticHandlers({diagnostics:diag,processRef:fakeProcess,exitFn:code=>{exitCode=code;resolveExit();}});
  const error=Object.assign(new Error('unexpected crash'),{code:'BOOM'});fakeProcess.emit('uncaughtException',error);await exited;uninstall();
  assert.equal(exitCode,1);const report=JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8'));assert.equal(report.outcome.status,'UNCAUGHT_EXCEPTION');assert.equal(report.errors[0].error.code,'BOOM');assert.match(report.errors[0].error.stack,/unexpected crash/);
});

test('fatal diagnostic handlers capture unhandled rejection values',async()=>{
  const root=await tmp();const fakeProcess=new EventEmitter();fakeProcess.pid=456;fakeProcess.version='v24-test';fakeProcess.platform='win32';fakeProcess.arch='x64';fakeProcess.cwd=()=>root;
  const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'range',runId:'rejection-run',processRef:fakeProcess,env:{}});await diag.start({logger:new RunnerLogger()});
  let resolveExit;const exited=new Promise(resolve=>{resolveExit=resolve;});const uninstall=installFatalDiagnosticHandlers({diagnostics:diag,processRef:fakeProcess,exitFn:()=>resolveExit()});fakeProcess.emit('unhandledRejection','promise exploded');await exited;uninstall();
  const report=JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8'));assert.equal(report.outcome.status,'UNHANDLED_REJECTION');assert.match(report.errors[0].error.message,/promise exploded/);
});
