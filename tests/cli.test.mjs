import test from 'node:test';import assert from 'node:assert/strict';import { parseCli } from '../src/cli.mjs';import { runDoctor } from '../src/doctor.mjs';
test('CLI parses deterministic range and resume flags',()=>{const p=parseCli(['range','--start','5','--end','10','--no-resume','--json']);assert.equal(p.command,'range');assert.equal(p.options.start,'5');assert.equal(p.options.end,'10');assert.equal(p.options.resume,false);assert.equal(p.options.json,true);});
test('CLI parses human Chrome command and CDP overrides',()=>{const p=parseCli(['browser','--chrome','C:/Chrome/chrome.exe','--port','9333']);assert.equal(p.command,'browser');assert.equal(p.options.chrome,'C:/Chrome/chrome.exe');assert.equal(p.options.port,'9333');});
test('doctor validates playwright-core and external Chrome independently from CDP running state',async()=>{const result=await runDoctor({config:{profileDir:'/p',outputRoot:'/o',chromePath:process.execPath,cdpEndpoint:'http://127.0.0.1:9222'},playwrightLoader:async()=>({chromium:{connectOverCDP(){}}}),fetchImpl:async()=>{throw new Error('not running');}});assert.equal(result.node.ok,true);assert.equal(result.playwrightCore.ok,true);assert.equal(result.chrome.ok,true);assert.equal(result.cdp.running,false);});
import { login } from '../src/cli.mjs';
test('login keeps Playwright detached until human Cloudflare/login gate completes',async()=>{
  let loaderCalls=0,launches=0;
  class FakeLauncher{constructor(){}async ensureRunning(){launches++;return{ok:true};}}
  const sentinel=new Error('human-done-test');
  const configStore={rememberLesson:async()=>{}};
  await assert.rejects(()=>login({
    configStore,
    runtime:{profileDir:'/p',cdpEndpoint:'http://127.0.0.1:9222',chromePath:'/chrome'},
    launcherFactory:FakeLauncher,
    playwrightLoader:async()=>{loaderCalls++;return{chromium:{connectOverCDP(){}}};},
    humanGate:async()=>{assert.equal(launches,1);assert.equal(loaderCalls,0);throw sentinel;},
  }),e=>e===sentinel);
  assert.equal(loaderCalls,0);
});

test('CLI parses diagnose-reposition target',()=>{const p=parseCli(['diagnose-reposition','--target','65','--json']);assert.equal(p.command,'diagnose-reposition');assert.equal(p.options.target,'65');assert.equal(p.options.json,true);});
