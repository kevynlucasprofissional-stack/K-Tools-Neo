import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { getRunnerInfo } from '../src/version-info.mjs';
import { runDoctor } from '../src/doctor.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { StateStore } from '../src/state.mjs';import { NavigationIndex } from '../src/navigation-index.mjs';
import { FakeBrowser,DiskFakeDownloader,lesson } from './helpers.mjs';

async function tmp(){return fs.mkdtemp(path.join(os.tmpdir(),'xc-diagnose-'));}
function lessons(n){return Array.from({length:n},(_,i)=>lesson(i+1,n));}

test('runner info exposes version and actual CLI/install paths',async()=>{const info=await getRunnerInfo();assert.match(info.version,/^4\.3\.0$/);assert.match(info.cliPath,/src[\\/]cli\.mjs$/);assert.ok(info.installRoot);assert.match(info.packageJson,/package\.json$/);});
test('doctor includes runnerVersion, cliPath and installRoot',async()=>{const d=await runDoctor({config:{profileDir:'/p',outputRoot:'/o',chromePath:process.execPath,cdpEndpoint:'http://127.0.0.1:9222'},playwrightLoader:async()=>({chromium:{connectOverCDP(){}}}),fetchImpl:async()=>{throw new Error('off');}});assert.equal(d.runnerVersion,'4.3.0');assert.ok(d.cliPath);assert.ok(d.installRoot);});
test('diagnoseReposition computes plan without navigation/click/download',async()=>{const root=await tmp();const s=new StateStore({outputRoot:root,courseName:'Fake Course',totalPositions:90});await s.initialize({resume:false,workPageUrl:'https://www.xcursos.com/aula/80'});const idx=new NavigationIndex({filePath:s.navigationPath,courseName:'Fake Course',totalPositions:90});await idx.load();await idx.record(40,'https://www.xcursos.com/aula/40');const b=new FakeBrowser(lessons(90),{startPosition:80});const dl=new DiskFakeDownloader();const r=new XCursosCourseRunner({outputRoot:root,browser:b,downloader:dl});try{const result=await r.diagnoseReposition({target:65,resume:true});assert.equal(result.ok,true);assert.equal(result.plan.strategy,'WALK_FROM_CHECKPOINT');assert.equal(result.plan.checkpoint.position,40);assert.equal(b.stats.clickNext,0);assert.equal(b.stats.goToPosition,0);assert.equal(dl.calls.length,0);}finally{await r.dispose();}});
