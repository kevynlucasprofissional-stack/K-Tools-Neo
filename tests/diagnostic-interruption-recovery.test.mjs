import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as recoveryModule from '../src/diagnostic-recovery.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-interrupted-run-'));}
async function seedRun(root,{runId='old-run',pid=4242,hostname=os.hostname(),startedAt='2026-08-16T20:00:00.000Z',events=[]}={}){
  const dir=path.join(root,'_xcursos-diagnostics',runId);await fs.mkdir(dir,{recursive:true});
  await fs.writeFile(path.join(dir,'run-meta.json'),JSON.stringify({schemaVersion:1,runId,command:'download',startedAt,process:{pid,hostname,nodeVersion:'v24',platform:'win32',arch:'x64'},context:{courseName:'Curso X'}}));
  await fs.writeFile(path.join(dir,'events.jsonl'),events.map(x=>JSON.stringify({runId,...x})).join('\n')+'\n');return dir;
}

test('dead same-host run without final report is reconstructed as INTERRUPTED on next startup',async()=>{
  assert.equal(typeof recoveryModule.recoverInterruptedDiagnosticRuns,'function');
  const root=await tmp();const dir=await seedRun(root,{events:[
    {timestamp:'2026-08-16T20:00:01.000Z',sequence:1,level:'INFO',scope:'DIAGNOSTIC',event:'RUN_STARTED',message:'start',context:{position:7}},
    {timestamp:'2026-08-16T20:00:05.000Z',sequence:2,level:'INFO',scope:'DOWNLOAD',event:'SUBPROCESS_START',message:'yt-dlp',context:{position:7},data:{pid:999}},
    {timestamp:'2026-08-16T20:00:10.000Z',sequence:3,level:'INFO',scope:'RUNNER',event:'INSPECT',message:'last progress',context:{position:7}},
  ]});
  const result=await recoveryModule.recoverInterruptedDiagnosticRuns({outputRoot:root,nowFn:()=>Date.parse('2026-08-16T21:00:00Z'),isPidAlive:()=>false,hostname:os.hostname()});
  assert.equal(result.recovered.length,1);const report=JSON.parse(await fs.readFile(path.join(dir,'recovered-diagnostic-report.json'),'utf8'));
  assert.equal(report.outcome.status,'INTERRUPTED');assert.equal(report.runId,'old-run');assert.equal(report.recovery.lastPosition,7);assert.equal(report.recovery.lastEvent.event,'INSPECT');assert.equal(report.timeline.totalEvents,3);
});

test('live same-host PID is never misclassified as interrupted',async()=>{
  const root=await tmp();const dir=await seedRun(root,{runId:'still-live',pid:555,events:[{timestamp:'2026-08-16T20:00:01Z',sequence:1,level:'INFO',scope:'DIAGNOSTIC',event:'RUN_STARTED',message:'start'}]});
  const result=await recoveryModule.recoverInterruptedDiagnosticRuns({outputRoot:root,nowFn:()=>Date.parse('2026-08-16T21:00:00Z'),isPidAlive:pid=>pid===555,hostname:os.hostname()});
  assert.equal(result.recovered.length,0);assert.equal(result.active.length,1);await assert.rejects(()=>fs.access(path.join(dir,'recovered-diagnostic-report.json')));
});

test('completed run is ignored even if its old PID is dead',async()=>{
  const root=await tmp();const dir=await seedRun(root,{runId:'done',events:[{timestamp:'2026-08-16T20:00:01Z',sequence:1,level:'INFO',scope:'DIAGNOSTIC',event:'RUN_STARTED',message:'start'}]});
  await fs.writeFile(path.join(dir,'diagnostic-report.json'),JSON.stringify({runId:'done',outcome:{status:'COMPLETE',ok:true}}));
  const result=await recoveryModule.recoverInterruptedDiagnosticRuns({outputRoot:root,isPidAlive:()=>false,hostname:os.hostname()});assert.equal(result.recovered.length,0);assert.equal(result.completed.length,1);
});
