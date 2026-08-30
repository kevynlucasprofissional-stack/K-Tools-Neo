import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { PageController } from '../src/page-controller.mjs';
import { DiskFakeDownloader, lesson, readJsonlFile } from './helpers.mjs';

const timeoutError=()=>Object.assign(new Error('locator.click: Timeout 20000ms exceeded. - waiting for element to be visible, enabled and stable'),{name:'TimeoutError'});
const stable=()=>({found:true,visible:true,enabled:true,ariaDisabled:false,display:'block',visibility:'visible',opacity:'1',pointerEvents:'auto',boundingBox:{x:10,y:10,width:100,height:30},boundingBoxes:[{x:10,y:10,width:100,height:30},{x:10,y:10,width:100,height:30},{x:10,y:10,width:100,height:30}],viewport:{width:1280,height:720},centerPoint:{x:60,y:25},centerElement:{same:true,contains:true,tag:'button',role:'button',text:'Próxima'},receivesEvents:true,animations:[],transitions:{property:'background-color',duration:'0.1s',delay:'0s'},stable:true,geometryMotion:false});
const unstable=()=>({...stable(),boundingBoxes:[{x:10,y:10,width:100,height:30},{x:12,y:10,width:100,height:30},{x:14,y:10,width:100,height:30}],boundingBox:{x:14,y:10,width:100,height:30},stable:false,geometryMotion:true,animations:[{playState:'running',name:'slide'}],transitions:{property:'transform',duration:'1s',delay:'0s'}});

class HarnessLocator{
  constructor(h){this.h=h;}
  filter(){return this;}first(){return this;}async count(){return 1;}
  async evaluate(_fn,args={}){
    if(args.mode==='neutralize'){this.h.neutralized=true;this.h.neutralizeCount++;return{count:1};}
    if(args.mode==='restore'){this.h.neutralized=false;return true;}
    return this.h.current===4&&!this.h.neutralized?unstable():stable();
  }
  async click(options={}){
    const source=this.h.current;
    if(options.trial){if(source===4&&!this.h.neutralized)throw timeoutError();return;}
    this.h.normal.set(source,(this.h.normal.get(source)||0)+1);
    if(source===3)throw timeoutError();
    if(source===6){this.h.current=7;throw timeoutError();}
    if(source===7)throw timeoutError();
    this.h.current=Math.min(10,source+1);
  }
  async dispatchEvent(type){assert.equal(type,'click');const source=this.h.current;this.h.dispatch.set(source,(this.h.dispatch.get(source)||0)+1);if(source===3)this.h.current=4;/* source 7 intentionally stays put */}
}
class HarnessPage{constructor(h){this.h=h;this.locatorNext=new HarnessLocator(h);}getByRole(role){return role==='button'?this.locatorNext:{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}}

class NextHarnessBrowser{
  constructor(){
    this.h={current:1,normal:new Map(),dispatch:new Map(),neutralized:false,neutralizeCount:0,recoveries:0};
    this.rawPage=new HarnessPage(this.h);
    this.ref={id:'next-harness',handle:this.rawPage,get url(){return `https://www.xcursos.com/curso/fake/aula/${this.handle.h.current}`;},title:'Assistir Aula | XCURSOS'};
    const observer={attach(){},detach(){},snapshot(){return[];},history(){return[];}};
    const session={capabilities:{engine:'fake-next'},connect:async()=>({engine:'fake-next'}),disconnect:async()=>{},reconnect:async()=>{},getPages:async()=>[]};
    this.controller=new PageController({session,limits:{transitionTimeoutMs:25,transitionPollMs:1},authObserver:{...observer,assertLesson:async()=>{}},networkObserver:{...observer,best(){return null;},clear(){}}});
    this.controller.inspectPosition=async()=>({current:this.h.current,total:10});
    this.controller.inspectLesson=async()=>this._lesson();
    this.controller.recoverRef=async ref=>{this.h.recoveries++;if(this.h.current===7)this.h.current=8;return ref;};
    this.capabilities=this.controller.capabilities;
  }
  _lesson(){const p=this.h.current;return{...lesson(p,10,{course:'Scientific Fake Course',module:p>=9?'2. Advanced':'1. Core',title:`Lesson ${p}`}),pageUrl:`https://www.xcursos.com/curso/fake/aula/${p}`};}
  async connect(){return this.capabilities;}async close(){}async cleanupCreatedPages(){}
  async chooseWorkingPage(){return{page:this.ref,lesson:this._lesson(),cloned:false};}
  async inspectLesson(){return this._lesson();}
  async navigateNext(ref,opts){return await this.controller.navigateNext(ref,opts);}
  async navigateExact(_ref,url){const m=String(url).match(/\/aula\/(\d+)/);if(!m)throw new Error('bad url');this.h.current=Number(m[1]);return this.ref;}
  async goToPosition(_ref,target){this.h.current=target;return{page:this.ref,lesson:this._lesson()};}
  async recoverWorkingPage(){return this.ref;}async refreshSameLesson(){return this.ref;}networkSnapshot(){return[];}
}

test('systemic fake 1..10 survives live Next failure modes without duplicate or double-advance',async()=>{
  const outputRoot=await fs.mkdtemp(path.join(os.tmpdir(),'xc-next-system-'));const browser=new NextHarnessBrowser();const downloader=new DiskFakeDownloader();const runner=new XCursosCourseRunner({outputRoot,browser,downloader,limits:{navigationRetries:0,transitionTimeoutMs:20,transitionPollMs:1}});
  try{
    const result=await runner.runCourse({resume:false});assert.equal(result.status,'COMPLETE');assert.equal(result.audit.processed,10);assert.deepEqual(result.audit.missingPositions,[]);assert.deepEqual(result.audit.duplicatePositions,[]);
    assert.equal(browser.h.normal.get(3),1);assert.equal(browser.h.dispatch.get(3),1);
    assert.equal(browser.h.normal.get(6),1);assert.equal(browser.h.dispatch.get(6)||0,0,'timeout after navigation must not dispatch again');
    assert.equal(browser.h.normal.get(7),1);assert.equal(browser.h.dispatch.get(7),1);assert.ok(browser.h.recoveries>=1);
    assert.ok(browser.h.neutralizeCount>=1,'unstable position 4 must use evidence-based neutralization');
    const manifest=await readJsonlFile(path.join(result.courseRoot,'_xcursos-runner','manifest.jsonl'));assert.deepEqual(manifest.map(r=>r.position),[1,2,3,4,5,6,7,8,9,10]);assert.equal(manifest.find(r=>r.position===9).moduleName,'2. Advanced');
  }finally{await runner.dispose();}
});
