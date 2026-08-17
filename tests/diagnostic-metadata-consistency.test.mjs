import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { IntegratedRunDiagnostics } from '../src/integrated-diagnostics.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-meta-'));}
async function readJson(file){return JSON.parse(await fs.readFile(file,'utf8'));}
async function readEvents(file){return (await fs.readFile(file,'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);}

test('run-meta, final report and terminal event converge on the effective execution context',async()=>{
  const root=await tmp();const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'range',runId:'meta-effective',env:{}});await diag.start({logger:new RunnerLogger(),context:{command:'range'}});
  diag.setContext({resume:false,cdpEndpoint:'http://127.0.0.1:9333',outputRoot:root});
  await diag.phase('COMMAND','START');
  const courseRoot=path.join(root,'Curso Teste');diag.attachCourseArtifacts({courseName:'Curso Teste',metaDir:path.join(courseRoot,'_xcursos-runner')});diag.setContext({courseRoot});
  await diag.finalize({status:'RANGE_COMPLETE',ok:true,exitCode:0,result:{status:'RANGE_COMPLETE'}});
  const meta=await readJson(diag.metaPath);const report=await readJson(diag.reportJsonPath);const timeline=await readEvents(diag.eventPath);const terminal=timeline.findLast(e=>e.event==='RUN_FINALIZED');
  assert.deepEqual(meta.context,report.context);
  assert.deepEqual(terminal.context,report.context);
  assert.equal(meta.context.resume,false);assert.equal(meta.context.courseName,'Curso Teste');assert.equal(meta.context.courseRoot,courseRoot);
});

test('metadata is synchronized at an awaited phase boundary without excessive writes being required by callers',async()=>{
  const root=await tmp();const diag=new IntegratedRunDiagnostics({outputRoot:root,command:'download',runId:'meta-phase',env:{}});await diag.start({logger:new RunnerLogger()});
  diag.setContext({resume:true,cdpEndpoint:'http://127.0.0.1:9222',outputRoot:root});await diag.phase('COMMAND','START');
  const meta=await readJson(diag.metaPath);assert.equal(meta.context.resume,true);assert.equal(meta.context.cdpEndpoint,'http://127.0.0.1:9222');assert.equal(meta.context.outputRoot,root);
  await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});
});
