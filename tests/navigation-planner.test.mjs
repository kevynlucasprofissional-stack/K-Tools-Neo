import test from 'node:test';
import assert from 'node:assert/strict';
import { NavigationPlanner } from '../src/navigation-planner.mjs';

function plan(opts){return new NavigationPlanner().plan({total:198,...opts});}

test('planner: current == target -> ALREADY_AT_TARGET',()=>{
  assert.deepEqual(plan({currentPosition:65,targetPosition:65}),{strategy:'ALREADY_AT_TARGET',currentPosition:65,targetPosition:65,steps:0});
});

test('planner: exact target URL wins when current differs',()=>{
  const p=plan({currentPosition:1,targetPosition:65,exactTargetUrl:'https://www.xcursos.com/aula/65'});
  assert.equal(p.strategy,'EXACT_URL');assert.equal(p.url,'https://www.xcursos.com/aula/65');assert.equal(p.steps,0);
});

test('planner: current == target - 1 can walk one proven step',()=>{
  const p=plan({currentPosition:64,targetPosition:65});assert.equal(p.strategy,'WALK_FROM_CURRENT');assert.equal(p.fromPosition,64);assert.equal(p.steps,1);
});

test('planner: browser below target walks from current without download-health assumptions',()=>{
  const p=plan({currentPosition:1,targetPosition:65});assert.equal(p.strategy,'WALK_FROM_CURRENT');assert.equal(p.steps,64);
});

test('planner: browser above target chooses nearest earlier checkpoint',()=>{
  const p=plan({currentPosition:80,targetPosition:65,checkpoint:{position:40,url:'https://www.xcursos.com/aula/40'}});
  assert.equal(p.strategy,'WALK_FROM_CHECKPOINT');assert.equal(p.checkpoint.position,40);assert.equal(p.steps,25);
});

test('planner: browser above target uses course anchor when checkpoint unavailable',()=>{
  const p=plan({currentPosition:120,targetPosition:65,courseAnchor:{position:1,url:'https://www.xcursos.com/aula/1'}});
  assert.equal(p.strategy,'WALK_FROM_COURSE_ANCHOR');assert.equal(p.anchor.position,1);assert.equal(p.steps,64);
});

test('planner: no route produces observable NO_SAFE_PATH plan',()=>{
  const p=plan({currentPosition:80,targetPosition:65});assert.equal(p.strategy,'NO_SAFE_PATH');assert.equal(p.currentPosition,80);assert.equal(p.targetPosition,65);assert.deepEqual(p.strategiesConsidered,['ALREADY_AT_TARGET','EXACT_URL','WALK_FROM_CURRENT','WALK_FROM_CHECKPOINT','WALK_FROM_COURSE_ANCHOR']);
});
