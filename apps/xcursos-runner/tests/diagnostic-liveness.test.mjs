import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as livenessModule from '../src/diagnostic-liveness.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-liveness-'));}

test('liveness classifies prolonged no-progress as POSSIBLE_STALL with fake time',()=>{
  assert.equal(typeof livenessModule.DiagnosticLiveness,'function');
  let now=1_000;const live=new livenessModule.DiagnosticLiveness({nowFn:()=>now,stallThresholdMs:60_000,memoryUsageFn:()=>({rss:100,heapUsed:50})});
  live.noteProgress({stage:'DOWNLOAD',position:8,operation:'DOWNLOAD'});now+=61_000;
  const snap=live.snapshot();assert.equal(snap.status,'POSSIBLE_STALL');assert.equal(snap.stage,'DOWNLOAD');assert.equal(snap.position,8);assert.equal(snap.msSinceProgress,61_000);
});

test('active subprocess is treated as legitimate long operation rather than silent stall',()=>{
  let now=1_000;const live=new livenessModule.DiagnosticLiveness({nowFn:()=>now,stallThresholdMs:60_000,memoryUsageFn:()=>({rss:100,heapUsed:50})});
  live.noteProgress({stage:'DOWNLOAD',position:9,operation:'YTDLP'});live.noteSubprocessStart({pid:4321,command:'yt-dlp'});now+=10*60_000;
  const snap=live.snapshot();assert.equal(snap.status,'ACTIVE_LONG_OPERATION');assert.equal(snap.activeSubprocess.pid,4321);assert.equal(snap.position,9);
  live.noteSubprocessEnd({pid:4321});assert.equal(live.snapshot().activeSubprocess,null);
});

test('retry/backoff wait is classified as EXPECTED_WAIT and never as a hang',()=>{
  let now=1_000;const live=new livenessModule.DiagnosticLiveness({nowFn:()=>now,stallThresholdMs:30_000,memoryUsageFn:()=>({rss:100,heapUsed:50})});
  live.noteProgress({stage:'RETRY',position:3,operation:'BACKOFF'});live.setWaiting('RETRY_BACKOFF',{untilMs:now+120_000});now+=90_000;
  assert.equal(live.snapshot().status,'EXPECTED_WAIT');
});

test('heartbeat exposes timer/event-loop delay independently from work progress',()=>{
  let now=10_000;const live=new livenessModule.DiagnosticLiveness({nowFn:()=>now,eventLoopDelayWarnMs:2_000,memoryUsageFn:()=>({rss:500,heapUsed:250})});
  live.noteProgress({stage:'INSPECT',position:2,operation:'DOM'});const expectedAt=now+30_000;now=expectedAt+5_000;
  const snap=live.heartbeat({expectedAtMs:expectedAt});assert.equal(snap.eventLoopDelayMs,5_000);assert.equal(snap.eventLoopStatus,'DELAYED');assert.equal(snap.memory.rss,500);
});

test('RunnerLogger can feed liveness without changing log persistence semantics',async()=>{
  let now=1_000;const observed=[];const logger=new RunnerLogger({nowFn:()=>now,eventObserver:e=>observed.push(e)});await logger.log('RUNNER','inspected',{position:5},{event:'INSPECT'});await logger.log('PROCESS','started',{pid:777,command:'yt-dlp'},{event:'SUBPROCESS_START'});
  assert.equal(observed.length,2);assert.equal(observed[0].event,'INSPECT');assert.equal(observed[0].data.position,5);assert.equal(observed[1].event,'SUBPROCESS_START');
});

test('liveness snapshot can be persisted fail-soft in the diagnostic run directory',async()=>{
  const root=await tmp();let now=1_000;const live=new livenessModule.DiagnosticLiveness({nowFn:()=>now,memoryUsageFn:()=>({rss:123,heapUsed:45})});live.noteProgress({stage:'VERIFY',position:11,operation:'FFPROBE'});
  const out=path.join(root,'liveness.json');const result=await live.persist(out);assert.equal(result.ok,true);const stored=JSON.parse(await fs.readFile(out,'utf8'));assert.equal(stored.position,11);assert.equal(stored.stage,'VERIFY');
});
