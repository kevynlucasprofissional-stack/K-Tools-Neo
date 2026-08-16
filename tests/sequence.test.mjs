import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { BrowserAutomationError } from '../src/errors.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-seq-'));}
function makeLessons(n,opts={}){return Array.from({length:n},(_,i)=>lesson(i+1,n,typeof opts==='function'?opts(i+1):opts));}
async function run(lessons,{browserOpts={},downloaderOpts={},start=1,end=lessons.length}={}){const outputRoot=await tmp();const browser=new FakeBrowser(lessons,browserOpts);const downloader=new DiskFakeDownloader(downloaderOpts);const runner=new XCursosCourseRunner({outputRoot,browser,downloader,limits:{navigationRetries:1,transitionTimeoutMs:10,transitionPollMs:1}});try{return{result:await runner.runRange({start,end,resume:false}),browser,downloader,runner,outputRoot};}finally{await runner.dispose();}}

test('M4 1→5 exactly five positions and four Next transitions',async()=>{const x=await run(makeLessons(5));assert.equal(x.result.audit.processed,5);assert.equal(x.browser.stats.clickNext,4);assert.deepEqual(x.downloader.calls.map(c=>c.pos),[1,2,3,4,5]);assert.deepEqual(x.result.audit.missingPositions,[]);});

test('M4 module changes do not interrupt sequence',async()=>{const lessons=makeLessons(5,p=>({module:p<3?'1. A':'2. B'}));const x=await run(lessons);const manifest=await readJsonlFile(path.join(x.result.courseRoot,'_xcursos-runner','manifest.jsonl'));assert.deepEqual(manifest.map(x=>x.moduleName),['1. A','1. A','2. B','2. B','2. B']);});

test('M4 NO_VIDEO is terminal and next lesson continues',async()=>{const lessons=makeLessons(5,p=>({video:p!==3,materials:p===3}));const x=await run(lessons);assert.equal(x.result.audit.noVideo,1);assert.equal(x.browser.stats.clickNext,4);});

test('M4 download failure remains pending while sequence continues',async()=>{const x=await run(makeLessons(5),{downloaderOpts:{failPositions:[3]}});assert.equal(x.result.status,'RANGE_PARTIAL');assert.equal(x.result.ok,false);assert.deepEqual(x.result.retryableFailures,[{position:3,status:'DOWNLOAD_FAILED'}]);assert.equal(x.result.audit.processed,4);assert.deepEqual(x.result.audit.missingPositions,[3]);});

test('M4 expired signed URL refreshes once then succeeds',async()=>{const lessons=makeLessons(3,p=>({signed:p===2}));const x=await run(lessons,{downloaderOpts:{expiredOncePositions:[2]}});assert.equal(x.browser.stats.refresh,1);assert.equal(x.result.audit.downloaded,3);assert.equal(x.downloader.attemptByPos.get(2),2);});

test('M4 stuck navigation retries once then stops',async()=>{await assert.rejects(()=>run(makeLessons(5),{browserOpts:{transitionPlan:{2:'stuck'}}}),e=>e.code==='POSITION_STUCK');});

test('M4 N→N+2 is POSITION_SKIP and does not continue blindly',async()=>{await assert.rejects(()=>run(makeLessons(5),{browserOpts:{transitionPlan:{2:'skip'}}}),e=>e.code==='POSITION_SKIP');});

test('M4 regression is detected',async()=>{await assert.rejects(()=>run(makeLessons(5),{browserOpts:{transitionPlan:{3:'regress'}}}),e=>e.code==='POSITION_REGRESSION');});

test('M4 1→10 regression sequence',async()=>{const x=await run(makeLessons(10));assert.equal(x.result.audit.processed,10);assert.equal(x.browser.stats.clickNext,9);assert.deepEqual(x.downloader.calls.map(c=>c.pos),[1,2,3,4,5,6,7,8,9,10]);});

test('M3/M4 direct MP4 is not skipped by generic DRM marker',async()=>{const ls=makeLessons(2,p=>({drm:p===1,video:true,mediaType:'DIRECT_MP4'}));const x=await run(ls);assert.equal(x.result.audit.drmProtected,0);assert.equal(x.result.audit.downloaded,2);});

test('M3/M4 DASH with DRM marker is classified without downloader call',async()=>{const ls=makeLessons(2,p=>p===1?{drm:true,video:true,mediaType:'DASH',url:'https://cdn.example/1.mpd'}:{});const x=await run(ls);assert.equal(x.result.audit.drmProtected,1);assert.equal(x.downloader.calls.some(c=>c.pos===1),false);});

test('M4 rejects non-integer ranges',async()=>{const outputRoot=await tmp();const runner=new XCursosCourseRunner({outputRoot,browser:new FakeBrowser(makeLessons(3)),downloader:new DiskFakeDownloader()});await assert.rejects(()=>runner.runRange({start:1.5,end:3,resume:false}),e=>e.code==='RANGE_INVALID');await runner.dispose();});

test('M4 browser target closed during Next is recovered once and sequence continues',async()=>{
  const ls=makeLessons(3);
  class ClosingBrowser extends FakeBrowser {
    constructor(...args){super(...args);this.closedOnce=false;}
    async clickNext(){
      if(!this.closedOnce){this.closedOnce=true;throw new BrowserAutomationError('Target page, context or browser has been closed',{code:'PAGE_CLOSED'});}
      return await super.clickNext();
    }
  }
  const outputRoot=await tmp();const browser=new ClosingBrowser(ls);const downloader=new DiskFakeDownloader();
  const runner=new XCursosCourseRunner({outputRoot,browser,downloader,limits:{navigationRetries:1,transitionTimeoutMs:10,transitionPollMs:1}});
  try{const result=await runner.runRange({start:1,end:3,resume:false});assert.equal(result.status,'RANGE_COMPLETE');assert.ok(browser.stats.recover>=1);}
  finally{await runner.dispose();}
});

test('NEXT_TRANSITION_FAILED from safe PageController path is structural and is not clicked again by runner navigationRetries',async()=>{
  const ls=makeLessons(3);const outputRoot=await tmp();
  class SafeFailBrowser extends FakeBrowser{constructor(...args){super(...args);this.navigateCalls=0;}async navigateNext(){this.navigateCalls++;throw new BrowserAutomationError('Next fallback budget exhausted',{code:'NEXT_TRANSITION_FAILED'});}}
  const browser=new SafeFailBrowser(ls);const runner=new XCursosCourseRunner({outputRoot,browser,downloader:new DiskFakeDownloader(),limits:{navigationRetries:3,transitionTimeoutMs:10,transitionPollMs:1}});
  try{await assert.rejects(()=>runner.runRange({start:1,end:3,resume:false}),e=>e.code==='NEXT_TRANSITION_FAILED');assert.equal(browser.navigateCalls,1);}finally{await runner.dispose();}
});
