import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { StateStore, readJsonl } from '../src/state.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-state-'));}

test('M5 commit is unique and crash-after-commit never duplicates',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:3});await s.initialize({resume:true,workPageUrl:'https://xc/1'});await s.commit({position:1,status:'NO_VIDEO',lessonTitle:'A',lessonUrl:'https://xc/1'});const again=await s.commit({position:1,status:'NO_VIDEO',lessonTitle:'A',lessonUrl:'https://xc/1'});assert.equal(again.alreadyCommitted,true);assert.equal((await readJsonl(s.manifestPath)).length,1);});

test('M5 trailing partial JSONL is tolerated after crash',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});await fs.mkdir(s.metaDir,{recursive:true});await fs.writeFile(s.manifestPath,'{"position":1,"status":"NO_VIDEO"}\n{"position":');await s.initialize({resume:true});assert.equal(s.hasTerminal(1),true);assert.equal(s.firstMissingPosition(),2);});

test('M5 corrupted state.json recovers from manifest',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:2});await fs.mkdir(s.metaDir,{recursive:true});await fs.writeFile(s.manifestPath,'{"position":1,"status":"NO_VIDEO"}\n');await fs.writeFile(s.statePath,'{bad');await s.initialize({resume:true,workPageUrl:'https://xc/1'});assert.equal(s.state.lastCommittedPosition,1);assert.equal(s.state.currentTarget,2);});

test('M5 manifest DOWNLOADED but file missing is detected',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:1});await s.initialize({resume:true});await s.commit({position:1,status:'DOWNLOADED',lessonTitle:'A',outputFile:path.join(root,'missing.mp4')});assert.deepEqual(await s.verifyFileBackedEntries(async()=>{}),[1]);});

test('M5 crash after download before commit becomes ALREADY_PRESENT on resume',async()=>{const root=await tmp();const lessons=[lesson(1,2),lesson(2,2)];const d=new DiskFakeDownloader();const b1=new FakeBrowser(lessons);const r1=new XCursosCourseRunner({outputRoot:root,browser:b1,downloader:d});await r1.boot({resume:true,requireDownloader:true});const paths=d.buildPaths({root,courseName:'Fake Course',moduleName:'1. Module',lessonTitle:'Lesson 1',position:1,total:2});await fs.mkdir(paths.moduleDir,{recursive:true});await fs.writeFile(path.join(paths.moduleDir,`${paths.baseName}.mp4`),'VIDEO-1');await r1.dispose();const b2=new FakeBrowser(lessons);const r2=new XCursosCourseRunner({outputRoot:root,browser:b2,downloader:d});const result=await r2.runRange({start:1,end:1,resume:true});const m=await readJsonlFile(path.join(result.courseRoot,'_xcursos-runner','manifest.jsonl'));assert.equal(m[0].status,'ALREADY_PRESENT');await r2.dispose();});

test('M5 partial course resume does not redownload committed positions',async()=>{const root=await tmp();const lessons=Array.from({length:5},(_,i)=>lesson(i+1,5));const d1=new DiskFakeDownloader();const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:d1});await r1.runRange({start:1,end:3,resume:true});await r1.dispose();const d2=new DiskFakeDownloader();const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons,{startPosition:3}),downloader:d2});const res=await r2.runRange({start:1,end:5,resume:true});assert.deepEqual(d2.calls.map(x=>x.pos),[4,5]);assert.equal(res.audit.processed,5);await r2.dispose();});

test('M5 corrupt committed file is repaired without duplicate manifest position',async()=>{const root=await tmp();const lessons=[lesson(1,2),lesson(2,2)];const d=new DiskFakeDownloader();const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:d});const first=await r1.runRange({start:1,end:1,resume:true});await r1.dispose();const manifestPath=path.join(first.courseRoot,'_xcursos-runner','manifest.jsonl');const m1=await readJsonlFile(manifestPath);await fs.writeFile(m1[0].outputFile,'CORRUPT');const d2=new DiskFakeDownloader();const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:d2});await r2.runRange({start:1,end:1,resume:true});await r2.dispose();const m2=await readJsonlFile(manifestPath);assert.equal(m2.length,1);assert.equal(d2.calls.length,1);});

test('M5 signed media-like query is never persisted in state or manifest URL',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:1});const signed='https://www.xcursos.com/aula/1?X-Amz-Signature=SECRET&X-Amz-Expires=10';await s.initialize({resume:true,workPageUrl:signed});await s.commit({position:1,status:'NO_VIDEO',lessonTitle:'A',lessonUrl:signed});const stateText=await fs.readFile(s.statePath,'utf8');const manText=await fs.readFile(s.manifestPath,'utf8');assert.equal(stateText.includes('SECRET'),false);assert.equal(manText.includes('SECRET'),false);assert.ok(stateText.includes('https://www.xcursos.com/aula/1'));});

test('M5 crash during navigation resumes from first uncommitted position',async()=>{const root=await tmp();const lessons=Array.from({length:3},(_,i)=>lesson(i+1,3));const d1=new DiskFakeDownloader();const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons,{transitionPlan:{1:'stuck'}}),downloader:d1,limits:{navigationRetries:0,transitionTimeoutMs:10,transitionPollMs:1}});await assert.rejects(()=>r1.runRange({start:1,end:3,resume:true}),e=>e.code==='POSITION_STUCK');await r1.dispose();assert.deepEqual(d1.calls.map(x=>x.pos),[1]);const d2=new DiskFakeDownloader();const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons,{startPosition:1}),downloader:d2});const result=await r2.runRange({start:1,end:3,resume:true});assert.deepEqual(d2.calls.map(x=>x.pos),[2,3]);assert.equal(result.audit.processed,3);await r2.dispose();});

test('M5 browser reopened can bootstrap from persisted workPageUrl when no live page is discoverable',async()=>{const root=await tmp();const lessons=Array.from({length:2},(_,i)=>lesson(i+1,2));const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:new DiskFakeDownloader()});await r1.runRange({start:1,end:1,resume:true});await r1.dispose();class ReopenedBrowser extends FakeBrowser{constructor(){super(lessons,{startPosition:1});this.calls=[];}async chooseWorkingPage(opts={}){this.calls.push(opts);if(!opts.preferredUrl){const e=new Error('no pages');e.code='XC_PAGE_NOT_FOUND';throw e;}const m=opts.preferredUrl.match(/\/aula\/(\d+)/);this.current=Number(m?.[1]||1);return{page:this.page,lesson:this._lesson(),cloned:true};}}const b=new ReopenedBrowser();const r2=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});const res=await r2.runRange({start:1,end:2,resume:true});assert.equal(res.audit.processed,2);assert.ok(b.calls.some(x=>x.preferredUrl));await r2.dispose();});

test('M5 repair preserves manifest output path even if live metadata changed',async()=>{const root=await tmp();const original=[lesson(1,1,{title:'Original',module:'1. Old'})];const d1=new DiskFakeDownloader();const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(original),downloader:d1});const first=await r1.runRange({start:1,end:1,resume:true});await r1.dispose();const mp=path.join(first.courseRoot,'_xcursos-runner','manifest.jsonl');const before=(await readJsonlFile(mp))[0];await fs.writeFile(before.outputFile,'CORRUPT');const changed=[lesson(1,1,{title:'Renamed',module:'2. New'})];const d2=new DiskFakeDownloader();const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(changed),downloader:d2});await r2.runRange({start:1,end:1,resume:true});await r2.dispose();assert.equal((await fs.readFile(before.outputFile,'utf8')).startsWith('VIDEO-1'),true);assert.equal((await readJsonlFile(mp)).length,1);});

test('M5 trailing partial manifest tail is physically repaired before next commit',async()=>{
  const outputRoot=await tmp();
  const store=new StateStore({outputRoot,courseName:'C',totalPositions:3});
  await store.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});
  await store.commit({position:1,lessonTitle:'L1',moduleName:'M',lessonUrl:'https://www.xcursos.com/aula/1',status:'NO_VIDEO'});
  await fs.appendFile(store.manifestPath,'{"position":2,"broken"','utf8');

  const resumed=new StateStore({outputRoot,courseName:'C',totalPositions:3});
  await resumed.initialize({resume:true,workPageUrl:'https://www.xcursos.com/aula/2'});
  await resumed.commit({position:2,lessonTitle:'L2',moduleName:'M',lessonUrl:'https://www.xcursos.com/aula/2',status:'NO_VIDEO'});

  const strict=await readJsonl(resumed.manifestPath,{tolerateTrailingPartial:false});
  assert.deepEqual(strict.map(r=>r.position),[1,2]);
});

test('M5 manifest commit path uses durable append with fsync before state advances',async()=>{
  const source=await fs.readFile(new URL('../src/state.mjs',import.meta.url),'utf8');
  assert.match(source,/handle\.sync\(\)/);
  assert.match(source,/appendJsonlDurable\(this\.manifestPath,record\)/);
});

test('V4.2.3 state exposes lastContiguousCommittedPosition while preserving legacy field',async()=>{
  const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'C',totalPositions:5});await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});await s.commit({position:1,status:'NO_VIDEO',lessonTitle:'1'});await s.commit({position:3,status:'NO_VIDEO',lessonTitle:'3'});assert.equal(s.state.lastCommittedPosition,1);assert.equal(s.state.lastContiguousCommittedPosition,1);const reload=new StateStore({outputRoot:root,courseName:'C',totalPositions:5});await reload.initialize({resume:true});assert.equal(reload.state.lastCommittedPosition,1);assert.equal(reload.state.lastContiguousCommittedPosition,1);
});
