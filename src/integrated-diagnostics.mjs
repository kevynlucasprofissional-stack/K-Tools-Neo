import fs from 'node:fs/promises';
import path from 'node:path';
import { RunDiagnostics } from './run-diagnostics.mjs';
import { redactSensitiveText, sanitizeForPersistence, safeError } from './utils.mjs';

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
function errorCodes(report){return [...(report.summary?.persistedErrors||[]).map(x=>x.code||x.status),...(report.errors||[]).map(x=>x.error?.code)].filter(Boolean).map(String);}
function matches(codes,re){return codes.filter(code=>re.test(code));}
function finding(code,severity,title,evidence,recommendation){return sanitizeForPersistence({code,severity,title,evidence,recommendation});}

export function deriveDiagnosticFindings(report={}){
  const codes=errorCodes(report);const audit=report.summary?.audit||{};const stats=report.summary?.stats||{};const byEvent=report.eventSummary?.byEvent||{};const live=report.liveness||{};const findings=[];
  const network=matches(codes,/(?:NETWORK|ECONN|ETIMEDOUT|EAI_AGAIN|DNS|TLS|HTTP_429|HTTP_5XX|NAV_NETWORK)/i);if(network.length)findings.push(finding('NETWORK_INSTABILITY','WARN','Falhas de rede/conectividade foram observadas',{codes:[...new Set(network)]},'Revisar os eventos e retries imediatamente anteriores, estado da conexão CDP e disponibilidade da rede.'));
  const browser=matches(codes,/(?:PAGE_CLOSED|CDP_|BROWSER_DISCONNECTED|LESSON_REFRESH)/i);if(browser.length)findings.push(finding('BROWSER_SESSION_INSTABILITY','WARN','A sessão do navegador/página exigiu recuperação',{codes:[...new Set(browser)]},'Revisar reconexões CDP, snapshots e mudanças de target/página durante a execução.'));
  const nav=matches(codes,/(?:NEXT_NOT_FOUND|NEXT_ACTIONABILITY_TIMEOUT|POSITION_UNOBSERVABLE|POSITION_OBSERVATION_FAILED)/i);if(nav.length)findings.push(finding('NAVIGATION_CONFIDENCE','WARN','A automação não conseguiu confirmar a navegação com confiança suficiente',{codes:[...new Set(nav)]},'Revisar snapshot da UI, actionability e candidatos de Próxima. Este é o equivalente mais próximo de baixa confiança heurística; o projeto não usa um modelo de IA para decidir a navegação.'));
  const media=matches(codes,/(?:MEDIA_NOT_READY|MEDIA_NOT_FOUND|NATIVE_.*FAILED|YTDLP_FAILED)/i);if(media.length)findings.push(finding('MEDIA_DETECTION_OR_DOWNLOAD','WARN','Houve dificuldade para provar ou obter a mídia da aula',{codes:[...new Set(media)]},'Comparar metadata, network snapshot, botão de download nativo e fallback yt-dlp da posição afetada.'));
  const verify=matches(codes,/(?:VERIFY_|CORRUPT|INVALID_FILE)/i);const invalid=Array.isArray(audit.invalidFilePositions)?audit.invalidFilePositions:[];if(verify.length||invalid.length)findings.push(finding('FILE_INTEGRITY','ERROR','Validação ou integridade de arquivo requer atenção',{codes:[...new Set(verify)],positions:invalid},'Revisar ffprobe, quarentena, tamanho/duração/codec e staging da posição afetada.'));
  const missing=Array.isArray(audit.missingPositions)?audit.missingPositions:[];if(missing.length)findings.push(finding('COVERAGE_GAP','ERROR','A auditoria encontrou posições sem resultado terminal',{positions:missing},'Revisar scheduler/checkpoint e o último erro de cada posição ausente.'));
  const processEvents=Number(byEvent.SUBPROCESS_TIMEOUT||0)+Number(byEvent.SUBPROCESS_ABORTED||0)+Number(byEvent.SUBPROCESS_ERROR||0);if(processEvents>0)findings.push(finding('SUBPROCESS_FAILURE','WARN','Subprocessos externos falharam, expiraram ou foram abortados',{events:processEvents},'Revisar eventos PROCESS para yt-dlp/ffprobe, exit code, duração e stderr sanitizado.'));
  const retries=Number(stats.retries||0);if(retries>0)findings.push(finding('RETRY_PRESSURE','INFO','A execução precisou repetir operações',{retries},'Usar os eventos RETRY para verificar causa, tentativa, delay e se o problema se concentrou em uma posição.'));
  if(live.status==='POSSIBLE_STALL')findings.push(finding('POSSIBLE_STALL','WARN','A execução ficou sem progresso real além do limite esperado',{stage:live.stage,position:live.position,operation:live.operation,msSinceProgress:live.msSinceProgress},'Revisar o último progresso real, operação atual e eventos imediatamente anteriores.'));
  if(live.eventLoopStatus==='DELAYED')findings.push(finding('EVENT_LOOP_DELAY','WARN','O heartbeat observou atraso relevante do event loop',{eventLoopDelayMs:live.eventLoopDelayMs},'Correlacionar com CPU/memória, subprocessos e operação ativa no mesmo período.'));
  const fatal=(report.errors||[]).filter(x=>x.fatal);if(fatal.length)findings.push(finding('FATAL_PROCESS_ERROR','ERROR','A execução terminou por erro não recuperado',{codes:fatal.map(x=>x.error?.code||'UNKNOWN')},'Começar pela stack capturada no relatório e pelos eventos imediatamente anteriores ao erro fatal.'));
  if(audit.healthyComplete===false&&!missing.length&&!invalid.length)findings.push(finding('FINAL_AUDIT_UNHEALTHY','WARN','A cobertura existe, mas a auditoria final não considerou o curso saudável',{failureSummary:report.summary?.failureSummary||null},'Revisar failureSummary, posições bloqueadas e erros persistidos.'));
  return findings;
}

export class IntegratedRunDiagnostics extends RunDiagnostics {
  constructor(options={}){super(options);this.integratedFinalized=false;this.liveness=null;}
  reference(){return sanitizeForPersistence({...super.reference(),liveness:this.liveness?.filePath||null});}

  async persistenceSummary(){
    const manifest=since(await readJsonl(this.artifacts.get('manifest')?.path),this.startedAtMs).map(workItem);
    const errors=since(await readJsonl(this.artifacts.get('errors')?.path),this.startedAtMs).map(persistedError);
    return sanitizeForPersistence({currentRunWorkItems:manifest,currentRunWorkItemCount:manifest.length,currentRunWorkItemsByStatus:countBy(manifest,x=>x.status),persistedErrors:errors,persistedErrorCount:errors.length,persistedErrorsByScope:countBy(errors,x=>x.scope),persistedErrorsByCode:countBy(errors,x=>x.code||x.status)});
  }

  async finalize(options={}){
    if(this.integratedFinalized)return await this.readReport();
    const base=await super.finalize(options);if(!base)return base;
    await this.liveness?.stop?.({persist:true});const live=this.liveness?.snapshot?.()||null;
    const persistence=await this.persistenceSummary();let report=sanitizeForPersistence({...base,liveness:live,summary:{...base.summary,...persistence}});report=sanitizeForPersistence({...report,diagnosticFindings:deriveDiagnosticFindings(report),diagnosticHealth:this.diagnosticHealth()});
    this.finalReport=report;
    await this.persistReport(report,this.renderIntegratedMarkdown(report));
    this.refreshReportStorage(report);this.finalReport=report;this.integratedFinalized=true;return report;
  }

  renderIntegratedMarkdown(report){
    let text=super.renderMarkdown(report);const items=report.summary?.currentRunWorkItems||[];const errors=report.summary?.persistedErrors||[];const findings=report.diagnosticFindings||[];const live=report.liveness||null;
    const extra=['','## Reconstrução desta execução','',`- Unidades/posições concluídas nesta execução: ${items.length}`,`- Erros persistidos nesta execução: ${errors.length}`];
    if(live)extra.push(`- Liveness final: **${md(live.status)}** | etapa=${md(live.stage||'n/d')} | posição=${md(live.position??'n/d')} | sem progresso=${md(live.msSinceProgress??'n/d')} ms | event-loop=${md(live.eventLoopStatus||'n/d')}`);
    if(items.length){extra.push('','### Unidades processadas','', '| Posição | Status | Tentativas | Aula | Módulo |','|---|---|---|---|---|',...items.map(x=>`| ${md(x.position)} | ${md(x.status)} | ${md(x.attempts)} | ${md(x.lessonTitle||'')} | ${md(x.moduleName||'')} |`));}
    if(errors.length){extra.push('','### Erros persistidos do fluxo','', '| Hora | Escopo | Posição | Código/Status | Mensagem |','|---|---|---|---|---|',...errors.map(x=>`| ${md(x.timestamp)} | ${md(x.scope)} | ${md(x.position??'')} | ${md(x.code||x.status||'')} | ${md(x.message||'')} |`));}
    extra.push('','## Possíveis pontos de falha','');
    if(!findings.length)extra.push('Nenhum padrão de falha foi derivado das evidências registradas nesta execução.');
    else for(const item of findings)extra.push(`### ${md(item.code)} — ${md(item.title)}`,'',`- Severidade: **${md(item.severity)}**`,`- Evidência: ${md(JSON.stringify(item.evidence||{}))}`,`- Próxima investigação: ${md(item.recommendation||'')}`,'');
    return `${text.trimEnd()}\n${extra.join('\n')}\n`;
  }

  async emergency(error,status='DIAGNOSTIC_FINALIZE_FAILED'){
    await this.liveness?.stop?.({persist:true});
    const payload=sanitizeForPersistence({schemaVersion:1,runId:this.runId,command:this.command,startedAt:this.startedAt,timestamp:new Date().toISOString(),status,error:{...safeError(error),stack:redactSensitiveText(String(error?.stack||''))},context:this.context,liveness:this.liveness?.snapshot?.()||null,diagnosticHealth:this.diagnosticHealth()});
    const write=async()=>{await fs.mkdir(this.runDir,{recursive:true});await fs.writeFile(path.join(this.runDir,'emergency-crash.json'),`${JSON.stringify(payload,null,2)}\n`,'utf8');};
    try{if(!this.memoryOnly){await write();return payload;}}
    catch(writeError){
      const switched=await this.activateFallback('EMERGENCY_WRITE',writeError,path.join(this.runDir,'emergency-crash.json'));
      if(switched){try{await write();return payload;}catch(fallbackError){this.recordStorageFailure('EMERGENCY_FALLBACK_WRITE',fallbackError,path.join(this.runDir,'emergency-crash.json'));this.memoryOnly=true;this.logger?.configure?.({eventFile:null});}}
    }
    return sanitizeForPersistence({...payload,diagnosticHealth:this.diagnosticHealth()});
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
