import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { StateStore, readJsonl } from '../src/state.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-resume-cache-'));}
function fingerprint(stat){return{size:stat.size,mtimeMs:stat.mtimeMs};}
async function makeStore({withFingerprint=true}={}){
  const root=await tmp();const store=new StateStore({outputRoot:root,courseName:'Cache Course',totalPositions:1});
  await store.initialize({resume:false,workPageUrl:'https://www.xcursos.com/curso/c/aula/1'});
  const file=path.join(store.courseDir,'001 - Aula.mp4');await fs.mkdir(store.courseDir,{recursive:true});await fs.writeFile(file,'video-data');
  const stat=await fs.stat(file);const validation={size:stat.size,duration:42,codec:'h264',...(withFingerprint?{fileFingerprint:fingerprint(stat)}:{})};
  await store.commit({position:1,status:'DOWNLOADED',lessonTitle:'Aula',lessonUrl:'https://www.xcursos.com/curso/c/aula/1',outputFile:file,validation});
  return{root,store,file};
}

test('resume skips validator when persisted fingerprint and validation still match',async()=>{
  const{store}=await makeStore();let calls=0;
  const invalid=await store.verifyFileBackedEntries(async()=>{calls++;throw new Error('should not run');});
  assert.deepEqual(invalid,[]);assert.equal(calls,0);
});

test('changed file refuses persisted cache and runs validator again',async()=>{
  const{store,file}=await makeStore();let calls=0;await fs.appendFile(file,'changed');
  const invalid=await store.verifyFileBackedEntries(async p=>{calls++;const stat=await fs.stat(p);return{size:stat.size,duration:42,codec:'h264',fileFingerprint:fingerprint(stat)};});
  assert.deepEqual(invalid,[]);assert.equal(calls,1);
  await store.verifyFileBackedEntries(async()=>{calls++;throw new Error('second resume should use refreshed cache');});assert.equal(calls,1);
});

test('same-size file with changed mtime refuses persisted cache',async()=>{
  const{store,file}=await makeStore();let calls=0;const before=await fs.stat(file);
  await fs.writeFile(file,'VIDEO-DATA');
  const future=new Date(Date.now()+2_000);await fs.utimes(file,future,future);
  const after=await fs.stat(file);assert.equal(after.size,before.size);assert.notEqual(after.mtimeMs,before.mtimeMs);
  const invalid=await store.verifyFileBackedEntries(async p=>{calls++;const stat=await fs.stat(p);return{size:stat.size,duration:42,codec:'h264',fileFingerprint:fingerprint(stat)};});
  assert.deepEqual(invalid,[]);assert.equal(calls,1);
});

test('legacy manifest without fingerprint validates once and is migrated durably',async()=>{
  const{store}=await makeStore({withFingerprint:false});let calls=0;
  await store.verifyFileBackedEntries(async p=>{calls++;const stat=await fs.stat(p);return{size:stat.size,duration:42,codec:'h264',fileFingerprint:fingerprint(stat)};});
  assert.equal(calls,1);
  const records=await readJsonl(store.manifestPath);assert.ok(records[0].validation.fileFingerprint);
  await store.verifyFileBackedEntries(async()=>{calls++;throw new Error('migrated cache should be used');});assert.equal(calls,1);
});

test('explicit audit ignores resume cache and performs full validation',async()=>{
  const{store}=await makeStore();let calls=0;
  const audit=await store.audit({validator:async p=>{calls++;const stat=await fs.stat(p);return{size:stat.size,duration:42,codec:'h264',fileFingerprint:fingerprint(stat)};}});
  assert.equal(calls,1);assert.deepEqual(audit.invalidFilePositions,[]);
});
