import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const packageJson=fileURLToPath(new URL('../package.json',import.meta.url));
const installRoot=path.dirname(packageJson);
const cliPath=fileURLToPath(new URL('./cli.mjs',import.meta.url));
const SHA40=/^[0-9a-f]{40}$/i;

async function readText(filePath){try{return (await fs.readFile(filePath,'utf8')).trim();}catch{return null;}}

async function resolveGitDir(root){
  const dotGit=path.join(root,'.git');
  try{
    const stat=await fs.stat(dotGit);
    if(stat.isDirectory())return dotGit;
    if(stat.isFile()){
      const text=await readText(dotGit);const match=/^gitdir:\s*(.+)$/i.exec(text||'');
      if(match)return path.resolve(root,match[1].trim());
    }
  }catch{}
  return null;
}

async function packedRef(gitDir,refName){
  const text=await readText(path.join(gitDir,'packed-refs'));if(!text)return null;
  for(const raw of text.split(/\r?\n/)){
    const line=raw.trim();if(!line||line.startsWith('#')||line.startsWith('^'))continue;
    const [sha,name]=line.split(/\s+/,2);if(name===refName&&SHA40.test(sha||''))return sha.toLowerCase();
  }
  return null;
}

async function resolveGitIdentity(root){
  const gitDir=await resolveGitDir(root);if(!gitDir)return null;
  const head=await readText(path.join(gitDir,'HEAD'));if(!head)return null;
  if(SHA40.test(head))return{commit:head.toLowerCase(),branch:null};
  const match=/^ref:\s*(.+)$/i.exec(head);if(!match)return null;
  const refName=match[1].trim();
  const direct=await readText(path.join(gitDir,...refName.split('/')));
  const commit=SHA40.test(direct||'')?direct.toLowerCase():await packedRef(gitDir,refName);
  if(!commit)return null;
  return{commit,branch:refName.startsWith('refs/heads/')?refName.slice('refs/heads/'.length):null};
}

function buildIdentity(env={}){
  const rawCommit=env.XCURSOS_BUILD_COMMIT||env.GITHUB_SHA||null;if(!SHA40.test(String(rawCommit||'')))return null;
  const branch=env.XCURSOS_BUILD_BRANCH||env.GITHUB_REF_NAME||null;
  return{commit:String(rawCommit).toLowerCase(),branch:branch?String(branch):null};
}

export async function resolveCodeIdentity({installRoot:root=installRoot,env=process.env}={}){
  const resolvedRoot=path.resolve(root);const pkgPath=path.join(resolvedRoot,'package.json');
  const pkg=JSON.parse(await fs.readFile(pkgPath,'utf8'));const version=String(pkg.version);
  const build=buildIdentity(env);const git=build?null:await resolveGitIdentity(resolvedRoot);const source=build||git;
  return{
    packageVersion:version,runnerVersion:version,
    commit:source?.commit||null,branch:source?.branch||null,
    sourceIdentity:build?'BUILD_ENV':git?'GIT_COMMIT':'PACKAGE_VERSION_ONLY',
    cliPath:path.join(resolvedRoot,'src','cli.mjs'),installRoot:resolvedRoot,packageJson:pkgPath,nodeVersion:process.version,
  };
}

export async function getRunnerInfo(){
  const identity=await resolveCodeIdentity({installRoot,env:process.env});
  return{version:identity.runnerVersion,runnerVersion:identity.runnerVersion,cliPath,installRoot,packageJson,node:process.version,commit:identity.commit,branch:identity.branch,sourceIdentity:identity.sourceIdentity,codeIdentity:{...identity,cliPath,installRoot,packageJson}};
}
