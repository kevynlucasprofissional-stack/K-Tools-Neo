import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { IntegratedRunDiagnostics } from './integrated-diagnostics.mjs';
import { RunnerLogger } from './logger.mjs';
import { DiagnosticLiveness } from './diagnostic-liveness.mjs';
import { createObservedProcessRunner } from './process-observer.mjs';
import { runProcess } from './process.mjs';
import { sanitizeForPersistence } from './utils.mjs';

const SELFTEST_SECRET='DIAGNOSTIC_SELFTEST_SECRET';

async function readJson(filePath){return JSON.parse(await fs.readFile(filePath,'utf8'));}
async function readText(filePath){return await fs.readFile(filePath,'utf8');}
async function readEvents(filePath){return (await readText(filePath)).split(/\r?\n/).filter(Boolean).map(line=>JSON.parse(line));}
function addCheck(checks,name,ok,details=null){checks.push(sanitizeForPersistence({name,ok:Boolean(ok),details}));return Boolean(ok);}
function countByEvent(events){const out={};for(const event of events){const key=String(event?.event||'UNKNOWN');out[key]=(out[key]||0)+1;}return out;}
function equality(a,b){return JSON.stringify(a)===JSON.stringify(b);}

export async function runDiagnosticsSelfTest({outputRoot=null,processRef=process,env=process.env}={}){
  const base=path.resolve(outputRoot||os.tmpdir());
  await fs.mkdir(base,{recursive:true}).catch(()=>{});
  const tempRoot=await fs.mkdtemp(path.join(os.tmpdir(),'xcursos-diagnostics-check-'));
  const checks=[];let temporaryRunDir=null;let temporaryArtifactsCleaned=false;let result=null;
  try{
    const diagnostics=new IntegratedRunDiagnostics({outputRoot:tempRoot,command:'diagnostics-selftest',env,processRef});
    const liveness=new DiagnosticLiveness({runId:diagnostics.runId,pid:processRef?.pid??process.pid,heartbeatIntervalMs:60_000});
    const logger=new RunnerLogger({eventObserver:event=>liveness.noteEvent(event)});
    diagnostics.liveness=liveness;
    await diagnostics.start({logger,context:{command:'diagnostics-selftest',purpose:'SELF_TEST'}});
    temporaryRunDir=diagnostics.runDir;
    const livenessPath=path.join(diagnostics.runDir,'liveness.json');
    liveness.configure({filePath:livenessPath,runId:diagnostics.runId,pid:processRef?.pid??process.pid});
    diagnostics.addArtifact('liveness',livenessPath,{description:'Self-test liveness snapshot'});
    await liveness.persist();

    diagnostics.setContext({position:1,stage:'SELF_TEST'});
    diagnostics.setConfiguration({schemaVersion:1,runtime:{resume:false,cdpEndpoint:'http://127.0.0.1:9222',outputRoot:tempRoot},limits:{downloadRetries:3,navigationRetries:2}});
    await diagnostics.phase('SELF_TEST','START',{step:'begin'});
    await logger.warn('SELFTEST',`sanitization token=${SELFTEST_SECRET}`,{position:1},{event:'SELFTEST_WARN'});
    const simulated=Object.assign(new Error(`simulated nonfatal token=${SELFTEST_SECRET}`),{code:'SELFTEST_SIMULATED'});
    await diagnostics.captureError(simulated,{scope:'SELFTEST',fatal:false,data:{expected:true}});

    const observedProcess=createObservedProcessRunner({logger,baseRunner:runProcess});
    const child=await observedProcess(process.execPath,['-e',"process.stdout.write('diagnostic-selftest-ok')"],{timeoutMs:5_000});
    addCheck(checks,'subprocess-execution',child.code===0&&child.stdout==='diagnostic-selftest-ok',{exitCode:child.code});

    liveness.noteProgress({stage:'SELF_TEST',position:1,operation:'VALIDATE'});
    await liveness.persist();
    await diagnostics.phase('SELF_TEST','PASS',{step:'finalize'});
    const finalized=await diagnostics.finalize({status:'DIAGNOSTICS_CHECK',ok:true,exitCode:0,result:{status:'DIAGNOSTICS_CHECK',ok:true}});

    const report=await readJson(diagnostics.reportJsonPath);
    const markdown=await readText(diagnostics.reportMarkdownPath);
    const metadata=await readJson(diagnostics.metaPath);
    const events=await readEvents(diagnostics.eventPath);
    const livenessStored=await readJson(livenessPath);
    const combined=[JSON.stringify(report),markdown,JSON.stringify(metadata),events.map(e=>JSON.stringify(e)).join('\n'),JSON.stringify(livenessStored)].join('\n');

    addCheck(checks,'report-json',Boolean(report?.runId&&report?.outcome?.status==='DIAGNOSTICS_CHECK'));
    addCheck(checks,'report-markdown',markdown.includes('Relatório de Diagnóstico')&&markdown.length>100);
    addCheck(checks,'run-id-consistency',metadata.runId===report.runId&&events.length>0&&events.every(e=>e.runId===report.runId));
    addCheck(checks,'event-summary-consistency',report.eventSummary?.count===events.length&&equality(report.eventSummary?.byEvent,countByEvent(events)),{reported:report.eventSummary?.count,physical:events.length});
    addCheck(checks,'timeline-embedded',report.timeline?.totalEvents===events.length&&Array.isArray(report.timeline?.events)&&report.timeline.events.length>0);
    addCheck(checks,'sanitization',!combined.includes(SELFTEST_SECRET));
    addCheck(checks,'subprocess-observability',events.some(e=>e.event==='SUBPROCESS_START')&&events.some(e=>e.event==='SUBPROCESS_END'));
    addCheck(checks,'metadata-context',metadata.context?.purpose==='SELF_TEST'&&metadata.effectiveConfig?.limits?.downloadRetries===3);
    addCheck(checks,'code-identity',Boolean(report.codeIdentity?.runnerVersion&&report.codeIdentity?.sourceIdentity));
    addCheck(checks,'liveness',Boolean(report.liveness&&livenessStored.runId===report.runId&&report.liveness.position===1));
    addCheck(checks,'intentional-error-capture',report.errors?.some(e=>e.error?.code==='SELFTEST_SIMULATED'));
    addCheck(checks,'diagnostic-storage-health',finalized?.diagnosticHealth?.degraded!==true,{diagnosticHealth:finalized?.diagnosticHealth||null});

    const diagnosticsHealthy=checks.every(check=>check.ok);
    result=sanitizeForPersistence({
      ok:diagnosticsHealthy,status:'DIAGNOSTICS_CHECK',diagnosticsHealthy,checks,
      temporaryRunDir:diagnostics.runDir,temporaryArtifactsCleaned:false,
      summary:{checkCount:checks.length,passed:checks.filter(x=>x.ok).length,failed:checks.filter(x=>!x.ok).length},
    });
    if(diagnosticsHealthy){
      await fs.rm(tempRoot,{recursive:true,force:true});temporaryArtifactsCleaned=true;
      result.temporaryArtifactsCleaned=true;
    }
    return result;
  }catch(error){
    addCheck(checks,'selftest-execution',false,{code:error?.code||null,message:error?.message||String(error)});
    return sanitizeForPersistence({
      ok:false,status:'DIAGNOSTICS_CHECK',diagnosticsHealthy:false,checks,temporaryRunDir,temporaryArtifactsCleaned,
      summary:{checkCount:checks.length,passed:checks.filter(x=>x.ok).length,failed:checks.filter(x=>!x.ok).length},
      error:{code:error?.code||null,message:error?.message||String(error)},
    });
  }
}
