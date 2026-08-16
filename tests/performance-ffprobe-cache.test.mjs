import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { MediaDownloader } from '../src/downloader.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-ffprobe-fast-'));}
function goodProbe(){return{code:0,stdout:JSON.stringify({streams:[{codec_type:'video',codec_name:'h264'}],format:{duration:'42'}}),stderr:''};}
function nativePage(){
  const locator={async count(){return 1;},async getAttribute(){return '/api/video/download?lessonId=lesson-7';},async click(){}};
  const download={failure:async()=>null,suggestedFilename:()=> 'server.mp4',async saveAs(file){await fs.writeFile(file,'native-video');}};
  return{isClosed:()=>false,locator:()=>({first:()=>locator}),waitForEvent:async()=>download};
}

test('native download plus runner-style validation invokes ffprobe only once',async()=>{
  const root=await tmp();let ffprobeCalls=0;
  const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',pageResolver:async()=>nativePage(),processRunner:async command=>{if(command==='ff'){ffprobeCalls++;return goodProbe();}throw new Error('yt-dlp must not run');}});
  const paths={moduleDir:root,baseName:'007 - Aula',template:path.join(root,'007 - Aula.%(ext)s')};
  const result=await d.download({mediaUrl:'https://cdn.example/7.mp4',refererUrl:'https://www.xcursos.com/curso/c/aula/7',paths});
  assert.equal(result.ok,true);assert.equal(result.downloadMethod,'XCURSOS_NATIVE');assert.equal(ffprobeCalls,1);
  const validation=await d.validateVideo(result.finalPath);
  assert.equal(ffprobeCalls,1);assert.equal(validation.downloadMethod,'XCURSOS_NATIVE');assert.ok(validation.fileFingerprint);assert.equal(validation.fileFingerprint.size,(await fs.stat(result.finalPath)).size);
});

test('validation cache is invalidated when file fingerprint changes',async()=>{
  const root=await tmp();const file=path.join(root,'x.mp4');await fs.writeFile(file,'abc');let ffprobeCalls=0;
  const d=new MediaDownloader({ffprobePath:'ff',processRunner:async()=>{ffprobeCalls++;return goodProbe();}});
  await d.validateVideo(file);await d.validateVideo(file);assert.equal(ffprobeCalls,1);
  await fs.appendFile(file,'changed');await d.validateVideo(file);assert.equal(ffprobeCalls,2);
});
