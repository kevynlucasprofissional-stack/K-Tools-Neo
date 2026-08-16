import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const execFileAsync=promisify(execFile);

const script=await fs.readFile(new URL('../download-all.ps1',import.meta.url),'ascii');
const installer=await fs.readFile(new URL('../install.ps1',import.meta.url),'ascii');

test('xcursos-all configures UTF-8 native/console I/O explicitly for Windows PowerShell 5.1',()=>{
  assert.match(script,/System\.Text\.UTF8Encoding/);
  assert.match(script,/\[Console\]::OutputEncoding\s*=\s*\$utf8/i);
  assert.match(script,/\[Console\]::InputEncoding\s*=\s*\$utf8/i);
  assert.match(script,/\$OutputEncoding\s*=\s*\$utf8/i);
});

test('UTF-8 hardening preserves JSON stdout separation from native progress stderr',()=>{
  assert.match(script,/xcursos download --json \| Out-String/);
  assert.doesNotMatch(script,/2>&1/);
  assert.match(script,/\$ErrorActionPreference = 'Continue'/);
});

test('operational PowerShell remains ASCII source so PS5.1 never misparses UTF-8 source bytes',async()=>{
  for(const name of ['download-all.ps1','install.ps1','uninstall.ps1']){const bytes=await fs.readFile(new URL(`../${name}`,import.meta.url));assert.equal([...bytes].some(b=>b>0x7f),false,name);}
  assert.doesNotMatch(installer,/Próxima/);
});

test('UTF-8 bytes for Portuguese navigation text round-trip exactly in Node',()=>{const text='Próxima — Ação, transição, módulo, conteúdo';assert.equal(Buffer.from(text,'utf8').toString('utf8'),text);assert.equal(Buffer.from(text,'utf8').toString('latin1').includes('Próxima'),false);});


test('real Node child preserves Portuguese stderr while JSON stdout stays independently parseable',async()=>{
  const code="process.stderr.write('Próxima — transição\\n');process.stdout.write(JSON.stringify({ok:true,text:'ação'})+'\\n')";
  const {stdout,stderr}=await execFileAsync(process.execPath,['-e',code],{encoding:'utf8'});
  assert.equal(stderr,'Próxima — transição\n');
  assert.deepEqual(JSON.parse(stdout),{ok:true,text:'ação'});
  assert.equal(stdout.includes('Próxima'),false);
});
