import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { HumanChromeLauncher } from '../src/chrome-launcher.mjs';
import { PageController } from '../src/page-controller.mjs';
import { normalizeLiveLessonMeta } from '../src/parser.mjs';
import { MediaDownloader } from '../src/downloader.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-v426-'));}

class Locator{async waitFor(){} async innerText(){return '';}}
class Page{
  constructor(url,targetId){this._url=url;this.targetId=targetId;this.closed=false;this.events=new Map();}
  url(){return this._url;} isClosed(){return this.closed;} locator(){return new Locator();}
  async title(){return 'Assistir Aula | XCURSOS';}
  async content(){return '<html><body><h2>Course</h2><p>1. Module</p><h1>Lesson</h1><div>1 / 2</div></body></html>';}
  async waitForFunction(){}
  on(name,fn){this.events.set(name,fn);} off(name,fn){if(this.events.get(name)===fn)this.events.delete(name);}
  mainFrame(){return this;}
  async evaluate(){return{videoUrl:null,iframeUrl:null,pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS',modulePath:['1. Module']};}
  getByRole(){return{filter(){return this;},async count(){return 0;}};} getByText(){return{filter(){return this;},async count(){return 0;}};}
}
class Session{
  constructor(pages){this._pages=pages;this.capabilities={engine:'fake-cdp'};this.reconnects=0;}
  async connect(){return this.capabilities;} async disconnect(){} async reconnect(){this.reconnects++;return this.capabilities;}
  async getPages(){return this._pages;} async newPage(){const p=new Page('about:blank',`new-${Date.now()}`);this._pages.push(p);return p;}
  async getTargetId(page){return page?.targetId||null;}
}
function observers(){
  const auth={attached:new Set(),attach(p){this.attached.add(p);},detach(p){this.attached.delete(p);},async assertLesson(){},history(){return[];}};
  const network={attached:new Set(),attach(p){this.attached.add(p);},detach(p){this.attached.delete(p);},best(){return null;},currentGeneration(){return 0;},generationInfo(){return null;},snapshot(){return[];},beginGeneration(){return 0;}};
  return{auth,network};
}

test('V4.2.6 RED: Chrome dedicated to XCursos is launched without background throttling',async()=>{
  const dir=await tmp();const fake=path.join(dir,'chrome');await fs.writeFile(fake,'');let calls=0,capture=null;
  const fetchImpl=async()=>{calls++;if(calls===1)return{ok:false,status:404};return{ok:true,status:200,json:async()=>({Browser:'Chrome/151.0',webSocketDebuggerUrl:'ws://127.0.0.1/devtools/browser/x'})};};
  const child={pid:42,unref(){}};
  const launcher=new HumanChromeLauncher({profileDir:path.join(dir,'profile'),cdpEndpoint:'http://127.0.0.1:9333',chromePath:fake,fetchImpl,spawnImpl:(exe,args,opts)=>{capture={exe,args,opts};return child;},launchTimeoutMs:1000});
  await launcher.ensureRunning({url:'https://www.xcursos.com/'});
  for(const flag of ['--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows'])assert.ok(capture.args.includes(flag),flag);
});

test('V4.2.6 RED: enumerating Chrome tabs is passive and observers attach only to pinned work tab',async()=>{
  const work=new Page('https://www.xcursos.com/curso/c/aula/1','target-work');const other=new Page('https://example.com/','target-other');
  const session=new Session([work,other]);const {auth,network}=observers();const controller=new PageController({session,authObserver:auth,networkObserver:network});
  await controller.pages();assert.equal(auth.attached.size,0);assert.equal(network.attached.size,0);
  const chosen=await controller.chooseWorkingPage();assert.equal(chosen.page.handle,work);assert.deepEqual([...auth.attached],[work]);assert.deepEqual([...network.attached],[work]);
  await controller.close();
});

test('V4.2.6 RED: recovery prefers pinned Chrome target even when another tab has the same lesson URL',async()=>{
  const url='https://www.xcursos.com/curso/c/aula/1';const work=new Page(url,'target-work');const session=new Session([work]);const {auth,network}=observers();const controller=new PageController({session,authObserver:auth,networkObserver:network});
  const chosen=await controller.chooseWorkingPage();const decoy=new Page(url,'target-decoy');session._pages=[decoy,work];
  const recovered=await controller.recoverRef(chosen.page,{url});assert.equal(recovered.handle,work);await controller.close();
});

test('V4.2.6 RED: live lesson metadata preserves arbitrary-depth module hierarchy',()=>{
  const modulePath=['2. Regravação VTSD 2026','05. Copywriting','5. Vídeo de vendas - VSL'];
  const meta=normalizeLiveLessonMeta({courseName:'Course',lessonTitle:'e_Aula',moduleName:'5. Vídeo de vendas - VSL',modulePath,currentPosition:108,totalPositions:198,videoUrl:'https://cdn.example/108.mp4'});
  assert.deepEqual(meta.modulePath,modulePath);assert.equal(meta.moduleName,modulePath.at(-1));
});

test('V4.2.6 RED: downloader mirrors module and submodule tree on disk',()=>{
  const root=path.join(os.tmpdir(),'xc-output');const d=new MediaDownloader();const modulePath=['2. Regravação VTSD 2026','05. Copywriting','5. Vídeo de vendas - VSL'];
  const paths=d.buildPaths({root,courseName:'Venda Todo Santo Dia',moduleName:modulePath.at(-1),modulePath,lessonTitle:'e_Aula',position:108,total:198});
  assert.equal(paths.moduleDir,path.join(root,'Venda Todo Santo Dia',...modulePath));
  assert.equal(paths.template,path.join(root,'Venda Todo Santo Dia',...modulePath,'108 - e_Aula.%(ext)s'));
});

test('V4.2.6 RED: runner forwards modulePath to path builder instead of flattening to moduleName',async()=>{
  const root=await tmp();const modulePath=['2. Regravação VTSD 2026','05. Copywriting','5. Vídeo de vendas - VSL'];const nested={...lesson(1,2,{module:modulePath.at(-1)}),modulePath};
  const browser=new FakeBrowser([nested,lesson(2,2)]);
  class CaptureDownloader extends DiskFakeDownloader{buildPaths(args){this.pathArgs=args;return super.buildPaths(args);}}
  const downloader=new CaptureDownloader();const runner=new XCursosCourseRunner({outputRoot:root,browser,downloader});
  try{await runner.runCurrent({resume:true});assert.deepEqual(downloader.pathArgs.modulePath,modulePath);}finally{await runner.dispose();}
});

test('V4.2.6 RED: PageController live inspection contains sidebar hierarchy extraction',async()=>{
  const source=await fs.readFile(new URL('../src/page-controller.mjs',import.meta.url),'utf8');
  assert.match(source,/modulePath/);assert.match(source,/closest\(['"]aside['"]\)/);assert.match(source,/aulas\?|arquivos\?/i);
});
