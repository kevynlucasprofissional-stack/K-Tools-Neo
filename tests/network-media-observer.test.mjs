import test from 'node:test';
import assert from 'node:assert/strict';
import { NetworkMediaObserver, classifyNetworkMedia } from '../src/network-media-observer.mjs';

class Page{constructor(){this.handlers=new Map();this.order=[];}on(name,fn){this.order.push(`on:${name}`);this.handlers.set(name,fn);}off(name,fn){this.order.push(`off:${name}`);if(this.handlers.get(name)===fn)this.handlers.delete(name);}emit(name,value){return this.handlers.get(name)?.(value);}}
function response(url,{status=200,resourceType='media',headers={}}={}){return{url:()=>url,status:()=>status,request:()=>({resourceType:()=>resourceType}),allHeaders:async()=>headers};}

test('network classifier recognizes MP4, HLS and DASH and rejects materials',()=>{
  assert.equal(classifyNetworkMedia('https://cdn/x.mp4')?.type,'DIRECT_MP4');
  assert.equal(classifyNetworkMedia('https://cdn/x.m3u8')?.type,'HLS');
  assert.equal(classifyNetworkMedia('https://cdn/x.mpd')?.type,'DASH');
  assert.equal(classifyNetworkMedia('https://www.xcursos.com/api/materials/download?lessonId=1'),null);
});

test('observer captures successful signed MP4 without exposing it in snapshot',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);
  await page.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/a/x.mp4?X-Amz-Signature=SECRET'));
  assert.match(o.best(page).url,/SECRET/);const snap=o.snapshot(page);assert.equal(JSON.stringify(snap).includes('SECRET'),false);assert.match(snap[0].url,/sensitive-query-redacted/);
});

test('403 media response is observed but never selected as best usable media',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);await page.emit('response',response('https://cdn/x.mp4',{status:403}));
  assert.equal(o.best(page),null);assert.equal(o.snapshot(page)[0].status,403);
});

test('expired signed URL followed by fresh URL chooses latest successful response',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);
  await page.emit('response',response('https://cdn/x.mp4?X-Amz-Signature=OLD',{status:403}));
  await page.emit('response',response('https://cdn/x.mp4?X-Amz-Signature=NEW',{status:200}));
  assert.match(o.best(page).url,/NEW/);
});

test('multiple video requests prefer latest successful direct media candidate',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);
  await page.emit('response',response('https://cdn/master.m3u8'));
  await page.emit('response',response('https://cdn/final.mp4'));
  assert.equal(o.best(page).type,'DIRECT_MP4');assert.match(o.best(page).url,/final\.mp4$/);
});

test('known XCursos media host can be classified from content-type even without extension',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);
  await page.emit('response',response('https://xcursos-videos.abc.r2.cloudflarestorage.com/videos/a/stream',{headers:{'content-type':'video/mp4'}}));
  assert.equal(o.best(page).type,'DIRECT_MP4');
});

test('observer can be installed before navigation and detached cleanly',()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);page.order.push('goto');assert.deepEqual(page.order.slice(0,2),['on:response','on:requestfailed']);
  o.detach(page);assert.equal(page.handlers.size,0);assert.ok(page.order.includes('off:response'));
});

test('clear removes stale media so a reload can capture a fresh signed URL',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);await page.emit('response',response('https://cdn/old.mp4'));assert.ok(o.best(page));o.clear(page);assert.equal(o.best(page),null);await page.emit('response',response('https://cdn/new.mp4'));assert.match(o.best(page).url,/new\.mp4/);
});

test('PageController source priority is network over blob/DOM fallback when observer captured media',async()=>{
  const { BrowserSession }=await import('../src/browser-session.mjs');
  const { PageController }=await import('../src/page-controller.mjs');
  class L{async waitFor(){}async innerText(){return '';}}
  class P extends Page{constructor(){super();this._url='https://www.xcursos.com/curso/c/aula/1';}url(){return this._url;}isClosed(){return false;}locator(){return new L();}async waitForFunction(){}async title(){return 'Assistir Aula | XCURSOS';}async content(){return '<html><body><h2>Course</h2><h1>Lesson</h1><p>1. Module</p><div>1 / 2</div><video src="blob:https://www.xcursos.com/x"></video></body></html>';}async evaluate(){return{videoUrl:'blob:https://www.xcursos.com/x',pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS'};}mainFrame(){return this;}getByRole(){return{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}}
  const p=new P();const context={pages:()=>[p],setDefaultTimeout(){},setDefaultNavigationTimeout(){}};const browser={contexts:()=>[context],isConnected:()=>true,on(){},close:async()=>{}};
  const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);await controller.pinWorkingPage(ref);
  await p.emit('response',response('https://cdn/network.mp4?X-Amz-Signature=LIVE'));
  const lesson=await controller.inspectLesson(ref);assert.equal(lesson.mediaSource,'network.response');assert.match(lesson.videoUrl,/network\.mp4/);await controller.close();
});

test('V4.2.4 RED: media generation isolates old lesson responses after navigation boundary',async()=>{
  const page=new Page();const o=new NetworkMediaObserver();o.attach(page);
  await page.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/107.mp4?X-Amz-Signature=OLD'));
  assert.match(o.best(page).url,/107\.mp4/);
  const g=o.beginGeneration(page,{reason:'next',lessonUrl:'https://www.xcursos.com/curso/c/aula/108'});
  assert.equal(typeof g,'number');
  assert.equal(o.best(page),null,'old 107 candidate must not be visible in the 108 generation');
  await page.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=NEW'));
  assert.match(o.best(page).url,/108\.mp4/);
  assert.equal(o.best(page).generation,g);
});

test('V4.2.4 RED: PageController does not let stale network media from previous lesson override current direct video.src',async()=>{
  const { BrowserSession }=await import('../src/browser-session.mjs');
  const { PageController }=await import('../src/page-controller.mjs');
  class L{async waitFor(){}async innerText(){return '';}}
  class P extends Page{
    constructor(){super();this._url='https://www.xcursos.com/curso/c/aula/108';}
    url(){return this._url;}isClosed(){return false;}locator(){return new L();}async waitForFunction(){}async title(){return 'Assistir Aula | XCURSOS';}
    async content(){return '<html><body><h2>Course</h2><h1>e_Aula</h1><p>5. VSL</p><div>108 / 198</div><video src="https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOM"></video></body></html>';}
    async evaluate(){return{videoUrl:'https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOM',pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS'};}
    mainFrame(){return this;}getByRole(){return{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}
  }
  const p=new P();const context={pages:()=>[p],setDefaultTimeout(){},setDefaultNavigationTimeout(){}};const browser={contexts:()=>[context],isConnected:()=>true,on(){},close:async()=>{}};
  const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);
  await p.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/107.mp4?X-Amz-Signature=OLD'));
  controller.networkObserver.beginGeneration(p,{reason:'test-lesson-change',lessonUrl:p._url});
  const lesson=await controller.inspectLesson(ref);
  assert.equal(lesson.mediaSource,'live');
  assert.match(lesson.videoUrl,/108\.mp4/);
  assert.doesNotMatch(lesson.videoUrl,/107\.mp4/);
  await controller.close();
});

test('V4.2.4 RED: current-generation network URL may refresh signature only when media object matches current DOM object',async()=>{
  const { BrowserSession }=await import('../src/browser-session.mjs');
  const { PageController }=await import('../src/page-controller.mjs');
  class L{async waitFor(){}async innerText(){return '';}}
  class P extends Page{
    constructor(){super();this._url='https://www.xcursos.com/curso/c/aula/108';}
    url(){return this._url;}isClosed(){return false;}locator(){return new L();}async waitForFunction(){}async title(){return 'Assistir Aula | XCURSOS';}
    async content(){return '<html><body><h2>Course</h2><h1>e_Aula</h1><p>5. VSL</p><div>108 / 198</div><video src="https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOMOLD"></video></body></html>';}
    async evaluate(){return{videoUrl:'https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOMOLD',pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS'};}
    mainFrame(){return this;}getByRole(){return{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}
  }
  const p=new P();const context={pages:()=>[p],setDefaultTimeout(){},setDefaultNavigationTimeout(){}};const browser={contexts:()=>[context],isConnected:()=>true,on(){},close:async()=>{}};
  const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);
  controller.networkObserver.beginGeneration(p,{reason:'current'});
  await p.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=NETNEW'));
  const lesson=await controller.inspectLesson(ref);
  assert.equal(lesson.mediaSource,'network.response');
  assert.match(lesson.videoUrl,/NETNEW/);
  await controller.close();
});

test('V4.2.4 RED: PageController exposes sanitized media correlation diagnostics without signed URL',async()=>{
  const { BrowserSession }=await import('../src/browser-session.mjs');const { PageController }=await import('../src/page-controller.mjs');
  class L{async waitFor(){}async innerText(){return '';}}
  class P extends Page{constructor(){super();this._url='https://www.xcursos.com/curso/c/aula/108';}url(){return this._url;}isClosed(){return false;}locator(){return new L();}async waitForFunction(){}async title(){return 'Assistir Aula | XCURSOS';}async content(){return '<html><body><h2>Course</h2><h1>e_Aula</h1><p>5. VSL</p><div>108 / 198</div><video src="https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOMSECRET"></video></body></html>';}async evaluate(){return{videoUrl:'https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/108.mp4?X-Amz-Signature=DOMSECRET',pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS'};}mainFrame(){return this;}getByRole(){return{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}}
  const p=new P();const context={pages:()=>[p],setDefaultTimeout(){},setDefaultNavigationTimeout(){}};const browser={contexts:()=>[context],isConnected:()=>true,on(){},close:async()=>{}};const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);
  controller.networkObserver.beginGeneration(p,{reason:'current'});await p.emit('response',response('https://xcursos-videos.test.r2.cloudflarestorage.com/videos/course/107.mp4?X-Amz-Signature=NETSECRET'));
  await controller.inspectLesson(ref);const d=controller.mediaDiagnostics(ref);assert.equal(d.correlation.sameObject,false);assert.equal(d.selectedSource,'live');assert.equal(typeof d.liveObjectFingerprint,'string');assert.equal(typeof d.networkObjectFingerprint,'string');assert.equal(JSON.stringify(d).includes('SECRET'),false);assert.equal(JSON.stringify(d).includes('https://'),false);await controller.close();
});
