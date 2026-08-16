import test from 'node:test';
import assert from 'node:assert/strict';
import { PageController } from '../src/page-controller.mjs';

class FakePage {
  constructor({safe=true}={}){this.safe=safe;this.contentCalls=0;this.evaluateCalls=0;this.shellCalls=0;this._url='https://www.xcursos.com/curso/c/aula/1';}
  url(){return this._url;}
  isClosed(){return false;}
  async title(){return 'Assistir Aula | XCURSOS';}
  locator(){return{waitFor:async()=>{this.shellCalls++;}};}
  async waitForFunction(){this.shellCalls++;return true;}
  async content(){this.contentCalls++;return `<html><head><title>Assistir Aula | XCURSOS</title></head><body><h2>Course</h2><h1>Aula 1</h1><span>1 / 2</span>${this.safe?'<video src="https://cdn.example/1.mp4"></video>':''}</body></html>`;}
  async evaluate(){this.evaluateCalls++;return{videoUrl:this.safe?'https://cdn.example/1.mp4':null,iframeUrl:null,modulePath:[],pageUrl:this._url,pageTitle:'Assistir Aula | XCURSOS'};}
}

function makeController(page,{ttl=750}={}){
  const session={capabilities:{},async disconnect(){},async getTargetId(){return'fake-target';}};
  const authObserver={attach(){},detach(){},async assertLesson(){},history(){return[];}};
  const networkObserver={attach(){},detach(){},best(){return null;},snapshot(){return[];},currentGeneration(){return 1;},generationInfo(){return null;}};
  const controller=new PageController({session,authObserver,networkObserver,limits:{inspectionCacheTtlMs:ttl,inspectTimeoutMs:50}});
  return{controller,ref:controller.ref(page)};
}

test('safe lesson inspection is reused on immediate duplicate reads',async()=>{
  const page=new FakePage({safe:true});const{controller,ref}=makeController(page);
  const first=await controller.inspectLesson(ref);const second=await controller.inspectLesson(ref);
  assert.equal(first.currentPosition,1);assert.equal(second.videoUrl,'https://cdn.example/1.mp4');
  assert.equal(page.contentCalls,1);assert.equal(page.evaluateCalls,1);assert.equal(page.shellCalls,2);
});

test('unproven media is never cached, so readiness polling can observe changes',async()=>{
  const page=new FakePage({safe:false});const{controller,ref}=makeController(page);
  await controller.inspectLesson(ref);await controller.inspectLesson(ref);
  assert.equal(page.contentCalls,2);assert.equal(page.evaluateCalls,2);
});

test('explicit invalidation forces a fresh inspection even inside TTL',async()=>{
  const page=new FakePage({safe:true});const{controller,ref}=makeController(page);
  await controller.inspectLesson(ref);controller.invalidateInspection(ref);await controller.inspectLesson(ref);
  assert.equal(page.contentCalls,2);assert.equal(page.evaluateCalls,2);
});