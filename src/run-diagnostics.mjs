import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import { atomicWriteJson, redactSensitiveText, sanitizeForPersistence, safeError } from './utils.mjs';

function iso(nowFn){return new Date(Number(nowFn())).toISOString();}
function runStamp(date=new Date()){return date.toISOString().replace(/[-:.]/g,'').replace('Z','Z');}
function md(value=''){return String(value??'').replace(/\|/g,'\\|').replace(/\r?\n/g,' ');}
function code(value=''){return `\`${String(value??'').replace(/`/g,"'")}\``;}
async function exists(filePath){try{const stat=await fs.stat(filePath);return{exists:true,isDirectory:stat.isDirectory(),size:stat.isFile()?stat.size:null,mtime:stat.mtime.toISOString()};}catch{return{exists:false,isDirectory:false,size:null,mtime:null};}}
async function readJsonlSafe(filePath){try{return (await fs.readFile(filePath,'utf8')).split(/\r?\n/).filter(Boolean).map(line=>JSON.parse(line));}catch{return[];}}
function countBy(items,keyFn){const out={};for(const item of items){const key=String(keyFn(item)||'UNKNOWN');out[key]=(out[key]||0)+1;}return out;}
function safeArg(arg){return redactSensitiveText(String(arg));}

export class RunDiagnostics {
  constructor({outputRoot,command='unknown',argv=[],runId=null,nowFn=Date.now,processRef=process,env=process.env}={}){
    this.outputRoot=path.resolve(outputRoot||process.cwd());this.command=String(command||'unknown');this.argv=(Array.isArray(argv)?argv:[]).map(safeArg);this.nowFn=nowFn;this.processRef=processRef;this.env=env||{};
    this.runId=runId||`${runStamp(new Date(Number(nowFn())))}-${crypto.randomUUID().slice(0,8)}`;
    this.rootDir=path.join(this.outputRoot,'_xcursos-diagnostics');this.runDir=path.join(this.rootDir,this.runId);this.eventPath=path.join(this.runDir,'events.jsonl');this.reportJsonPath=path.join(this.runDir,'diagnostic-report.json');this.reportMarkdownPath=path.join(this.runDir,'diagnostic-report.md');this.metaPath=path.join(this.runDir,'run-meta.json');
    this.startedAtMs=Number(nowFn());this.startedAt=new Date(this.startedAtMs).toISOString();this.context={};this.phases=[];this.anomalies=[];this.errors=[];this.artifacts=new Map();this.logger=null;this.started=false;this.finalized=false;
  }

  async start({logger=null,context=null}={}){
    await fs.mkdir(this.runDir,{recursive:true});this.started=true;this.logger=logger||this.logger;
    if(context)this.setContext(context);
    this.logger?.configure?.({eventFile:this.eventPath,runId:this.runId,context:{command:this.command,...this.context}});
    const meta=this.baseMetadata();await atomicWriteJson(this.metaPath,meta);
    await this.logger?.log?.('DIAGNOSTIC','Run diagnostics started',{runId:this.runId,runDir:this.runDir},{event:'RUN_STARTED'});
    return meta;
  }

  baseMetadata(){
    const p=this.processRef||process;
    return sanitizeForPersistence({
      schemaVersion:1,runId:this.runId,command:this.command,argv:this.argv,startedAt:this.startedAt,
      process:{pid:p.pid??null,nodeVersion:p.version??process.version,platform:p.platform??process.platform,arch:p.arch??process.arch,cwd:typeof p.cwd==='function'?p.cwd():process.cwd(),hostname:os.hostname()},
      context:this.context,
    });
  }

  setContext(patch={}){
    this.context=sanitizeForPersistence({...this.context,...patch});
    this.logger?.setContext?.({command:this.command,...this.context});
    return this.context;
  }

  async phase(name,status='INFO',data=null){
    const entry=sanitizeForPersistence({timestamp:iso(this.nowFn),name:String(name),status:String(status),data});this.phases.push(entry);
    await this.logger?.log?.('PHASE',`${entry.name}: ${entry.status}`,entry.data,{event:'PHASE',level:entry.status==='FAIL'?'ERROR':'INFO'});return entry;
  }

  async anomaly(codeValue,{severity='WARN',message=null,data=null}={}){
    const entry=sanitizeForPersistence({timestamp:iso(this.nowFn),code:String(codeValue||'ANOMALY'),severity:String(severity||'WARN').toUpperCase(),message:message?redactSensitiveText(message):null,data});this.anomalies.push(entry);
    const method=entry.severity==='FATAL'?'fatal':entry.severity==='ERROR'?'error':'warn';await this.logger?.[method]?.('ANOMALY',entry.message||entry.code,{code:entry.code,...(entry.data||{})},{event:'ANOMALY'});return entry;
  }

  async captureError(error,{scope='APP',fatal=false,data=null}={}){
    const entry=sanitizeForPersistence({timestamp:iso(this.nowFn),scope,fatal:Boolean(fatal),error:{...safeError(error),stack:redactSensitiveText(String(error?.stack||''))||null},details:error?.details||null,data});this.errors.push(entry);
    const method=fatal?'fatal':'error';await this.logger?.[method]?.(scope,entry.error.message,{code:entry.error.code,details:entry.details,data:entry.data},{event:fatal?'FATAL_ERROR':'ERROR'});return entry;
  }

  addArtifact(name,filePath,{type='file',description=null}={}){
    if(!filePath)return null;const entry={name:String(name),path:path.resolve(String(filePath)),type,description};this.artifacts.set(entry.name,entry);return entry;
  }

  attachCourseArtifacts({courseName=null,metaDir=null,statePath=null,manifestPath=null,errorsPath=null,logPath=null,schedulerPath=null,navigationPath=null,debugRoot=null}={}){
    if(courseName)this.setContext({courseName});
    if(metaDir)this.addArtifact('courseMetadataDir',metaDir,{type:'directory',description:'Diretório persistente de metadados do curso'});
    for(const [name,value,description] of [
      ['state',statePath,'Estado atual/resume'],['manifest',manifestPath,'Resultado terminal por posição'],['errors',errorsPath,'Erros persistidos'],['runnerLog',logPath,'Log humano legado'],['schedulerCheckpoint',schedulerPath,'Checkpoint do scheduler'],['navigationIndex',navigationPath,'Índice de navegação'],['debugSnapshots',debugRoot,'Snapshots HTML/PNG/network de falhas estruturais'],
    ])if(value)this.addArtifact(name,value,{type:name==='debugSnapshots'?'directory':'file',description});
    return this;
  }

  async artifactIndex(){
    const entries=[...this.artifacts.values()];
    const transcript=this.env?.XCURSOS_POWERSHELL_TRANSCRIPT;if(transcript&&!this.artifacts.has('powershellTranscript'))entries.push({name:'powershellTranscript',path:path.resolve(String(transcript)),type:'file',description:'Transcrição do wrapper PowerShell'});
    const out=[];for(const entry of entries){out.push(sanitizeForPersistence({...entry,...await exists(entry.path)}));}return out;
  }

  async finalize({status='UNKNOWN',ok=null,result=null,error=null,exitCode=null,reason=null}={}){
    if(this.finalized)return await this.readReport();if(!this.started)await this.start({logger:this.logger});
    if(error)await this.captureError(error,{scope:'FINALIZE',fatal:true});
    const endedAtMs=Number(this.nowFn());const events=await readJsonlSafe(this.eventPath);const artifacts=await this.artifactIndex();
    const eventSummary={count:events.length,byLevel:countBy(events,x=>x.level),byScope:countBy(events,x=>x.scope),byEvent:countBy(events,x=>x.event)};
    const safeResult=sanitizeForPersistence(result);
    const audit=safeResult?.audit||safeResult?.result?.audit||null;const stats=safeResult?.stats||safeResult?.result?.stats||null;
    const report=sanitizeForPersistence({
      schemaVersion:1,runId:this.runId,command:this.command,argv:this.argv,startedAt:this.startedAt,endedAt:new Date(endedAtMs).toISOString(),durationMs:Math.max(0,endedAtMs-this.startedAtMs),
      outcome:{status:String(status||'UNKNOWN'),ok:ok==null?null:Boolean(ok),exitCode:exitCode==null?null:Number(exitCode),reason:reason||null},
      environment:this.baseMetadata().process,context:this.context,
      summary:{audit,stats,resultStatus:safeResult?.status||null,failureSummary:safeResult?.failureSummary||null},
      phases:this.phases,anomalies:this.anomalies,errors:this.errors,eventSummary,artifacts,
      files:{events:this.eventPath,metadata:this.metaPath,reportJson:this.reportJsonPath,reportMarkdown:this.reportMarkdownPath},
    });
    await atomicWriteJson(this.reportJsonPath,report);await fs.writeFile(this.reportMarkdownPath,this.renderMarkdown(report),'utf8');this.finalized=true;
    await this.logger?.log?.('DIAGNOSTIC','Run diagnostics finalized',{status:report.outcome.status,report:this.reportMarkdownPath},{event:'RUN_FINALIZED'}).catch(()=>{});
    return report;
  }

  async readReport(){try{return JSON.parse(await fs.readFile(this.reportJsonPath,'utf8'));}catch{return null;}}

  renderMarkdown(report){
    const audit=report.summary?.audit||{};const lines=[
      '# XCursos Runner — Relatório de Diagnóstico','',
      `- **Run ID:** ${code(report.runId)}`,
      `- **Comando:** ${code(report.command)}`,
      `- **Início:** ${report.startedAt}`,
      `- **Fim:** ${report.endedAt}`,
      `- **Duração:** ${report.durationMs} ms`,
      `- **Resultado:** **${md(report.outcome?.status)}**${report.outcome?.ok==null?'':` — ok=${report.outcome.ok}`}${report.outcome?.exitCode==null?'':` — exit=${report.outcome.exitCode}`}`,
      '', '## Resumo da execução','',
    ];
    if(audit&&Object.keys(audit).length){lines.push(`- Processados: ${audit.processed??'n/d'} / ${audit.total??'n/d'}`,`- Downloads: ${audit.downloaded??'n/d'} | Já presentes: ${audit.alreadyPresent??'n/d'} | Sem vídeo: ${audit.noVideo??'n/d'}`,`- Posições pendentes: ${Array.isArray(audit.missingPositions)?audit.missingPositions.join(', ')||'nenhuma':'n/d'}`,`- Arquivos inválidos: ${Array.isArray(audit.invalidFilePositions)?audit.invalidFilePositions.join(', ')||'nenhum':'n/d'}`);}else lines.push('- Auditoria final não disponível para esta execução.');
    lines.push('', '## Eventos e anomalias','',`- Eventos estruturados: ${report.eventSummary?.count??0}`,`- Anomalias registradas: ${report.anomalies?.length??0}`,`- Erros registrados: ${report.errors?.length??0}`);
    if(report.anomalies?.length){lines.push('','### Anomalias','', '| Hora | Severidade | Código | Descrição |','|---|---|---|---|',...report.anomalies.map(x=>`| ${md(x.timestamp)} | ${md(x.severity)} | ${md(x.code)} | ${md(x.message||'')} |`));}
    if(report.errors?.length){lines.push('','### Erros','', '| Hora | Escopo | Fatal | Código | Mensagem |','|---|---|---|---|---|',...report.errors.map(x=>`| ${md(x.timestamp)} | ${md(x.scope)} | ${x.fatal?'sim':'não'} | ${md(x.error?.code||'')} | ${md(x.error?.message||'')} |`));}
    lines.push('','## Artefatos para investigação','', '| Artefato | Existe | Caminho | Descrição |','|---|---|---|---|',...report.artifacts.map(x=>`| ${md(x.name)} | ${x.exists?'sim':'não'} | ${code(x.path)} | ${md(x.description||'')} |`));
    lines.push('','## Como investigar','',`O arquivo principal para compartilhar é ${code(this.reportJsonPath)}. Para investigação detalhada, envie também ${code(this.reportMarkdownPath)} e, quando necessário, os artefatos listados acima. O relatório e os eventos usam a sanitização do XCursos Runner para remover tokens, cookies e URLs assinadas.`,'');
    return `${lines.join('\n')}\n`;
  }
}
