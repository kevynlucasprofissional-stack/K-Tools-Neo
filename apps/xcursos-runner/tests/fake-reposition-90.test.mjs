import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';import { StateStore } from '../src/state.mjs';import { NavigationIndex } from '../src/navigation-index.mjs';import { FakeBrowser,DiskFakeDownloader,lesson } from './helpers.mjs';
async function tmp(){return fs.mkdtemp(path.join(os.tmpdir(),'xc-fake90-'));}function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}

test('systemic 90-course: checkpoint reposition ignores repair/download gaps and only processes requested pending work',async()=>{
 const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'Fake Course',totalPositions:90});await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/80'});
 for(let p=1;p<=64;p++){if(p===25)continue;if(p===15)await s.commit({position:p,status:'DOWNLOADED',lessonTitle:`Lesson ${p}`,moduleName:'1. Module',outputFile:path.join(root,'missing-015.mp4'),lessonUrl:null});else await s.commit({position:p,status:'NO_VIDEO',lessonTitle:`Lesson ${p}`,moduleName:'1. Module',lessonUrl:null});}
 const idx=new NavigationIndex({filePath:s.navigationPath,courseName:'Fake Course',totalPositions:90});await idx.load();for(const p of [1,20,40])await idx.record(p,`https://www.xcursos.com/aula/${p}`);
 class NoSidebar extends FakeBrowser{async goToPosition(){throw new Error('sidebar must never be used');}}
 const browser=new NoSidebar(lessons(90),{startPosition:80});const dl=new DiskFakeDownloader();const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader:dl,limits:{transitionTimeoutMs:20,transitionPollMs:1}});
 try{const result=await runner.runRange({start:64,end:90,resume:true});assert.equal(result.status,'RANGE_COMPLETE');assert.deepEqual(dl.calls.map(x=>x.pos),Array.from({length:26},(_,i)=>i+65));assert.equal(runner.repairPositions.has(15),true);assert.equal(runner.state.hasTerminal(25),false);assert.equal(result.stats.repositionSteps,25);assert.equal(runner.navigationIndex.get(65),'https://www.xcursos.com/aula/65');assert.equal(browser.current,90);}finally{await runner.dispose();}
});
