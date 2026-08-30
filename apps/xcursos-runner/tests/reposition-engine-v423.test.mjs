import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore } from '../src/state.mjs';
import { NavigationIndex } from '../src/navigation-index.mjs';
import { BrowserAutomationError } from '../src/errors.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';
async function tmp(){return fs.mkdtemp(path.join(os.tmpdir(),'xc-repos423-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}
async function state(root,total=90){const s=new StateStore({outputRoot:root,courseName:'Fake Course',totalPositions:total});await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/80'});return s;}
async function nav(s,entries=[]){const n=new NavigationIndex({filePath:s.navigationPath,courseName:'Fake Course',totalPositions:s.totalPositions});await n.load();for(const [p,u] of entries)await n.record(p,u);return n;}
class NoSidebarBrowser extends FakeBrowser{async goToPosition(){this.stats.goToPosition++;throw new BrowserAutomationError('sidebar disabled',{code:'POSITION_REPOSITION_UNAVAILABLE'});}}

test('browser above target opens nearest checkpoint then walks to target',async()=>{
 const root=await tmp(),s=await state(root);await nav(s,[[40,'https://www.xcursos.com/aula/40']]);const b=new NoSidebarBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
 try{await r.boot({resume:true,requireDownloader:false});const l=await r.ensurePageAt(65);assert.equal(l.currentPosition,65);assert.equal(b.stats.goToPosition,0);assert.equal(b.stats.clickNext,25);}finally{await r.dispose();}
});

test('browser above target uses course anchor when no checkpoint before target exists',async()=>{
 const root=await tmp(),s=await state(root);await nav(s,[[1,'https://www.xcursos.com/aula/1']]);const b=new NoSidebarBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
 try{await r.boot({resume:true,requireDownloader:false});const l=await r.ensurePageAt(65);assert.equal(l.currentPosition,65);assert.equal(b.stats.clickNext,64);assert.equal(b.stats.goToPosition,0);}finally{await r.dispose();}
});

test('stale exact target URL is invalidated and another strategy reaches target',async()=>{
 const root=await tmp(),s=await state(root);await nav(s,[[1,'https://www.xcursos.com/aula/1'],[65,'https://www.xcursos.com/aula/stale-65']]);
 class StaleBrowser extends NoSidebarBrowser{async navigateExact(page,url){if(String(url).includes('stale-65')){this.current=66;this.page.url='https://www.xcursos.com/aula/66';return this.page;}return super.navigateExact(page,url);}}
 const b=new StaleBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader(),limits:{transitionTimeoutMs:20,transitionPollMs:1}});
 try{await r.boot({resume:true,requireDownloader:false});const l=await r.ensurePageAt(65);assert.equal(l.currentPosition,65);assert.equal(r.navigationIndex.get(65),'https://www.xcursos.com/aula/65');}finally{await r.dispose();}
});

test('exact indexed URL opening another course is rejected as COURSE_IDENTITY_MISMATCH',async()=>{
 const root=await tmp(),s=await state(root);await nav(s,[[65,'https://www.xcursos.com/aula/65']]);
 class OtherCourseBrowser extends NoSidebarBrowser{async navigateExact(page,url){await super.navigateExact(page,url);this.other=true;return this.page;}async inspectLesson(page){const l=await super.inspectLesson(page);return this.other?{...l,courseName:'Other Course'}:l;}}
 const b=new OtherCourseBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});try{await r.boot({resume:true,requireDownloader:false});await assert.rejects(()=>r.ensurePageAt(65),e=>e?.code==='COURSE_IDENTITY_MISMATCH');}finally{await r.dispose();}
});

test('no available route returns POSITION_REPOSITION_NO_SAFE_PATH with diagnostics and never calls sidebar',async()=>{
 const root=await tmp();await state(root);const b=new NoSidebarBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});try{await r.boot({resume:true,requireDownloader:false});await assert.rejects(()=>r.ensurePageAt(65),e=>{assert.equal(e.code,'POSITION_REPOSITION_NO_SAFE_PATH');assert.equal(e.details.currentPosition,80);assert.equal(e.details.targetPosition,65);assert.ok(Array.isArray(e.details.strategiesTried));return true;});assert.equal(b.stats.goToPosition,0);}finally{await r.dispose();}
});

test('AUTH_REQUIRED from inspectLesson is propagated instead of masked by reposition error',async()=>{
 const root=await tmp();await state(root);class AuthBrowser extends NoSidebarBrowser{async inspectLesson(){throw new BrowserAutomationError('login',{code:'AUTH_REQUIRED'});}}const b=new AuthBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});
 // boot cannot use inspect failure, so flip it only after boot
 b.inspectLesson=FakeBrowser.prototype.inspectLesson.bind(b);try{await r.boot({resume:true,requireDownloader:false});b.inspectLesson=async()=>{throw new BrowserAutomationError('login',{code:'AUTH_REQUIRED'});};await assert.rejects(()=>r.ensurePageAt(65),e=>e?.code==='AUTH_REQUIRED');}finally{await r.dispose();}
});

test('CLOUDFLARE_REQUIRED from inspectLesson is propagated instead of masked',async()=>{
 const root=await tmp();await state(root);const b=new NoSidebarBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});
 try{await r.boot({resume:true,requireDownloader:false});b.inspectLesson=async()=>{throw new BrowserAutomationError('human challenge',{code:'CLOUDFLARE_REQUIRED'});};await assert.rejects(()=>r.ensurePageAt(65),e=>e?.code==='CLOUDFLARE_REQUIRED');}finally{await r.dispose();}
});

test('exact indexed URL with changed TOTAL is rejected as TOTAL_CHANGED',async()=>{
 const root=await tmp(),s=await state(root);await nav(s,[[65,'https://www.xcursos.com/aula/65']]);class TotalBrowser extends NoSidebarBrowser{async navigateExact(page,url){await super.navigateExact(page,url);this.changed=true;return this.page;}async inspectLesson(page){const l=await super.inspectLesson(page);return this.changed?{...l,totalPositions:91}:l;}}
 const b=new TotalBrowser(lessons(90),{startPosition:80});const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:new DiskFakeDownloader()});try{await r.boot({resume:true,requireDownloader:false});await assert.rejects(()=>r.ensurePageAt(65),e=>e?.code==='TOTAL_CHANGED');}finally{await r.dispose();}
});
