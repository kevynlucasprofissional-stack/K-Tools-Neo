import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs/promises';import os from 'node:os';import path from 'node:path';
import { MediaDownloader } from '../src/downloader.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-dl-'));}

test('M3 Windows filename sanitization and reserved names',()=>{const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff'});const p=d.buildPaths({root:'C:\\Downloads',courseName:'CON',moduleName:'M:od*',lessonTitle:'A?ula<>',position:1,total:198});assert.ok(!/[<>:"|?*]/.test(path.basename(p.baseName)));assert.ok(p.courseDir.includes('_CON'));});

test('M3 .part and corrupt files are not final outputs',async()=>{const root=await tmp();const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff'});await fs.writeFile(path.join(root,'001 - A.mp4.part'),'x');await fs.writeFile(path.join(root,'001 - A.mp4.corrupt-1'),'x');assert.equal(await d.findExistingFinal(root,'001 - A'),null);});

test('M3 expired 403 is classified without leaking retry logic',async()=>{const runner=async()=>({code:1,stdout:'',stderr:'HTTP Error 403: Forbidden'});const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:runner});const root=await tmp();const paths={moduleDir:root,baseName:'001 - A',template:path.join(root,'001 - A.%(ext)s')};const r=await d.download({mediaUrl:'https://cdn/a.mp4?X-Amz-Signature=secret',refererUrl:'https://xc/a',paths});assert.equal(r.ok,false);assert.equal(r.kind,'EXPIRED');});

test('M3 DRM output is classified and never claimed valid',async()=>{const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:async()=>({code:1,stdout:'',stderr:'This video is DRM protected with Widevine'})});const root=await tmp();const r=await d.download({mediaUrl:'https://x',refererUrl:'https://xc',paths:{moduleDir:root,baseName:'x',template:path.join(root,'x.%(ext)s')}});assert.equal(r.kind,'DRM');});

test('M3 validation requires size, video stream and positive duration',async()=>{const root=await tmp();const f=path.join(root,'x.mp4');await fs.writeFile(f,'123');const good=async()=>({code:0,stdout:JSON.stringify({streams:[{codec_type:'video',codec_name:'h264'}],format:{duration:'12.5',size:'3'}}),stderr:''});const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:good});const v=await d.validateVideo(f);assert.equal(v.duration,12.5);const bad=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:async()=>({code:0,stdout:JSON.stringify({streams:[],format:{duration:'0'}}),stderr:''})});await assert.rejects(()=>bad.validateVideo(f),e=>e.code==='VERIFY_NO_VIDEO_STREAM');});

test('M3 ffprobe unavailable is explicit',async()=>{const root=await tmp();const f=path.join(root,'x.mp4');await fs.writeFile(f,'x');const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:null});await assert.rejects(()=>d.validateVideo(f),e=>e.code==='FFPROBE_UNAVAILABLE');});

test('M3 very long names are shortened to safe full path with stable hash',()=>{const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff'});const root='C:\\Users\\User\\Downloads\\Cursos';const p=d.buildPaths({root,courseName:'C'.repeat(200),moduleName:'M'.repeat(200),lessonTitle:'L'.repeat(300),position:198,total:198});assert.ok(p.template.length<=235);assert.ok(p.template.includes('~'));});

test('M3 yt-dlp command includes continue and no-overwrites',async()=>{let seen;const root=await tmp();const final=path.join(root,'001 - A.mp4');const runner=async(command,args)=>{seen=args;await fs.writeFile(final,'x');return{code:0,stdout:`${final}\n`,stderr:''};};const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:runner});const r=await d.download({mediaUrl:'https://cdn/a.mp4',refererUrl:'https://xc/a',paths:{moduleDir:root,baseName:'001 - A',template:path.join(root,'001 - A.%(ext)s')}});assert.equal(r.ok,true);assert.ok(seen.includes('--continue'));assert.ok(seen.includes('--no-overwrites'));});

test('M3 ffprobe metadata with audio-only stream is rejected explicitly',async()=>{
  const root=await tmp();const f=path.join(root,'audio-only.mp4');await fs.writeFile(f,'123');
  const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:async()=>({code:0,stdout:JSON.stringify({streams:[{codec_type:'audio',codec_name:'aac'}],format:{duration:'10'}}),stderr:''})});
  await assert.rejects(()=>d.validateVideo(f),e=>e.code==='VERIFY_NO_VIDEO_STREAM');
});

test('V4.2.4 RED: yt-dlp 403 diagnostics expose semantic failureCode and redact signed URL',async()=>{
  const secretUrl='https://xcursos-videos.test.r2.cloudflarestorage.com/videos/108.mp4?X-Amz-Signature=SUPERSECRET&X-Amz-Credential=ABC';
  const runner=async()=>({code:1,stdout:'',stderr:`ERROR: unable to download video data: HTTP Error 403: Forbidden ${secretUrl}`});
  const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:runner});const root=await tmp();
  const r=await d.download({mediaUrl:secretUrl,refererUrl:'https://www.xcursos.com/curso/c/aula/108',paths:{moduleDir:root,baseName:'108 - e_Aula',template:path.join(root,'108 - e_Aula.%(ext)s')}});
  assert.equal(r.ok,false);assert.equal(r.kind,'EXPIRED');assert.equal(r.failureCode,'HTTP_403');
  assert.match(r.diagnosticTail,/403/);assert.equal(r.diagnosticTail.includes('SUPERSECRET'),false);assert.match(r.diagnosticTail,/sensitive-query-redacted|<redacted>/);
});

test('V4.2.4 RED: yt-dlp connection reset is classified separately from generic failure',async()=>{
  const d=new MediaDownloader({ytDlpPath:'yt',ffprobePath:'ff',processRunner:async()=>({code:1,stdout:'',stderr:'ERROR: [download] Connection reset by peer'})});const root=await tmp();
  const r=await d.download({mediaUrl:'https://cdn/a.mp4',refererUrl:'https://xc/a',paths:{moduleDir:root,baseName:'001 - A',template:path.join(root,'001 - A.%(ext)s')}});
  assert.equal(r.ok,false);assert.equal(r.failureCode,'NETWORK_RESET');
});
