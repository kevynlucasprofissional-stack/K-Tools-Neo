import crypto from 'node:crypto';
import { MATERIALS_PATH } from './constants.mjs';
import { redactUrl, sanitizeForPersistence } from './utils.mjs';

const MEDIA_HOST_RE=/(?:^|\.)xcursos-videos\.[^.]+\.r2\.cloudflarestorage\.com$|\.r2\.cloudflarestorage\.com$/i;

export function classifyNetworkMedia(url,{contentType=null}={}){
  if(!url)return null;
  let parsed;try{parsed=new URL(String(url));}catch{return null;}
  if(!/^https?:$/.test(parsed.protocol)||parsed.pathname.includes(MATERIALS_PATH))return null;
  const full=parsed.toString();const ct=String(contentType||'').toLowerCase();let type=null;
  if(/\.mp4(?:$|[?#])/i.test(full)||ct.includes('video/mp4'))type='DIRECT_MP4';
  else if(/\.m3u8(?:$|[?#])/i.test(full)||ct.includes('mpegurl'))type='HLS';
  else if(/\.mpd(?:$|[?#])/i.test(full)||ct.includes('dash+xml'))type='DASH';
  else if(MEDIA_HOST_RE.test(parsed.hostname)&&/\/videos\//i.test(parsed.pathname))type='UNKNOWN';
  if(!type)return null;
  return{url:full,type,host:parsed.hostname};
}

export function mediaObjectKey(url){
  if(!url)return null;
  try{const u=new URL(String(url));if(!/^https?:$/.test(u.protocol))return null;return `${u.hostname.toLowerCase()}${u.pathname}`;}
  catch{return null;}
}

export function mediaObjectFingerprint(url){
  const key=mediaObjectKey(url);return key?crypto.createHash('sha256').update(key).digest('hex').slice(0,12):null;
}

export function correlateMediaObjects(networkUrl,liveUrl){
  const networkKey=mediaObjectKey(networkUrl),liveKey=mediaObjectKey(liveUrl);
  return{
    comparable:Boolean(networkKey&&liveKey),
    sameObject:Boolean(networkKey&&liveKey&&networkKey===liveKey),
    networkObjectFingerprint:mediaObjectFingerprint(networkUrl),
    liveObjectFingerprint:mediaObjectFingerprint(liveUrl),
  };
}

function score(candidate){
  const typeScore={DIRECT_MP4:30,HLS:20,DASH:15,UNKNOWN:5}[candidate.type]||0;
  const statusScore=candidate.status>=200&&candidate.status<300?50:(candidate.status>=300&&candidate.status<400?30:-100);
  const resourceScore=candidate.resourceType==='media'?10:['xhr','fetch'].includes(candidate.resourceType)?5:0;
  return statusScore+typeScore+resourceScore+candidate.seq/1e6;
}

export class NetworkMediaObserver {
  constructor({logger=null,maxEvents=80}={}){this.logger=logger;this.maxEvents=maxEvents;this.events=new WeakMap();this.handlers=new WeakMap();this.generations=new WeakMap();this.sequence=0;}
  attach(page){
    if(!page||this.handlers.has(page))return;
    const list=[];this.events.set(page,list);this.generations.set(page,{id:0,reason:'initial',lessonUrl:null,startedAt:new Date().toISOString()});
    const push=item=>{const generation=this.currentGeneration(page);list.push({...item,generation});while(list.length>this.maxEvents)list.shift();};
    const onResponse=async response=>{
      try{
        const url=response.url?.()||'';let headers={};try{headers=await response.allHeaders?.()||{};}catch{}
        const media=classifyNetworkMedia(url,{contentType:headers['content-type']||headers['Content-Type']});if(!media)return;
        const req=response.request?.();const candidate={...media,status:Number(response.status?.()??0),resourceType:req?.resourceType?.()||null,timestamp:new Date().toISOString(),seq:++this.sequence,source:'network.response'};
        push(candidate);await this.logger?.log('MEDIA',candidate.status>=200&&candidate.status<400?'Network media observed':'Network media error observed',{url:redactUrl(candidate.url),status:candidate.status,type:candidate.type,resourceType:candidate.resourceType,generation:this.currentGeneration(page)});
      }catch{}
    };
    const onFailed=request=>{
      try{const media=classifyNetworkMedia(request.url?.()||'');if(!media)return;push({...media,status:0,resourceType:request.resourceType?.()||null,timestamp:new Date().toISOString(),seq:++this.sequence,source:'network.requestfailed',failure:request.failure?.()?.errorText||'requestfailed'});}catch{}
    };
    page.on?.('response',onResponse);page.on?.('requestfailed',onFailed);this.handlers.set(page,{onResponse,onFailed});
  }
  detach(page){const h=this.handlers.get(page);if(!h)return;page.off?.('response',h.onResponse);page.off?.('requestfailed',h.onFailed);this.handlers.delete(page);this.events.delete(page);this.generations.delete(page);}
  currentGeneration(page){return Number(this.generations.get(page)?.id??0);}
  generationInfo(page){return this.generations.get(page)||{id:0,reason:'unknown',lessonUrl:null,startedAt:null};}
  beginGeneration(page,{reason='navigation',lessonUrl=null}={}){
    if(!page)return 0;if(!this.handlers.has(page))this.attach(page);
    const previous=this.generationInfo(page);const id=Number(previous.id||0)+1;
    this.generations.set(page,{id,reason,lessonUrl:lessonUrl||null,startedAt:new Date().toISOString()});
    return id;
  }
  clear(page){const list=this.events.get(page);if(list)list.length=0;}
  candidates(page,{generation=this.currentGeneration(page),includeAllGenerations=false}={}){const list=[...(this.events.get(page)||[])];return includeAllGenerations?list:list.filter(c=>c.generation===generation);}
  best(page,{generation=this.currentGeneration(page)}={}){return this.candidates(page,{generation}).filter(c=>c.status>=200&&c.status<400).sort((a,b)=>score(b)-score(a))[0]||null;}
  snapshot(page){return this.candidates(page,{includeAllGenerations:true}).map(c=>sanitizeForPersistence({...c,url:redactUrl(c.url)}));}
}
