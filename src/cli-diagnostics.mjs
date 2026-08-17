import path from 'node:path';
import { RunnerLogger } from './logger.mjs';
import { IntegratedRunDiagnostics, installFatalDiagnosticHandlers } from './integrated-diagnostics.mjs';
import { sanitizeSegment } from './utils.mjs';

function courseRootFromResult(result,outputRoot){
  if(result?.courseRoot)return path.resolve(result.courseRoot);
  const course=result?.course||result?.state?.courseName||null;
  return course?path.join(path.resolve(outputRoot),sanitizeSegment(course,'Curso XCursos',90)):null;
}

export async function startCliDiagnostics({outputRoot,command,argv=[],processRef=process,env=process.env,sink=null,diagnosticsFactory=null,logger=null,exitFn=null}={}){
  const sharedLogger=logger||new RunnerLogger({sink});
  const diagnostics=diagnosticsFactory?await diagnosticsFactory({outputRoot,command,argv,processRef,env,logger:sharedLogger}):new IntegratedRunDiagnostics({outputRoot,command,argv,processRef,env});
  await diagnostics.start({logger:sharedLogger,context:{command}});
  const uninstallFatal=installFatalDiagnosticHandlers({diagnostics,processRef,exitFn});
  return{logger:sharedLogger,diagnostics,uninstallFatal};
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
