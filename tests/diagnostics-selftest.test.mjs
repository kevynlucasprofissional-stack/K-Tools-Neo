import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as selftestModule from '../src/diagnostics-selftest.mjs';
import { main } from '../src/cli.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-selftest-'));}

test('diagnostics self-test validates the full diagnostic chain and cleans its temporary run on success',async()=>{
  assert.equal(typeof selftestModule.runDiagnosticsSelfTest,'function');const root=await tmp();
  const result=await selftestModule.runDiagnosticsSelfTest({outputRoot:root});
  assert.equal(result.ok,true);assert.equal(result.status,'DIAGNOSTICS_CHECK');assert.equal(result.diagnosticsHealthy,true);assert.ok(result.checks.length>=8);assert.equal(result.checks.every(x=>x.ok),true);assert.equal(result.temporaryArtifactsCleaned,true);
  assert.doesNotMatch(JSON.stringify(result),/DIAGNOSTIC_SELFTEST_SECRET/);
  if(result.temporaryRunDir)await assert.rejects(()=>fs.access(result.temporaryRunDir));
});

test('CLI diagnostics-check returns a structured healthy result without Chrome or XCursos credentials',async()=>{
  const root=await tmp();const outputs=[];const original=process.stdout.write;process.stdout.write=(chunk,...rest)=>{outputs.push(String(chunk));return true;};
  try{
    const config={outputRoot:root,profileDir:path.join(root,'profile'),cdpPort:9222,cdpEndpoint:'http://127.0.0.1:9222',chromePath:null,lastLessonUrl:null};
    const code=await main(['diagnostics-check','--json'],{configStore:{load:async()=>config,save:async patch=>({...config,...patch}),rememberLesson:async()=>{}},progressSink:()=>{}});
    assert.equal(code,0);const parsed=JSON.parse(outputs.join(''));assert.equal(parsed.status,'DIAGNOSTICS_CHECK');assert.equal(parsed.diagnosticsHealthy,true);assert.ok(parsed.diagnostics?.reportJson);
  }finally{process.stdout.write=original;}
});
