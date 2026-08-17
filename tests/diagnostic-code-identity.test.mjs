import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import * as versionInfo from '../src/version-info.mjs';
import { RunDiagnostics } from '../src/run-diagnostics.mjs';
import { RunnerLogger } from '../src/logger.mjs';

async function tmp(){return await fs.mkdtemp(path.join(os.tmpdir(),'xc-code-id-'));}

async function fakeInstall({git=false}={}){
  const root=await tmp();await fs.writeFile(path.join(root,'package.json'),JSON.stringify({name:'xcursos-runner',version:'9.8.7'}));
  if(git){const sha='1234567890abcdef1234567890abcdef12345678';await fs.mkdir(path.join(root,'.git','refs','heads'),{recursive:true});await fs.writeFile(path.join(root,'.git','HEAD'),'ref: refs/heads/main\n');await fs.writeFile(path.join(root,'.git','refs','heads','main'),`${sha}\n`);return{root,sha};}
  return{root,sha:null};
}

test('code identity resolves a trustworthy git checkout without invoking git',async()=>{
  assert.equal(typeof versionInfo.resolveCodeIdentity,'function');
  const {root,sha}=await fakeInstall({git:true});const identity=await versionInfo.resolveCodeIdentity({installRoot:root,env:{}});
  assert.equal(identity.packageVersion,'9.8.7');assert.equal(identity.runnerVersion,'9.8.7');assert.equal(identity.commit,sha);assert.equal(identity.branch,'main');assert.equal(identity.sourceIdentity,'GIT_COMMIT');
});

test('code identity explicitly falls back to package version when git identity is unavailable',async()=>{
  assert.equal(typeof versionInfo.resolveCodeIdentity,'function');
  const {root}=await fakeInstall();const identity=await versionInfo.resolveCodeIdentity({installRoot:root,env:{}});
  assert.equal(identity.packageVersion,'9.8.7');assert.equal(identity.commit,null);assert.equal(identity.branch,null);assert.equal(identity.sourceIdentity,'PACKAGE_VERSION_ONLY');
});

test('diagnostic JSON and Markdown include the code identity that generated the run',async()=>{
  const root=await tmp();const diag=new RunDiagnostics({outputRoot:root,command:'version',runId:'identity-report',env:{}});await diag.start({logger:new RunnerLogger()});const report=await diag.finalize({status:'VERSION',ok:true,exitCode:0});
  assert.ok(report.codeIdentity);assert.equal(report.codeIdentity.runnerVersion,'4.2.6');assert.ok(report.codeIdentity.cliPath);assert.ok(report.codeIdentity.installRoot);assert.ok(['GIT_COMMIT','BUILD_ENV','PACKAGE_VERSION_ONLY'].includes(report.codeIdentity.sourceIdentity));
  const markdown=await fs.readFile(diag.reportMarkdownPath,'utf8');assert.match(markdown,/Identidade do código/i);assert.match(markdown,/4\.2\.6/);
});
