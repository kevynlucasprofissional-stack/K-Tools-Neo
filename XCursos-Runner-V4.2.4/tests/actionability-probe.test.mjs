import test from 'node:test';
import assert from 'node:assert/strict';
import { ActionabilityProbe } from '../src/actionability-probe.mjs';

class FakeLocator {
  constructor({snapshot={},trialError=null,closed=false}={}){this.snapshot=snapshot;this.trialError=trialError;this.closed=closed;this.calls=[];this.neutralized=false;}
  async evaluate(_fn,args={}){
    this.calls.push(['evaluate',args]);
    if(this.closed)throw new Error('Target page, context or browser has been closed');
    if(args?.mode==='neutralize'){this.neutralized=true;return{className:args.className};}
    if(args?.mode==='restore'){this.neutralized=false;return true;}
    const base=typeof this.snapshot==='function'?this.snapshot(this.neutralized):this.snapshot;
    return structuredClone(base);
  }
  async click(options={}){this.calls.push(['click',options]);if(options.trial&&this.trialError)throw this.trialError;}
}

const box=(x=10,y=20,w=100,h=30)=>({x,y,width:w,height:h});
function stableSnapshot(overrides={}){return{
  found:true,visible:true,enabled:true,ariaDisabled:false,display:'block',visibility:'visible',opacity:'1',pointerEvents:'auto',
  boundingBox:box(),boundingBoxes:[box(),box(),box()],viewport:{width:1280,height:720},centerPoint:{x:60,y:35},
  centerElement:{same:true,contains:true,tag:'button',role:'button',text:'Próxima'},receivesEvents:true,
  animations:[],transitions:{property:'background-color',duration:'0.15s',delay:'0s'},stable:true,geometryMotion:false,...overrides,
};}

test('ActionabilityProbe reports a stable actionable element and successful trial click',async()=>{
  const locator=new FakeLocator({snapshot:stableSnapshot()});const p=new ActionabilityProbe({sampleFrames:3,trialTimeoutMs:25});const r=await p.probe(locator);
  assert.equal(r.found,true);assert.equal(r.visible,true);assert.equal(r.enabled,true);assert.equal(r.stable,true);assert.equal(r.receivesEvents,true);assert.equal(r.trial.passed,true);assert.equal(locator.calls.filter(c=>c[0]==='click').length,1);assert.equal(locator.calls.at(-1)[1].trial,true);
});

test('ActionabilityProbe detects moving geometry',async()=>{const boxes=[box(10),box(12),box(14)];const r=await new ActionabilityProbe().probe(new FakeLocator({snapshot:stableSnapshot({boundingBoxes:boxes,boundingBox:boxes.at(-1),stable:false,geometryMotion:true})}));assert.equal(r.stable,false);assert.equal(r.geometryMotion,true);assert.equal(new ActionabilityProbe().shouldNeutralize(r),true);});

test('ActionabilityProbe reports invisible and disabled states',async()=>{const r=await new ActionabilityProbe().probe(new FakeLocator({snapshot:stableSnapshot({visible:false,enabled:false,ariaDisabled:true,display:'none'})}));assert.equal(r.visible,false);assert.equal(r.enabled,false);assert.equal(r.ariaDisabled,true);});

test('ActionabilityProbe detects center overlay / receives-events failure',async()=>{const r=await new ActionabilityProbe().probe(new FakeLocator({snapshot:stableSnapshot({centerElement:{same:false,contains:false,tag:'div',role:null,text:'overlay'},receivesEvents:false})}));assert.equal(r.receivesEvents,false);assert.equal(r.centerElement.tag,'div');});

test('ActionabilityProbe exposes active animations and geometry transitions',async()=>{const r=await new ActionabilityProbe().probe(new FakeLocator({snapshot:stableSnapshot({animations:[{playState:'running',name:'pulse'}],transitions:{property:'transform, width',duration:'2s',delay:'0s'},stable:false,geometryMotion:true})}));assert.equal(r.animations.length,1);assert.equal(r.geometryMotion,true);assert.equal(new ActionabilityProbe().shouldNeutralize(r),true);});

test('ActionabilityProbe records TimeoutError from trial without throwing',async()=>{const e=Object.assign(new Error('locator.click: Timeout 1500ms exceeded.'),{name:'TimeoutError'});const r=await new ActionabilityProbe().probe(new FakeLocator({snapshot:stableSnapshot(),trialError:e}));assert.equal(r.trial.passed,false);assert.equal(r.trial.errorName,'TimeoutError');assert.match(r.trial.errorMessage,/Timeout 1500ms exceeded/);});

test('ActionabilityProbe rethrows page-closed failures as PAGE_CLOSED',async()=>{const locator=new FakeLocator({snapshot:stableSnapshot(),closed:true});await assert.rejects(()=>new ActionabilityProbe().probe(locator),e=>e.code==='PAGE_CLOSED');});

test('motion neutralization is temporary and reversible',async()=>{const locator=new FakeLocator({snapshot:n=>stableSnapshot(n?{stable:true,geometryMotion:false,animations:[],transitions:{property:'none',duration:'0s',delay:'0s'}}:{stable:false,geometryMotion:true,animations:[{playState:'running'}],transitions:{property:'transform',duration:'1s',delay:'0s'}})});const p=new ActionabilityProbe();const before=await p.probe(locator);assert.equal(before.stable,false);const cleanup=await p.neutralize(locator);const after=await p.probe(locator);assert.equal(after.stable,true);await cleanup();assert.equal(locator.neutralized,false);});
