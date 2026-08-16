import fs from 'node:fs/promises';
import path from 'node:path';
import { redactSensitiveText, sanitizeForPersistence, safePersistUrl } from './utils.mjs';

function stamp(){return new Date().toISOString().replace(/[:.]/g,'-');}
function safeHtml(text,maxBytes){let s=redactSensitiveText(String(text||''));s=s.replace(/(Authorization\s*[:=]\s*(?:Bearer\s+)?)[^\s<"']+/gi,'$1<redacted>').replace(/(Cookie\s*[:=]\s*)[^\n<]+/gi,'$1<redacted>').replace(/((?:token|apiKey|api_key|credential)\s*[=:]\s*)[^&\s<"']+/gi,'$1<redacted>');const b=Buffer.from(s);return b.length<=maxBytes?s:b.subarray(0,maxBytes).toString('utf8')+'\n<!-- truncated -->';}
export class DebugSnapshotManager {
  constructor({debugRoot,maxSnapshots=10,maxHtmlBytes=2*1024*1024,maxAgeMs=7*24*60*60*1000,maxTotalBytes=50*1024*1024,logger=null}={}){this.debugRoot=debugRoot;this.maxSnapshots=Math.max(1,maxSnapshots);this.maxHtmlBytes=maxHtmlBytes;this.maxAgeMs=Math.max(0,Number(maxAgeMs)||0);this.maxTotalBytes=Math.max(1,Number(maxTotalBytes)||1);this.logger=logger;}
  async rotate(){try{
    const names=(await fs.readdir(this.debugRoot,{withFileTypes:true})).filter(e=>e.isDirectory()).map(e=>e.name);const now=Date.now();const entries=[];
    const sizeOf=async dir=>{let total=0;for(const e of await fs.readdir(dir,{withFileTypes:true}).catch(()=>[])){const p=path.join(dir,e.name);if(e.isDirectory())total+=await sizeOf(p);else total+=(await fs.stat(p).catch(()=>({size:0}))).size;}return total;};
    for(const name of names){const dir=path.join(this.debugRoot,name),st=await fs.stat(dir).catch(()=>null);if(!st)continue;if(this.maxAgeMs&&now-st.mtimeMs>this.maxAgeMs){await fs.rm(dir,{recursive:true,force:true});continue;}entries.push({name,dir,mtime:st.mtimeMs,size:await sizeOf(dir)});}
    entries.sort((a,b)=>a.mtime-b.mtime);let total=entries.reduce((n,e)=>n+e.size,0);
    while(entries.length>this.maxSnapshots||total>this.maxTotalBytes){const old=entries.shift();if(!old)break;total-=old.size;await fs.rm(old.dir,{recursive:true,force:true});}
  }catch{}}
  async capture({position=null,pageRef=null,error=null,metadata=null,networkEvents=[]}={}){
    try{
      if(!this.debugRoot)throw new Error('debugRoot unavailable');await fs.mkdir(this.debugRoot,{recursive:true});const dir=path.join(this.debugRoot,`${String(position??'unknown').padStart(3,'0')}-${stamp()}`);await fs.mkdir(dir,{recursive:true});
      let html='';try{html=await pageRef?.handle?.content?.()||'';}catch{}
      await fs.writeFile(path.join(dir,'page.html'),safeHtml(html,this.maxHtmlBytes),'utf8');
      await fs.writeFile(path.join(dir,'metadata.json'),`${JSON.stringify(sanitizeForPersistence({...metadata,position,pageUrl:safePersistUrl(pageRef?.url)}),null,2)}\n`,'utf8');
      await fs.writeFile(path.join(dir,'network.jsonl'),(networkEvents||[]).map(x=>JSON.stringify(sanitizeForPersistence(x))).join('\n')+((networkEvents||[]).length?'\n':''),'utf8');
      await fs.writeFile(path.join(dir,'error.json'),`${JSON.stringify(sanitizeForPersistence({name:error?.name||null,code:error?.code||null,message:String(error?.message||error||'')}),null,2)}\n`,'utf8');
      try{const png=await pageRef?.handle?.screenshot?.({type:'png'});if(png)await fs.writeFile(path.join(dir,'screenshot.png'),png);}catch{}
      await this.rotate();return{ok:true,dir};
    }catch(captureError){await this.logger?.log?.('DEBUG','Snapshot capture failed',{error:String(captureError?.message||captureError)});return{ok:false,error:String(captureError?.message||captureError)};}
  }
}
