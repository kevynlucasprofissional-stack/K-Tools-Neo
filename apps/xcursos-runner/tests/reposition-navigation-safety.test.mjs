import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore } from '../src/state.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return fs.mkdtemp(path.join(os.tmpdir(),'xc-nav-safety-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}
class NoSidebarBrowser extends FakeBrowser{async goToPosition(){this.stats.goToPosition++;const e=new Error('sidebar disabled');e.code='POSITION_REPOSITION_UNAVAILABLE';throw e;}}
async function seed(root,total,positions){const s=new StateStore({outputRoot:root,courseName:'Fake Course',totalPositions:total});await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/1'});for(const p of positions)await s.commit({position:p,status:'NO_VIDEO',lessonTitle:`Lesson ${p}`,moduleName:'1. Module',lessonUrl:null});return s;}

test('repair position does not block pure reposition walk and remains repair',async()=>{
  const root=await tmp();await seed(root,70,Array.from({length:64},(_,i)=>i+1));
  const browser=new NoSidebarBrowser(lessons(70),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{await runner.boot({resume:true,requireDownloader:false});runner.repairPositions.add(15);const observed=await runner.ensurePageAt(65);assert.equal(observed.currentPosition,65);assert.equal(browser.stats.goToPosition,0);assert.equal(browser.stats.clickNext,64);assert.equal(runner.repairPositions.has(15),true);assert.equal(runner.state.hasTerminal(15),true);}finally{await runner.dispose();}
});

test('missing manifest position can be crossed without being committed',async()=>{
  const root=await tmp();const positions=Array.from({length:64},(_,i)=>i+1).filter(p=>p!==15);await seed(root,70,positions);
  const browser=new NoSidebarBrowser(lessons(70),{startPosition:1});
  const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
  try{await runner.boot({resume:true,requireDownloader:false});assert.equal(runner.state.hasTerminal(15),false);const observed=await runner.ensurePageAt(65);assert.equal(observed.currentPosition,65);assert.equal(browser.stats.goToPosition,0);assert.equal(browser.stats.clickNext,64);assert.equal(runner.state.hasTerminal(15),false,'navigation must not commit missing lesson');assert.equal(runner.navigationIndex.get(15),'https://www.xcursos.com/aula/15','observed navigation may learn URL');}finally{await runner.dispose();}
});
