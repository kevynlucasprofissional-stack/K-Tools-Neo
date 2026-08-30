import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { MediaDownloader, parseYtDlpProgress } from '../src/downloader.mjs';

test('yt-dlp progress parser extracts percent and speed without depending on locale text around it',()=>{const p=parseYtDlpProgress('[download]  38.2% of ~ 100.00MiB at 5.10MiB/s ETA 00:12');assert.equal(p.percent,38.2);assert.equal(p.speedText,'5.10MiB/s');assert.equal(p.eta,'00:12');});

test('MediaDownloader forwards progress callbacks while preserving after_move final path parsing',async()=>{
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'xc-prog-'));const final=path.join(dir,'001 - A.mp4');await fs.writeFile(final,'VIDEO');const progress=[];
  const processRunner=async(cmd,args,opts)=>{opts.onStderr?.('[download]  10.0% of 10MiB at 1.00MiB/s ETA 00:09\n');opts.onStdout?.('[download]  50.0% of 10MiB at 2.00MiB/s ETA 00:05\n');return{code:0,stdout:`${final}\n`,stderr:''};};
  const d=new MediaDownloader({processRunner,ytDlpPath:'yt-dlp',ffprobePath:'ffprobe'});const r=await d.download({mediaUrl:'https://cdn.example/1.mp4',refererUrl:'https://www.xcursos.com/aula/1',paths:{moduleDir:dir,baseName:'001 - A',template:path.join(dir,'001 - A.%(ext)s')},onProgress:p=>progress.push(p)});assert.equal(r.ok,true);assert.equal(r.finalPath,final);assert.deepEqual(progress.map(x=>x.percent),[10,50]);
});
