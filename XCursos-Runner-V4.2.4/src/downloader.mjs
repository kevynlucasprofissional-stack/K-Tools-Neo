import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import { DEFAULT_LIMITS } from './constants.mjs';
import { RunnerError } from './errors.mjs';
import { findExecutable, runProcess } from './process.mjs';
import { redactUrl, redactSensitiveText, sanitizeSegment, truncateWithHash } from './utils.mjs';

function looksExpired(output='') { return /(?:HTTP Error 403|\b403\b|forbidden|signature.*expired|request has expired|expiredtoken)/i.test(output); }
function looksDrm(output='') { return /(?:DRM|Widevine|PlayReady|FairPlay|encrypted media|This video is DRM protected)/i.test(output); }
export function classifyYtDlpFailure(output=''){
  const s=String(output||'');
  if(looksDrm(s))return'DRM';
  if(/(?:HTTP Error 403|\b403\b|forbidden)/i.test(s))return'HTTP_403';
  if(/(?:HTTP Error 404|\b404\b.*not found)/i.test(s))return'HTTP_404';
  if(/(?:HTTP Error 429|\b429\b|too many requests)/i.test(s))return'HTTP_429';
  if(/HTTP Error 5\d\d|\b5\d\d\b.*(?:server|gateway|service)/i.test(s))return'HTTP_5XX';
  if(/(?:connection reset|ECONNRESET|network reset)/i.test(s))return'NETWORK_RESET';
  if(/(?:timed? out|timeout|ETIMEDOUT)/i.test(s))return'NETWORK_TIMEOUT';
  if(/(?:TLS|SSL|certificate|handshake)/i.test(s))return'TLS_ERROR';
  if(/(?:temporary failure in name resolution|EAI_AGAIN|name or service not known|DNS)/i.test(s))return'DNS_ERROR';
  return'YTDLP_FAILED';
}
function diagnosticTail(output='',max=4000){const safe=redactSensitiveText(String(output||''));return safe.length>max?safe.slice(-max):safe;}
export function parseYtDlpProgress(line=''){const s=String(line);const pct=s.match(/\[download\]\s+(\d+(?:\.\d+)?)%/i);if(!pct)return null;const speed=s.match(/\bat\s+([^\s]+\/s)/i);const eta=s.match(/\bETA\s+([0-9:]+)/i);return{percent:Number(pct[1]),speedText:speed?.[1]||null,eta:eta?.[1]||null};}

export class MediaDownloader {
  constructor({ processRunner = runProcess, logger = null, limits = {}, ytDlpPath = null, ffprobePath = null } = {}) {
    this.processRunner = processRunner; this.logger=logger; this.limits={...DEFAULT_LIMITS,...limits};
    this.ytDlpPath=ytDlpPath; this.ffprobePath=ffprobePath;
  }

  async preflight() {
    if (!this.ytDlpPath) this.ytDlpPath=(await findExecutable('yt-dlp',{envVar:'YTDLP_PATH',processRunner:this.processRunner})).path;
    if (!this.ffprobePath) this.ffprobePath=(await findExecutable('ffprobe',{envVar:'FFPROBE_PATH',versionArgs:['-version'],processRunner:this.processRunner})).path;
    return { ytDlp:this.ytDlpPath, ffprobe:this.ffprobePath };
  }

  buildPaths({ root, courseName, moduleName, lessonTitle, position, total }) {
    let course= sanitizeSegment(courseName,'Curso XCursos',90);
    let module= sanitizeSegment(moduleName || 'Modulo desconhecido','Modulo desconhecido',80);
    let title= sanitizeSegment(lessonTitle,'Aula',110);
    const width=Math.max(3,String(total || 999).length);
    const prefix=position != null ? String(position).padStart(width,'0') : '000';
    const templateFor=()=>path.join(root,course,module,`${prefix} - ${title}.%(ext)s`);
    const maxPath=235;
    for (const [kind,min] of [['title',32],['module',24],['course',32]]) {
      while(templateFor().length>maxPath){
        if(kind==='title' && title.length>min) title=truncateWithHash(title,Math.max(min,title.length-10));
        else if(kind==='module' && module.length>min) module=truncateWithHash(module,Math.max(min,module.length-10));
        else if(kind==='course' && course.length>min) course=truncateWithHash(course,Math.max(min,course.length-10));
        else break;
      }
    }
    if(templateFor().length>maxPath) throw new RunnerError(`Caminho de saída excede limite seguro (${templateFor().length} > ${maxPath}). Escolha um outputRoot mais curto.`,{code:'OUTPUT_PATH_TOO_LONG'});
    const courseDir=path.join(root,course); const moduleDir=path.join(courseDir,module); const baseName=`${prefix} - ${title}`;
    return { courseDir,moduleDir,baseName,template:path.join(moduleDir,`${baseName}.%(ext)s`) };
  }

  async findExistingFinal(moduleDir, baseName) {
    try {
      const entries=await fs.readdir(moduleDir,{withFileTypes:true});
      const prefix=`${baseName}.`;
      const finals=entries.filter(e=>e.isFile() && e.name.startsWith(prefix) && e.name.slice(prefix.length).length>0 && !/\.(?:part|ytdl|temp)$/i.test(e.name) && !/\.corrupt-/i.test(e.name));
      if(finals.length===1)return path.join(moduleDir,finals[0].name);
      if(finals.length>1)throw new RunnerError(`Mais de um arquivo final corresponde a ${baseName}.`,{code:'DUPLICATE_OUTPUT_FILES'});
      return null;
    } catch(error){ if(error?.code==='ENOENT')return null; throw error; }
  }


  async quarantineCorrupt(filePath) {
    const quarantine=`${filePath}.corrupt-${Date.now()}`;
    try { await fs.rename(filePath,quarantine); return quarantine; }
    catch(error){ throw new RunnerError(`Arquivo inválido não pôde ser movido para quarentena: ${path.basename(filePath)}`,{code:'CORRUPT_FILE_QUARANTINE_FAILED',cause:error,details:{filePath}}); }
  }

  async validateVideo(filePath,{signal=null}={}) {
    if (!this.ffprobePath) throw new RunnerError('ffprobe não foi inicializado; validação completa indisponível.', { code:'FFPROBE_UNAVAILABLE' });
    let stat;
    try { stat=await fs.stat(filePath); } catch { throw new RunnerError('Arquivo final não existe.',{code:'VERIFY_FILE_MISSING'}); }
    if(!stat.isFile() || stat.size<=0)throw new RunnerError('Arquivo final está vazio.',{code:'VERIFY_EMPTY_FILE'});
    const r=await this.processRunner(this.ffprobePath,['-v','error','-select_streams','v:0','-show_entries','stream=codec_name,codec_type','-show_entries','format=duration,size','-of','json',filePath],{timeoutMs:this.limits.ffprobeTimeoutMs,signal});
    if(r.code!==0)throw new RunnerError(`ffprobe falhou: ${String(r.stderr||'').trim().slice(-1200)}`,{code:'VERIFY_FFPROBE_FAILED'});
    let meta; try{meta=JSON.parse(r.stdout);}catch{throw new RunnerError('ffprobe não retornou JSON válido.',{code:'VERIFY_FFPROBE_INVALID_JSON'});}
    const duration=Number(meta?.format?.duration||0); const streams=Array.isArray(meta?.streams)?meta.streams:[];
    const video=streams.find(s=>s.codec_type==='video');
    if(!video || !(duration>0))throw new RunnerError('Validação falhou: sem stream de vídeo ou duração positiva.',{code:'VERIFY_NO_VIDEO_STREAM'});
    return { size:stat.size,duration,codec:video.codec_name||null };
  }

  async download({ mediaUrl, refererUrl, paths, signal=null, onProgress=null }) {
    await fs.mkdir(paths.moduleDir,{recursive:true});
    const args=['--no-playlist','--continue','--no-overwrites','--retries','3','--fragment-retries','3','--referer',refererUrl,'--print','after_move:filepath','-o',paths.template,mediaUrl];
    await this.logger?.log('DOWNLOAD','Starting',{media:redactUrl(mediaUrl),output:paths.template});
    let r;
    const feed=chunk=>{if(!onProgress)return;for(const line of String(chunk).split(/\r?\n/)){const p=parseYtDlpProgress(line);if(p)onProgress(p);}};
    try{r=await this.processRunner(this.ytDlpPath,args,{timeoutMs:this.limits.downloadTimeoutMs,signal,onStdout:feed,onStderr:feed});}
    catch(error){
      if(error?.code==='PROCESS_ABORTED')throw error;
      const failureCode=error?.code==='PROCESS_TIMEOUT'?'PROCESS_TIMEOUT':String(error?.code||'SPAWN_ERROR');
      return {ok:false,kind:error?.code==='PROCESS_TIMEOUT'?'TIMEOUT':'SPAWN_ERROR',failureCode,diagnosticTail:diagnosticTail(error?.message||error),error};
    }
    const combined=`${r.stdout}\n${r.stderr}`;
    if(r.code!==0){const failureCode=classifyYtDlpFailure(combined);return {ok:false,kind:failureCode==='DRM'?'DRM':looksExpired(combined)?'EXPIRED':'FAILED',failureCode,diagnosticTail:diagnosticTail(combined),code:r.code,stdout:r.stdout,stderr:r.stderr};}
    let finalPath=r.stdout.split(/\r?\n/).map(x=>x.trim()).filter(Boolean).at(-1);
    if(!finalPath || !fsSync.existsSync(finalPath))finalPath=await this.findExistingFinal(paths.moduleDir,paths.baseName);
    if(!finalPath)return {ok:false,kind:'NO_FINAL_PATH',code:r.code,stdout:r.stdout,stderr:r.stderr};
    return {ok:true,finalPath,stdout:r.stdout,stderr:r.stderr};
  }
}
