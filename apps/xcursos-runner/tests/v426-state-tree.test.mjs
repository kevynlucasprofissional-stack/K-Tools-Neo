import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { StateStore } from '../src/state.mjs';
import { MediaDownloader } from '../src/downloader.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-v426-state-'));}

test('V4.2.6: manifest persists modulePath without breaking leaf moduleName',async()=>{
  const root=await tmp();
  const modulePath=['2. Regravação VTSD 2026','05. Copywriting','5. Vídeo de vendas - VSL'];
  const state=new StateStore({outputRoot:root,courseName:'Course',totalPositions:1});
  await state.initialize({resume:false,workPageUrl:'https://www.xcursos.com/curso/c/aula/1'});
  await state.commit({position:1,lessonTitle:'e_Aula',moduleName:modulePath.at(-1),modulePath,lessonUrl:'https://www.xcursos.com/curso/c/aula/1',status:'NO_VIDEO',outputFile:null,attempts:0,validation:null});
  const lines=(await fs.readFile(state.manifestPath,'utf8')).trim().split(/\r?\n/).filter(Boolean).map(JSON.parse);
  assert.equal(lines.length,1);
  assert.deepEqual(lines[0].modulePath,modulePath);
  assert.equal(lines[0].moduleName,modulePath.at(-1));
});

test('V4.2.6: deep module tree is shortened deterministically to a Windows-safe output path',()=>{
  const d=new MediaDownloader();
  const modulePath=[
    '01. '.concat('Modulo principal extremamente longo '.repeat(5)),
    '02. '.concat('Submodulo intermediario extremamente longo '.repeat(5)),
    '03. '.concat('Submodulo folha extremamente longo '.repeat(5)),
  ];
  const paths=d.buildPaths({root:'C:\\Users\\Kevyn\\Downloads\\Cursos',courseName:'Curso '.concat('Muito longo '.repeat(8)),moduleName:modulePath.at(-1),modulePath,lessonTitle:'Aula '.concat('Com um titulo muito longo '.repeat(8)),position:108,total:198});
  assert.ok(paths.template.length<=235,`template length=${paths.template.length}`);
  assert.equal(paths.modulePath.length,3);
  assert.match(paths.baseName,/^108 - /);
});
