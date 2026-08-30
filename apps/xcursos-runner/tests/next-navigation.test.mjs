import test from 'node:test';
import assert from 'node:assert/strict';
import { PageController } from '../src/page-controller.mjs';

const timeoutError=()=>Object.assign(new Error('locator.click: Timeout 20000ms exceeded.\n - waiting for element to be visible, enabled and stable'),{name:'TimeoutError',code:null});

class NextLocator {
  constructor({onClick=null,onDispatch=null}={}){this.onClick=onClick;this.onDispatch=onDispatch;this.normalClicks=0;this.dispatches=0;}
  filter(){return this;}first(){return this;}async count(){return 1;}
  async click(options={}){if(options.trial)return;this.normalClicks++;if(this.onClick)await this.onClick();}
  async dispatchEvent(type){assert.equal(type,'click');this.dispatches++;if(this.onDispatch)await this.onDispatch();}
}
class FakePage {constructor(locator){this.locatorNext=locator;}getByRole(role){return role==='button'?this.locatorNext:{filter(){return this;},count:async()=>0};}getByText(){return{filter(){return this;},count:async()=>0};}}
function session(){return{capabilities:{engine:'fake'},connect:async()=>({engine:'fake'}),disconnect:async()=>{},reconnect:async()=>{},getPages:async()=>[]};}
function noopObserver(){return{attach(){},detach(){},snapshot(){return[];},history(){return[];}};}
function makeController({locator,currentRef,probeResult=null,neutralize=false,snapshots=null}={}){
  const actionabilityProbe={
    probeCalls:0,neutralizeCalls:0,cleanupCalls:0,
    async probe(){this.probeCalls++;return probeResult||{found:true,visible:true,enabled:true,stable:true,receivesEvents:true,geometryMotion:false,animations:[],transitions:{property:'background-color'},trial:{passed:true}};},
    shouldNeutralize(r){return neutralize||r?.geometryMotion===true||r?.stable===false;},
    async neutralize(){this.neutralizeCalls++;return async()=>{this.cleanupCalls++;};},
  };
  const c=new PageController({session:session(),authObserver:{...noopObserver(),assertLesson:async()=>{}},networkObserver:{...noopObserver(),best(){return null;},clear(){}},actionabilityProbe,debugSnapshots:snapshots});
  c.inspectPosition=async()=>({current:currentRef.value,total:198});
  c.inspectLesson=async()=>({currentPosition:currentRef.value,totalPositions:198,pageUrl:`https://www.xcursos.com/curso/c/aula/${currentRef.value}`});
  c.recoverRef=async ref=>{c.recoverCalls=(c.recoverCalls||0)+1;return ref;};
  return{controller:c,probe:actionabilityProbe,ref:{handle:new FakePage(locator),url:'https://www.xcursos.com/curso/c/aula/39'}};
}

test('live regression: normal click TimeoutError + unchanged N uses one dispatchEvent and confirms 39→40',async()=>{
  const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=40;}});const {controller,ref}=makeController({locator,currentRef:pos});
  const result=await controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1});
  assert.equal(result.lesson.currentPosition,40);assert.equal(result.method,'dispatch-event');assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,1);
});

test('critical no-double-click: TimeoutError is thrown after page already changed, so dispatchEvent is never sent',async()=>{
  const pos={value:39};const locator=new NextLocator({onClick:async()=>{pos.value=40;throw timeoutError();},onDispatch:async()=>{pos.value=41;}});const {controller,ref}=makeController({locator,currentRef:pos});
  const result=await controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1});
  assert.equal(result.lesson.currentPosition,40);assert.equal(result.method,'normal-click-timeout-but-transitioned');assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,0);assert.equal(pos.value,40);
});

test('normal click timeout + dispatch unchanged performs limited recovery then NEXT_TRANSITION_FAILED',async()=>{
  const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{}});const {controller,ref}=makeController({locator,currentRef:pos});
  await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1,postDispatchObservationMs:2}),e=>e.code==='NEXT_TRANSITION_FAILED');
  assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,1);assert.equal(controller.recoverCalls,1);
});

test('dispatch resulting 39→41 is POSITION_SKIP',async()=>{const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=41;}});const {controller,ref}=makeController({locator,currentRef:pos});await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1}),e=>e.code==='POSITION_SKIP');assert.equal(locator.dispatches,1);});

test('dispatch resulting 39→38 is POSITION_REGRESSION',async()=>{const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=38;}});const {controller,ref}=makeController({locator,currentRef:pos});await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1}),e=>e.code==='POSITION_REGRESSION');assert.equal(locator.dispatches,1);});

test('stable button does not trigger motion neutralization',async()=>{const pos={value:39};const locator=new NextLocator({onClick:async()=>{pos.value=40;}});const {controller,ref,probe}=makeController({locator,currentRef:pos,probeResult:{found:true,visible:true,enabled:true,stable:true,receivesEvents:true,geometryMotion:false,animations:[],transitions:{property:'background-color'},trial:{passed:true}}});await controller.navigateNext(ref,{fromPosition:39,target:40});assert.equal(probe.neutralizeCalls,0);});

test('unstable geometry is neutralized temporarily before normal click, then cleanup runs',async()=>{const pos={value:39};const locator=new NextLocator({onClick:async()=>{pos.value=40;}});let n=0;const snapshots={capture:async()=>({ok:true})};const {controller,ref,probe}=makeController({locator,currentRef:pos,neutralize:true,probeResult:{found:true,visible:true,enabled:true,stable:false,receivesEvents:true,geometryMotion:true,animations:[{playState:'running'}],transitions:{property:'transform'},trial:{passed:false}},snapshots});const originalProbe=probe.probe.bind(probe);probe.probe=async()=>{n++;if(n===1)return await originalProbe();return{found:true,visible:true,enabled:true,stable:true,receivesEvents:true,geometryMotion:false,animations:[],transitions:{property:'none'},trial:{passed:true}};};const r=await controller.navigateNext(ref,{fromPosition:39,target:40});assert.equal(r.lesson.currentPosition,40);assert.equal(probe.neutralizeCalls,1);assert.equal(probe.cleanupCalls,1);});

test('actionability timeout emits diagnostic snapshot with semantic result',async()=>{const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=40;}});const calls=[];const snapshots={capture:async x=>{calls.push(x);return{ok:true};}};const {controller,ref}=makeController({locator,currentRef:pos,snapshots});await controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1});assert.equal(calls.length,1);assert.equal(calls[0].position,39);assert.equal(calls[0].metadata.target,'Próxima');assert.equal(calls[0].metadata.result,'NEXT_ACTIONABILITY_TIMEOUT');assert.equal(calls[0].metadata.strategy,'normal-click');});

test('motion neutralization is discarded when probe shows no improvement',async()=>{
  const pos={value:39};const locator=new NextLocator({onClick:async()=>{pos.value=40;}});const {controller,ref,probe}=makeController({locator,currentRef:pos,neutralize:true,probeResult:{found:true,visible:true,enabled:true,stable:false,receivesEvents:true,geometryMotion:true,animations:[{playState:'running'}],transitions:{property:'transform'},trial:{passed:false}}});
  const result=await controller.navigateNext(ref,{fromPosition:39,target:40});assert.equal(result.lesson.currentPosition,40);assert.equal(result.motionNeutralized,false);assert.equal(probe.neutralizeCalls,1);assert.equal(probe.cleanupCalls,1);
});

test('dispatch fallback never bypasses an explicitly disabled Próxima button',async()=>{
  const pos={value:39};const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=40;}});const {controller,ref}=makeController({locator,currentRef:pos,probeResult:{found:true,visible:true,enabled:false,ariaDisabled:true,stable:true,receivesEvents:true,geometryMotion:false,animations:[],transitions:{property:'none'},trial:{passed:false}}});
  await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1}),e=>e.code==='NEXT_TRANSITION_FAILED');assert.equal(locator.dispatches,0);
});

test('no-double-click when dispatchEvent throws target-closed after transition already reached N+1',async()=>{
  const pos={value:39};const targetClosed=()=>new Error('Target page, context or browser has been closed');
  const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{pos.value=40;throw targetClosed();}});
  const {controller,ref}=makeController({locator,currentRef:pos});
  const result=await controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1,postDispatchObservationMs:1});
  assert.equal(result.lesson.currentPosition,40);assert.equal(result.method,'dispatch-event-target-closed-but-transitioned');assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,1);assert.equal(controller.recoverCalls,1);
});

test('dispatchEvent target-closed with unchanged position recovers once and fails structurally without a second action',async()=>{
  const pos={value:39};const targetClosed=()=>new Error('Target page, context or browser has been closed');
  const locator=new NextLocator({onClick:async()=>{throw timeoutError();},onDispatch:async()=>{throw targetClosed();}});
  const {controller,ref}=makeController({locator,currentRef:pos});
  await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1,postDispatchObservationMs:1}),e=>e.code==='NEXT_TRANSITION_FAILED');
  assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,1);assert.equal(controller.recoverCalls,1);assert.equal(pos.value,39);
});

test('normal click target-closed after transition reached N+1 is observed before any retry action',async()=>{
  const pos={value:39};const targetClosed=()=>new Error('Target page, context or browser has been closed');
  const locator=new NextLocator({onClick:async()=>{pos.value=40;throw targetClosed();},onDispatch:async()=>{pos.value=41;}});
  const {controller,ref}=makeController({locator,currentRef:pos});
  const result=await controller.navigateNext(ref,{fromPosition:39,target:40,postActionObservationMs:1});
  assert.equal(result.lesson.currentPosition,40);assert.equal(result.method,'normal-click-target-closed-but-transitioned');assert.equal(locator.normalClicks,1);assert.equal(locator.dispatches,0);assert.equal(controller.recoverCalls,1);
});

test('V4.2.4 RED: transient null counter before Próxima is re-observed instead of misclassified as regression',async()=>{
  const pos={value:116};const locator=new NextLocator({onClick:async()=>{pos.value=117;}});const {controller,ref}=makeController({locator,currentRef:pos});let reads=0;controller.inspectPosition=async()=>{reads++;if(reads===1)return{current:null,total:null};return{current:pos.value,total:198};};controller.inspectLesson=async()=>({currentPosition:pos.value,totalPositions:198,pageUrl:`https://www.xcursos.com/curso/c/aula/${pos.value}`});
  const result=await controller.navigateNext(ref,{fromPosition:116,target:117});assert.equal(result.lesson.currentPosition,117);assert.equal(locator.normalClicks,1);assert.ok(reads>=2);
});

test('V4.2.4 RED: persistently unreadable counter before Próxima is POSITION_UNOBSERVABLE, never POSITION_REGRESSION',async()=>{
  const pos={value:116};const locator=new NextLocator();const {controller,ref}=makeController({locator,currentRef:pos});controller.inspectPosition=async()=>({current:null,total:null});
  await assert.rejects(()=>controller.navigateNext(ref,{fromPosition:116,target:117}),e=>e.code==='POSITION_UNOBSERVABLE');assert.equal(locator.normalClicks,0);assert.equal(locator.dispatches,0);
});
