import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-logger-'));}

test('RunnerLogger preserves human log and emits sanitized structured events with run correlation',async()=>{
  const root=await tmp();const logFile=path.join(root,'runner.log');const eventFile=path.join(root,'events.jsonl');
  let now=Date.parse('2026-08-16T21:00:00.000Z');
  const logger=new RunnerLogger({logFile,eventFile,runId:'run-123',context:{command:'download'},nowFn:()=>now});
  await logger.log('BOOT','starting',{position:1,url:'https://cdn.example/video.mp4?X-Amz-Signature=secret'});
  now+=1000;await logger.warn('RETRY','retrying',{token:'secret-token',attempt:2},{event:'RETRY_DECISION'});
  const human=await fs.readFile(logFile,'utf8');
  assert.match(human,/\[BOOT\] starting/);assert.match(human,/\[RETRY\] retrying/);assert.doesNotMatch(human,/secret-token|X-Amz-Signature=secret/);
  const events=(await fs.readFile(eventFile,'utf8')).trim().split(/\r?\n/).map(JSON.parse);
  assert.equal(events.length,2);assert.equal(events[0].runId,'run-123');assert.equal(events[0].sequence,1);assert.equal(events[1].sequence,2);
  assert.equal(events[0].context.command,'download');assert.equal(events[1].level,'WARN');assert.equal(events[1].event,'RETRY_DECISION');
  assert.doesNotMatch(JSON.stringify(events),/secret-token|X-Amz-Signature=secret/);
});

test('RunnerLogger can attach course/position context after boot without breaking legacy use',async()=>{
  const root=await tmp();const eventFile=path.join(root,'events.jsonl');const logger=new RunnerLogger({eventFile,runId:'run-ctx'});
  logger.setContext({course:'Course A',position:7});await logger.error('DOWNLOAD','failed',{code:'NETWORK_RESET'});
  const event=JSON.parse((await fs.readFile(eventFile,'utf8')).trim());
  assert.equal(event.context.course,'Course A');assert.equal(event.context.position,7);assert.equal(event.level,'ERROR');
});
