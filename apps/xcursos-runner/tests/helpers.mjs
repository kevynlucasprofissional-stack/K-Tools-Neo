import fs from 'node:fs/promises';
import path from 'node:path';
import { BrowserAutomationError } from '../src/errors.mjs';
import { sanitizeSegment } from '../src/utils.mjs';

export function lesson(position,total,{course='Fake Course',module='1. Module',title=`Lesson ${position}`,video=true,mediaType='DIRECT_MP4',signed=false,materials=false,drm=false,url=null}={}){
  const videoUrl=video?(url || `https://cdn.example/${position}.mp4${signed?'?X-Amz-Signature=secret':''}`):null;
  return {site:'xcursos',pageUrl:`https://www.xcursos.com/aula/${position}`,pageTitle:'Assistir Aula | XCURSOS',courseName:course,lessonTitle:title,moduleName:module,currentPosition:position,totalPositions:total,videoUrl,videoUrlRedacted:videoUrl?`https://cdn.example/${position}.mp4${signed?'?<sensitive-query-redacted>':''}`:null,mediaType:video?mediaType:'NONE',mediaSource:video?'video.currentSrc':null,isSignedDirectMp4:Boolean(video&&signed),hasMaterialsLinks:materials,drmDetected:drm};
}

export class FakeBrowser {
  constructor(lessons,{startPosition=1,transitionPlan={},ownership=false,loseOnInspectOnce=false}={}){
    this.lessons=lessons;this.current=startPosition;this.transitionPlan=transitionPlan;this.ownership=ownership;this.loseOnInspectOnce=loseOnInspectOnce;
    this.page={id:'fake-page',url:`https://www.xcursos.com/aula/${startPosition}`,title:'Assistir Aula | XCURSOS'};
    this.capabilities={evaluateScript:'evaluate_script',listPages:'list_pages',newPage:'new_page'};
    this.stats={clickNext:0,goToPosition:0,inspect:0,refresh:0,recover:0,connect:0};
  }
  async connect(){this.stats.connect++;return ['list_pages','evaluate_script','new_page'];}
  async close(){}
  async cleanupCreatedPages(){}
  _lesson(){const base=this.lessons[this.current-1];return {...base,pageUrl:`https://www.xcursos.com/aula/${this.current}`};}
  async chooseWorkingPage(){return{page:{...this.page,url:`https://www.xcursos.com/aula/${this.current}`},lesson:this._lesson(),cloned:this.ownership};}
  async inspectLesson(page){this.stats.inspect++;if(this.loseOnInspectOnce){this.loseOnInspectOnce=false;throw new BrowserAutomationError('page not found',{code:'MCP_TOOL_ERROR'});}return this._lesson();}
  async goToPosition(page,target){this.stats.goToPosition++;if(target<1||target>this.lessons.length)throw new BrowserAutomationError('bad target',{code:'POSITION_REPOSITION_FAILED'});this.current=target;this.page.url=`https://www.xcursos.com/aula/${target}`;return{page:this.page,lesson:this._lesson(),method:'fake-direct'};}
  async clickNext(){this.stats.clickNext++;const behavior=this.transitionPlan[this.current]||'normal';if(behavior==='stuck')return true;if(behavior==='skip'){this.current=Math.min(this.lessons.length,this.current+2);return true;}if(behavior==='regress'){this.current=Math.max(1,this.current-1);return true;}this.current=Math.min(this.lessons.length,this.current+1);this.page.url=`https://www.xcursos.com/aula/${this.current}`;return true;}
  async waitForPosition(page,target){const observed=this.current;if(observed===target)return this._lesson();let code='POSITION_STUCK';if(observed>target)code='POSITION_SKIP';else if(observed<target-1)code='POSITION_REGRESSION';throw new BrowserAutomationError(`expected ${target} got ${observed}`,{code,details:{target,observed}});}
  async navigateExact(page,url){const m=String(url).match(/\/aula\/(\d+)/);if(!m)throw new BrowserAutomationError('bad url',{code:'NAV_EXACT_FAILED'});this.current=Number(m[1]);this.page.url=url;return this.page;}
  async refreshSameLesson(){this.stats.refresh++;this.page={id:`fake-refresh-${this.stats.refresh}`,url:`https://www.xcursos.com/aula/${this.current}`,title:'Assistir Aula | XCURSOS'};return this.page;}
  async recoverWorkingPage(){this.stats.recover++;return this.page;}
}

export class DiskFakeDownloader {
  constructor({failPositions=[],expiredOncePositions=[],verifyFailPositions=[]}={}){
    this.failPositions=new Set(failPositions);this.expiredOncePositions=new Set(expiredOncePositions);this.verifyFailPositions=new Set(verifyFailPositions);
    this.calls=[];this.attemptByPos=new Map();this.ytDlpPath='fake';this.ffprobePath='fake';
  }
  async preflight(){return{ytDlp:'fake',ffprobe:'fake'};}
  buildPaths({root,courseName,moduleName,lessonTitle,position,total}){
    const courseDir=path.join(root,sanitizeSegment(courseName,'Course',90));const moduleDir=path.join(courseDir,sanitizeSegment(moduleName||'Modulo desconhecido','Modulo desconhecido',90));const width=Math.max(3,String(total).length);const baseName=`${String(position).padStart(width,'0')} - ${sanitizeSegment(lessonTitle,'Aula',110)}`;return{courseDir,moduleDir,baseName,template:path.join(moduleDir,`${baseName}.%(ext)s`)};
  }
  async findExistingFinal(moduleDir,baseName){try{const f=(await fs.readdir(moduleDir)).find(x=>x===`${baseName}.mp4`);return f?path.join(moduleDir,f):null;}catch{return null;}}
  async download({mediaUrl,paths}){
    const m=mediaUrl.match(/\/(\d+)\.mp4/);const pos=Number(m?.[1]||0);const attempt=(this.attemptByPos.get(pos)||0)+1;this.attemptByPos.set(pos,attempt);this.calls.push({pos,attempt,mediaUrl});
    if(this.expiredOncePositions.has(pos)&&attempt===1)return{ok:false,kind:'EXPIRED',code:1,stderr:'HTTP Error 403 Forbidden'};
    if(this.failPositions.has(pos))return{ok:false,kind:'FAILED',code:1,stderr:'network failed'};
    await fs.mkdir(paths.moduleDir,{recursive:true});const finalPath=path.join(paths.moduleDir,`${paths.baseName}.mp4`);await fs.writeFile(finalPath,`VIDEO-${pos}`);return{ok:true,finalPath,stdout:finalPath,stderr:''};
  }
  async quarantineCorrupt(filePath){const q=`${filePath}.corrupt-test`;await fs.rename(filePath,q);return q;}
  async validateVideo(filePath){const data=await fs.readFile(filePath,'utf8');const m=filePath.match(/(?:^|\D)(\d{3,5}) - /);const pos=Number(m?.[1]||0);if(this.verifyFailPositions.has(pos)||data.startsWith('CORRUPT'))throw new Error('ffprobe failed');return{size:Buffer.byteLength(data),duration:60+pos,codec:'h264'};}
}

export async function readJsonlFile(p){try{return(await fs.readFile(p,'utf8')).trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);}catch{return[];}}
