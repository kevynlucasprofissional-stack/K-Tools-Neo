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

export class RunnerLogger {
  constructor({ logFile = null, eventFile = null, sink = null, runId = null, context = null, nowFn = Date.now } = {}) {
    this.logFile=logFile;this.eventFile=eventFile;this.sink=sink;this.runId=runId||null;this.context=sanitizeForPersistence(context||{});this.nowFn=nowFn;this.sequence=0;
  }

  configure({logFile,eventFile,runId,context}={}){
    if(logFile!==undefined)this.logFile=logFile;
    if(eventFile!==undefined)this.eventFile=eventFile;
    if(runId!==undefined)this.runId=runId||null;
    if(context!==undefined)this.context=sanitizeForPersistence(context||{});
    return this;
  }

  setContext(patch={}){
    this.context=sanitizeForPersistence({...this.context,...patch});
    return this.context;
  }

  async log(scope, message, data = null, meta = null) {
    const timestamp=new Date(Number(this.nowFn())).toISOString();
    const safeData=data==null?null:sanitizeForPersistence(data);
    const safeMessage=safePart(String(message??''));
    const level=normalizeLevel(meta?.level);
    const suffix = safeData ? ` ${JSON.stringify(safeData)}` : '';
    const line = `[${timestamp}][${scope}] ${safeMessage}${suffix}`;
    if (this.sink) this.sink(line);
    if (this.logFile) {
      await fs.mkdir(path.dirname(this.logFile), { recursive: true });
      await fs.appendFile(this.logFile, `${line}\n`, 'utf8');
    }
    if(this.eventFile){
      const event=sanitizeForPersistence({
        timestamp,runId:this.runId,sequence:++this.sequence,level,scope:String(scope||'APP'),event:meta?.event||'LOG',message:safeMessage,
        context:this.context&&Object.keys(this.context).length?this.context:null,data:safeData,
      });
      await fs.mkdir(path.dirname(this.eventFile),{recursive:true});
      await fs.appendFile(this.eventFile,`${JSON.stringify(event)}\n`,'utf8');
    }
    return line;
  }

  async warn(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'WARN'});}
  async error(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'ERROR'});}
  async fatal(scope,message,data=null,meta=null){return await this.log(scope,message,data,{...(meta||{}),level:'FATAL'});}
}
