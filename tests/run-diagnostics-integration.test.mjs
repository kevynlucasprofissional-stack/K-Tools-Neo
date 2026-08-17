import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { RunnerLogger } from '../src/logger.mjs';
import { IntegratedRunDiagnostics } from '../src/integrated-diagnostics.mjs';
import { attachResultArtifacts } from '../src/cli-diagnostics.mjs';
import { XCursosCourseRunner } from '../src/runner.mjs';
import { FakeBrowser, DiskFakeDownloader, lesson } from './helpers.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-integration-'));}

async function runWithDiagnostics({failPositions=[]}={}){
  const root=await tmp();const logger=new RunnerLogger();const diagnostics=new IntegratedRunDiagnostics({outputRoot:root,command:'range',runId:`integration-${failPositions.length?'fail':'ok'}`,env:{}});await diagnostics.start({logger});
  const lessons=[lesson(1,3),lesson(2,3),lesson(3,3)];const runner=new XCursosCourseRunner({outputRoot:root,browser:new FakeBrowser(lessons),downloader:new DiskFakeDownloader({failPositions}),logger,limits:{downloadRetries:1,retryBaseDelayMs:1,retryMaxDelayMs:2,retryJitterRatio:0},sleepFn:async()=>{},progressSink:()=>{}});
  try{
    const result=await runner.runRange({start:1,end:3,resume:false,finalAudit:false});attachResultArtifacts(diagnostics,result,root);const report=await diagnostics.finalize({status:result.status,ok:result.ok,result,exitCode:result.ok?0:2});return{root,result,report,diagnostics};
  }finally{await runner.dispose();}
}

test('integrated success report reconstructs runner work, decisions, artifacts and final outcome',async()=>{
  const {result,report}=await runWithDiagnostics();assert.equal(result.status,'RANGE_COMPLETE');assert.equal(report.outcome.status,'RANGE_COMPLETE');assert.equal(report.summary.currentRunWorkItemCount,3);assert.deepEqual(report.summary.currentRunWorkItems.map(x=>x.position),[1,2,3]);
  assert.ok(report.eventSummary.count>5);assert.ok(report.eventSummary.byScope.VERIFY>=3);assert.ok(report.eventSummary.byScope.COMMIT>=3);
  assert.equal(report.artifacts.find(x=>x.name==='manifest').exists,true);assert.equal(report.artifacts.find(x=>x.name==='runnerLog').exists,true);assert.equal(report.diagnosticFindings.some(x=>x.severity==='ERROR'),false);
});

test('integrated partial run report exposes retry pressure and coverage gap instead of hiding failure',async()=>{
  const {result,report,diagnostics}=await runWithDiagnostics({failPositions:[2]});assert.equal(result.status,'RANGE_PARTIAL');assert.equal(result.ok,false);assert.ok(report.summary.persistedErrorCount>=1);assert.ok(report.eventSummary.byEvent.LOG>=1);
  const findings=report.diagnosticFindings.map(x=>x.code);assert.ok(findings.includes('COVERAGE_GAP'));assert.ok(findings.includes('RETRY_PRESSURE'));
  const markdown=await fs.readFile(diagnostics.reportMarkdownPath,'utf8');assert.match(markdown,/Possíveis pontos de falha/);assert.match(markdown,/COVERAGE_GAP/);assert.match(markdown,/RETRY_PRESSURE/);
});
