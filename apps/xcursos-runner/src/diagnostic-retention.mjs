import fs from 'node:fs/promises';
import path from 'node:path';
import { sanitizeForPersistence } from './utils.mjs';

const DAY=24*60*60*1000;
const FAILURE_STATUS=/(?:ERROR|FAIL|FAILED|FATAL|INTERRUPTED|UNCAUGHT|UNHANDLED|BLOCKED|ABORTED|CRASH)/i;

async function readJson(filePath){try{return JSON.parse(await fs.readFile(filePath,'utf8'));}catch{return null;}}
async function statSafe(filePath){try{return await fs.stat(filePath);}catch{return null;}}

async function recursiveSize(root){
  let total=0;let entries=[];
  try{entries=await fs.readdir(root,{withFileTypes:true});}catch{return 0;}
  for(const entry of entries){
    const full=path.join(root,entry.name);
    if(entry.isDirectory())total+=await recursiveSize(full);
    else if(entry.isFile()){const stat=await statSafe(full);total+=Number(stat?.size||0);}
  }
  return total;
}

function reportTimestamp(report,stat){
  for(const value of [report?.endedAt,report?.recovery?.recoveredAt,report?.startedAt]){
    const parsed=Date.parse(String(value||''));if(Number.isFinite(parsed))return parsed;
  }
  return Number(stat?.mtimeMs||0);
}

function isFailureReport(report,{recovered=false}={}){
  if(recovered)return true;
  if(report?.outcome?.ok===false)return true;
  return FAILURE_STATUS.test(String(report?.outcome?.status||report?.status||''));
}

async function inspectRun(runDir,name){
  const stat=await statSafe(runDir);if(!stat?.isDirectory())return null;
  const normal=await readJson(path.join(runDir,'diagnostic-report.json'));
  const recovered=normal?null:await readJson(path.join(runDir,'recovered-diagnostic-report.json'));
  const meta=normal||recovered?null:await readJson(path.join(runDir,'run-meta.json'));
  const report=normal||recovered||meta||{};
  return{
    runId:String(report.runId||name),name,runDir,
    failure:isFailureReport(report,{recovered:Boolean(recovered)}),
    timestampMs:reportTimestamp(report,stat),
    sizeBytes:await recursiveSize(runDir),
  };
}

function safeError(stage,error,extra={}){
  return sanitizeForPersistence({stage,...extra,code:error?.code||'DIAGNOSTIC_RETENTION_ERROR',message:error?.message||String(error)});
}

async function removeRun(run,rmFn,result){
  try{await rmFn(run.runDir,{recursive:true,force:true});result.deletedRuns.push(run.runId);return true;}
  catch(error){result.errors.push(safeError('DELETE_RUN',error,{runId:run.runId,path:run.runDir}));return false;}
}

async function cleanTranscripts({transcriptRoot,nowMs,maxAgeMs,rmFn,result}){
  if(!transcriptRoot)return;
  let entries=[];try{entries=await fs.readdir(transcriptRoot,{withFileTypes:true});}catch(error){if(error?.code!=='ENOENT')result.errors.push(safeError('LIST_TRANSCRIPTS',error,{path:transcriptRoot}));return;}
  for(const entry of entries){
    if(!entry.isFile()||!/^xcursos-all-.*\.log$/i.test(entry.name))continue;
    const full=path.join(transcriptRoot,entry.name);const stat=await statSafe(full);if(!stat)continue;
    if(nowMs-Number(stat.mtimeMs)<=maxAgeMs)continue;
    try{await rmFn(full,{force:true});result.deletedTranscripts.push(entry.name);}
    catch(error){result.errors.push(safeError('DELETE_TRANSCRIPT',error,{path:full}));}
  }
}

export async function enforceDiagnosticRetention({
  outputRoot,
  transcriptRoot=null,
  nowFn=Date.now,
  successMaxAgeMs=30*DAY,
  failureMaxAgeMs=90*DAY,
  transcriptMaxAgeMs=30*DAY,
  maxRuns=100,
  maxTotalBytes=500*1024*1024,
  protectedRunIds=[],
  rmFn=fs.rm,
}={}){
  const diagnosticRoot=path.join(path.resolve(outputRoot||process.cwd()),'_xcursos-diagnostics');
  const protectedIds=new Set((protectedRunIds||[]).map(String));
  const result={ok:true,deletedRuns:[],deletedTranscripts:[],keptRuns:[],protectedRuns:[],before:{runCount:0,totalBytes:0},after:{runCount:0,totalBytes:0},errors:[]};
  let entries=[];
  try{entries=await fs.readdir(diagnosticRoot,{withFileTypes:true});}
  catch(error){if(error?.code!=='ENOENT')result.errors.push(safeError('LIST_RUNS',error,{path:diagnosticRoot}));await cleanTranscripts({transcriptRoot,nowMs:Number(nowFn()),maxAgeMs:transcriptMaxAgeMs,rmFn,result});result.ok=result.errors.length===0;return result;}

  const runs=[];
  for(const entry of entries){
    if(!entry.isDirectory())continue;
    try{const inspected=await inspectRun(path.join(diagnosticRoot,entry.name),entry.name);if(inspected)runs.push(inspected);}
    catch(error){result.errors.push(safeError('INSPECT_RUN',error,{runId:entry.name,path:path.join(diagnosticRoot,entry.name)}));}
  }
  result.before={runCount:runs.length,totalBytes:runs.reduce((sum,run)=>sum+run.sizeBytes,0)};

  const nowMs=Number(nowFn());const remaining=[];
  for(const run of runs){
    if(protectedIds.has(run.runId)){remaining.push(run);result.protectedRuns.push(run.runId);continue;}
    const age=Math.max(0,nowMs-run.timestampMs);const maxAge=run.failure?Number(failureMaxAgeMs):Number(successMaxAgeMs);
    if(age>maxAge){const deleted=await removeRun(run,rmFn,result);if(!deleted)remaining.push(run);}else remaining.push(run);
  }

  const active=remaining.filter(run=>!result.deletedRuns.includes(run.runId));
  let totalBytes=active.reduce((sum,run)=>sum+run.sizeBytes,0);
  const eviction=active
    .filter(run=>!protectedIds.has(run.runId))
    .sort((a,b)=>Number(a.failure)-Number(b.failure)||a.timestampMs-b.timestampMs||a.runId.localeCompare(b.runId));
  const survivors=new Set(active.map(run=>run.runId));
  let activeCount=active.length;
  for(const run of eviction){
    if(activeCount<=Number(maxRuns)&&totalBytes<=Number(maxTotalBytes))break;
    if(!survivors.has(run.runId))continue;
    const deleted=await removeRun(run,rmFn,result);
    if(deleted){survivors.delete(run.runId);activeCount--;totalBytes=Math.max(0,totalBytes-run.sizeBytes);}
  }

  result.keptRuns=active.filter(run=>survivors.has(run.runId)).map(run=>run.runId);
  result.after={runCount:result.keptRuns.length,totalBytes:active.filter(run=>survivors.has(run.runId)).reduce((sum,run)=>sum+run.sizeBytes,0)};
  await cleanTranscripts({transcriptRoot,nowMs,maxAgeMs:Number(transcriptMaxAgeMs),rmFn,result});
  result.ok=result.errors.length===0;return sanitizeForPersistence(result);
}
