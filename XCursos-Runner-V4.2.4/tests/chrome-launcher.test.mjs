import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { HumanChromeLauncher, findChromeExecutable, getCdpStatus, cdpEndpointFromPort } from '../src/chrome-launcher.mjs';

function okFetch(){return async()=>({ok:true,status:200,json:async()=>({Browser:'Chrome/151.0','Protocol-Version':'1.3',webSocketDebuggerUrl:'ws://127.0.0.1/devtools/browser/abc'})});}

test('CDP endpoint is deterministic loopback from configured port',()=>{assert.equal(cdpEndpointFromPort(9222),'http://127.0.0.1:9222');assert.throws(()=>cdpEndpointFromPort(80),e=>e.code==='CDP_PORT_INVALID');});

test('CDP status reads Chrome json/version without exposing browser cookies',async()=>{const s=await getCdpStatus('http://127.0.0.1:9222',{fetchImpl:okFetch()});assert.equal(s.ok,true);assert.equal(s.browser,'Chrome/151.0');assert.match(s.webSocketDebuggerUrl,/^ws:\/\/127\.0\.0\.1/);});

test('Chrome executable accepts explicit existing path',async()=>{const dir=await fs.mkdtemp(path.join(os.tmpdir(),'xc-chrome-'));const fake=path.join(dir,process.platform==='win32'?'chrome.exe':'chrome');await fs.writeFile(fake,'');assert.equal(await findChromeExecutable({explicitPath:fake,extraCandidates:[]}),fake);});

test('human Chrome launcher does not spawn second browser when CDP is already available',async()=>{let spawns=0;const l=new HumanChromeLauncher({profileDir:'/tmp/xc-profile',cdpEndpoint:'http://127.0.0.1:9222',fetchImpl:okFetch(),spawnImpl:()=>{spawns++;}});const r=await l.ensureRunning();assert.equal(r.alreadyRunning,true);assert.equal(spawns,0);});

test('human Chrome launcher uses dedicated user-data-dir and remote debugging port before Playwright attaches',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'xc-chrome-launch-'));const fake=path.join(dir,'chrome');await fs.writeFile(fake,'');let calls=0,capture=null;
  const fetchImpl=async()=>{calls++;if(calls===1)return{ok:false,status:404};return{ok:true,status:200,json:async()=>({Browser:'Chrome/151.0',webSocketDebuggerUrl:'ws://127.0.0.1/devtools/browser/x'})};};
  const child={pid:1234,unref(){this.unrefd=true;}};
  const l=new HumanChromeLauncher({profileDir:path.join(dir,'profile'),cdpEndpoint:'http://127.0.0.1:9333',chromePath:fake,fetchImpl,spawnImpl:(exe,args,opts)=>{capture={exe,args,opts};return child;},launchTimeoutMs:1000});
  const r=await l.ensureRunning({url:'https://www.xcursos.com/'});assert.equal(r.alreadyRunning,false);assert.equal(capture.exe,fake);assert.ok(capture.args.includes('--remote-debugging-port=9333'));assert.ok(capture.args.some(x=>x.startsWith('--user-data-dir=')));assert.ok(capture.args.includes('--remote-debugging-address=127.0.0.1'));assert.ok(capture.args.includes('https://www.xcursos.com/'));assert.equal(capture.args.some(x=>/automation/i.test(x)),false);assert.equal(child.unrefd,true);
});
