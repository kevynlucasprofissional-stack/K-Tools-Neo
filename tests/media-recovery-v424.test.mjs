import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-media-v424-'));}

class NetworkResetOnceDownloader extends DiskFakeDownloader{
  async download(args){
    const m=args.mediaUrl.match(/\/(\d+)\.mp4/);const pos=Number(m?.[1]||0);const attempt=(this.attemptByPos.get(pos)||0)+1;
    if(attempt===1){this.attemptByPos.set(pos,attempt);this.calls.push({pos,attempt,mediaUrl:args.mediaUrl});return{ok:false,kind:'FAILED',failureCode:'NETWORK_RESET',code:1,diagnosticTail:'Connection reset by peer'};}
    return await super.download(args);
  }
}

class Persistent403Downloader extends DiskFakeDownloader{
  async download(args){const m=args.mediaUrl.match(/\/(\d+)\.mp4/);const pos=Number(m?.[1]||0);const attempt=(this.attemptByPos.get(pos)||0)+1;this.attemptByPos.set(pos,attempt);this.calls.push({pos,attempt,mediaUrl:args.mediaUrl});return{ok:false,kind:'EXPIRED',failureCode:'HTTP_403',code:1,diagnosticTail:'HTTP Error 403 https://cdn/108.mp4?X-Amz-Signature=SECRET'};}
}

test('V4.2.4 RED: signed direct MP4 network-reset triggers same-lesson media refresh before scheduler-level failure',async()=>{
  const root=await tmp();const ls=[lesson(1,2,{signed:true}),lesson(2,2,{signed:true})];const browser=new FakeBrowser(ls);const downloader=new NetworkResetOnceDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader});const result=await r.runCurrent({resume:true});
  assert.equal(result.ok,true);assert.ok(['DOWNLOADED','ALREADY_PRESENT'].includes(result.status));assert.equal(browser.stats.refresh,1);assert.equal(downloader.calls.length,2);await r.dispose();
});

test('V4.2.4 RED: persistent download failure is written with sanitized diagnostic cause and surfaced in failure summary',async()=>{
  const root=await tmp();const ls=[lesson(1,1,{signed:true})];const browser=new FakeBrowser(ls);const downloader=new Persistent403Downloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{downloadRetries:0,mediaRefreshRetries:1}});const result=await r.runRange({start:1,end:1,resume:true});
  assert.equal(result.ok,false);assert.equal(result.retryableFailures[0].failureCode,'HTTP_403');assert.deepEqual(result.failureSummary,[{code:'HTTP_403',count:1,positions:[1]}]);
  const errors=await readJsonlFile(r.state.errorsPath);const dl=errors.find(x=>x.scope==='DOWNLOAD');assert.equal(dl.failureCode,'HTTP_403');assert.match(dl.diagnosticTail,/403/);assert.equal(JSON.stringify(dl).includes('SECRET'),false);await r.dispose();
});

test('V4.2.4 RED: download error record carries sanitized media correlation diagnostics',async()=>{
  const root=await tmp();const ls=[lesson(1,1,{signed:true})];const browser=new FakeBrowser(ls);browser.mediaDiagnostics=()=>({generation:7,selectedSource:'live',correlation:{sameObject:false},networkObjectFingerprint:'abc123',liveObjectFingerprint:'def456'});const downloader=new Persistent403Downloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{downloadRetries:0,mediaRefreshRetries:0}});await r.runRange({start:1,end:1,resume:true});const errors=await readJsonlFile(r.state.errorsPath);const dl=errors.find(x=>x.scope==='DOWNLOAD');assert.equal(dl.mediaDiagnostics.generation,7);assert.equal(dl.mediaDiagnostics.correlation.sameObject,false);await r.dispose();
});

test('V4.2.4 RED: probe surfaces media diagnostics without exposing media URL',async()=>{
  const ls=[lesson(1,2,{signed:true})];const browser=new FakeBrowser(ls);browser.mediaDiagnostics=()=>({generation:2,selectedSource:'network.response',correlation:{sameObject:true},networkObjectFingerprint:'abc123',liveObjectFingerprint:'abc123'});
  const r=new XCursosCourseRunner({browser,outputRoot:await tmp(),downloader:new DiskFakeDownloader()});const result=await r.probe();assert.equal(result.mediaDiagnostics.generation,2);assert.equal(result.mediaDiagnostics.correlation.sameObject,true);assert.equal(JSON.stringify(result.mediaDiagnostics).includes('https://'),false);
});

test('V4.2.4 RED: downloadCourse BLOCKED result exposes aggregated failureSummary',async()=>{
  const { downloadCourse }=await import('../src/runner.mjs');const root=await tmp();const browser=new FakeBrowser([lesson(1,1,{signed:true})]);const downloader=new Persistent403Downloader();
  const result=await downloadCourse({outputRoot:root,browser,downloader,limits:{downloadRetries:0,mediaRefreshRetries:0}});assert.equal(result.status,'BLOCKED');assert.deepEqual(result.failureSummary,[{code:'HTTP_403',count:1,positions:[1]}]);
});

test('V4.2.4 media refresh refuses a different video object for the same position',async()=>{
  const root=await tmp();const base=lesson(1,1,{signed:true,url:'https://cdn.example/1.mp4?X-Amz-Signature=OLD'});const browser=new FakeBrowser([base]);let afterRefresh=false;const originalRefresh=browser.refreshSameLesson.bind(browser);browser.refreshSameLesson=async()=>{afterRefresh=true;return await originalRefresh();};const originalInspect=browser.inspectLesson.bind(browser);browser.inspectLesson=async page=>{const x=await originalInspect(page);return afterRefresh?{...x,videoUrl:'https://cdn.example/DIFFERENT.mp4?X-Amz-Signature=NEW'}:x;};const downloader=new Persistent403Downloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{downloadRetries:0,mediaRefreshRetries:1}});await assert.rejects(()=>r.runCurrent({resume:true}),e=>e.code==='MEDIA_REFRESH_OBJECT_CHANGED');assert.equal(downloader.calls.length,1);await r.dispose();
});

class FailOnceThenSuccessDownloader extends DiskFakeDownloader{
  async download(args){const m=args.mediaUrl.match(/\/(\d+)\.mp4/);const pos=Number(m?.[1]||0);const attempt=(this.attemptByPos.get(pos)||0)+1;if(attempt===1){this.attemptByPos.set(pos,1);this.calls.push({pos,attempt,mediaUrl:args.mediaUrl});return{ok:false,kind:'FAILED',failureCode:'YTDLP_FAILED',code:1,diagnosticTail:'temporary generic failure'};}return await super.download(args);}
}

test('V4.2.4 RED: failureSummary forgets a transient failure after the same position succeeds later in the scheduler run',async()=>{
  const root=await tmp();const browser=new FakeBrowser([lesson(1,1,{signed:false})]);const downloader=new FailOnceThenSuccessDownloader();const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{downloadRetries:2,retryBaseDelayMs:0,retryMaxDelayMs:1}});const result=await r.runRange({start:1,end:1,resume:true});assert.equal(result.ok,true);assert.deepEqual(result.retryableFailures,[]);assert.deepEqual(result.failureSummary,[]);await r.dispose();
});
