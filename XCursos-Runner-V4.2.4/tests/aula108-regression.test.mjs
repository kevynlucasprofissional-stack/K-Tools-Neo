import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseXcursosLessonHtml } from '../src/parser.mjs';

const here=path.dirname(fileURLToPath(import.meta.url));
const fixture=await fs.readFile(path.join(here,'../test-fixtures/xcursos-aula-108-sanitized.htm'),'utf8');

test('V4.2.4 real Aula 108 regression: direct signed R2 MP4 is discoverable and not DRM',()=>{
  const x=parseXcursosLessonHtml(fixture,'https://www.xcursos.com/curso/venda-todo-santo-dia-leandro-ladeira/aula/108-redacted');
  assert.equal(x.courseName,'VENDA TODO SANTO DIA 2026 - LEANDRO LADEIRA');
  assert.equal(x.moduleName,'5. Vídeo de vendas - VSL');
  assert.equal(x.lessonTitle,'e_Aula');assert.equal(x.currentPosition,108);assert.equal(x.totalPositions,198);
  assert.equal(x.mediaType,'DIRECT_MP4');assert.equal(x.mediaSource,'video.src');assert.equal(x.isSignedDirectMp4,true);assert.equal(x.drmDetected,false);assert.equal(x.hasMaterialsLinks,true);
  assert.match(x.videoUrl,/\/videos\/1kICdVFIVr1XfZYa6-5KutVUN6sy2EEkg\.mp4/);assert.match(x.videoUrlRedacted,/sensitive-query-redacted/);
});
