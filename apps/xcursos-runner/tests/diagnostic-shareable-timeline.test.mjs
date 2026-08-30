import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as runDiagnosticsModule from '../src/run-diagnostics.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-shareable-timeline-'));}

test('bounded timeline preserves boundaries and critical evidence from a long run',()=>{
  assert.equal(typeof runDiagnosticsModule.buildBoundedTimeline,'function');
  const events=Array.from({length:1200},(_,i)=>({timestamp:new Date(i*1000).toISOString(),runId:'r',sequence:i+1,level:'INFO',scope:'RUNNER',event:'LOG',message:`event ${i}`}));
  events[0].event='RUN_STARTED';events[300]={...events[300],level:'WARN',event:'RETRY',message:'retry'};events[600]={...events[600],level:'ERROR',event:'SUBPROCESS_ERROR',message:'ffprobe failed'};events[900]={...events[900],event:'COMMIT',message:'position committed'};events[1199].event='RUN_FINALIZED';
  const timeline=runDiagnosticsModule.buildBoundedTimeline(events,{maxEvents:100});
  assert.equal(timeline.totalEvents,1200);assert.equal(timeline.truncated,true);assert.ok(timeline.events.length<=100);
  assert.equal(timeline.events[0].event,'RUN_STARTED');assert.equal(timeline.events.at(-1).event,'RUN_FINALIZED');
  for(const required of ['RETRY','SUBPROCESS_ERROR','COMMIT'])assert.ok(timeline.events.some(e=>e.event===required),required);
});

test('diagnostic-report.json embeds enough sanitized timeline evidence to share without events.jsonl',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'download',runId:'shareable',env:{}});const logger=new RunnerLogger();await diag.start({logger});
  await logger.log('INSPECT','position inspected',{position:4},{event:'INSPECT'});await logger.warn('RETRY','retry token=SECRET',{position:4,attempt:1},{event:'RETRY'});await logger.log('VERIFY','ffprobe valid',{position:4},{event:'VERIFY'});await logger.log('COMMIT','position committed',{position:4},{event:'COMMIT'});
  await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});const report=JSON.parse(await fs.readFile(diag.reportJsonPath,'utf8'));
  assert.ok(report.timeline);assert.equal(report.timeline.totalEvents,report.eventSummary.count);assert.ok(report.timeline.events.some(e=>e.event==='RETRY'));assert.ok(report.timeline.events.some(e=>e.event==='COMMIT'));
  assert.doesNotMatch(JSON.stringify(report.timeline),/SECRET/);
  await fs.rm(diag.eventPath,{force:true});assert.ok(report.timeline.events.length>0);
});
