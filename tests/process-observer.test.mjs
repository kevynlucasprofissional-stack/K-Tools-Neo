import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { createObservedProcessRunner } from '../src/process-observer.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-proc-observer-'));}
async function events(file){return (await fs.readFile(file,'utf8')).trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);}

test('observed subprocess logs start/end, pid, duration and sanitized arguments',async()=>{
  const root=await tmp();const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'proc-run'});let now=1000;
  const runner=createObservedProcessRunner({logger,nowFn:()=>now,baseRunner:async()=>{now=1300;return{pid:77,code:0,signal:null,stdout:'ok',stderr:'',stdoutTruncated:false,stderrTruncated:false};}});
  const result=await runner('yt-dlp',['https://cdn.example/a.mp4?X-Amz-Signature=secret','--continue'],{timeoutMs:5000});assert.equal(result.pid,77);
  const e=await events(eventFile);assert.equal(e[0].event,'SUBPROCESS_START');assert.equal(e[1].event,'SUBPROCESS_END');assert.equal(e[1].data.pid,77);assert.equal(e[1].data.durationMs,300);assert.doesNotMatch(JSON.stringify(e),/X-Amz-Signature=secret/);
});

test('observed subprocess records non-zero stderr tail and truncation flags',async()=>{
  const root=await tmp();const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'proc-fail'});
  const runner=createObservedProcessRunner({logger,baseRunner:async()=>({pid:88,code:1,signal:null,stdout:'partial',stderr:'network token=hidden-value',stdoutTruncated:true,stderrTruncated:false})});
  await runner('yt-dlp',['x'],{});const e=await events(eventFile);const end=e.at(-1);assert.equal(end.level,'WARN');assert.equal(end.data.exitCode,1);assert.equal(end.data.stdoutTruncated,true);assert.doesNotMatch(JSON.stringify(end),/hidden-value/);
});

test('observed subprocess records timeout/abort style exceptions before rethrowing',async()=>{
  const root=await tmp();const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'proc-timeout'});const error=Object.assign(new Error('too slow'),{code:'PROCESS_TIMEOUT',details:{pid:99}});
  const runner=createObservedProcessRunner({logger,baseRunner:async()=>{throw error;}});await assert.rejects(()=>runner('ffprobe',['a.mp4'],{timeoutMs:10}),e=>e===error);
  const e=await events(eventFile);const last=e.at(-1);assert.equal(last.event,'SUBPROCESS_TIMEOUT');assert.equal(last.level,'ERROR');assert.equal(last.data.code,'PROCESS_TIMEOUT');
});
