import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as retention from '../src/diagnostic-retention.mjs';

const DAY=24*60*60*1000;
async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-retention-'));}
async function seedRun(root,name,{status='COMPLETE',ok=true,ageDays=0,size=128,now=Date.now()}={}){
  const dir=path.join(root,'_xcursos-diagnostics',name);await fs.mkdir(dir,{recursive:true});
  await fs.writeFile(path.join(dir,'diagnostic-report.json'),JSON.stringify({runId:name,outcome:{status,ok}}));await fs.writeFile(path.join(dir,'payload.bin'),'x'.repeat(size));
  const when=new Date(now-ageDays*DAY);await fs.utimes(dir,when,when);for(const f of ['diagnostic-report.json','payload.bin'])await fs.utimes(path.join(dir,f),when,when);return dir;
}
async function exists(p){try{await fs.access(p);return true;}catch{return false;}}

test('age retention removes old success but preserves a same-age failure with longer failure retention',async()=>{
  assert.equal(typeof retention.enforceDiagnosticRetention,'function');const root=await tmp();const now=Date.parse('2026-08-17T00:00:00Z');
  const success=await seedRun(root,'old-success',{ageDays:45,now,status:'COMPLETE',ok:true});const failure=await seedRun(root,'old-failure',{ageDays:45,now,status:'ERROR',ok:false});const recent=await seedRun(root,'recent',{ageDays:2,now});
  const result=await retention.enforceDiagnosticRetention({outputRoot:root,nowFn:()=>now,successMaxAgeMs:30*DAY,failureMaxAgeMs:90*DAY,maxRuns:100,maxTotalBytes:1000000});
  assert.equal(await exists(success),false);assert.equal(await exists(failure),true);assert.equal(await exists(recent),true);assert.ok(result.deletedRuns.includes('old-success'));assert.equal(result.errors.length,0);
});

test('count/size pressure evicts oldest successful runs before a failure',async()=>{
  const root=await tmp();const now=Date.parse('2026-08-17T00:00:00Z');
  const s1=await seedRun(root,'s1',{ageDays:10,now,size:1000});const s2=await seedRun(root,'s2',{ageDays:5,now,size:1000});const failure=await seedRun(root,'failure',{ageDays:20,now,size:1000,status:'ERROR',ok:false});
  const result=await retention.enforceDiagnosticRetention({outputRoot:root,nowFn:()=>now,successMaxAgeMs:365*DAY,failureMaxAgeMs:365*DAY,maxRuns:2,maxTotalBytes:100000});
  assert.equal(await exists(s1),false);assert.equal(await exists(s2),true);assert.equal(await exists(failure),true);assert.ok(result.deletedRuns.includes('s1'));
});

test('cleanup never touches course files or unrelated log files and only rotates xcursos-all transcripts',async()=>{
  const root=await tmp();const logs=path.join(root,'logs');await fs.mkdir(logs,{recursive:true});const now=Date.parse('2026-08-17T00:00:00Z');
  const courseFile=path.join(root,'Curso X','video.mp4');await fs.mkdir(path.dirname(courseFile),{recursive:true});await fs.writeFile(courseFile,'video');
  const transcript=path.join(logs,'xcursos-all-20260101-000000-10.log');const unrelated=path.join(logs,'keep-me.log');await fs.writeFile(transcript,'old');await fs.writeFile(unrelated,'keep');const old=new Date(now-60*DAY);await fs.utimes(transcript,old,old);await fs.utimes(unrelated,old,old);
  await retention.enforceDiagnosticRetention({outputRoot:root,transcriptRoot:logs,nowFn:()=>now,transcriptMaxAgeMs:30*DAY,maxRuns:100,maxTotalBytes:1000000});
  assert.equal(await exists(courseFile),true);assert.equal(await exists(transcript),false);assert.equal(await exists(unrelated),true);
});

test('retention deletion errors are fail-soft and reported',async()=>{
  const root=await tmp();const now=Date.parse('2026-08-17T00:00:00Z');await seedRun(root,'old',{ageDays:50,now});
  const result=await retention.enforceDiagnosticRetention({outputRoot:root,nowFn:()=>now,successMaxAgeMs:30*DAY,maxRuns:100,maxTotalBytes:1000000,rmFn:async()=>{const e=new Error('denied');e.code='EACCES';throw e;}});
  assert.equal(result.errors.length,1);assert.equal(result.errors[0].code,'EACCES');assert.equal(result.ok,false);
});
