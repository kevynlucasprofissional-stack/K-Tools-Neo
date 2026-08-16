import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { AdaptiveLocator, scoreNextCandidate } from '../src/adaptive-locator.mjs';
import { DebugSnapshotManager } from '../src/debug-snapshots.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-debug-'));}

test('AdaptiveLocator accepts semantic Próxima aula change with high score',()=>{const s=scoreNextCandidate({tag:'button',role:'button',text:'Próxima aula',ariaLabel:''});assert.ok(s>=0.85);});
test('AdaptiveLocator rejects low-score wrong action and ambiguous candidates',async()=>{
  assert.ok(scoreNextCandidate({tag:'button',role:'button',text:'Voltar ao curso'})<0.85);
  const page={evaluate:async()=>[{index:0,tag:'button',role:'button',text:'Próxima aula'},{index:1,tag:'button',role:'button',text:'Próxima aula'}],locator:()=>({nth:()=>({})})};
  const a=new AdaptiveLocator({threshold:0.85,ambiguityDelta:0.05});assert.equal(await a.findNext(page),null);
});
test('AdaptiveLocator returns locator only for unique high-confidence candidate',async()=>{
  const clicked={};const locator={nth:i=>({click:async()=>{clicked.i=i;}})};
  const page={evaluate:async()=>[{index:0,tag:'a',role:'link',text:'Anterior'},{index:1,tag:'button',role:'button',text:'Próxima aula'}],locator:()=>locator};
  const a=new AdaptiveLocator();const found=await a.findNext(page);assert.equal(found.candidate.index,1);await found.locator.click();assert.equal(clicked.i,1);
});

test('DebugSnapshotManager creates sanitized bounded diagnostic bundle',async()=>{
  const root=await tmp();
  const page={content:async()=>'<html>https://cdn.example/v.mp4?X-Amz-Signature=SUPERSECRET Authorization: Bearer TOPSECRET token=ABC123</html>',screenshot:async()=>Buffer.from('PNG')};
  const m=new DebugSnapshotManager({debugRoot:root,maxSnapshots:2,maxHtmlBytes:10000});
  for(let i=1;i<=3;i++)await m.capture({position:i,pageRef:{handle:page,url:`https://www.xcursos.com/curso/c/aula/${i}`},error:{code:'TEST',message:'Authorization: Bearer NOPE'},metadata:{Authorization:'Bearer SECRET',Cookie:'sid=SECRET'},networkEvents:[{url:'https://cdn.example/v.mp4?token=SECRET'}]});
  const dirs=(await fs.readdir(root)).filter(x=>!x.startsWith('.'));assert.equal(dirs.length,2);
  const latest=path.join(root,dirs.sort().at(-1));const combined=(await Promise.all(['page.html','metadata.json','network.jsonl','error.json'].map(f=>fs.readFile(path.join(latest,f),'utf8')))).join('\n');
  for(const secret of ['SUPERSECRET','TOPSECRET','NOPE','sid=SECRET','token=SECRET'])assert.equal(combined.includes(secret),false,secret);
  assert.equal((await fs.readFile(path.join(latest,'screenshot.png'))).toString(),'PNG');
});

test('Debug snapshot filesystem failure never replaces original execution error',async()=>{const m=new DebugSnapshotManager({debugRoot:'/dev/null/nope'});const r=await m.capture({position:1,error:new Error('x')});assert.equal(r.ok,false);});

test('Debug snapshot rotation enforces age and total-size limits',async()=>{
  const root=await tmp();await fs.mkdir(root,{recursive:true});
  const old=path.join(root,'001-old');await fs.mkdir(old);await fs.writeFile(path.join(old,'x.bin'),Buffer.alloc(200));const ancient=new Date(Date.now()-10_000);await fs.utimes(old,ancient,ancient);
  const fresh=path.join(root,'002-fresh');await fs.mkdir(fresh);await fs.writeFile(path.join(fresh,'x.bin'),Buffer.alloc(200));
  const m=new DebugSnapshotManager({debugRoot:root,maxSnapshots:10,maxAgeMs:1000,maxTotalBytes:250});await m.rotate();const dirs=await fs.readdir(root);assert.equal(dirs.includes('001-old'),false);assert.ok(dirs.length<=1);
});
