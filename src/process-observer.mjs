import path from 'node:path';
import { runProcess } from './process.mjs';
import { redactSensitiveText, sanitizeForPersistence } from './utils.mjs';

function safeArgs(args=[]){return (Array.isArray(args)?args:[]).map(value=>redactSensitiveText(String(value)));}
function tail(value='',max=1600){const text=redactSensitiveText(String(value||''));return text.length>max?text.slice(-max):text;}

export function createObservedProcessRunner({logger=null,baseRunner=runProcess,nowFn=Date.now}={}){
  return async(command,args=[],options={})=>{
    const startedAt=Number(nowFn());const commandName=path.basename(String(command||'process'));const safe=safeArgs(args);
    await logger?.log?.('PROCESS','Subprocess starting',{command:commandName,args:safe,cwd:options?.cwd||null,timeoutMs:Number(options?.timeoutMs||0)},{event:'SUBPROCESS_START'});
    try{
      const result=await baseRunner(command,args,options);const durationMs=Math.max(0,Number(nowFn())-startedAt);const failed=Number(result?.code)!==0;
      const data=sanitizeForPersistence({command:commandName,pid:result?.pid??null,exitCode:result?.code??null,signal:result?.signal??null,durationMs,stdoutTruncated:Boolean(result?.stdoutTruncated),stderrTruncated:Boolean(result?.stderrTruncated),stdoutTail:failed?tail(result?.stdout):null,stderrTail:failed?tail(result?.stderr):null});
      if(failed)await logger?.warn?.('PROCESS','Subprocess exited with non-zero status',data,{event:'SUBPROCESS_END'});else await logger?.log?.('PROCESS','Subprocess completed',data,{event:'SUBPROCESS_END'});
      return result;
    }catch(error){
      const durationMs=Math.max(0,Number(nowFn())-startedAt);const data=sanitizeForPersistence({command:commandName,durationMs,code:error?.code||null,message:error?.message||String(error),details:error?.details||null});
      await logger?.error?.('PROCESS','Subprocess failed or was interrupted',data,{event:error?.code==='PROCESS_TIMEOUT'?'SUBPROCESS_TIMEOUT':error?.code==='PROCESS_ABORTED'?'SUBPROCESS_ABORTED':'SUBPROCESS_ERROR'});throw error;
    }
  };
}
