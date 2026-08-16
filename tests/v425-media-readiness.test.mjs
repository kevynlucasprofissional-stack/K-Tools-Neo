import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { parseXcursosLessonHtml, normalizeLiveLessonMeta } from '../src/parser.mjs';
import { LessonScheduler } from '../src/lesson-scheduler.mjs';
import { MediaDownloader } from '../src/downloader.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-v425-'));}

const GTM='https://www.googletagmanager.com/ns.html?id=GTM-M2DB2F7P';

test('V4.2.5: Google Tag Manager iframe is never classified as lesson media',()=>{
  const html=`<h2>Course</h2><h1>e_Aula</h1><span>108 / 198</span><iframe src="${GTM}"></iframe>`;
  const r=parseXcursosLessonHtml(html);
  assert.equal(r.videoUrl,null);
  assert.equal(r.mediaType,'NONE');
  assert.equal(r.mediaSourceConfidence,'UNTRUSTED');
  assert.equal(r.hasUntrustedIframe,true);
});

test('V4.2.5: multiple analytics/tracking iframes are ignored as lesson media',()=>{
  const html='<h2>Course</h2><h1>e_Aula</h1><span>108 / 198</span>'+
    '<iframe src="https://www.googletagmanager.com/ns.html?id=GTM-X"></iframe>'+
    '<iframe src="https://stats.doubleclick.net/frame"></iframe>'+
    '<iframe src="https://connect.facebook.net/frame"></iframe>';
  const r=parseXcursosLessonHtml(html);
  assert.equal(r.videoUrl,null);
  assert.equal(r.mediaType,'NONE');
  assert.equal(r.hasUntrustedIframe,true);
});

test('V4.2.5: live normalization does not promote analytics iframe to EXTERNAL_IFRAME',()=>{
  const r=normalizeLiveLessonMeta({courseName:'Course',lessonTitle:'e_Aula',currentPosition:108,totalPositions:198,videoUrl:null,iframeUrl:GTM});
  assert.equal(r.videoUrl,null);
  assert.equal(r.mediaType,'NONE');
  assert.equal(r.mediaSourceConfidence,'UNTRUSTED');
});

test('V4.2.5: recognized player iframe remains supported',()=>{
  const r=parseXcursosLessonHtml('<h2>C</h2><h1>A</h1>1/2<iframe src="https://player.vimeo.com/video/123"></iframe>');
  assert.equal(r.mediaType,'EXTERNAL_IFRAME');
  assert.equal(r.mediaSourceConfidence,'SUPPORTED_IFRAME');
  assert.match(r.videoUrl,/vimeo/);
});

test('V4.2.5: runner waits for proven media instead of committing NO_VIDEO while player is still loading',async()=>{
  const root=await tmp();
  const pending=lesson(1,1,{video:false,materials:true,title:'e_Aula'});
  const ready=lesson(1,1,{video:true,materials:true,signed:true,title:'e_Aula'});
  class DelayedBrowser extends FakeBrowser{
    constructor(){super([pending]);this.waitCalls=0;}
    async waitForMediaReady(){this.waitCalls++;this.lessons[0]=ready;return this._lesson();}
  }
  const browser=new DelayedBrowser();const downloader=new DiskFakeDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaReadyTimeoutMs:10,mediaReadyPollMs:1}});
  const result=await r.runCurrent({resume:true});
  assert.equal(browser.waitCalls,1);
  assert.equal(result.status,'DOWNLOADED');
  await r.dispose();
});

test('V4.2.5: production-style polling waits through GTM-only state until signed MP4 appears',async()=>{
  const root=await tmp();
  const pending={...lesson(1,1,{video:false,materials:true,title:'e_Aula'}),hasUntrustedIframe:true,mediaSourceConfidence:'UNTRUSTED'};
  const ready={...lesson(1,1,{video:true,materials:true,signed:true,title:'e_Aula'}),mediaSourceConfidence:'PROVEN'};
  class PollingBrowser extends FakeBrowser{
    async inspectLesson(){this.stats.inspect++;if(this.stats.inspect>=2)this.lessons[0]=ready;return this._lesson();}
  }
  const browser=new PollingBrowser([pending]);const downloader=new DiskFakeDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaReadyTimeoutMs:50,mediaReadyPollMs:1}});
  const result=await r.runCurrent({resume:true});
  assert.equal(result.status,'DOWNLOADED');
  assert.equal(downloader.calls.length,1);
  await r.dispose();
});

test('V4.2.5: untrusted media can never reach the downloader',async()=>{
  const root=await tmp();
  const unsafe={...lesson(1,1,{video:false,materials:true,title:'e_Aula'}),videoUrl:GTM,mediaType:'UNKNOWN',mediaSource:'iframe',mediaSourceConfidence:'UNTRUSTED',hasUntrustedIframe:true};
  const browser=new FakeBrowser([unsafe]);const downloader=new DiskFakeDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaReadyTimeoutMs:0,mediaReadyPollMs:1,downloadRetries:0}});
  const result=await r.runCurrent({resume:true});
  assert.equal(result.status,'MEDIA_NOT_READY');
  assert.equal(downloader.calls.length,0);
  await r.dispose();
});

test('V4.2.5: VERIFY_FAILED on signed MP4 refreshes same lesson and performs clean redownload',async()=>{
  const root=await tmp();const browser=new FakeBrowser([lesson(1,1,{signed:true,title:'e_Aula'})]);
  class CorruptOnceDownloader extends DiskFakeDownloader{
    constructor(){super();this.cleanFlags=[];this.n=0;}
    async download(args){
      this.cleanFlags.push(Boolean(args.cleanStart));this.n++;
      if(this.n===1){await fs.mkdir(args.paths.moduleDir,{recursive:true});const finalPath=path.join(args.paths.moduleDir,`${args.paths.baseName}.mp4`);await fs.writeFile(finalPath,'CORRUPT');return{ok:true,finalPath,stdout:finalPath,stderr:''};}
      return await super.download(args);
    }
  }
  const downloader=new CorruptOnceDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaRefreshRetries:1,downloadRetries:0}});
  const result=await r.runCurrent({resume:true});
  assert.equal(result.status,'DOWNLOADED');
  assert.equal(browser.stats.refresh,1);
  assert.equal(downloader.n,2);
  assert.deepEqual(downloader.cleanFlags,[false,true]);
  await r.dispose();
});

test('V4.2.5: generic yt-dlp failure on proven signed MP4 gets one safe refresh',async()=>{
  const root=await tmp();const browser=new FakeBrowser([lesson(1,1,{signed:true,title:'e_Aula'})]);
  class GenericOnceDownloader extends DiskFakeDownloader{
    constructor(){super();this.n=0;}
    async download(args){this.n++;if(this.n===1)return{ok:false,kind:'FAILED',failureCode:'YTDLP_FAILED',code:1,diagnosticTail:'generic failure'};return await super.download(args);}
  }
  const downloader=new GenericOnceDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaRefreshRetries:1,downloadRetries:0}});
  const result=await r.runCurrent({resume:true});
  assert.equal(result.status,'DOWNLOADED');
  assert.equal(browser.stats.refresh,1);
  assert.equal(downloader.n,2);
  await r.dispose();
});

test('V4.2.5: persistent ffprobe failure exposes its concrete verify code in failureSummary',async()=>{
  const root=await tmp();const browser=new FakeBrowser([lesson(1,1,{signed:true,title:'e_Aula'})]);
  class VerifyCodeDownloader extends DiskFakeDownloader{
    async validateVideo(){const error=new Error('sem stream de vídeo ou duração positiva');error.code='VERIFY_NO_VIDEO_STREAM';throw error;}
  }
  const downloader=new VerifyCodeDownloader();
  const r=new XCursosCourseRunner({outputRoot:root,browser,downloader,limits:{mediaRefreshRetries:0,downloadRetries:0}});
  const result=await r.runRange({start:1,end:1,resume:true,finalAudit:false});
  assert.equal(result.status,'RANGE_PARTIAL');
  assert.deepEqual(result.failureSummary,[{code:'VERIFY_NO_VIDEO_STREAM',count:1,positions:[1]}]);
  await r.dispose();
});

test('V4.2.5: cleanStart instructs yt-dlp not to resume partial bytes',async()=>{
  let argsSeen=null;
  const moduleDir=await tmp();
  const d=new MediaDownloader({ytDlpPath:'yt-dlp',ffprobePath:'ffprobe',processRunner:async(_cmd,args)=>{argsSeen=args;return{code:1,stdout:'',stderr:'failed'};}});
  await d.download({mediaUrl:'https://cdn.example/108.mp4',refererUrl:'https://www.xcursos.com/aula/108',paths:{moduleDir,baseName:'108 - e_Aula',template:path.join(moduleDir,'108 - e_Aula.%(ext)s')},cleanStart:true});
  assert.ok(argsSeen.includes('--no-continue'));
  assert.equal(argsSeen.includes('--continue'),false);
});

test('V4.2.5: BLOCKED checkpoint starts a fresh retry budget on a new scheduler execution',()=>{
  const checkpoint={schedulerVersion:1,ready:[],retryLater:[],inFlight:[],blocked:[{position:1,status:'BLOCKED',attempts:9,priority:-30,lastError:{code:'VERIFY_FAILED'}}]};
  const s=new LessonScheduler({total:1});s.reconcile({donePositions:[],checkpoint});
  assert.equal(s.get(1).status,'READY');
  assert.equal(s.get(1).attempts,0);
  assert.equal(s.claimNext().task.attempts,1);
});

test('V4.2.5: no-progress fingerprint is coverage-based, not failure-label-based',async()=>{
  const ps=await fs.readFile(new URL('../download-all.ps1',import.meta.url),'utf8');
  const fn=ps.match(/function Get-FailureFingerprint[\s\S]*?\n\}/)?.[0]||'';
  assert.match(fn,/downloaded=/i);
  assert.match(fn,/processed=/i);
  assert.match(fn,/missing=/i);
  assert.doesNotMatch(fn,/causes=/i);
});
