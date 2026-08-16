import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { NavigationIndex } from '../src/navigation-index.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore } from '../src/state.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-nav-index-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}

async function seed(outputRoot,total,end,{urls=[]}={}){
  const s=new StateStore({outputRoot,courseName:'Fake Course',totalPositions:total});
  await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});
  const u=new Set(urls);
  for(let p=1;p<=end;p++)await s.commit({position:p,status:'NO_VIDEO',lessonTitle:`Lesson ${p}`,lessonUrl:u.has(p)?`https://www.xcursos.com/aula/${p}`:null});
  return s;
}

test('NavigationIndex persists sanitized position→URL mappings and resolves nearest checkpoint',async()=>{
  const root=await tmp();const file=path.join(root,'lesson-navigation-index.json');
  const index=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:70});
  await index.load();
  await index.record(10,'https://www.xcursos.com/aula/10?token=SECRET');
  await index.record(20,'https://www.xcursos.com/aula/20');
  const reloaded=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:70});await reloaded.load();
  assert.equal(reloaded.get(10),'https://www.xcursos.com/aula/10');
  assert.equal(reloaded.nearestBefore(25).position,20);
  assert.equal(reloaded.nearestBefore(20).position,10);
});

test('runner boot migrates historical manifest lesson URLs into navigation index',async()=>{
  const root=await tmp();const seeded=await seed(root,10,5,{urls:[2,4]});
  const runner=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons(10),{startPosition:1}),downloader:new DiskFakeDownloader()});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    assert.equal(runner.navigationIndex.get(2),'https://www.xcursos.com/aula/2');
    assert.equal(runner.navigationIndex.get(4),'https://www.xcursos.com/aula/4');
    assert.equal(runner.navigationIndex.get(1),'https://www.xcursos.com/aula/1','current confirmed page is indexed too');
    assert.equal(path.basename(seeded.navigationPath),'lesson-navigation-index.json');
  }finally{await runner.dispose();}
});

test('safe forward walk records every confirmed position into navigation index',async()=>{
  const root=await tmp();await seed(root,8,6);
  const browser=new FakeBrowser(lessons(8),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    await runner.ensurePageAt(7);
    for(let p=1;p<=7;p++)assert.equal(runner.navigationIndex.get(p),`https://www.xcursos.com/aula/${p}`);
  }finally{await runner.dispose();}
});

test('ensurePageAt uses exact navigation-index URL without sidebar when manifest lacks lessonUrl',async()=>{
  const root=await tmp();const seeded=await seed(root,10,6);
  const nav=new NavigationIndex({filePath:seeded.navigationPath,courseName:'Fake Course',totalPositions:10});await nav.load();await nav.record(7,'https://www.xcursos.com/aula/7');
  class NoSidebarBrowser extends FakeBrowser{async goToPosition(){this.stats.goToPosition++;const e=new Error('no sidebar');e.code='POSITION_REPOSITION_UNAVAILABLE';throw e;}}
  const browser=new NoSidebarBrowser(lessons(10),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader()});
  try{
    await runner.boot({resume:true,requireDownloader:false});
    const observed=await runner.ensurePageAt(7);
    assert.equal(observed.currentPosition,7);
    assert.equal(browser.stats.goToPosition,0);
    assert.equal(browser.stats.clickNext,0);
  }finally{await runner.dispose();}
});

test('corrupt navigation index is quarantined and rebuilt empty instead of blocking resume',async()=>{
  const root=await tmp();const file=path.join(root,'lesson-navigation-index.json');await fs.writeFile(file,'{"version":1,"positions":','utf8');
  const index=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:10});const loaded=await index.load();
  assert.deepEqual(loaded.positions,{});
  const names=await fs.readdir(root);assert.ok(names.some(name=>name.startsWith('lesson-navigation-index.json.corrupt-')));
  await index.record(1,'https://www.xcursos.com/aula/1');assert.equal(index.get(1),'https://www.xcursos.com/aula/1');
});

test('V4.2.3 navigation index migrates v1 and derives durable course anchor from position 1',async()=>{
  const root=await tmp();const file=path.join(root,'lesson-navigation-index.json');
  await fs.writeFile(file,JSON.stringify({version:1,courseName:'Fake Course',totalPositions:10,updatedAt:new Date().toISOString(),positions:{'1':'https://www.xcursos.com/aula/1?token=OLD','5':'https://www.xcursos.com/aula/5'}}),'utf8');
  const index=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:10});await index.load();
  assert.equal(index.anchor().position,1);assert.equal(index.anchor().url,'https://www.xcursos.com/aula/1');assert.equal(index.get(5),'https://www.xcursos.com/aula/5');
  const persisted=JSON.parse(await fs.readFile(file,'utf8'));assert.equal(persisted.version,2);assert.equal(persisted.courseAnchor.position,1);assert.equal(JSON.stringify(persisted).includes('OLD'),false);
});

test('recording confirmed position 1 maintains course anchor and never persists query secrets',async()=>{
  const root=await tmp();const file=path.join(root,'lesson-navigation-index.json');const index=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:10});await index.load();
  await index.record(1,'https://www.xcursos.com/aula/1?X-Amz-Signature=SUPERSECRET');
  assert.deepEqual(index.anchor(),{position:1,url:'https://www.xcursos.com/aula/1'});
  assert.equal((await fs.readFile(file,'utf8')).includes('SUPERSECRET'),false);
});

test('stale navigation entry can be invalidated durably without deleting course anchor',async()=>{
  const root=await tmp();const file=path.join(root,'lesson-navigation-index.json');const index=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:10});await index.load();
  await index.record(1,'https://www.xcursos.com/aula/1');await index.record(5,'https://www.xcursos.com/aula/5');
  await index.invalidate(5,{reason:'POSITION_MISMATCH',observedPosition:6});
  assert.equal(index.get(5),null);assert.equal(index.anchor().position,1);
  const reload=new NavigationIndex({filePath:file,courseName:'Fake Course',totalPositions:10});await reload.load();assert.equal(reload.get(5),null);assert.equal(reload.anchor().position,1);
});
