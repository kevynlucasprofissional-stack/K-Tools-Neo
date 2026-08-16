import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { MediaDownloader } from '../src/downloader.mjs';
import { StateStore, readJsonl } from '../src/state.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

async function tmp(prefix='xc-hard-'){ return await fs.mkdtemp(path.join(os.tmpdir(),prefix)); }

test('hardening: resume=false starts a fresh manifest instead of reusing terminal positions',async()=>{
  const root=await tmp();
  const first=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});
  await first.initialize({resume:true,workPageUrl:'https://www.xcursos.com/aula/1'});
  await first.commit({position:1,status:'NO_VIDEO',lessonTitle:'L1',lessonUrl:'https://www.xcursos.com/aula/1'});
  const fresh=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});
  await fresh.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});
  assert.equal(fresh.hasTerminal(1),false);
  assert.equal(fresh.firstMissingPosition(),1);
  assert.equal((await readJsonl(fresh.manifestPath)).length,0);
});

test('hardening: manifest from a different course cannot be adopted after sanitized folder collision',async()=>{
  const root=await tmp();
  const a=new StateStore({outputRoot:root,courseName:'Course:A',totalPositions:2});
  await a.initialize({resume:true});
  await a.commit({position:1,status:'NO_VIDEO',lessonTitle:'L1'});
  await fs.rm(a.statePath,{force:true});
  const b=new StateStore({outputRoot:root,courseName:'Course?A',totalPositions:2});
  await assert.rejects(()=>b.initialize({resume:true}),e=>e.code==='MANIFEST_COURSE_MISMATCH');
});

test('hardening: state URL persistence redacts generic key-like secrets too',async()=>{
  const root=await tmp();
  const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:1});
  const url='https://www.xcursos.com/aula/1?key=SUPERSECRET&foo=ok';
  await s.initialize({resume:true,workPageUrl:url});
  await s.commit({position:1,status:'NO_VIDEO',lessonTitle:'A',lessonUrl:url});
  const persisted=(await fs.readFile(s.statePath,'utf8'))+(await fs.readFile(s.manifestPath,'utf8'));
  assert.equal(persisted.includes('SUPERSECRET'),false);
});

test('hardening: parseable but non-object state.json is treated as corrupt and rebuilt',async()=>{
  const root=await tmp();
  const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});
  await fs.mkdir(s.metaDir,{recursive:true});
  await fs.writeFile(s.manifestPath,'{"position":1,"courseName":"C","status":"NO_VIDEO"}\n');
  await fs.writeFile(s.statePath,'["garbage"]');
  await s.initialize({resume:true,workPageUrl:'https://www.xcursos.com/aula/1'});
  assert.equal(s.state.courseName,'C');
  assert.equal(s.state.lastCommittedPosition,1);
  assert.equal(Object.prototype.hasOwnProperty.call(s.state,'0'),false);
  const errors=await readJsonl(s.errorsPath);
  assert.ok(errors.some(x=>x.status==='STATE_CORRUPT_RECOVERED'));
});

test('hardening: existing-file detection does not accept prefix-collision filenames',async()=>{
  const root=await tmp();
  await fs.writeFile(path.join(root,'001 - Aula extra.mp4'),'x');
  const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff'});
  assert.equal(await d.findExistingFinal(root,'001 - Aula'),null);
});

test('hardening: safe reposition updates workPage to the PageRef returned by navigateNext',async()=>{
  const root=await tmp();
  const lessons=[lesson(1,2),lesson(2,2)];
  class ReplacementBrowser extends FakeBrowser {
    async navigateNext(_page,{target}={}){
      this.current=target;
      const page2={id:'replacement-page',url:`https://www.xcursos.com/aula/${target}`,title:'Assistir Aula | XCURSOS'};
      this.page=page2;
      return {page:page2,lesson:this._lesson(),method:'replacement'};
    }
  }
  const browser=new ReplacementBrowser(lessons);
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader()});
  await runner.runRange({start:2,end:2,resume:true});
  assert.equal(runner.workPage.id,'replacement-page');
  await runner.dispose();
});

test('hardening: concurrent writers for the same course are rejected by an exclusive run lock',async()=>{
  const root=await tmp();
  const a=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});
  const b=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});
  await a.acquireRunLock();
  await assert.rejects(()=>b.acquireRunLock(),e=>e.code==='RUN_ALREADY_ACTIVE');
  await a.releaseRunLock();
  await b.acquireRunLock();
  await b.releaseRunLock();
});

test('hardening: crash-after-download resume reuses in-flight output even if live title/module changed',async()=>{
  const root=await tmp();
  const original=[lesson(1,1,{title:'Original title',module:'1. Old'})];
  const changed=[lesson(1,1,{title:'Renamed title',module:'2. New'})];
  const d1=new DiskFakeDownloader();
  const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(original),downloader:d1});
  await r1.boot({resume:true,requireDownloader:true});
  const oldPaths=d1.buildPaths({root,courseName:'Fake Course',moduleName:'1. Old',lessonTitle:'Original title',position:1,total:1});
  await r1.state.setInFlight({position:1,lessonTitle:'Original title',moduleName:'1. Old',lessonUrl:'https://www.xcursos.com/aula/1',relativeOutputBase:path.relative(r1.state.courseDir,path.join(oldPaths.moduleDir,oldPaths.baseName))});
  await fs.mkdir(oldPaths.moduleDir,{recursive:true});
  await fs.writeFile(path.join(oldPaths.moduleDir,`${oldPaths.baseName}.mp4`),'VIDEO-1');
  await r1.dispose();

  const d2=new DiskFakeDownloader();
  const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(changed),downloader:d2});
  const result=await r2.runRange({start:1,end:1,resume:true});
  const manifest=await readJsonlFile(path.join(result.courseRoot,'_xcursos-runner','manifest.jsonl'));
  assert.equal(manifest[0].status,'ALREADY_PRESENT');
  assert.equal(d2.calls.length,0);
  assert.match(manifest[0].outputFile,/Original title\.mp4$/);
  await r2.dispose();
});

test('hardening: logger redacts signed URL embedded inside a longer message without destroying context',async()=>{
  const { RunnerLogger }=await import('../src/logger.mjs');
  const lines=[];const logger=new RunnerLogger({sink:x=>lines.push(x)});
  await logger.log('ERR','failed at https://cdn.example/a.mp4?key=SUPERSECRET&foo=1',{note:'retry https://cdn.example/b.mp4?X-Amz-Signature=ABC'});
  const text=lines.join('\n');
  assert.match(text,/failed at/);
  assert.equal(text.includes('SUPERSECRET'),false);
  assert.equal(text.includes('ABC'),false);
});

test('hardening: final tool result redacts signed URLs from structured error details',async()=>{
  const { downloadCourse }=await import('../src/runner.mjs');
  class SecretBrowser extends FakeBrowser { async chooseWorkingPage(){const e=new Error('bad https://cdn.example/a.mp4?token=SECRET');e.code='PAGE_CLOSED';e.details={media:'https://cdn.example/a.mp4?key=TOPSECRET'};throw e;} }
  const result=await downloadCourse({outputRoot:await tmp(),browser:new SecretBrowser([lesson(1,1)]),downloader:new DiskFakeDownloader()});
  const text=JSON.stringify(result);
  assert.equal(text.includes('SECRET'),false);
  assert.equal(text.includes('TOPSECRET'),false);
  assert.equal(result.status,'BLOCKED');
});

test('hardening: downloadRetries configuration is honored beyond a single retry',async()=>{
  const root=await tmp();
  const lessons=[lesson(1,1)];
  class RetryDownloader extends DiskFakeDownloader { async download(opts){const n=this.calls.length+1;this.calls.push({n});if(n<4)return{ok:false,kind:'FAILED',code:1};await fs.mkdir(opts.paths.moduleDir,{recursive:true});const f=path.join(opts.paths.moduleDir,`${opts.paths.baseName}.mp4`);await fs.writeFile(f,'VIDEO-1');return{ok:true,finalPath:f};} }
  const d=new RetryDownloader();
  const runner=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:d,limits:{downloadRetries:3}});
  const result=await runner.runRange({start:1,end:1,resume:true});
  assert.equal(result.audit.downloaded,1);
  assert.equal(d.calls.length,4);
  await runner.dispose();
});

test('hardening: mediaRefreshRetries configuration can refresh more than once but stays bounded',async()=>{
  const root=await tmp();
  const lessons=[lesson(1,1,{signed:true})];
  class RefreshBrowser extends FakeBrowser { async refreshSameLesson(){this.stats.refresh++;this.page={...this.page,id:`refresh-${this.stats.refresh}`};return this.page;} }
  class ExpireDownloader extends DiskFakeDownloader { async download(opts){const n=this.calls.length+1;this.calls.push({n});if(n<3)return{ok:false,kind:'EXPIRED',code:1};await fs.mkdir(opts.paths.moduleDir,{recursive:true});const f=path.join(opts.paths.moduleDir,`${opts.paths.baseName}.mp4`);await fs.writeFile(f,'VIDEO-1');return{ok:true,finalPath:f};} }
  const browser=new RefreshBrowser(lessons);const d=new ExpireDownloader();
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:d,limits:{mediaRefreshRetries:2,downloadRetries:0}});
  const result=await runner.runRange({start:1,end:1,resume:true});
  assert.equal(result.audit.downloaded,1);
  assert.equal(browser.stats.refresh,2);
  assert.equal(d.calls.length,3);
  await runner.dispose();
});

test('hardening: runner-level exclusive lock blocks a concurrent run and releases on dispose',async()=>{
  const root=await tmp();const lessons=[lesson(1,1)];
  const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:new DiskFakeDownloader()});
  const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:new DiskFakeDownloader()});
  await r1.boot({resume:true,requireDownloader:true});
  await assert.rejects(()=>r2.boot({resume:true,requireDownloader:true}),e=>e.code==='RUN_ALREADY_ACTIVE');
  await r1.dispose();
  await r2.boot({resume:true,requireDownloader:true});
  await r2.dispose();
});

test('hardening: resume=false cannot rotate or adopt another course that collides after Windows sanitization',async()=>{
  const root=await tmp();
  const a=new StateStore({outputRoot:root,courseName:'Course:A',totalPositions:1});
  await a.initialize({resume:true});
  await a.commit({position:1,status:'NO_VIDEO',lessonTitle:'L1'});
  const before=await fs.readFile(a.manifestPath,'utf8');
  const b=new StateStore({outputRoot:root,courseName:'Course?A',totalPositions:1});
  await assert.rejects(()=>b.initialize({resume:false}),e=>['COURSE_DIR_COLLISION','MANIFEST_COURSE_MISMATCH'].includes(e.code));
  assert.equal(await fs.readFile(a.manifestPath,'utf8'),before);
});

test('hardening: persistent course identity survives fresh metadata rotation for the same course',async()=>{
  const root=await tmp();
  const a=new StateStore({outputRoot:root,courseName:'Course:A',totalPositions:1});
  await a.initialize({resume:true});
  const identityPath=path.join(a.metaDir,'course.identity.json');
  assert.equal(JSON.parse(await fs.readFile(identityPath,'utf8')).courseName,'Course:A');
  const b=new StateStore({outputRoot:root,courseName:'Course:A',totalPositions:1});
  await b.initialize({resume:false});
  assert.equal(JSON.parse(await fs.readFile(identityPath,'utf8')).courseName,'Course:A');
});

test('hardening: orphaned same-host lock from a dead PID is reclaimed after crash',async()=>{
  const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:1});
  await fs.mkdir(s.metaDir,{recursive:true});
  await fs.writeFile(s.lockPath,JSON.stringify({version:1,token:'old',pid:2147483646,hostname:os.hostname(),startedAt:new Date().toISOString()}));
  await s.acquireRunLock();
  assert.ok(s.lockToken);
  await s.releaseRunLock();
});

test('hardening: recent unreadable run lock is not deleted speculatively',async()=>{
  const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:1});
  await fs.mkdir(s.metaDir,{recursive:true});await fs.writeFile(s.lockPath,'not-json');
  await assert.rejects(()=>s.acquireRunLock(),e=>e.code==='RUN_LOCK_CORRUPT');
  assert.equal(await fs.readFile(s.lockPath,'utf8'),'not-json');
});
