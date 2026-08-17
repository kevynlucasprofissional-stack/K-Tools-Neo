import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { deriveDiagnosticFindings } from '../src/integrated-diagnostics.mjs';
import { writeBootstrapFailureReport } from '../src/cli-diagnostics.mjs';

test('diagnostic findings map evidence to investigation areas without claiming root cause',()=>{
  const findings=deriveDiagnosticFindings({
    summary:{audit:{healthyComplete:false,missingPositions:[4],invalidFilePositions:[7]},stats:{retries:3},persistedErrors:[
      {code:'ERR_NETWORK_ACCESS_DENIED',status:'RETRY_LATER'},
      {code:'NEXT_ACTIONABILITY_TIMEOUT'},
      {code:'VERIFY_FFPROBE_FAILED'},
      {code:'MEDIA_NOT_READY'},
    ]},
    errors:[],eventSummary:{byEvent:{SUBPROCESS_TIMEOUT:1}},
  });
  const codes=findings.map(x=>x.code);assert.ok(codes.includes('NETWORK_INSTABILITY'));assert.ok(codes.includes('NAVIGATION_CONFIDENCE'));assert.ok(codes.includes('FILE_INTEGRITY'));assert.ok(codes.includes('COVERAGE_GAP'));assert.ok(codes.includes('SUBPROCESS_FAILURE'));assert.ok(codes.includes('RETRY_PRESSURE'));
  const nav=findings.find(x=>x.code==='NAVIGATION_CONFIDENCE');assert.match(nav.recommendation,/não usa um modelo de IA/i);
});

test('bootstrap failure produces a shareable fallback report before normal CLI diagnostics exist',async()=>{
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'xc-bootstrap-'));const fakeProcess={pid:91,version:'v24-test',platform:'win32',arch:'x64',cwd:()=>root};
  const ref=await writeBootstrapFailureReport(Object.assign(new Error('config exploded'),{code:'CONFIG_BOOT_FAIL'}),{argv:['download','--json'],processRef:fakeProcess,env:{LOCALAPPDATA:root}});
  const report=JSON.parse(await fs.readFile(ref.reportJson,'utf8'));assert.equal(report.outcome.status,'BOOTSTRAP_ERROR');assert.equal(report.errors[0].error.code,'CONFIG_BOOT_FAIL');assert.equal(report.command,'bootstrap');assert.match(ref.reportJson,/_xcursos-diagnostics/);
});
