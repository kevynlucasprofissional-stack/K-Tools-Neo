import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { runProcess, findExecutable } from '../src/process.mjs';import { MediaDownloader } from '../src/downloader.mjs';import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-proc-'));}

test('subprocess timeout is enforced',async()=>{await assert.rejects(()=>runProcess(process.execPath,['-e','setTimeout(()=>{},5000)'],{timeoutMs:50}),e=>e.code==='PROCESS_TIMEOUT');});

test('findExecutable locates real ffprobe when available',async(t)=>{try{const f=await findExecutable('ffprobe',{envVar:'FFPROBE_PATH',versionArgs:['-version']});assert.ok(f.path);}catch(e){t.skip(`ffprobe ausente neste ambiente: ${e.message}`);}});

test('real ffmpeg-generated MP4 passes real ffprobe validation',async(t)=>{let ffmpeg,ffprobe;try{ffmpeg=(await findExecutable('ffmpeg',{versionArgs:['-version']})).path;ffprobe=(await findExecutable('ffprobe',{versionArgs:['-version']})).path;}catch(e){t.skip(`ffmpeg/ffprobe ausente: ${e.message}`);return;}const root=await tmp();const file=path.join(root,'tiny.mp4');const r=await runProcess(ffmpeg,['-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=black:s=32x32:d=0.3','-c:v','libx264','-pix_fmt','yuv420p','-y',file],{timeoutMs:15000});assert.equal(r.code,0);const d=new MediaDownloader({ytDlpPath:'fake',ffprobePath:ffprobe});const v=await d.validateVideo(file);assert.ok(v.size>0);assert.ok(v.duration>0);assert.ok(v.codec);});

test('logger redacts signed URL query',async()=>{const lines=[];const l=new RunnerLogger({sink:x=>lines.push(x)});await l.log('MEDIA','url https://cdn.example/a.mp4?X-Amz-Signature=SECRET&X-Amz-Expires=10');assert.equal(lines.some(x=>x.includes('SECRET')),false);});

test('subprocess capture is bounded and keeps the tail needed for final-path parsing',async()=>{
  const { runProcess }=await import('../src/process.mjs');
  const script="process.stdout.write('A'.repeat(20000)); process.stdout.write('TAIL_MARKER'); process.stderr.write('B'.repeat(20000)); process.stderr.write('ERR_TAIL');";
  const r=await runProcess(process.execPath,['-e',script],{timeoutMs:5000,maxCaptureBytes:4096});
  assert.ok(Buffer.byteLength(r.stdout)<=4096);
  assert.ok(Buffer.byteLength(r.stderr)<=4096);
  assert.match(r.stdout,/TAIL_MARKER$/);
  assert.match(r.stderr,/ERR_TAIL$/);
  assert.equal(r.stdoutTruncated,true);
  assert.equal(r.stderrTruncated,true);
});

test('subprocess timeout does not return control while a SIGTERM-resistant child is still running',async()=>{
  const { runProcess }=await import('../src/process.mjs');
  const root=await fs.mkdtemp(path.join(os.tmpdir(),'xc-proc-timeout-'));
  const marker=path.join(root,'alive.txt');
  const script=`const fs=require('fs');process.on('SIGTERM',()=>{});setInterval(()=>fs.writeFileSync(${JSON.stringify(marker)},String(Date.now())),25);`;
  const start=Date.now();
  await assert.rejects(()=>runProcess(process.execPath,['-e',script],{timeoutMs:400,killGraceMs:150}),e=>e.code==='PROCESS_TIMEOUT');
  const elapsed=Date.now()-start;
  assert.ok(elapsed>=500,`timeout returned too early for a SIGTERM-resistant ready child: ${elapsed}ms`);
  const before=await fs.readFile(marker,'utf8').catch(()=>null);
  await new Promise(r=>setTimeout(r,120));
  const after=await fs.readFile(marker,'utf8').catch(()=>null);
  assert.equal(after,before,'child kept writing after runProcess returned');
});
