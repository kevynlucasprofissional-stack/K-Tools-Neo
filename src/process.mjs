import { spawn } from 'node:child_process';
import path from 'node:path';
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import os from 'node:os';
import { RunnerError } from './errors.mjs';

const DEFAULT_MAX_CAPTURE_BYTES=4*1024*1024;

function appendTail(current, chunk, maxBytes) {
  if (!(maxBytes > 0)) return { text:current+chunk, truncated:false };
  let combined=current+chunk;
  const bytes=Buffer.byteLength(combined);
  if(bytes<=maxBytes)return{text:combined,truncated:false};
  // Keep the tail: yt-dlp prints after_move:filepath at the end and diagnostics are usually most useful there.
  let buf=Buffer.from(combined);
  buf=buf.subarray(Math.max(0,buf.length-maxBytes));
  // Avoid beginning in the middle of a UTF-8 continuation byte.
  while(buf.length && (buf[0]&0xC0)===0x80)buf=buf.subarray(1);
  return{text:buf.toString('utf8'),truncated:true};
}

export async function runProcess(command, args = [], { cwd, timeoutMs = 0, env, onStdout, onStderr, maxCaptureBytes=DEFAULT_MAX_CAPTURE_BYTES, killGraceMs=1500, signal=null } = {}) {
  return await new Promise((resolve, reject) => {
    let settled = false;
    let child;
    try { child = spawn(command, args, { cwd, env: env || process.env, windowsHide: true, shell: false }); }
    catch(error){ reject(error); return; }
    let stdout = '', stderr = '', stdoutTruncated=false, stderrTruncated=false;
    let timeoutTimer=null, hardKillTimer=null, failSafeTimer=null, timeoutError=null, abortError=null;
    let abortHandler=null;
    const clearTimers=()=>{if(timeoutTimer)clearTimeout(timeoutTimer);if(hardKillTimer)clearTimeout(hardKillTimer);if(failSafeTimer)clearTimeout(failSafeTimer);if(signal&&abortHandler)signal.removeEventListener?.('abort',abortHandler);};
    const finishReject = error => { if (settled) return; settled = true; clearTimers(); reject(error); };
    child.stdout?.on('data', d => { const s=d.toString(); const next=appendTail(stdout,s,maxCaptureBytes);stdout=next.text;stdoutTruncated ||= next.truncated;onStdout?.(s); });
    child.stderr?.on('data', d => { const s=d.toString(); const next=appendTail(stderr,s,maxCaptureBytes);stderr=next.text;stderrTruncated ||= next.truncated;onStderr?.(s); });
    child.on('error', error => finishReject(timeoutError || error));

    const forceKill=()=>{
      if(child.exitCode!==null)return;
      if(process.platform==='win32' && child.pid){
        try {
          const killer=spawn('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true,stdio:'ignore',shell:false});
          killer.unref?.();
        } catch { try{child.kill('SIGKILL');}catch{} }
      } else {
        try { child.kill('SIGKILL'); } catch {}
      }
    };

    if(signal){
      abortHandler=()=>{
        abortError=new RunnerError(`${path.basename(command)} foi interrompido por force stop`,{code:'PROCESS_ABORTED'});
        forceKill();
        failSafeTimer=setTimeout(()=>finishReject(abortError),Math.max(0,killGraceMs)+1000);failSafeTimer.unref?.();
      };
      if(signal.aborted){abortHandler();return;}
      signal.addEventListener?.('abort',abortHandler,{once:true});
    }

    if (timeoutMs > 0) timeoutTimer = setTimeout(() => {
      timeoutError=new RunnerError(`${path.basename(command)} excedeu timeout de ${timeoutMs}ms`, { code:'PROCESS_TIMEOUT' });
      if(process.platform==='win32') forceKill();
      else { try { if(child.exitCode===null)child.kill('SIGTERM'); } catch {} }
      hardKillTimer=setTimeout(forceKill,Math.max(0,killGraceMs));
      // Last-resort guard: never hang forever if the OS does not deliver close after a kill attempt.
      failSafeTimer=setTimeout(()=>finishReject(timeoutError),Math.max(0,killGraceMs)+5000);
      hardKillTimer.unref?.(); failSafeTimer.unref?.();
    }, timeoutMs);

    child.on('close', (code, signal) => {
      if (settled) return;
      clearTimers();
      if(timeoutError){finishReject(timeoutError);return;}
      if(abortError){finishReject(abortError);return;}
      settled = true;
      resolve({ code: code ?? -1, signal, stdout, stderr, stdoutTruncated, stderrTruncated });
    });
  });
}

function splitPathEnv() { return String(process.env.PATH || '').split(path.delimiter).filter(Boolean); }

export async function findExecutable(name, { envVar = null, versionArgs = ['--version'], processRunner = runProcess } = {}) {
  const explicit = envVar ? process.env[envVar] : null;
  const candidates = [];
  if (explicit) candidates.push(explicit);
  candidates.push(name);
  if (process.platform === 'win32' && !/\.exe$/i.test(name)) candidates.push(`${name}.exe`);
  if (process.platform === 'win32') {
    const local = process.env.LOCALAPPDATA, app = process.env.APPDATA;
    if (local) candidates.push(path.join(local, 'Programs', name, `${name}.exe`));
    if (app) candidates.push(path.join(app, 'Python', 'Scripts', `${name}.exe`));
    for (const dir of splitPathEnv()) candidates.push(path.join(dir, `${name}.exe`));
  }
  const seen = new Set();
  for (const candidate of candidates) {
    if (!candidate || seen.has(candidate)) continue; seen.add(candidate);
    if (candidate.includes(path.sep) && !fsSync.existsSync(candidate)) continue;
    try {
      const r = await processRunner(candidate, versionArgs, { timeoutMs: 15_000 });
      if (r.code === 0) return { path: candidate, version: (r.stdout || r.stderr || '').trim().split(/\r?\n/)[0] || null };
    } catch {}
  }
  throw new RunnerError(`${name} não está disponível. Configure ${envVar || 'PATH'} e tente novamente.`, { code:`${name.toUpperCase().replace(/-/g,'_')}_UNAVAILABLE` });
}

export async function ensureDir(dir) { await fs.mkdir(dir, { recursive:true }); return dir; }
export function homeDownloads() { return path.join(os.homedir(), 'Downloads'); }
