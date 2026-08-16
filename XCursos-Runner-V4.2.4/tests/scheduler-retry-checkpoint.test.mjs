import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { LessonScheduler } from '../src/lesson-scheduler.mjs';
import { RetryPolicy, RetryClass } from '../src/retry-policy.mjs';
import { DurableSchedulerCheckpoint } from '../src/scheduler-checkpoint.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-sched-'));}

test('LessonScheduler builds deterministic 1..5 ready queue and deduplicates positions',()=>{
  const s=new LessonScheduler({total:5,start:1,end:5,nowFn:()=>1000});s.reconcile({donePositions:[2]});
  assert.deepEqual(s.snapshot().ready.map(t=>t.position),[1,3,4,5]);assert.equal(new Set(s.snapshot().ready.map(t=>t.position)).size,4);
});

test('LessonScheduler priority wins while equal priority preserves position order',()=>{
  const s=new LessonScheduler({total:5,nowFn:()=>1000});s.reconcile({donePositions:[]});s.setPriority(4,50);
  assert.equal(s.claimNext().task.position,4);s.markDone(4);assert.equal(s.claimNext().task.position,1);
});

test('transient failure goes to RETRY_LATER and other ready lessons continue first',()=>{
  let now=1000;const s=new LessonScheduler({total:5,nowFn:()=>now});s.reconcile({donePositions:[]});
  const a=s.claimNext().task;assert.equal(a.position,1);s.markDone(1);
  const b=s.claimNext().task;assert.equal(b.position,2);s.requeue(2,{delayMs:500,lastError:{code:'PROCESS_TIMEOUT'},priorityPenalty:10});
  assert.equal(s.claimNext().task.position,3);assert.equal(s.get(2).status,'RETRY_LATER');now=2000;
  s.markDone(3);s.markDone(4);s.markDone(5);assert.equal(s.claimNext().task.position,2);
});

test('crashed IN_FLIGHT checkpoint becomes READY on reconstruction and completed position never returns',()=>{
  const checkpoint={schedulerVersion:1,ready:[{position:3,status:'READY',attempts:0,priority:0}],retryLater:[],inFlight:[{position:2,status:'IN_FLIGHT',attempts:1,priority:0,lessonUrl:'https://www.xcursos.com/curso/c/aula/2'}],blocked:[]};
  const s=new LessonScheduler({total:3,nowFn:()=>1000});s.reconcile({donePositions:[1],checkpoint});
  assert.equal(s.get(1).status,'DONE');assert.equal(s.get(2).status,'READY');assert.equal(s.get(2).lessonUrl,'https://www.xcursos.com/curso/c/aula/2');assert.deepEqual(s.snapshot().inFlight,[]);
});

test('scheduler cannot have duplicate IN_FLIGHT claims for the same position',()=>{
  const s=new LessonScheduler({total:2});s.reconcile({donePositions:[]});const t=s.claimNext().task;assert.equal(t.status,'IN_FLIGHT');assert.throws(()=>s.claim(t.position),/IN_FLIGHT|claim/i);
});

test('RetryPolicy exponential backoff grows, caps, and jitter stays bounded',()=>{
  const p=new RetryPolicy({baseDelayMs:1000,maxDelayMs:5000,maxAttempts:5,jitterRatio:0.2,randomFn:()=>1});
  const d1=p.decide({attempt:1,error:{code:'PROCESS_TIMEOUT'}});const d2=p.decide({attempt:2,error:{code:'PROCESS_TIMEOUT'}});const d5=p.decide({attempt:5,error:{code:'PROCESS_TIMEOUT'}});
  assert.equal(d1.classification,RetryClass.TRANSIENT);assert.equal(d1.delayMs,1200);assert.equal(d2.delayMs,2400);assert.equal(d5.retry,false);assert.ok(d2.delayMs>d1.delayMs);
});

test('RetryPolicy does not auto-retry auth, structural, or permanent DRM errors',()=>{
  const p=new RetryPolicy();for(const code of ['AUTH_REQUIRED','POSITION_SKIP','COURSE_IDENTITY_MISMATCH','DRM_PROTECTED'])assert.equal(p.decide({attempt:1,error:{code}}).retry,false,code);
});

test('DurableSchedulerCheckpoint round-trips scheduler state atomically',async()=>{
  const dir=await tmp();const file=path.join(dir,'scheduler.checkpoint.json');const c=new DurableSchedulerCheckpoint({filePath:file});const s=new LessonScheduler({total:3,nowFn:()=>1000});s.reconcile({donePositions:[1]});s.claimNext();await c.save(s.snapshot());const loaded=await c.load();assert.equal(loaded.schedulerVersion,1);assert.equal(loaded.inFlight[0].position,2);assert.equal((await fs.readdir(dir)).some(x=>x.includes('.tmp-')),false);
});

test('invalid/truncated checkpoint is quarantined and returns null instead of losing manifest truth',async()=>{
  const dir=await tmp();const file=path.join(dir,'scheduler.checkpoint.json');await fs.writeFile(file,'{"schedulerVersion":1,"ready":');const c=new DurableSchedulerCheckpoint({filePath:file});assert.equal(await c.load(),null);const entries=await fs.readdir(dir);assert.ok(entries.some(x=>x.startsWith('scheduler.checkpoint.json.corrupt-')));
});

test('manifest done positions win over a newer checkpoint that still says READY',()=>{
  const checkpoint={schedulerVersion:1,ready:[{position:1,status:'READY',attempts:1,priority:0},{position:2,status:'READY',attempts:0,priority:0}],retryLater:[],inFlight:[],blocked:[]};
  const s=new LessonScheduler({total:2});s.reconcile({donePositions:[1],checkpoint});assert.equal(s.get(1).status,'DONE');assert.equal(s.claimNext().task.position,2);
});

test('V4.2.3 reposition no-safe-path and invalid walk are structural, never auto-retried',()=>{const p=new RetryPolicy({maxAttempts:5});for(const code of ['POSITION_REPOSITION_NO_SAFE_PATH','NAV_WALK_INVALID','REPOSITION_INSPECTION_EMPTY']){const d=p.decide({attempt:1,error:{code}});assert.equal(d.classification,'STRUCTURAL',code);assert.equal(d.retry,false,code);}});
