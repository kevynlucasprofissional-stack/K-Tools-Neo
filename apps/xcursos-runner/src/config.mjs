import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { atomicWriteJson, readJsonIfExists, safePersistUrl } from './utils.mjs';
import { cdpEndpointFromPort } from './chrome-launcher.mjs';

export function defaultAppRoot(env=process.env, platform=process.platform){
  if(platform==='win32')return path.join(env.LOCALAPPDATA || path.join(os.homedir(),'AppData','Local'),'XCursosRunner');
  if(platform==='darwin')return path.join(os.homedir(),'Library','Application Support','XCursosRunner');
  return path.join(env.XDG_STATE_HOME || path.join(os.homedir(),'.local','state'),'xcursos-runner');
}
export function defaultOutputRoot(){return path.join(os.homedir(),'Downloads','Cursos');}

export class AppConfigStore {
  constructor({appRoot=defaultAppRoot()}={}){
    this.appRoot=appRoot;this.configPath=path.join(appRoot,'config.json');this.profileDir=path.join(appRoot,'chrome-profile');
  }
  async load(){
    let raw=null;try{raw=await readJsonIfExists(this.configPath);}catch{}
    const cfg=raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{};
    const cdpPort=Number.isInteger(Number(cfg.cdpPort))?Number(cfg.cdpPort):9222;
    return{
      version:2,
      profileDir:String(cfg.profileDir||this.profileDir),
      outputRoot:String(cfg.outputRoot||defaultOutputRoot()),
      lastLessonUrl:safePersistUrl(cfg.lastLessonUrl)||null,
      chromePath:cfg.chromePath?String(cfg.chromePath):null,
      cdpPort,
      cdpEndpoint:cdpEndpointFromPort(cdpPort),
      updatedAt:cfg.updatedAt||null,
    };
  }
  async save(patch={}){
    const current=await this.load();
    const next={...current,...patch,version:2};
    next.lastLessonUrl=safePersistUrl(next.lastLessonUrl)||null;
    next.cdpPort=Number(next.cdpPort||9222);
    next.cdpEndpoint=cdpEndpointFromPort(next.cdpPort);
    next.updatedAt=new Date().toISOString();
    await fs.mkdir(this.appRoot,{recursive:true});await atomicWriteJson(this.configPath,next);return next;
  }
  async rememberLesson(url){return await this.save({lastLessonUrl:url});}
}
