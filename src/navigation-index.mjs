import fs from 'node:fs/promises';
import path from 'node:path';
import { atomicWriteJsonDurable, nowIso, safePersistUrl, sanitizeForPersistence } from './utils.mjs';

function validPosition(value,total){const n=Number(value);return Number.isInteger(n)&&n>=1&&n<=Number(total);}
function fresh(courseName,totalPositions){return{version:2,courseName,totalPositions:Number(totalPositions),updatedAt:nowIso(),courseAnchor:null,positions:{}};}
function normalizedPositions(raw,total){const positions={};for(const [key,value] of Object.entries(raw||{})){const p=Number(key);const url=safePersistUrl(typeof value==='string'?value:value?.url);if(validPosition(p,total)&&url)positions[String(p)]=url;}return positions;}

export class NavigationIndex {
  constructor({filePath,courseName,totalPositions,logger=null}={}){
    if(!filePath)throw new Error('filePath is required');
    this.filePath=filePath;this.courseName=courseName;this.totalPositions=Number(totalPositions)||0;this.logger=logger;this.data=fresh(courseName,this.totalPositions);
  }
  async load(){
    let raw;try{raw=await fs.readFile(this.filePath,'utf8');}catch(error){if(error?.code==='ENOENT')return this.data;throw error;}
    try{
      const parsed=JSON.parse(raw);const version=Number(parsed?.version);
      if(!parsed||![1,2].includes(version)||Number(parsed.totalPositions)!==this.totalPositions||String(parsed.courseName||'')!==String(this.courseName||'')||!parsed.positions||typeof parsed.positions!=='object'||Array.isArray(parsed.positions))throw new Error('invalid navigation index identity/version');
      const positions=normalizedPositions(parsed.positions,this.totalPositions);
      const parsedAnchor=version>=2?parsed.courseAnchor:null;const anchorUrl=safePersistUrl(parsedAnchor?.url)||positions['1']||null;
      const courseAnchor=anchorUrl?{position:1,url:anchorUrl}:null;
      this.data={version:2,courseName:this.courseName,totalPositions:this.totalPositions,updatedAt:parsed.updatedAt||nowIso(),courseAnchor,positions};
      if(version!==2 || JSON.stringify(parsed.courseAnchor||null)!==JSON.stringify(courseAnchor))await this.persist();
      return this.data;
    }catch(error){
      const quarantine=`${this.filePath}.corrupt-${Date.now()}`;try{await fs.rename(this.filePath,quarantine);}catch{}
      await this.logger?.log?.('STATE','Navigation index quarantined',{file:path.basename(quarantine),reason:String(error?.message||error)});
      this.data=fresh(this.courseName,this.totalPositions);return this.data;
    }
  }
  get(position){return this.data.positions[String(Number(position))]||null;}
  anchor(){return this.data.courseAnchor?{...this.data.courseAnchor}:null;}
  entries(){return Object.entries(this.data.positions).map(([p,url])=>[Number(p),url]).sort((a,b)=>a[0]-b[0]);}
  nearestBefore(targetPosition){
    const target=Number(targetPosition);let best=null;
    for(const [position,url] of this.entries())if(position<target&&(!best||position>best.position))best={position,url};
    return best;
  }
  async persist(){this.data.updatedAt=nowIso();await atomicWriteJsonDurable(this.filePath,sanitizeForPersistence(this.data));return this.data;}
  async record(position,url,{persist=true}={}){
    const p=Number(position);const safe=safePersistUrl(url);
    if(!validPosition(p,this.totalPositions)||!safe)return false;
    const key=String(p);let changed=false;
    if(this.data.positions[key]!==safe){this.data.positions[key]=safe;changed=true;}
    if(p===1 && this.data.courseAnchor?.url!==safe){this.data.courseAnchor={position:1,url:safe};changed=true;}
    if(changed&&persist)await this.persist();return changed;
  }
  async recordMany(records=[]){
    let changed=false;
    for(const rec of records){const p=Number(rec?.position);const safe=safePersistUrl(rec?.lessonUrl||rec?.pageUrl);if(validPosition(p,this.totalPositions)&&safe){if(this.data.positions[String(p)]!==safe){this.data.positions[String(p)]=safe;changed=true;}if(p===1&&this.data.courseAnchor?.url!==safe){this.data.courseAnchor={position:1,url:safe};changed=true;}}}
    if(changed)await this.persist();return changed;
  }
  async invalidate(position,{reason=null,observedPosition=null}={}){
    const p=Number(position);if(!validPosition(p,this.totalPositions))return false;const key=String(p);if(!this.data.positions[key])return false;
    const removed=this.data.positions[key];delete this.data.positions[key];
    if(p===1&&this.data.courseAnchor?.url===removed)this.data.courseAnchor=null;
    await this.persist();await this.logger?.log?.('NAV','Invalidated stale navigation index entry',{position:p,reason,observedPosition});return true;
  }
}
