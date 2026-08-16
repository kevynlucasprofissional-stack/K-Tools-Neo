import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { spawn } from 'node:child_process';
import { BrowserAutomationError } from './errors.mjs';
import { XCURSOS_HOME_URL } from './constants.mjs';
import { sleep } from './utils.mjs';

const LOOPBACK_HOSTS=new Set(['127.0.0.1','localhost','::1','[::1]']);

async function exists(file){try{await fs.access(file);return true;}catch{return false;}}

export function cdpEndpointFromPort(port=9222){
  const n=Number(port);
  if(!Number.isInteger(n)||n<1024||n>65535)throw new BrowserAutomationError(`Porta CDP inválida: ${port}`,{code:'CDP_PORT_INVALID'});
  return `http://127.0.0.1:${n}`;
}

export function assertLocalCdpEndpoint(endpoint){
  let u;try{u=new URL(endpoint);}catch{throw new BrowserAutomationError(`Endpoint CDP inválido: ${endpoint}`,{code:'CDP_ENDPOINT_INVALID'});}
  if(u.protocol!=='http:'||!LOOPBACK_HOSTS.has(u.hostname))throw new BrowserAutomationError('Por segurança, o XCursos Runner só aceita CDP local em 127.0.0.1/localhost.',{code:'CDP_ENDPOINT_NOT_LOCAL',details:{endpoint}});
  return u.toString().replace(/\/$/,'');
}

export async function findChromeExecutable({explicitPath=null,env=process.env,platform=process.platform,extraCandidates=[]}={}){
  const candidates=[];
  if(explicitPath)candidates.push(explicitPath);
  if(env.XCURSOS_CHROME_PATH)candidates.push(env.XCURSOS_CHROME_PATH);
  if(env.CHROME_PATH)candidates.push(env.CHROME_PATH);
  candidates.push(...extraCandidates);
  if(platform==='win32'){
    const pf=env.PROGRAMFILES, pf86=env['PROGRAMFILES(X86)'], local=env.LOCALAPPDATA;
    if(pf)candidates.push(path.join(pf,'Google','Chrome','Application','chrome.exe'));
    if(pf86)candidates.push(path.join(pf86,'Google','Chrome','Application','chrome.exe'));
    if(local)candidates.push(path.join(local,'Google','Chrome','Application','chrome.exe'));
  }else if(platform==='darwin'){
    candidates.push('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome');
    candidates.push(path.join(os.homedir(),'Applications','Google Chrome.app','Contents','MacOS','Google Chrome'));
  }else{
    candidates.push('/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/opt/google/chrome/google-chrome');
  }
  const seen=new Set();
  for(const candidate of candidates){
    if(!candidate||seen.has(candidate))continue;seen.add(candidate);
    if(await exists(candidate))return candidate;
  }
  throw new BrowserAutomationError('Google Chrome Stable não foi encontrado. Instale o Chrome ou configure `xcursos config --chrome "C:\\...\\chrome.exe"` / XCURSOS_CHROME_PATH.',{code:'CHROME_NOT_FOUND'});
}

export async function getCdpStatus(endpoint,{fetchImpl=globalThis.fetch,timeoutMs=2000}={}){
  const base=assertLocalCdpEndpoint(endpoint);
  if(typeof fetchImpl!=='function')return{ok:false,endpoint:base,error:'fetch indisponível'};
  try{
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),timeoutMs);
    let response;
    try{response=await fetchImpl(`${base}/json/version`,{signal:controller.signal,cache:'no-store'});}finally{clearTimeout(timer);}
    if(!response?.ok)return{ok:false,endpoint:base,status:response?.status??null};
    const json=await response.json();
    return{ok:Boolean(json?.webSocketDebuggerUrl),endpoint:base,browser:json?.Browser||null,protocolVersion:json?.['Protocol-Version']||null,webSocketDebuggerUrl:json?.webSocketDebuggerUrl||null};
  }catch(error){return{ok:false,endpoint:base,error:String(error?.message||error)};}
}

export async function waitForCdp(endpoint,{timeoutMs=15_000,pollMs=200,fetchImpl=globalThis.fetch}={}){
  const deadline=Date.now()+timeoutMs;let last=null;
  while(Date.now()<=deadline){last=await getCdpStatus(endpoint,{fetchImpl,timeoutMs:Math.min(2000,Math.max(250,pollMs*4))});if(last.ok)return last;await sleep(pollMs);}
  throw new BrowserAutomationError(`Chrome abriu, mas o endpoint CDP não ficou disponível em ${endpoint}. Feche instâncias antigas do perfil XCursos e tente novamente.`,{code:'CDP_NOT_READY',details:{endpoint,last}});
}

export class HumanChromeLauncher {
  constructor({profileDir,cdpEndpoint='http://127.0.0.1:9222',chromePath=null,logger=null,fetchImpl=globalThis.fetch,spawnImpl=spawn,launchTimeoutMs=15_000}={}){
    if(!profileDir)throw new BrowserAutomationError('profileDir é obrigatório para o Chrome humano.',{code:'PROFILE_DIR_REQUIRED'});
    this.profileDir=profileDir;this.cdpEndpoint=assertLocalCdpEndpoint(cdpEndpoint);this.chromePath=chromePath;this.logger=logger;this.fetchImpl=fetchImpl;this.spawnImpl=spawnImpl;this.launchTimeoutMs=launchTimeoutMs;
  }
  async status(){return await getCdpStatus(this.cdpEndpoint,{fetchImpl:this.fetchImpl});}
  async ensureRunning({url=XCURSOS_HOME_URL,bringUp=true}={}){
    const existing=await this.status();
    if(existing.ok){await this.logger?.log('BROWSER','Chrome CDP already available',{endpoint:this.cdpEndpoint});return{...existing,alreadyRunning:true,chromePath:this.chromePath||null,profileDir:this.profileDir};}
    const chromePath=await findChromeExecutable({explicitPath:this.chromePath});
    await fs.mkdir(this.profileDir,{recursive:true});
    const port=Number(new URL(this.cdpEndpoint).port||9222);
    const args=[
      `--remote-debugging-port=${port}`,
      '--remote-debugging-address=127.0.0.1',
      `--user-data-dir=${this.profileDir}`,
      '--no-first-run',
      '--no-default-browser-check',
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows',
    ];
    if(bringUp&&url)args.push(url);
    let child;
    try{
      child=this.spawnImpl(chromePath,args,{detached:true,stdio:'ignore',windowsHide:false,shell:false});
      child.unref?.();
    }catch(error){throw new BrowserAutomationError(`Falha ao abrir Google Chrome: ${String(error?.message||error)}`,{code:'CHROME_LAUNCH_FAILED',cause:error,details:{chromePath}});}
    const ready=await waitForCdp(this.cdpEndpoint,{timeoutMs:this.launchTimeoutMs,fetchImpl:this.fetchImpl});
    await this.logger?.log('BROWSER','Human Chrome started with local CDP',{endpoint:this.cdpEndpoint,profileDir:this.profileDir});
    return{...ready,alreadyRunning:false,chromePath,profileDir:this.profileDir,pid:child?.pid??null};
  }
}
