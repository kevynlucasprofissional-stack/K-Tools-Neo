import fs from 'node:fs/promises';
import path from 'node:path';
import { atomicWriteJsonDurable, sanitizeForPersistence } from './utils.mjs';

function validTask(t){return t&&Number.isInteger(Number(t.position))&&Number(t.position)>0;}
function validateCheckpoint(v){
  if(!v||typeof v!=='object'||Array.isArray(v)||Number(v.schedulerVersion)!==1)throw new Error('Invalid scheduler checkpoint version');
  for(const key of ['ready','retryLater','inFlight','blocked'])if(!Array.isArray(v[key])||v[key].some(x=>!validTask(x)))throw new Error(`Invalid scheduler checkpoint bucket: ${key}`);
  return v;
}
export class DurableSchedulerCheckpoint {
  constructor({filePath,logger=null}={}){if(!filePath)throw new Error('filePath is required');this.filePath=filePath;this.logger=logger;}
  async save(snapshot){validateCheckpoint(snapshot);const safe=sanitizeForPersistence(snapshot);await atomicWriteJsonDurable(this.filePath,safe);return safe;}
  async load(){
    let raw;try{raw=await fs.readFile(this.filePath,'utf8');}catch(error){if(error?.code==='ENOENT')return null;throw error;}
    try{return validateCheckpoint(JSON.parse(raw));}
    catch(error){const quarantine=`${this.filePath}.corrupt-${Date.now()}`;try{await fs.rename(this.filePath,quarantine);}catch{}await this.logger?.log?.('STATE','Scheduler checkpoint quarantined',{file:path.basename(quarantine),reason:String(error?.message||error)});return null;}
  }
  async clear(){await fs.rm(this.filePath,{force:true});}
}
