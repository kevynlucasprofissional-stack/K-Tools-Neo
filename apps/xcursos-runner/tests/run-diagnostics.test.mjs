import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-'));}

test('RunDiagnostics writes shareable JSON and Markdown reports with event/artifact indexes',async()=>{
  const root=await tmp();let now=Date.parse('2026-08-16T21:00:00Z');const logger=new RunnerLogger();
  const diag=new RunDiagnostics({outputRoot:root,command:'download',argv:['--url','https://cdn.example/a.mp4?X-Amz-Signature=secret'],runId:'run-success',nowFn:()=>now,env:{}});
  await diag.start({logger,context:{mode:'test'}});diag.setContext({courseName:'Course A'});
  const statePath=path.join(root,'Course A','_xcursos-runner','state.json');await fs.mkdir(path.dirname(statePath),{recursive:true});await fs.writeFile(statePath,'{}\n');
  diag.attachCourseArtifacts({courseName:'Course A',metaDir:path.dirname(statePath),statePath});
  await diag.phase('BOOT','PASS',{total:3});now+=500;await logger.log('DOWNLOAD','lesson complete',{position:1});now+=500;
  const report=await diag.finalize({status:'COMPLETE',ok:true,exitCode:0,result:{status:'COMPLETE',audit:{total:3,processed:3,downloaded:2,alreadyPresent:0,noVideo:1,missingPositions:[],invalidFilePositions:[]}}});
  assert.equal(report.runId,'run-success');assert.equal(report.outcome.status,'COMPLETE');assert.equal(report.summary.audit.processed,3);assert.ok(report.eventSummary.count>=2);
  assert.equal(report.artifacts.find(x=>x.name==='state').exists,true);
  assert.doesNotMatch(JSON.stringify(report),/X-Amz-Signature=secret/);
  const markdown=await fs.readFile(diag.reportMarkdownPath,'utf8');assert.match(markdown,/Relatório de Diagnóstico/);assert.match(markdown,/Processados: 3 \/ 3/);
  assert.deepEqual(JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8')),report);
});

test('RunDiagnostics preserves fatal error/stack in sanitized report and records missing artifacts without failing finalization',async()=>{
  const root=await tmp();const logger=new RunnerLogger();const diag=new RunDiagnostics({outputRoot:root,command:'download',runId:'run-fail',env:{XCURSOS_POWERSHELL_TRANSCRIPT:path.join(root,'missing-transcript.txt')}});
  await diag.start({logger});diag.addArtifact('missingFile',path.join(root,'missing.json'));
  const error=Object.assign(new Error('request failed token=secret-value https://cdn.example/a.mp4?X-Amz-Signature=abc'),{code:'NETWORK_RESET',details:{authorization:'Bearer nope'}});
  const report=await diag.finalize({status:'ERROR',ok:false,exitCode:2,error});
  assert.equal(report.errors.length,1);assert.equal(report.errors[0].fatal,true);assert.equal(report.errors[0].error.code,'NETWORK_RESET');
  assert.equal(report.artifacts.find(x=>x.name==='missingFile').exists,false);assert.equal(report.artifacts.find(x=>x.name==='powershellTranscript').exists,false);
  assert.doesNotMatch(JSON.stringify(report),/secret-value|X-Amz-Signature=abc|Bearer nope/);
});

test('RunDiagnostics finalization is idempotent and does not overwrite the first outcome',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'probe',runId:'run-idempotent'});await diag.start();
  const first=await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});const second=await diag.finalize({status:'ERROR',ok:false,exitCode:2});
  assert.equal(first.outcome.status,'COMPLETE');assert.equal(second.outcome.status,'COMPLETE');
});
