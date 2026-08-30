import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { createObservedProcessRunner } from '../src/process-observer.mjs';
import { runDoctor } from '../src/doctor.mjs';
import { HumanChromeLauncher } from '../src/chrome-launcher.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-coverage-'));}
async function readEvents(file){return (await fs.readFile(file,'utf8')).trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);}

test('doctor routes yt-dlp and ffprobe executable probes through the observed process runner',async()=>{
  const root=await tmp();const chrome=path.join(root,process.platform==='win32'?'chrome.exe':'chrome');await fs.writeFile(chrome,'');const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'doctor-run'});
  const observed=createObservedProcessRunner({logger,baseRunner:async(command,args)=>({pid:command.includes('ffprobe')?22:11,code:0,signal:null,stdout:command.includes('ffprobe')?'ffprobe version test':'2026.08.16',stderr:'',stdoutTruncated:false,stderrTruncated:false})});
  const result=await runDoctor({config:{chromePath:chrome,cdpEndpoint:'http://127.0.0.1:9222',profileDir:path.join(root,'profile'),outputRoot:root},playwrightLoader:async()=>({chromium:{connectOverCDP(){}}}),fetchImpl:async()=>({ok:true,json:async()=>({Browser:'Chrome/Test',webSocketDebuggerUrl:'ws://127.0.0.1/devtools/browser/test'})}),processRunner:observed});
  assert.equal(result.ytDlp.ok,true);assert.equal(result.ffprobe.ok,true);const events=await readEvents(eventFile);assert.equal(events.filter(x=>x.event==='SUBPROCESS_START').length,2);assert.equal(events.filter(x=>x.event==='SUBPROCESS_END').length,2);
});

test('detached Chrome launch writes spawn pid and CDP readiness events',async()=>{
  const root=await tmp();const chrome=path.join(root,'chrome');await fs.writeFile(chrome,'');const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'chrome-run'});let fetchCalls=0;
  const fetchImpl=async()=>{fetchCalls++;if(fetchCalls===1)return{ok:false,status:404};return{ok:true,status:200,json:async()=>({Browser:'Chrome/Test',webSocketDebuggerUrl:'ws://127.0.0.1/devtools/browser/test'})};};
  const launcher=new HumanChromeLauncher({profileDir:path.join(root,'profile'),cdpEndpoint:'http://127.0.0.1:9333',chromePath:chrome,logger,fetchImpl,spawnImpl:()=>({pid:4321,unref(){}}),launchTimeoutMs:1000});
  const result=await launcher.ensureRunning({url:'https://www.xcursos.com/'});assert.equal(result.pid,4321);const events=await readEvents(eventFile);assert.ok(events.some(x=>x.event==='CHROME_SPAWN_START'));assert.ok(events.some(x=>x.event==='CHROME_SPAWNED'&&x.data.pid===4321));assert.ok(events.some(x=>x.event==='CHROME_READY'&&x.data.pid===4321));
});
