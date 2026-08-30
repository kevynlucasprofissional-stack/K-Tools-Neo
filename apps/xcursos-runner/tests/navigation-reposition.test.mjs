import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore } from '../src/state.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-reposition-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}
async function seedDone(outputRoot,total,end,{urlPositions=new Set()}={}){
  const s=new StateStore({outputRoot,courseName:'Fake Course',totalPositions:total});
  await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});
  for(let p=1;p<=end;p++)await s.commit({position:p,status:'NO_VIDEO',lessonTitle:`Lesson ${p}`,moduleName:'1. Module',lessonUrl:urlPositions.has(p)?`https://www.xcursos.com/aula/${p}`:null});
  return s;
}

test('ensurePageAt uses current proven predecessor N-1 before any arbitrary reposition',async()=>{
  const root=await tmp();await seedDone(root,70,64);
  const browser=new FakeBrowser(lessons(70),{startPosition:64});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    const observed=await runner.ensurePageAt(65);
    assert.equal(observed.currentPosition,65);
    assert.equal(browser.stats.clickNext,1);
    assert.equal(browser.stats.goToPosition,0);
  }finally{await runner.dispose();}
});

test('ensurePageAt uses nearest known completed checkpoint and walks forward deterministically',async()=>{
  const root=await tmp();await seedDone(root,70,64,{urlPositions:new Set([62])});
  const browser=new FakeBrowser(lessons(70),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    const observed=await runner.ensurePageAt(65);
    assert.equal(observed.currentPosition,65);
    assert.equal(browser.stats.goToPosition,0);
    assert.equal(browser.stats.clickNext,3);
    assert.equal(browser.current,65);
  }finally{await runner.dispose();}
});

test('ensurePageAt walks from current page when every crossed position is already terminal',async()=>{
  const root=await tmp();await seedDone(root,70,64);
  const browser=new FakeBrowser(lessons(70),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    const observed=await runner.ensurePageAt(65);
    assert.equal(observed.currentPosition,65);
    assert.equal(browser.stats.goToPosition,0);
    assert.equal(browser.stats.clickNext,64);
  }finally{await runner.dispose();}
});

test('ensurePageAt may cross an uncommitted gap but navigation never commits it',async()=>{
  const root=await tmp();await seedDone(root,70,63);
  class NoSidebarBrowser extends FakeBrowser{async goToPosition(){this.stats.goToPosition++;const e=new Error('sidebar disabled');e.code='POSITION_REPOSITION_UNAVAILABLE';throw e;}}
  const browser=new NoSidebarBrowser(lessons(70),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    assert.equal(runner.state.hasTerminal(64),false);
    const observed=await runner.ensurePageAt(65);
    assert.equal(observed.currentPosition,65);
    assert.equal(browser.stats.goToPosition,0);
    assert.equal(browser.stats.clickNext,64);
    assert.equal(runner.state.hasTerminal(64),false,'reposition traversal must not commit missing position 64');
  }finally{await runner.dispose();}
});

test('live regression: manifest 1..64 + browser at 1 can run range 64..70 without sidebar or redownload',async()=>{
  const root=await tmp();await seedDone(root,70,64);
  class NoSidebarBrowser extends FakeBrowser{async goToPosition(){this.stats.goToPosition++;const e=new Error('sidebar disabled');e.code='POSITION_REPOSITION_UNAVAILABLE';throw e;}}
  const browser=new NoSidebarBrowser(lessons(70),{startPosition:1});
  const downloader=new DiskFakeDownloader();
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    const result=await runner.runRange({start:64,end:70,resume:true});
    assert.equal(result.status,'RANGE_COMPLETE');
    assert.deepEqual(downloader.calls.map(x=>x.pos),[65,66,67,68,69,70]);
    assert.equal(browser.stats.goToPosition,0);
    assert.deepEqual(result.audit.missingPositions,[]);
    assert.equal(result.stats.coverageProcessed,70);
    assert.equal(result.stats.runOperations,6);
  }finally{await runner.dispose();}
});
