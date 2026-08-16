import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore, summarizeAudit } from '../src/state.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-retry-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}

test('audit is not healthy when a terminal-looking legacy download failure exists',()=>{
  const a=summarizeAudit({total:2,manifestRecords:[{position:1,status:'DOWNLOADED'},{position:2,status:'DOWNLOAD_FAILED'}]});
  assert.equal(a.coverageComplete,true);
  assert.equal(a.healthyComplete,false);
  assert.equal(a.downloadFailed,1);
});

test('V4.1.0 retryable failures are reopened automatically on resume',async()=>{
  const root=await tmp();
  const store=new StateStore({outputRoot:root,courseName:'Retry Course',totalPositions:3});
  await store.initialize({resume:true,workPageUrl:'https://www.xcursos.com/aula/1'});
  await store.commit({position:1,status:'NO_VIDEO',lessonUrl:'https://www.xcursos.com/aula/1'});
  await fs.appendFile(store.manifestPath,`${JSON.stringify({position:2,courseName:'Retry Course',status:'DOWNLOAD_FAILED',lessonTitle:'Legacy',lessonUrl:'https://www.xcursos.com/aula/2'})}\n`,'utf8');
  await store.releaseRunLock();

  const resumed=new StateStore({outputRoot:root,courseName:'Retry Course',totalPositions:3});
  await resumed.initialize({resume:true,workPageUrl:'https://www.xcursos.com/aula/1'});
  assert.equal(resumed.get(2),null);
  assert.equal(resumed.firstMissingPosition(),2);
  const manifest=await readJsonlFile(resumed.manifestPath);
  assert.deepEqual(manifest.map(r=>r.position),[1]);
  const errors=await readJsonlFile(resumed.errorsPath);
  assert.ok(errors.some(e=>e.position===2 && e.status==='RETRYABLE_FAILURE_REOPENED'));
});

test('failed download stays pending and a second pass fills it without duplicate manifest rows',async()=>{
  const root=await tmp();
  const ls=lessons(5);
  const firstDownloader=new DiskFakeDownloader({failPositions:[3]});
  const first=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(ls),downloader:firstDownloader});
  const r1=await first.runRange({start:1,end:5,resume:true});
  await first.dispose();
  assert.equal(r1.ok,false);
  assert.equal(r1.status,'RANGE_PARTIAL');
  assert.deepEqual(r1.retryableFailures,[{position:3,status:'DOWNLOAD_FAILED'}]);
  assert.deepEqual(r1.audit.missingPositions.slice(0,1),[3]);

  const secondDownloader=new DiskFakeDownloader();
  const second=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(ls),downloader:secondDownloader});
  const r2=await second.runRange({start:1,end:5,resume:true});
  assert.equal(r2.ok,true);
  assert.equal(r2.status,'RANGE_COMPLETE');
  assert.equal(r2.audit.processed,5);
  assert.deepEqual(r2.audit.missingPositions,[]);
  assert.equal(r2.audit.duplicatePositions.length,0);
  const manifest=await readJsonlFile(second.state.manifestPath);
  assert.equal(manifest.filter(r=>r.position===3).length,1);
  assert.ok(['DOWNLOADED','ALREADY_PRESENT'].includes(manifest.find(r=>r.position===3)?.status));
  await second.dispose();
});

test('new StateStore commits reject retryable failure statuses as progress',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'No Failure Commit',totalPositions:1});await s.initialize({resume:true});await assert.rejects(()=>s.commit({position:1,status:'DOWNLOAD_FAILED'}),e=>e.code==='COMMIT_RETRYABLE_STATUS');});
