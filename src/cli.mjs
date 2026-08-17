#!/usr/bin/env node
import { parseArgs } from 'node:util';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { pathToFileURL } from 'node:url';
import { AppConfigStore } from './config.mjs';
import { PlaywrightBrowser } from './playwright-browser.mjs';
import { HumanChromeLauncher } from './chrome-launcher.mjs';
import { probeCurrentLesson, diagnoseReposition, downloadCurrentLesson, downloadRange, downloadCourse } from './runner.mjs';
import { getRunnerInfo } from './version-info.mjs';
import { persistObservedNavigation } from './observed-navigation.mjs';
import { runDoctor } from './doctor.mjs';
import { safeError, sanitizeForPersistence } from './utils.mjs';
import { StateStore, discoverRecentState } from './state.mjs';
import { MediaDownloader } from './downloader.mjs';
import { startCliDiagnostics, finalizeCliDiagnostics } from './cli-diagnostics.mjs';
import { createObservedProcessRunner } from './process-observer.mjs';

process.stdout.setDefaultEncoding?.('utf8');
process.stderr.setDefaultEncoding?.('utf8');

const HELP=`XCursos Runner V4.2.4 — Node + Playwright CDP + Chrome humano + CLI\n\nComandos:\n  xcursos browser [--url URL]        Abre/reusa o Chrome dedicado com CDP local\n  xcursos login [--url URL]          Abre Chrome, permite Cloudflare/login humano e salva a aula atual\n  xcursos probe [--url URL]          Conecta ao Chrome aberto e inspeciona a aula sem baixar\n  xcursos current [--url URL]        Baixa/valida somente a aula atual\n  xcursos range --start N --end M    Processa intervalo determinístico\n  xcursos download [--url URL]       Baixa o curso inteiro (primeira execução deve começar na aula 1)\n  xcursos status                     Mostra configuração e último estado conhecido\n  xcursos doctor                     Verifica Node, playwright-core, Chrome, CDP, yt-dlp e ffprobe\n  xcursos version                    Mostra versão e caminhos reais da instalação\n  xcursos diagnose-reposition --target N --json  Planeja reposicionamento sem navegar\n  xcursos config --output DIR        Altera diretório de saída\n  xcursos config --chrome PATH       Define chrome.exe manualmente\n  xcursos config --port 9222         Altera porta CDP local\n\nOpções comuns:\n  --url URL            URL exata de uma aula XCursos\n  --output DIR         Sobrescreve diretório de saída nesta execução\n  --chrome PATH        Sobrescreve caminho do Google Chrome nesta execução\n  --port N             Sobrescreve porta CDP local nesta execução\n  --no-resume          Inicia novo manifesto para o curso\n  --json               Saída somente JSON\n`;

export function parseCli(argv=process.argv.slice(2)){
  const command=argv[0]||'help';const rest=argv.slice(1);
  const {values}=parseArgs({args:rest,allowPositionals:true,strict:false,options:{
    url:{type:'string'},output:{type:'string'},start:{type:'string'},end:{type:'string'},target:{type:'string'},chrome:{type:'string'},port:{type:'string'},
    resume:{type:'boolean',default:true},json:{type:'boolean',default:false},help:{type:'boolean',short:'h'},
  }});
  if(rest.includes('--no-resume'))values.resume=false;
  return{command,options:values};
}

function printJson(value){process.stdout.write(`${JSON.stringify(sanitizeForPersistence(value),null,2)}\n`);}
function printHuman(value){if(typeof value==='string'){console.log(value);return;}console.log(JSON.stringify(sanitizeForPersistence(value),null,2));}

function runtimeConfig(config,options){
  const port=options.port!=null?Number(options.port):Number(config.cdpPort||9222);
  if(!Number.isInteger(port)||port<1024||port>65535)throw Object.assign(new Error('`--port` deve ser um inteiro entre 1024 e 65535.'),{code:'CDP_PORT_INVALID'});
  return{
    profileDir:config.profileDir,
    cdpPort:port,
    cdpEndpoint:`http://127.0.0.1:${port}`,
    chromePath:options.chrome||config.chromePath||null,
    startUrl:options.url||config.lastLessonUrl||null,
    outputRoot:options.output||config.outputRoot,
    resume:options.resume!==false,
  };
}

async function openHumanChrome({runtime,logger=null,launcherFactory=null,url=null}={}){
  const Launcher=launcherFactory||HumanChromeLauncher;
  const launcher=new Launcher({profileDir:runtime.profileDir,cdpEndpoint:runtime.cdpEndpoint,chromePath:runtime.chromePath,logger});
  return await launcher.ensureRunning({url:url||'https://www.xcursos.com/'});
}

export async function login({configStore,runtime,url=null,playwrightLoader=null,launcherFactory=null,humanGate=null,logger=null}){
  await openHumanChrome({runtime,launcherFactory,logger,url:url||'https://www.xcursos.com/'});
  let rl=null;
  try{
    if(humanGate){
      await humanGate();
    }else{
      rl=readline.createInterface({input,output});
      console.log('\nUse a janela do Google Chrome normalmente. Passe pelo Cloudflare manualmente, faça login no XCursos e abra a videoaula desejada.');
      await rl.question('Quando a videoaula estiver aberta no Chrome, pressione ENTER... ');
    }
    const browser=new PlaywrightBrowser({profileDir:runtime.profileDir,cdpEndpoint:runtime.cdpEndpoint,logger,playwrightLoader});
    try{
      const ref=await browser.findOpenLessonPage();
      if(!ref)throw Object.assign(new Error('Nenhuma videoaula XCursos foi encontrada no Chrome dedicado. Abra uma aula antes de pressionar ENTER.'),{code:'LOGIN_LESSON_NOT_FOUND'});
      const lesson=await browser.inspectLesson(ref);await configStore.rememberLesson(lesson.pageUrl);await persistObservedNavigation({outputRoot:runtime.outputRoot,lesson}).catch(()=>{});
      return{ok:true,status:'LOGIN_SAVED',lesson:{courseName:lesson.courseName,lessonTitle:lesson.lessonTitle,currentPosition:lesson.currentPosition,totalPositions:lesson.totalPositions,pageUrl:lesson.pageUrl},profileDir:runtime.profileDir,cdpEndpoint:runtime.cdpEndpoint};
    }finally{await browser.close();}
  }finally{rl?.close();}
}

async function status(config){const recent=await discoverRecentState(config.outputRoot);return{ok:true,status:'STATUS',config:{profileDir:config.profileDir,outputRoot:config.outputRoot,lastLessonUrl:config.lastLessonUrl,chromePath:config.chromePath,cdpEndpoint:config.cdpEndpoint},recentState:recent?.state||null};}

async function auditRecent(config,{logger=null,processRunner=null}={}){
  const recent=await discoverRecentState(config.outputRoot);
  if(!recent?.state?.courseName||!recent.state.totalPositions)throw Object.assign(new Error('Nenhum estado de curso encontrado para auditar.'),{code:'STATE_NOT_FOUND'});
  const store=new StateStore({outputRoot:config.outputRoot,courseName:recent.state.courseName,totalPositions:Number(recent.state.totalPositions),logger});
  await store.initialize({resume:true,workPageUrl:recent.state.workPageUrl});const dl=new MediaDownloader({logger,...(processRunner?{processRunner}:{})});await dl.preflight();const audit=await store.audit({validator:f=>dl.validateVideo(f)});return{ok:audit.healthyComplete,status:'AUDIT',course:recent.state.courseName,courseRoot:store.courseDir,audit};
}

export async function main(argv=process.argv.slice(2),deps={}){
  const parsed=parseCli(argv);if(parsed.command==='help'||parsed.options.help){console.log(HELP);return 0;}
  const configStore=deps.configStore||new AppConfigStore();let config=await configStore.load();
  if(parsed.command==='config'){
    const patch={};if(parsed.options.output)patch.outputRoot=parsed.options.output;if(parsed.options.chrome)patch.chromePath=parsed.options.chrome;if(parsed.options.port!=null)patch.cdpPort=Number(parsed.options.port);
    if(Object.keys(patch).length)config=await configStore.save(patch);
    const lifecycle=await startCliDiagnostics({outputRoot:config.outputRoot,command:'config',argv,processRef:deps.processRef||process,env:deps.env||process.env,diagnosticsFactory:deps.diagnosticsFactory,logger:deps.logger||null,exitFn:deps.exitFn});
    try{
      const result={ok:true,status:'CONFIG',config,diagnostics:lifecycle.diagnostics.reference()};await lifecycle.diagnostics.phase('CONFIG','PASS',{updated:Object.keys(patch)});await finalizeCliDiagnostics({diagnostics:lifecycle.diagnostics,result,exitCode:0,outputRoot:config.outputRoot});parsed.options.json?printJson(result):printHuman(result);return 0;
    }finally{lifecycle.uninstallFatal();}
  }
  const runtime=runtimeConfig(config,parsed.options);
  const lifecycle=await startCliDiagnostics({outputRoot:runtime.outputRoot,command:parsed.command,argv,processRef:deps.processRef||process,env:deps.env||process.env,diagnosticsFactory:deps.diagnosticsFactory,logger:deps.logger||null,exitFn:deps.exitFn});
  const logger=lifecycle.logger;const diagnostics=lifecycle.diagnostics;const observedProcessRunner=createObservedProcessRunner({logger,...(deps.processRunner?{baseRunner:deps.processRunner}:{})});
  diagnostics.setContext({resume:runtime.resume,cdpEndpoint:runtime.cdpEndpoint,outputRoot:runtime.outputRoot});
  const runtimeDownloader=deps.downloader||new MediaDownloader({logger,processRunner:observedProcessRunner});
  const runnerRuntime={profileDir:runtime.profileDir,cdpEndpoint:runtime.cdpEndpoint,startUrl:runtime.startUrl,outputRoot:runtime.outputRoot,resume:runtime.resume,browser:deps.browser||null,downloader:runtimeDownloader,logger,enableSignalHandlers:true,progressSink:deps.progressSink||((line)=>process.stderr.write(`${line}\n`))};
  let result;
  try{
    await diagnostics.phase('COMMAND','START',{command:parsed.command});
    switch(parsed.command){
      case 'browser':result={ok:true,status:'BROWSER_READY',...(await openHumanChrome({runtime,logger,launcherFactory:deps.launcherFactory,url:parsed.options.url||'https://www.xcursos.com/'}))};break;
      case 'login':result=await login({configStore,runtime,url:parsed.options.url||null,playwrightLoader:deps.playwrightLoader,launcherFactory:deps.launcherFactory,humanGate:deps.humanGate,logger});break;
      case 'probe':result=await probeCurrentLesson({...runnerRuntime,playwrightLoader:deps.playwrightLoader});if(result?.lesson?.pageUrl){await configStore.rememberLesson(result.lesson.pageUrl);await persistObservedNavigation({outputRoot:runtime.outputRoot,lesson:result.lesson}).catch(()=>{});}break;
      case 'current':result=await downloadCurrentLesson({...runnerRuntime,playwrightLoader:deps.playwrightLoader});break;
      case 'range':{
        const start=Number(parsed.options.start),end=Number(parsed.options.end);if(!Number.isInteger(start)||!Number.isInteger(end))throw Object.assign(new Error('`range` exige --start N --end M.'),{code:'RANGE_ARGS_REQUIRED'});
        result=await downloadRange({...runnerRuntime,start,end,playwrightLoader:deps.playwrightLoader});break;
      }
      case 'download':result=await downloadCourse({...runnerRuntime,playwrightLoader:deps.playwrightLoader});break;
      case 'status':result=await status({...config,outputRoot:runtime.outputRoot,cdpEndpoint:runtime.cdpEndpoint});break;
      case 'audit':result=await auditRecent({...config,outputRoot:runtime.outputRoot},{logger,processRunner:observedProcessRunner});break;
      case 'version':result={ok:true,status:'VERSION',...(await getRunnerInfo())};break;
      case 'diagnose-reposition':{const target=Number(parsed.options.target);if(!Number.isInteger(target))throw Object.assign(new Error('`diagnose-reposition` exige --target N.'),{code:'TARGET_REQUIRED'});result=await diagnoseReposition({...runnerRuntime,target,playwrightLoader:deps.playwrightLoader});break;}
      case 'doctor':result=await runDoctor({config:{...config,outputRoot:runtime.outputRoot,chromePath:runtime.chromePath,cdpEndpoint:runtime.cdpEndpoint},playwrightLoader:deps.playwrightLoader,fetchImpl:deps.fetchImpl});break;
      default:throw Object.assign(new Error(`Comando desconhecido: ${parsed.command}`),{code:'CLI_UNKNOWN_COMMAND'});
    }
    const remembered=result?.lesson?.pageUrl||result?.workPageUrl||result?.state?.workPageUrl||null;
    if(remembered&&['probe','current','range','download'].includes(parsed.command))await configStore.rememberLesson(remembered);
    result={...result,diagnostics:diagnostics.reference()};const exitCode=result?.ok===false?2:0;
    await diagnostics.phase('COMMAND',exitCode===0?'PASS':'FAIL',{status:result?.status||null,exitCode});await finalizeCliDiagnostics({diagnostics,result,exitCode,outputRoot:runtime.outputRoot});
    parsed.options.json?printJson(result):printHuman(result);return exitCode;
  }catch(error){
    const failure={ok:false,status:'ERROR',error:safeError(error),details:sanitizeForPersistence(error?.details||null),diagnostics:diagnostics.reference()};
    await diagnostics.phase('COMMAND','FAIL',{code:error?.code||null,message:error?.message||null});await finalizeCliDiagnostics({diagnostics,result:failure,error,exitCode:2,outputRoot:runtime.outputRoot});
    parsed.options.json?printJson(failure):printHuman(failure);return 2;
  }finally{lifecycle.uninstallFatal();}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){main().then(code=>{process.exitCode=code;});}
