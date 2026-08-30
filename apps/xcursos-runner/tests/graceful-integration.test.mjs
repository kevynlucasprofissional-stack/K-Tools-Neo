import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { GracefulShutdownController } from '../src/shutdown-controller.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';
async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-stop-'));}
const lessons=n=>Array.from({length:n},(_,i)=>lesson(i+1,n));

test('first Ctrl+C during download finishes atomic lesson, commits, checkpoints, then stops before next lesson',async()=>{
  const root=await tmp();const stop=new GracefulShutdownController();
  class StopDownloader extends DiskFakeDownloader{async download(opts){await stop.requestStop('SIGINT');return await super.download(opts);}}
  const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(3)),downloader:new StopDownloader(),shutdownController:stop});const result=await r.runRange({start:1,end:3,resume:true});
  assert.equal(result.status,'STOPPED');const manifest=await readJsonlFile(r.state.manifestPath);assert.deepEqual(manifest.map(x=>x.position),[1]);assert.ok(await fs.stat(r.state.schedulerPath));await r.dispose();
});

test('Ctrl+C during navigation stops before starting the newly navigated lesson',async()=>{
  const root=await tmp();const stop=new GracefulShutdownController();class StopNavBrowser extends FakeBrowser{async clickNext(...a){const x=await super.clickNext(...a);await stop.requestStop('SIGINT');return x;}}
  const d=new DiskFakeDownloader();const r=new XCursosCourseRunner({outputRoot:root,browser:new StopNavBrowser(lessons(3)),downloader:d,shutdownController:stop});const result=await r.runRange({start:1,end:3,resume:true});assert.equal(result.status,'STOPPED');assert.deepEqual(d.calls.map(x=>x.pos),[1]);await r.dispose();
});

test('double Ctrl+C during download force-aborts work and leaves position recoverable in checkpoint',async()=>{
  const root=await tmp();const stop=new GracefulShutdownController();class ForceDownloader extends DiskFakeDownloader{async download(){await stop.requestStop('SIGINT');await stop.requestStop('SIGINT');const e=new Error('force');e.code='PROCESS_ABORTED';throw e;}}
  const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(2)),downloader:new ForceDownloader(),shutdownController:stop});const result=await r.runRange({start:1,end:2,resume:true});assert.equal(result.status,'STOPPED');assert.equal((await readJsonlFile(r.state.manifestPath)).length,0);const cp=JSON.parse(await fs.readFile(r.state.schedulerPath,'utf8'));assert.ok(cp.ready.some(x=>x.position===1));await r.dispose();
});

test('important structural error triggers debug snapshot without replacing original error',async()=>{
  const root=await tmp();let captures=0;const debug={capture:async()=>{captures++;return{ok:true};}};const b=new FakeBrowser(lessons(3),{transitionPlan:{1:'skip'}});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader(),debugSnapshots:debug});await assert.rejects(()=>r.runRange({start:1,end:3,resume:true}),e=>e.code==='POSITION_SKIP');assert.equal(captures,1);await r.dispose();
});

test('stop requested before first lesson creates checkpoint and starts no download',async()=>{const root=await tmp();const stop=new GracefulShutdownController();await stop.requestStop('SIGINT');const d=new DiskFakeDownloader();const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(2)),downloader:d,shutdownController:stop});const result=await r.runRange({start:1,end:2,resume:true});assert.equal(result.status,'STOPPED');assert.equal(d.calls.length,0);assert.ok(await fs.stat(r.state.schedulerPath));await r.dispose();});

test('first Ctrl+C during ffprobe validation allows validation+commit before stopping',async()=>{const root=await tmp();const stop=new GracefulShutdownController();class StopVerifyDownloader extends DiskFakeDownloader{async validateVideo(file,...rest){await stop.requestStop('SIGINT');return await super.validateVideo(file,...rest);}}const d=new StopVerifyDownloader();const r=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(2)),downloader:d,shutdownController:stop});const result=await r.runRange({start:1,end:2,resume:true});assert.equal(result.status,'STOPPED');const manifest=await readJsonlFile(r.state.manifestPath);assert.deepEqual(manifest.map(x=>x.position),[1]);await r.dispose();});
