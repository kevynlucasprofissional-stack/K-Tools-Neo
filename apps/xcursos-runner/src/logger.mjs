import fs from 'node:fs/promises';
import path from 'node:path';
import { redactSensitiveText, sanitizeForPersistence } from './utils.mjs';

function safePart(value) {
  if (typeof value !== 'string') return value;
  return redactSensitiveText(value);
}

function normalizeLevel(level='INFO'){
  const value=String(level||'INFO').toUpperCase();
  return ['DEBUG','INFO','WARN','ERROR','FATAL'].includes(value)?value:'INFO';
}

function diagnosticFailure({timestamp,target,filePath,error}){
  return sanitizeForPersistence({
    timestamp,target,filePath:filePath?path.resolve(String(filePath)):null,
    code:error?.code||'DIAGNOSTIC_IO_ERROR',message:String(error?.message||error||'Diagnostic I/O failure'),
  });
}

export class RunnerLogger {
  constructor({ logFile = null, eventFile = null, sink = null, runId = null, context = null, nowFn = Date.now, diagnosticFailureSink = null, eventObserver = null, maxDiagnosticFailures = 20 } = {}) {
    this.logFile=logFile;this.eventFile=eventFile;this.sink=sink;this.runId=runId||null;this.context=sanitizeForPersistence(context||{});this.nowFn=nowFn;this.sequence=0;
    this.diagnosticFailureSink=diagnosticFailureSink;this.eventObserver=eventObserver;this.maxDiagnosticFailures=Math.max(1,Number(maxDiagnosticFailures)||20);this.diagnosticFailures=[];
  }

  configure({logFile,eventFile,runId,context,diagnosticFailureSink,eventObserver}={}){
    if(logFile!==undefined)this.logFile=logFile;
    if(eventFile!==undefined)this.eventFile=eventFile;
    if(runId!==undefined)this.runId=runId||null;
    if(context!==undefined)this.context=sanitizeForPersistence(context||{});
    if(diagnosticFailureSink!==undefined)this.diagnosticFailureSink=diagnosticFailureSink;
    if(eventObserver!==undefined)this.eventObserver=eventObserver;
    return this;
  }

  setContext(patch={}){
    this.context=sanitizeForPersistence({...this.context,...patch});
    return this.context;
  }

  recordDiagnosticFailure(target,error,filePath=null){
    const entry=diagnosticFailure({timestamp:new Date(Number(this.nowFn())).toISOString(),target,filePath,error});
    this.diagnosticFailures.push(entry);if(this.diagnosticFailures.length>this.maxDiagnosticFailures)this.diagnosticFailures.shift();
    try{this.diagnosticFailureSink?.(entry);}catch{}
    return entry;
  }

  diagnosticHealth(){
    return sanitizeForPersistence({degraded:this.diagnosticFailures.length>0,failures:[...this.diagnosticFailures]});
  }

  async appendDiagnosticFile(target,filePath,text){
    if(!filePath)return true;
    try{
      await fs.mkdir(path.dirname(filePath),{recursive:true});
      await fs.appendFile(filePath,text,'utf8');
      return true;
    }catch(error){
      this.recordDiagnosticFailure(target,error,filePath);return false;
    }
  }

  async log(scope, message, data = null, meta = null) {
    const timestamp=new Date(Number(this.nowFn())).toISOString();
    const safeData=data==null?null:sanitizeForPersistence(data);
    const safeMessage=safePart(String(message??''));
    const level=normalizeLevel(meta?.level);
    const suffix = safeData ? ` ${JSON.stringify(safeData)}` : '';
    const line = `[${timestamp}][${scope}] ${safeMessage}${suffix}`;
    if (this.sink) {try{this.sink(line);}catch(error){this.recordDiagnosticFailure('SINK',error,null);}}
    if (this.logFile) await this.appendDiagnosticFile('HUMAN_LOG',this.logFile,`${line}\n`);
    const shouldBuildEvent=Boolean(this.eventFile||this.eventObserver);
    if(shouldBuildEvent){
      const event=sanitizeForPersistence({
        timestamp,runId:this.runId,sequence:++this.sequence,level,scope:String(scope||'APP'),event:meta?.event||'LOG',message:safeMessage,
        context:this.context&&Object.keys(this.context).length?this.context:null,data:safeData,
      });
      if(this.eventFile)await this.appendDiagnosticFile('EVENT_LOG',this.eventFile,`${JSON.stringify(event)}\n`);
      if(this.eventObserver){try{this.eventObserver(event);}catch(error){this.recordDiagnosticFailure('EVENT_OBSERVER',error,null);}}
    }
    return line;
  }

  async warn(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'WARN'});}
  async error(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'ERROR'});}
  async fatal(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'FATAL'});}
}
