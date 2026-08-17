import fs from 'node:fs/promises';
import { RunDiagnostics } from './run-diagnostics.mjs';
import { atomicWriteJson, redactSensitiveText, sanitizeForPersistence, safeError } from './utils.mjs';

async function readJsonl(filePath){
  if(!filePath)return[];
  try{return (await fs.readFile(filePath,'utf8')).split(/\r?\n/).filter(Boolean).map(line=>JSON.parse(line));}catch{return[];}
}
function since(records,startedAtMs){return records.filter(record=>{const n=Date.parse(record?.timestamp||'');return Number.isFinite(n)&&n>=startedAtMs;});}
function countBy(records,keyFn){const out={};for(const record of records){const key=String(keyFn(record)||'UNKNOWN');out[key]=(out[key]||0)+1;}return out;}
function workItem(record){
  const v=record?.validation||null;
  return sanitizeForPersistence({position:record?.position??null,status:record?.status||null,attempts:Number(record?.attempts||0),lessonTitle:record?.lessonTitle||null,moduleName:record?.moduleName||null,modulePath:record?.modulePath||[],outputFile:record?.outputFile||null,timestamp:record?.timestamp||null,validation:v?{duration:v.duration??null,codec:v.codec??null,size:v.size??null,downloadMethod:v.downloadMethod??null}:null});
}
function persistedError(record){return sanitizeForPersistence({timestamp:record?.timestamp||null,scope:record?.scope||null,position:record?.position??null,status:record?.status||null,code:record?.code||record?.failureCode||null,message:record?.message||null,attempt:record?.attempt??null,maxAttempts:record?.maxAttempts??null,delayMs:record?.delayMs??null});}
function reasonError(reason,code){if(reason instanceof Error){if(!reason.code)reason.code=code;return reason;}const error=new Error(redactSensitiveText(String(reason??code)));error.code=code;return error;}
function md(value=''){return String(value??'').replace(/\|/g,'\\|').replace(/\r?\n/g,' ');}

export class IntegratedRunDiagnostics extends RunDiagnostics {
  constructor(options={}){super(options);this.integratedFinalized=false;}

  async persistenceSummary(){
    const manifest=since(await readJsonl(this.artifacts.get('manifest')?.path),this.startedAtMs).map(workItem);
    const errors=since(await readJsonl(this.artifacts.get('errors')?.path),this.startedAtMs).map(persistedError);
    return sanitizeForPersistence({currentRunWorkItems:manifest,currentRunWorkItemCount:manifest.length,currentRunWorkItemsByStatus:countBy(manifest,x=>x.status),persistedErrors:errors,persistedErrorCount:errors.length,persistedErrorsByScope:countBy(errors,x=>x.scope),persistedErrorsByCode:countBy(errors,x=>x.code||x.status)});
  }

  async finalize(options={}){
    if(this.integratedFinalized)return await this.readReport();
    const base=await super.finalize(options);if(!base)return base;
    const persistence=await this.persistenceSummary();const report=sanitizeForPersistence({...base,summary:{...base.summary,...persistence}});
    await atomicWriteJson(this.reportJsonPath,report);
    await fs.writeFile(this.reportMarkdownPath,this.renderIntegratedMarkdown(report),'utf8');
    this.integratedFinalized=true;return report;
  }

  renderIntegratedMarkdown(report){
    let text=super.renderMarkdown(report);const items=report.summary?.currentRunWorkItems||[];const errors=report.summary?.persistedErrors||[];
    const extra=['','## Reconstrução desta execução','',`- Unidades/posições concluídas nesta execução: ${items.length}`,`- Erros persistidos nesta execução: ${errors.length}`];
    if(items.length){extra.push('','### Unidades processadas','', '| Posição | Status | Tentativas | Aula | Módulo |','|---|---|---|---|---|',...items.map(x=>`| ${md(x.position)} | ${md(x.status)} | ${md(x.attempts)} | ${md(x.lessonTitle||'')} | ${md(x.moduleName||'')} |`));}
    if(errors.length){extra.push('','### Erros persistidos do fluxo','', '| Hora | Escopo | Posição | Código/Status | Mensagem |','|---|---|---|---|---|',...errors.map(x=>`| ${md(x.timestamp)} | ${md(x.scope)} | ${md(x.position??'')} | ${md(x.code||x.status||'')} | ${md(x.message||'')} |`));}
    return `${text.trimEnd()}\n${extra.join('\n')}\n`;
  }

  async emergency(error,status='DIAGNOSTIC_FINALIZE_FAILED'){
    try{await fs.mkdir(this.runDir,{recursive:true});const payload=sanitizeForPersistence({schemaVersion:1,runId:this.runId,command:this.command,startedAt:this.startedAt,timestamp:new Date().toISOString(),status,error:{...safeError(error),stack:redactSensitiveText(String(error?.stack||''))},context:this.context});await fs.writeFile(`${this.runDir}/emergency-crash.json`,`${JSON.stringify(payload,null,2)}\n`,'utf8');return payload;}catch{return null;}
  }
}

export function installFatalDiagnosticHandlers({diagnostics,processRef=process,exitFn=null}={}){
  if(!diagnostics||!processRef?.on)return()=>{};
  let handling=false;const exit=exitFn||((code)=>processRef.exit?.(code));
  const handle=async(kind,reason)=>{if(handling)return;handling=true;const error=reasonError(reason,kind);try{await diagnostics.finalize({status:kind,ok:false,exitCode:1,error,reason:kind});}catch(finalizeError){await diagnostics.emergency?.(finalizeError,`${kind}_REPORT_FAILED`);}exit?.(1);};
  const uncaught=error=>{void handle('UNCAUGHT_EXCEPTION',error);};const rejection=reason=>{void handle('UNHANDLED_REJECTION',reason);};
  processRef.on('uncaughtException',uncaught);processRef.on('unhandledRejection',rejection);
  return()=>{processRef.off?.('uncaughtException',uncaught);processRef.off?.('unhandledRejection',rejection);};
}
