import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { BrowserAutomationError } from '../src/errors.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';
async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-v42-fake-'));}
function course(){return Array.from({length:10},(_,i)=>{const p=i+1;return lesson(p,10,{signed:p===2||p===8,video:p!==5,materials:p===5,module:p<=5?'1. Start':'2. Advanced',title:p===9?'Continue to next lesson':`Lesson ${p}`});});}
class MixedDownloader extends DiskFakeDownloader{
  async download(opts){const m=opts.mediaUrl.match(/\/(\d+)\.mp4/);const p=Number(m?.[1]||0);if(p===3&&!this.once3){this.once3=true;this.calls.push({pos:3,attempt:1,mediaUrl:opts.mediaUrl});return{ok:false,kind:'FAILED',code:1,stderr:'timeout'};}return await super.download(opts);}
}
class ResilientBrowser extends FakeBrowser{
  async clickNext(){if(this.current===6&&!this.closedOnce){this.closedOnce=true;throw new BrowserAutomationError('Target page, context or browser has been closed',{code:'PAGE_CLOSED'});}return await super.clickNext();}
}

test('fake 10-course completes with retry, NO_VIDEO, module change, page-close recovery and expired media',async()=>{
  const root=await tmp();const d=new MixedDownloader({expiredOncePositions:[8]});const b=new ResilientBrowser(course());const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:d,limits:{navigationRetries:1,retryBaseDelayMs:1,retryMaxDelayMs:5}});const result=await r.runCourse({resume:true});
  assert.equal(result.status,'COMPLETE');assert.equal(result.audit.processed,10);assert.equal(result.audit.noVideo,1);assert.deepEqual(result.audit.missingPositions,[]);assert.equal(result.audit.duplicatePositions.length,0);assert.ok(b.stats.recover>=1);assert.ok(d.calls.filter(x=>x.pos===3).length>=2);assert.ok(d.calls.filter(x=>x.pos===8).length>=2);await r.dispose();
});

test('fake course crash checkpoint at position 4 restarts without redownloading committed prefix',async()=>{
  const root=await tmp();const ls=course();const d1=new DiskFakeDownloader();const r1=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(ls),downloader:d1,limits:{retryBaseDelayMs:1}});await r1.runRange({start:1,end:3,resume:true});await r1.dispose();
  const d2=new DiskFakeDownloader();const r2=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(ls,{startPosition:3}),downloader:d2,limits:{retryBaseDelayMs:1}});const result=await r2.runCourse({resume:true});assert.equal(result.status,'COMPLETE');assert.equal(d2.calls.some(x=>[1,2,3].includes(x.pos)),false);const rows=await readJsonlFile(r2.state.manifestPath);assert.equal(new Set(rows.map(x=>x.position)).size,10);await r2.dispose();
});
