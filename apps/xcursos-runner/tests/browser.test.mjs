import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { PlaywrightBrowser, isLessonUrl } from '../src/playwright-browser.mjs';

const fixture=await fs.readFile(new URL('../test-fixtures/xcursos-real.htm',import.meta.url),'utf8');
const lessonUrl='https://www.xcursos.com/curso/venda-todo-santo-dia-leandro-ladeira/aula/0fab13fe-de80-47b9-a105-d0de0171ad80';
const isLessonLike=url=>String(url).includes('/curso/')&&String(url).includes('/aula/');

class FakeLocator {
  constructor({count=0,onClick=null}={}){this._count=count;this.onClick=onClick;}
  filter(){return this;}first(){return this;}async count(){return this._count;}async click(){await this.onClick?.();}async waitFor(){}
}
class FakePage {
  constructor({url=lessonUrl,html=fixture,title='Assistir Aula | XCURSOS',positionTexts=[],liveVideoUrl='https://cdn.example/live.mp4?X-Amz-Signature=secret',redirectTo=null}={}){this._url=url;this.redirectTo=redirectTo;this._html=html;this._title=title;this.liveVideoUrl=liveVideoUrl;this.closed=false;this.positionTexts=[...positionTexts];this.gotoCalls=[];this.reloadCalls=0;this.nextClicks=0;}
  url(){return this._url;}isClosed(){return this.closed;}async title(){return this._title;}async content(){return this._html;}
  locator(sel){if(sel==='body')return new FakeLocator({count:1});return new FakeLocator();}
  getByRole(role,{name}={}){if(role==='button'&&String(name).includes('Próxima'))return new FakeLocator({count:1,onClick:async()=>{this.nextClicks++;}});return new FakeLocator();}
  getByText(){return new FakeLocator();}async waitForFunction(){}
  async evaluate(fn){const src=String(fn);if(src.includes('querySelectorAll'))return{videoUrl:this.liveVideoUrl,iframeUrl:null,pageUrl:this._url,pageTitle:this._title};return this.positionTexts.length?this.positionTexts.shift():'5 / 198';}
  async goto(url){this.gotoCalls.push(url);this._url=this.redirectTo||url;if(isLessonLike(this._url)){this._html=fixture;this._title='Assistir Aula | XCURSOS';}}
  async reload(){this.reloadCalls++;}async bringToFront(){}
}
class FakeContext {
  constructor(pages=[]){this._pages=pages;this.closed=false;this.defaultTimeout=null;this.defaultNavTimeout=null;}
  pages(){return this._pages;}async newPage(){const p=new FakePage({url:'about:blank',html:'<html><body></body></html>',title:''});this._pages.push(p);return p;}
  setDefaultTimeout(v){this.defaultTimeout=v;}setDefaultNavigationTimeout(v){this.defaultNavTimeout=v;}async close(){this.closed=true;}
}
class FakeBrowser {
  constructor(context){this.context=context;this.disconnected=false;}
  contexts(){return [this.context];}
  async close(){this.disconnected=true;}
}
function loader(context,capture={}){return async()=>({chromium:{
  async connectOverCDP(endpoint,options){capture.endpoint=endpoint;capture.options=options;capture.browser=new FakeBrowser(context);return capture.browser;}
}});}


test('Playwright adapter attaches to external human Chrome over local CDP and disconnects without closing context',async()=>{
  const capture={};const ctx=new FakeContext([new FakePage()]);
  const b=new PlaywrightBrowser({profileDir:'C:/Profiles/XCursos',cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(ctx,capture)});
  await b.connect();
  assert.equal(capture.endpoint,'http://127.0.0.1:9222');
  assert.equal(b.capabilities.externalChrome,true);assert.equal(b.capabilities.mcp,false);assert.equal(b.capabilities.engine,'playwright-cdp');
  await b.close();assert.equal(capture.browser.disconnected,true);assert.equal(ctx.closed,false);
});

test('Playwright adapter parses real XCursos fixture and prefers live currentSrc over HTML media',async()=>{
  const p=new FakePage();const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(new FakeContext([p]))});
  await b.connect();const lesson=await b.inspectLesson(b.ref(p));
  assert.equal(lesson.courseName,'VENDA TODO SANTO DIA 2026 - LEANDRO LADEIRA');assert.equal(lesson.lessonTitle,'Visão Geral');assert.equal(lesson.currentPosition,5);assert.equal(lesson.totalPositions,198);
  assert.equal(lesson.videoUrl,'https://cdn.example/live.mp4?X-Amz-Signature=secret');assert.equal(lesson.mediaType,'DIRECT_MP4');await b.close();
});

test('Playwright CDP inspection falls back to parsed direct MP4 when live currentSrc is blob',async()=>{
  const p=new FakePage({liveVideoUrl:'blob:https://www.xcursos.com/abc'});const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(new FakeContext([p]))});
  await b.connect();const lesson=await b.inspectLesson(b.ref(p));assert.equal(lesson.mediaType,'DIRECT_MP4');assert.match(lesson.videoUrl,/^https:\/\/.*r2\.cloudflarestorage\.com\//);await b.close();
});

test('Playwright CDP chooseWorkingPage opens exact preferred lesson URL in human Chrome context',async()=>{
  const blank=new FakePage({url:'about:blank',html:'<html><body></body></html>',title:''});const ctx=new FakeContext([blank]);const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(ctx)});
  const chosen=await b.chooseWorkingPage({preferredUrl:lessonUrl});assert.equal(chosen.page.url,lessonUrl);assert.equal(blank.gotoCalls.at(-1),lessonUrl);assert.equal(chosen.lesson.currentPosition,5);await b.close();
});

test('Playwright CDP navigation reports AUTH_REQUIRED when XCursos redirects away from lesson',async()=>{
  const p=new FakePage({url:'about:blank',html:'<html><body></body></html>',redirectTo:'https://www.xcursos.com/login'});const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(new FakeContext([p]))});
  await b.connect();await assert.rejects(()=>b.navigateExact(b.ref(p),lessonUrl),e=>e.code==='AUTH_REQUIRED');await b.close();
});

test('Playwright CDP full-position reposition refuses unproven sidebar indexing',async()=>{const p=new FakePage();const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(new FakeContext([p]))});await b.connect();await assert.rejects(()=>b.goToPosition(b.ref(p),1),e=>e.code==='POSITION_REPOSITION_UNAVAILABLE');await b.close();});

test('Playwright CDP Next uses locator click and exact target observation',async()=>{
  const p=new FakePage({positionTexts:['5 / 198','6 / 198']});const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(new FakeContext([p])),limits:{transitionPollMs:1}});await b.connect();const ref=b.ref(p);await b.clickNext(ref);assert.equal(p.nextClicks,1);const l=await b.waitForPosition(ref,6,{timeoutMs:50,pollMs:1});assert.equal(l.currentPosition,5);await b.close();
});

test('Playwright CDP refuses non-local debugging endpoint',()=>{assert.throws(()=>new PlaywrightBrowser({cdpEndpoint:'http://192.168.1.50:9222'}),e=>e.code==='CDP_ENDPOINT_NOT_LOCAL');});

test('isLessonUrl accepts only XCursos lesson routes',()=>{assert.equal(isLessonUrl(lessonUrl),true);assert.equal(isLessonUrl('https://www.xcursos.com/curso/x'),false);assert.equal(isLessonUrl('https://evil.example/curso/x/aula/y'),false);});

test('Playwright CDP reconnects when the previous Browser connection is no longer connected',async()=>{
  const p1=new FakePage({url:'about:blank',html:'<html><body></body></html>',title:''});
  const p2=new FakePage({url:lessonUrl});
  const contexts=[new FakeContext([p1]),new FakeContext([p2])];
  const browsers=[];let connects=0;
  const playwrightLoader=async()=>({chromium:{
    async connectOverCDP(){
      const context=contexts[Math.min(connects,contexts.length-1)];
      const browser=new FakeBrowser(context);browser._connected=true;browser.isConnected=()=>browser._connected;
      browsers.push(browser);connects++;return browser;
    }
  }});
  const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader});
  await b.connect();assert.equal(connects,1);
  browsers[0]._connected=false;
  const refs=await b.pages();
  assert.equal(connects,2);assert.equal(refs.some(r=>r.url===lessonUrl),true);
  await b.close();
});

test('Playwright CDP media refresh recovers a closed lesson target and reloads the same lesson in another page',async()=>{
  const broken=new FakePage({url:lessonUrl});
  broken.reload=async()=>{broken.closed=true;throw new Error('page.reload: Target page, context or browser has been closed');};
  const spare=new FakePage({url:'about:blank',html:'<html><body></body></html>',title:''});
  const ctx=new FakeContext([broken,spare]);
  const b=new PlaywrightBrowser({cdpEndpoint:'http://127.0.0.1:9222',playwrightLoader:loader(ctx)});
  await b.connect();
  const recovered=await b.refreshSameLesson(b.ref(broken));
  assert.equal(recovered.url,lessonUrl);assert.equal(spare.gotoCalls.at(-1),lessonUrl);assert.equal(recovered.handle,spare);
  await b.close();
});
