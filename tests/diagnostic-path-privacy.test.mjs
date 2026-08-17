import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as utils from '../src/utils.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-path-privacy-'));}

test('redactHomePath anonymizes Windows home paths case-insensitively and respects path boundaries',()=>{
  assert.equal(typeof utils.redactHomePath,'function');
  const home='C:\\Users\\Kevyn Lucas';
  assert.equal(utils.redactHomePath('C:\\Users\\Kevyn Lucas\\Downloads\\Cursos',{homeDir:home}),'$HOME\\Downloads\\Cursos');
  assert.equal(utils.redactHomePath('c:\\users\\kevyn lucas\\AppData\\Local',{homeDir:home}),'$HOME\\AppData\\Local');
  assert.equal(utils.redactHomePath('C:\\Users\\Kevyn Lucas-outro\\file.txt',{homeDir:home}),'C:\\Users\\Kevyn Lucas-outro\\file.txt');
});

test('redactHomePath anonymizes POSIX home paths and leaves paths outside home unchanged',()=>{
  const home='/home/kevyn';
  assert.equal(utils.redactHomePath('/home/kevyn/Downloads/Cursos',{homeDir:home}),'$HOME/Downloads/Cursos');
  assert.equal(utils.redactHomePath('/home/kevyn-other/file.txt',{homeDir:home}),'/home/kevyn-other/file.txt');
  assert.equal(utils.redactHomePath('/srv/xcursos/file.txt',{homeDir:home}),'/srv/xcursos/file.txt');
});

test('sanitizeForSharing redacts home paths recursively while retaining ordinary diagnostic text',()=>{
  assert.equal(typeof utils.sanitizeForSharing,'function');
  const value={path:'C:\\Users\\Pessoa\\Downloads\\Cursos',message:'failed at C:\\Users\\Pessoa\\Downloads\\Cursos\\a.mp4',nested:['C:\\Users\\Pessoa\\AppData\\Local']};
  const safe=utils.sanitizeForSharing(value,{homeDir:'C:\\Users\\Pessoa'});const text=JSON.stringify(safe);
  assert.doesNotMatch(text,/C:\\\\Users\\\\Pessoa/i);assert.match(text,/\$HOME/);assert.match(safe.message,/failed at/);
});

test('shareable diagnostic report hides user home while local reference keeps real operational paths',async()=>{
  const root=await tmp();const fakeHome=path.join(root,'Users','Pessoa');const outputRoot=path.join(fakeHome,'Downloads','Cursos');await fs.mkdir(outputRoot,{recursive:true});
  const diag=new RunDiagnostics({outputRoot,command:'download',runId:'path-private',env:{HOME:fakeHome},shareHomeDir:fakeHome});await diag.start({logger:new RunnerLogger()});
  diag.setContext({outputRoot,courseRoot:path.join(outputRoot,'Curso X')});diag.setConfiguration({runtime:{outputRoot,profileDir:path.join(fakeHome,'AppData','Local','XCursos')},limits:{downloadRetries:3}});diag.addArtifact('example',path.join(outputRoot,'Curso X','_xcursos-runner','runner.log'));
  await diag.phase('COMMAND','START');await diag.finalize({status:'COMPLETE',ok:true,exitCode:0});
  const reportText=await fs.readFile(diag.reportJsonPath,'utf8');const markdown=await fs.readFile(diag.reportMarkdownPath,'utf8');const ref=diag.reference();
  assert.doesNotMatch(reportText,new RegExp(fakeHome.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));assert.doesNotMatch(markdown,new RegExp(fakeHome.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));assert.match(reportText,/\$HOME/);
  assert.ok(ref.reportJson.startsWith(fakeHome));assert.equal(ref.reportJson,diag.reportJsonPath);
});
