import path from 'node:path';
import { RunnerLogger } from './logger.mjs';
import { IntegratedRunDiagnostics, installFatalDiagnosticHandlers } from './integrated-diagnostics.mjs';
import { recoverInterruptedDiagnosticRuns } from './diagnostic-recovery.mjs';
import { sanitizeForPersistence, sanitizeSegment } from './utils.mjs';

const SAFE_RUNTIME_KEYS=['resume','cdpEndpoint','cdpPort','outputRoot','profileDir','chromePath'];
const SAFE_LIMIT_KEYS=[
  'browserLaunchTimeoutMs','navigationTimeoutMs','inspectTimeoutMs','inspectionCacheTtlMs','transitionTimeoutMs','transitionPollMs',
  'actionabilityTrialTimeoutMs','nextPostActionObservationMs','nextRecoveryObservationMs','mediaReadyTimeoutMs','mediaReadyPollMs',
  'nativeDownloadEventTimeoutMs','navigationRetries','mediaRefreshRetries','downloadRetries','retryBaseDelayMs','retryMaxDelayMs','retryJitterRatio',
  'throttleMinDelayMs','throttleMaxDelayMs','downloadTimeoutMs','ffprobeTimeoutMs','minVideoBytes','minDurationSeconds','maxFullPath',
  'processTailBytes','nativeBrowserLockWaitMs','nativeBrowserLockPollMs','nativeBrowserLockStaleMs','repositionMaxWalkSteps',
];

function pick(source,keys){const out={};for(const key of keys)if(source&&source[key]!==undefined)out[key]=source[key];return out;}

export function buildEffectiveDiagnosticConfig({runtime={},limits={}}={}){
  return sanitizeForPersistence({schemaVersion:1,runtime:pick(runtime,SAFE_RUNTIME_KEYS),limits:pick(limits,SAFE_LIMIT_KEYS)});
}

function courseRootFromResult(result,outputRoot){
  if(result?.courseRoot)return path.resolve(result.courseRoot);
  const course=result?.course||result?.state?.courseName||null;
  return course?path.join(path.resolve(outputRoot),sanitizeSegment(course,'Curso XCursos',90)):null;
}
function bootstrapRoot(env=process.env,processRef=process){
  if(env?.LOCALAPPDATA)return path.join(env.LOCALAPPDATA,'XCursosRunner');
  if(env?.XDG_STATE_HOME)return path.join(env.XDG_STATE_HOME,'xcursos-runner');
  return path.join(typeof processRef?.cwd==='function'?processRef.cwd():process.cwd(),'.xcursos-runner-bootstrap');
}

export async function startCliDiagnostics({outputRoot,command,argv=[],processRef=process,env=process.env,sink=null,diagnosticsFactory=null,logger=null,exitFn=null,recoveryFn=recoverInterruptedDiagnosticRuns}={}){
  let recovery=null;
  try{recovery=await recoveryFn({outputRoot,hostname:env?.COMPUTERNAME||env?.HOSTNAME||undefined});}catch{}
  const sharedLogger=logger||new RunnerLogger({sink});
  const diagnostics=diagnosticsFactory?await diagnosticsFactory({outputRoot,command,argv,processRef,env,logger:sharedLogger}):new IntegratedRunDiagnostics({outputRoot,command,argv,processRef,env});
  await diagnostics.start({logger:sharedLogger,context:{command}});
  if(recovery?.recovered?.length)await diagnostics.phase('DIAGNOSTIC_RECOVERY','PASS',{recoveredRuns:recovery.recovered.map(x=>x.runId)});
  const uninstallFatal=installFatalDiagnosticHandlers({diagnostics,processRef,exitFn});
  return{logger:sharedLogger,diagnostics,uninstallFatal,recovery};
}

export function attachResultArtifacts(diagnostics,result,outputRoot){
  const courseRoot=courseRootFromResult(result,outputRoot);if(!courseRoot)return diagnostics;
  const metaDir=path.join(courseRoot,'_xcursos-runner');
  diagnostics.attachCourseArtifacts({courseName:result?.course||result?.state?.courseName||null,metaDir,statePath:path.join(metaDir,'state.json'),manifestPath:path.join(metaDir,'manifest.jsonl'),errorsPath:path.join(metaDir,'errors.jsonl'),logPath:path.join(metaDir,'runner.log'),schedulerPath:path.join(metaDir,'scheduler.checkpoint.json'),navigationPath:path.join(metaDir,'lesson-navigation-index.json'),debugRoot:path.join(metaDir,'debug')});
  diagnostics.setContext({courseRoot});return diagnostics;
}

export async function finalizeCliDiagnostics({diagnostics,result=null,error=null,exitCode=null,outputRoot=null}={}){
  if(result&&outputRoot)attachResultArtifacts(diagnostics,result,outputRoot);
  const status=error?'ERROR':(result?.status||'COMPLETE');const ok=error?false:(result?.ok??true);const code=exitCode==null?(ok===false?2:0):exitCode;
  try{return await diagnostics.finalize({status,ok,result,error,exitCode:code});}
  catch(finalizeError){await diagnostics.emergency?.(finalizeError,'CLI_REPORT_FAILED');return null;}
}

export async function writeBootstrapFailureReport(error,{argv=[],processRef=process,env=process.env}={}){
  const diagnostics=new IntegratedRunDiagnostics({outputRoot:bootstrapRoot(env,processRef),command:'bootstrap',argv,processRef,env});
  try{await diagnostics.start({logger:new RunnerLogger(),context:{phase:'CLI_BOOTSTRAP'}});await diagnostics.finalize({status:'BOOTSTRAP_ERROR',ok:false,error,exitCode:2,reason:'Failure before normal diagnostic lifecycle'});}
  catch(reportError){await diagnostics.emergency?.(reportError,'BOOTSTRAP_REPORT_FAILED');}
  return diagnostics.reference();
}
