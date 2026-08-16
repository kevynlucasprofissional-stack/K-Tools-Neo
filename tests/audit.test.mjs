import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { summarizeAudit } from '../src/state.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-audit-'));}
function lessons(n,fn=()=>({})){return Array.from({length:n},(_,i)=>lesson(i+1,n,fn(i+1)));}

test('M6 audit refuses a missing position',()=>{const records=[1,2,4,5].map(position=>({position,status:'NO_VIDEO'}));const a=summarizeAudit({total:5,manifestRecords:records});assert.equal(a.coverageComplete,false);assert.deepEqual(a.missingPositions,[3]);});

test('M6 audit detects duplicate positions',()=>{const a=summarizeAudit({total:2,manifestRecords:[{position:1,status:'NO_VIDEO'},{position:1,status:'NO_VIDEO'},{position:2,status:'NO_VIDEO'}]});assert.equal(a.coverageComplete,false);assert.deepEqual(a.duplicatePositions,[1]);});

test('M6 fake 5 lesson course completes and processes last lesson',async()=>{const root=await tmp();const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(5)),downloader:new DiskFakeDownloader()});const result=await r.runCourse({resume:true});assert.equal(result.status,'COMPLETE');assert.equal(result.audit.processed,5);assert.equal(result.audit.missingPositions.length,0);await r.dispose();});

test('M6 fake 10 course refuses COMPLETE while a retryable download failure remains',async()=>{const ls=lessons(10,p=>({signed:p===2,video:p!==4,materials:p===4,module:p<=5?'1. A':'2. B'}));const root=await tmp();const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(ls),downloader:new DiskFakeDownloader({failPositions:[7],expiredOncePositions:[2]})});await assert.rejects(()=>r.runCourse({resume:true}),e=>e?.code==='AUDIT_INCOMPLETE' && e?.details?.missingPositions?.includes(7));await r.dispose();});

test('M6 full runner stops on N→N+2 instead of declaring complete',async()=>{const root=await tmp();const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(5),{transitionPlan:{2:'skip'}}),downloader:new DiskFakeDownloader(),limits:{navigationRetries:1,transitionTimeoutMs:10,transitionPollMs:1}});await assert.rejects(()=>r.runCourse({resume:true}),e=>e.code==='POSITION_SKIP');await r.dispose();});
