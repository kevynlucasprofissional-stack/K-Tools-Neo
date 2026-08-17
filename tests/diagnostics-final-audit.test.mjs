import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { IntegratedRunDiagnostics } from '../src/integrated-diagnostics.mjs';
import { DiagnosticLiveness } from '../src/diagnostic-liveness.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-diag-final-audit-'));}
async function readJson(file){return JSON.parse(await fs.readFile(file,'utf8'));}
async function readEvents(file){return (await fs.readFile(file,'utf8')).split(/\r?\n/).filter(Boolean).map(JSON.parse);}

function countByEvent(events){const out={};for(const event of events){const key=String(event?.event||'UNKNOWN');out[key]=(out[key]||0)+1;}return out;}

test('final audit reconstructs one run consistently across report, events, metadata, liveness, manifest and errors',async()=>{
  const root=await tmp();const fakeHome=path.join(root,'Pessoa Usuária');const outputRoot=path.join(fakeHome,'Downloads','Cursos');await fs.mkdir(outputRoot,{recursive:true});
  const courseRoot=path.join(outputRoot,'Curso Diagnóstico');const metaDir=path.join(courseRoot,'_xcursos-runner');await fs.mkdir(metaDir,{recursive:true});
  const outputFile=path.join(courseRoot,'01 Aula.mp4');await fs.writeFile(outputFile,Buffer.alloc(1024));
  const manifestPath=path.join(metaDir,'manifest.jsonl');const errorsPath=path.join(metaDir,'errors.jsonl');
  const codeIdentity={packageVersion:'4.2.6',runnerVersion:'4.2.6',commit:'a'.repeat(40),branch:'audit',sourceIdentity:'GIT_COMMIT',cliPath:path.join(fakeHome,'xcursos','src','cli.mjs'),installRoot:path.join(fakeHome,'xcursos'),packageJson:path.join(fakeHome,'xcursos','package.json'),nodeVersion:process.version};
  const diag=new IntegratedRunDiagnostics({outputRoot,command:'download',runId:'final-audit-run',env:{HOME:fakeHome},shareHomeDir:fakeHome,codeIdentity});
  const livenessPath=path.join(diag.runDir,'liveness.json');const liveness=new DiagnosticLiveness({runId:diag.runId,pid:process.pid,filePath:livenessPath,heartbeatIntervalMs:60_000});
  const logger=new RunnerLogger({eventObserver:event=>liveness.noteEvent(event)});diag.liveness=liveness;diag.addArtifact('liveness',livenessPath,{description:'Final audit liveness'});
  await diag.start({logger,context:{command:'download'}});liveness.configure({filePath:livenessPath,runId:diag.runId,pid:process.pid});await liveness.persist();
  diag.setContext({resume:true,cdpEndpoint:'http://127.0.0.1:9222',outputRoot});diag.setConfiguration({schemaVersion:1,runtime:{resume:true,cdpEndpoint:'http://127.0.0.1:9222',outputRoot,profileDir:path.join(fakeHome,'AppData','Local','XCursosProfile')},limits:{downloadRetries:3,navigationRetries:2,mediaReadyTimeoutMs:15000}});
  diag.attachCourseArtifacts({courseName:'Curso Diagnóstico',metaDir,statePath:path.join(metaDir,'state.json'),manifestPath,errorsPath,logPath:path.join(metaDir,'runner.log'),schedulerPath:path.join(metaDir,'scheduler.checkpoint.json'),navigationPath:path.join(metaDir,'lesson-navigation-index.json'),debugRoot:path.join(metaDir,'debug')});
  // Mirrors cli-diagnostics.attachResultArtifacts(): attaching artifacts and setting the effective course root are separate operations.
  diag.setContext({courseRoot});
  await diag.phase('COMMAND','START',{command:'download'});

  const timestamp=new Date().toISOString();
  await fs.writeFile(manifestPath,`${JSON.stringify({timestamp,position:1,status:'DOWNLOADED',attempts:2,lessonTitle:'Aula 1',moduleName:'Módulo 1',modulePath:['Módulo 1'],outputFile,validation:{duration:120,codec:'h264',size:1024,downloadMethod:'XCURSOS_NATIVE'}})}\n`,'utf8');
  await fs.writeFile(errorsPath,`${JSON.stringify({timestamp,scope:'NAVIGATION',position:1,status:'RETRY_LATER',code:'NAV_NETWORK_ERROR',failureCode:'ERR_NETWORK_ACCESS_DENIED',message:'transient network issue',attempt:1,maxAttempts:3,delayMs:250})}\n`,'utf8');

  await logger.log('INSPECT','lesson inspected',{position:1},{event:'INSPECT'});
  await logger.warn('RETRY','navigation retry',{position:1,code:'NAV_NETWORK_ERROR',networkCode:'ERR_NETWORK_ACCESS_DENIED',attempt:1,maxAttempts:3,delayMs:250},{event:'RETRY'});
  await logger.log('PROCESS','ffprobe started',{position:1,pid:777,command:'ffprobe'},{event:'SUBPROCESS_START'});
  await logger.log('PROCESS','ffprobe finished',{position:1,pid:777,code:0,durationMs:42},{event:'SUBPROCESS_END'});
  await logger.log('VERIFY','video validated',{position:1,duration:120,codec:'h264'},{event:'VERIFY'});
  await logger.log('COMMIT','position committed',{position:1,status:'DOWNLOADED',downloadMethod:'XCURSOS_NATIVE'},{event:'COMMIT'});
  await liveness.persist();

  const result={ok:true,status:'COMPLETE',course:'Curso Diagnóstico',courseRoot,audit:{healthyComplete:true,processed:1,total:1,downloaded:1,alreadyPresent:0,noVideo:0,missingPositions:[],invalidFilePositions:[]},stats:{retries:1}};
  const returned=await diag.finalize({status:'COMPLETE',ok:true,exitCode:0,result});
  const report=await readJson(diag.reportJsonPath);const metadata=await readJson(diag.metaPath);const events=await readEvents(diag.eventPath);const live=await readJson(livenessPath);const markdown=await fs.readFile(diag.reportMarkdownPath,'utf8');const reportText=await fs.readFile(diag.reportJsonPath,'utf8');

  assert.equal(returned.runId,report.runId);assert.equal(report.runId,metadata.runId);assert.equal(report.runId,live.runId);assert.ok(events.length>0);assert.equal(events.every(event=>event.runId===report.runId),true);
  assert.equal(report.eventSummary.count,events.length);assert.deepEqual(report.eventSummary.byEvent,countByEvent(events));assert.equal(report.timeline.totalEvents,events.length);assert.equal(report.timeline.events.at(-1).event,'RUN_FINALIZED');
  assert.equal(report.outcome.status,'COMPLETE');assert.equal(report.outcome.ok,true);assert.equal(report.diagnosticHealth.degraded,false);

  assert.equal(report.codeIdentity.runnerVersion,metadata.codeIdentity.runnerVersion);assert.equal(report.codeIdentity.commit,metadata.codeIdentity.commit);assert.equal(report.codeIdentity.sourceIdentity,metadata.codeIdentity.sourceIdentity);
  assert.equal(metadata.effectiveConfig.runtime.outputRoot,outputRoot);assert.equal(report.effectiveConfig.runtime.outputRoot.startsWith('$HOME'),true);assert.equal(report.effectiveConfig.limits.downloadRetries,3);
  assert.equal(metadata.context.courseRoot,courseRoot);assert.equal(report.context.courseRoot.startsWith('$HOME'),true);assert.ok(events.some(event=>event.context?.courseRoot===courseRoot));

  assert.equal(report.summary.currentRunWorkItemCount,1);const item=report.summary.currentRunWorkItems[0];assert.equal(item.position,1);assert.equal(item.status,'DOWNLOADED');assert.equal(item.validation.downloadMethod,'XCURSOS_NATIVE');assert.equal(item.validation.codec,'h264');assert.equal(item.outputFile.startsWith('$HOME'),true);assert.equal(await fs.stat(outputFile).then(s=>s.isFile()),true);
  assert.equal(report.summary.persistedErrorCount,1);assert.equal(report.summary.persistedErrors[0].code,'NAV_NETWORK_ERROR');assert.ok(report.diagnosticFindings.some(x=>x.code==='NETWORK_INSTABILITY'));assert.ok(report.diagnosticFindings.some(x=>x.code==='RETRY_PRESSURE'));

  assert.equal(report.liveness.position,1);assert.equal(report.liveness.activeSubprocess,null);assert.ok(['HEALTHY','EXPECTED_WAIT'].includes(report.liveness.status));
  assert.doesNotMatch(reportText,new RegExp(fakeHome.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));assert.doesNotMatch(markdown,new RegExp(fakeHome.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));assert.match(reportText,/\$HOME/);
  assert.equal(diag.reference().reportJson,diag.reportJsonPath);assert.ok(diag.reference().reportJson.startsWith(fakeHome));
});
