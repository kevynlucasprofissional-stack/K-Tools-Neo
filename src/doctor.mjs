import { findExecutable } from './process.mjs';
import { findChromeExecutable, getCdpStatus } from './chrome-launcher.mjs';
import { getRunnerInfo } from './version-info.mjs';

async function executable(name,envVar,versionArgs=['--version']){try{return{ok:true,...await findExecutable(name,{envVar,versionArgs})};}catch(error){return{ok:false,error:String(error?.message||error)};}}

export async function runDoctor({config,playwrightLoader=null,fetchImpl=globalThis.fetch}={}){
  const major=Number(process.versions.node.split('.')[0]);const info=await getRunnerInfo();
  const result={
    runnerVersion:info.version,cliPath:info.cliPath,installRoot:info.installRoot,
    ok:true,
    node:{ok:major>=22&&major<27,version:process.version,required:'22.x, 24.x or 26.x'},
    playwrightCore:{ok:false},chrome:{ok:false},cdp:{ok:false,running:false,endpoint:config?.cdpEndpoint||null},
    ytDlp:await executable('yt-dlp','YTDLP_PATH'),
    ffprobe:await executable('ffprobe','FFPROBE_PATH',['-version']),
    profileDir:config?.profileDir||null,outputRoot:config?.outputRoot||null,
  };
  try{const mod=playwrightLoader?await playwrightLoader():await import('playwright-core');result.playwrightCore={ok:Boolean(mod.chromium?.connectOverCDP),version:null};}
  catch(error){result.playwrightCore={ok:false,error:String(error?.message||error)};}
  try{const chromePath=await findChromeExecutable({explicitPath:config?.chromePath||null});result.chrome={ok:true,path:chromePath};}
  catch(error){result.chrome={ok:false,error:String(error?.message||error)};}
  if(config?.cdpEndpoint){const cdp=await getCdpStatus(config.cdpEndpoint,{fetchImpl});result.cdp={...cdp,running:Boolean(cdp.ok)};}
  result.ok=Boolean(result.node.ok&&result.playwrightCore.ok&&result.chrome.ok&&result.ytDlp.ok&&result.ffprobe.ok);
  return result;
}
