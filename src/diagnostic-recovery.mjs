import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { atomicWriteJson, sanitizeForPersistence } from './utils.mjs';
import { buildBoundedTimeline } from './run-diagnostics.mjs';

async function readJson(filePath){try{return JSON.parse(await fs.readFile(filePath,'utf8'));}catch{return null;}}
async function readJsonl(filePath){
  try{
    const lines=(await fs.readFile(filePath,'utf8')).split(/\r?\n/).filter(Boolean);const out=[];
    for(const line of lines){try{out.push(JSON.parse(line));}catch{}}
    return out;
  }catch{return[];}
}
async function fileExists(filePath){try{await fs.access(filePath);return true;}catch{return false;}}
function countBy(items,keyFn){const out={};for(const item of items){const key=String(keyFn(item)||'UNKNOWN');out[key]=(out[key]||0)+1;}return out;}
function eventSummary(events){return{count:events.length,byLevel:countBy(events,e=>e.level),byScope:countBy(events,e=>e.scope),byEvent:countBy(events,e=>e.event)};}
function eventPosition(event){const value=event?.context?.position??event?.data?.position??null;const n=Number(value);return Number.isInteger(n)?n:null;}
function lastMatching(events,predicate){for(let i=events.length-1;i>=0;i--)if(predicate(events[i]))return events[i];return null;}
function latestTimestampMs(meta,events){
  const last=events.at(-1)?.timestamp||meta?.startedAt||null;const parsed=Date.parse(String(last||''));return Number.isFinite(parsed)?parsed:0;
}
function defaultIsPidAlive(pid){
  const value=Number(pid);if(!Number.isInteger(value)||value<=0)return false;
  try{process.kill(value,0);return true;}catch(error){return error?.code==='EPERM';}
}
function markdown(report){
  const r=report.recovery||{};return `# XCursos Runner — Execução Interrompida\n\n- **Run ID:** \`${report.runId}\`\n- **Comando:** \`${report.command||'unknown'}\`\n- **Status:** **INTERRUPTED**\n- **Início:** ${report.startedAt||'n/d'}\n- **Recuperado em:** ${r.recoveredAt||'n/d'}\n- **PID anterior:** ${r.previousPid??'n/d'}\n- **Última posição observada:** ${r.lastPosition??'n/d'}\n- **Último evento:** \`${r.lastEvent?.event||'n/d'}\`\n- **Eventos preservados:** ${report.eventSummary?.count??0}\n\nEste relatório foi reconstruído na inicialização seguinte porque a execução anterior terminou sem produzir um relatório final válido.\n`;
}

export async function recoverInterruptedDiagnosticRuns({
  outputRoot,
  nowFn=Date.now,
  isPidAlive=defaultIsPidAlive,
  hostname=os.hostname(),
  foreignHostGraceMs=15*60*1000,
}={}){
  const root=path.join(path.resolve(outputRoot||process.cwd()),'_xcursos-diagnostics');
  const result={recovered:[],active:[],completed:[],ignored:[],errors:[]};
  let entries=[];try{entries=await fs.readdir(root,{withFileTypes:true});}catch(error){if(error?.code==='ENOENT')return result;result.errors.push(sanitizeForPersistence({stage:'LIST',code:error?.code||null,message:error?.message||String(error)}));return result;}
  for(const entry of entries){
    if(!entry.isDirectory())continue;
    const runDir=path.join(root,entry.name);const metaPath=path.join(runDir,'run-meta.json');const eventsPath=path.join(runDir,'events.jsonl');const finalPath=path.join(runDir,'diagnostic-report.json');const recoveredPath=path.join(runDir,'recovered-diagnostic-report.json');const recoveredMarkdownPath=path.join(runDir,'recovered-diagnostic-report.md');
    try{
      const final=await readJson(finalPath);if(final?.outcome){result.completed.push({runId:final.runId||entry.name,runDir,report:finalPath});continue;}
      const previousRecovered=await readJson(recoveredPath);if(previousRecovered?.outcome?.status==='INTERRUPTED'){result.completed.push({runId:previousRecovered.runId||entry.name,runDir,report:recoveredPath,recovered:true});continue;}
      const meta=await readJson(metaPath);if(!meta?.runId){result.ignored.push({runId:entry.name,runDir,reason:'RUN_META_MISSING_OR_INVALID'});continue;}
      const events=await readJsonl(eventsPath);const previousHost=meta?.process?.hostname||null;const previousPid=Number(meta?.process?.pid)||null;const sameHost=Boolean(previousHost&&hostname&&String(previousHost)===String(hostname));const alive=sameHost&&previousPid?Boolean(isPidAlive(previousPid)):false;
      if(alive){result.active.push({runId:meta.runId,runDir,pid:previousPid,hostname:previousHost});continue;}
      if(!sameHost){const age=Math.max(0,Number(nowFn())-latestTimestampMs(meta,events));if(age<foreignHostGraceMs){result.active.push({runId:meta.runId,runDir,pid:previousPid,hostname:previousHost,remoteHost:true,ageMs:age});continue;}}
      const lastEvent=events.at(-1)||null;const lastPosition=eventPosition(lastMatching(events,e=>eventPosition(e)!=null));const lastSubprocess=lastMatching(events,e=>/^SUBPROCESS_/i.test(String(e?.event||'')));const recoveredAt=new Date(Number(nowFn())).toISOString();
      const report=sanitizeForPersistence({
        schemaVersion:1,runId:meta.runId,command:meta.command||'unknown',startedAt:meta.startedAt||null,endedAt:recoveredAt,durationMs:Math.max(0,Number(nowFn())-Date.parse(meta.startedAt||recoveredAt)),
        outcome:{status:'INTERRUPTED',ok:false,exitCode:null,reason:'Previous process ended without a complete diagnostic report'},
        codeIdentity:meta.codeIdentity||null,effectiveConfig:meta.effectiveConfig||null,environment:meta.process||null,context:lastEvent?.context||meta.context||{},
        eventSummary:eventSummary(events),timeline:buildBoundedTimeline(events),
        recovery:{recoveredAt,previousPid,previousHostname:previousHost,sameHost,lastEvent,lastPosition,lastSubprocess,finalEventObserved:events.some(e=>e?.event==='RUN_FINALIZED')},
        files:{events:eventsPath,metadata:metaPath,recoveredReport:recoveredPath,recoveredMarkdown:recoveredMarkdownPath},
      });
      await atomicWriteJson(recoveredPath,report);await fs.writeFile(recoveredMarkdownPath,markdown(report),'utf8');
      result.recovered.push({runId:meta.runId,runDir,report:recoveredPath,markdown:recoveredMarkdownPath});
    }catch(error){result.errors.push(sanitizeForPersistence({runId:entry.name,runDir,stage:'RECOVER',code:error?.code||null,message:error?.message||String(error)}));}
  }
  return result;
}
