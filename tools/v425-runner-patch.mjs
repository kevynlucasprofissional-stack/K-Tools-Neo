import fs from 'node:fs';

const file='src/runner.mjs';
let source=fs.readFileSync(file,'utf8');

const importNeedle="import { correlateMediaObjects } from './network-media-observer.mjs';";
const importReplacement=`${importNeedle}\nimport { isSafeDownloadMedia } from './parser.mjs';`;
if(!source.includes("import { isSafeDownloadMedia } from './parser.mjs';")){
  if(!source.includes(importNeedle))throw new Error('runner import anchor not found');
  source=source.replace(importNeedle,importReplacement);
}

const oldRefresh="const REFRESHABLE_SIGNED_MEDIA_FAILURES=new Set(['HTTP_403','HTTP_429','HTTP_5XX','NETWORK_RESET','NETWORK_TIMEOUT','DNS_ERROR','TLS_ERROR','PROCESS_TIMEOUT']);";
const newRefresh="const REFRESHABLE_SIGNED_MEDIA_FAILURES=new Set(['HTTP_403','HTTP_429','HTTP_5XX','NETWORK_RESET','NETWORK_TIMEOUT','DNS_ERROR','TLS_ERROR','PROCESS_TIMEOUT','YTDLP_FAILED']);";
if(source.includes(oldRefresh))source=source.replace(oldRefresh,newRefresh);
else if(!source.includes(newRefresh))throw new Error('refreshable failure anchor not found');

const start=source.indexOf('  async processPosition(position){');
const end=source.indexOf('\n  async navigateSequential',start);
if(start<0||end<0)throw new Error('processPosition boundaries not found');

const replacement=`  shouldWaitForMedia(lesson){
    if(isSafeDownloadMedia(lesson))return false;
    return Boolean(typeof this.browser.waitForMediaReady==='function'||lesson?.hasVideoElement||lesson?.hasTrustedPlayerIframe||lesson?.hasUntrustedIframe||lesson?.mediaNotReady);
  }

  assertLessonIdentity(lesson,position,{context='MEDIA'}={}){
    if(!lesson)throw new RunnerError('A inspeção da aula não retornou metadata.',{code:'LESSON_INSPECT_FAILED',details:{position,context}});
    if(Number(lesson.currentPosition)!==Number(position))throw new RunnerError(\`Posição observada \${lesson.currentPosition}, esperada \${position}.\`,{code:'POSITION_MISMATCH',details:{position,observed:lesson.currentPosition,context}});
    if(!sameCourse(lesson.courseName,this.courseName))throw new RunnerError(\`Página mudou para outro curso: \${lesson.courseName}\`,{code:'COURSE_IDENTITY_MISMATCH',details:{position,context}});
    if(Number(lesson.totalPositions)!==Number(this.total))throw new RunnerError(\`TOTAL mudou de \${this.total} para \${lesson.totalPositions}.\`,{code:'TOTAL_CHANGED',details:{position,context}});
    return lesson;
  }

  async waitForProvenMedia(initialLesson,{position,force=false}={}){
    let lesson=this.assertLessonIdentity(initialLesson,position,{context:'MEDIA_READY_INITIAL'});
    if(isSafeDownloadMedia(lesson))return lesson;
    if(!force&&!this.shouldWaitForMedia(lesson))return lesson;

    if(typeof this.browser.waitForMediaReady==='function'){
      const supplied=await this.browser.waitForMediaReady(this.workPage,{position,timeoutMs:this.limits.mediaReadyTimeoutMs,pollMs:this.limits.mediaReadyPollMs});
      if(supplied){lesson=this.assertLessonIdentity(supplied,position,{context:'MEDIA_READY_BROWSER'});if(isSafeDownloadMedia(lesson))return lesson;}
    }

    const timeout=Math.max(0,Number(this.limits.mediaReadyTimeoutMs)||0);
    const poll=Math.max(1,Number(this.limits.mediaReadyPollMs)||250);
    const deadline=Date.now()+timeout;
    while(Date.now()<deadline){
      await this.sleepFn(Math.min(poll,Math.max(1,deadline-Date.now())));
      lesson=this.assertLessonIdentity(await this.browser.inspectLesson(this.workPage),position,{context:'MEDIA_READY_POLL'});
      if(isSafeDownloadMedia(lesson))return lesson;
    }
    return {...lesson,mediaNotReady:true};
  }

  async refreshMediaForPosition(position,lesson,{failureCode='UNKNOWN'}={}){
    const previousMediaUrl=lesson?.videoUrl||null;
    this.runtimeStats.recordMediaRefresh();
    await this.logger.log('RECOVERY','Refreshing same lesson media',{position,failureCode});
    const refreshedPage=await this.browser.refreshSameLesson(this.workPage);
    if(!refreshedPage)return null;
    this.workPage=refreshedPage;
    let refreshed=this.assertLessonIdentity(await this.browser.inspectLesson(this.workPage),position,{context:'MEDIA_REFRESH'});
    refreshed=await this.waitForProvenMedia(refreshed,{position,force:true});
    if(!isSafeDownloadMedia(refreshed)||!refreshed.videoUrl)return null;
    if(previousMediaUrl){
      const correlation=correlateMediaObjects(previousMediaUrl,refreshed.videoUrl);
      if(correlation.comparable&&!correlation.sameObject)throw new RunnerError('Refresh de mídia apontou para outro objeto de vídeo.',{code:'MEDIA_REFRESH_OBJECT_CHANGED',details:{position,previousObjectFingerprint:correlation.networkObjectFingerprint,refreshedObjectFingerprint:correlation.liveObjectFingerprint}});
    }
    return refreshed;
  }

  async processPosition(position){
    let existing=this.state.get(position); const repair=this.repairPositions.has(position);
    if(existing && RETRYABLE_FAILURE_STATUSES.has(existing.status))existing=null;
    if(existing && !repair){await this.logger.log(\`LESSON \${position}/\${this.total}\`,'Already terminal; skipping',{status:existing.status});return {status:existing.status,skipped:true,page:this.workPage,lesson:null,outputFile:existing.outputFile||null,validation:existing.validation||null};}
    let lesson=this.assertLessonIdentity(await this.ensurePageAt(position),position,{context:'PROCESS_POSITION'});
    lesson=await this.waitForProvenMedia(lesson,{position});
    this.assertLessonIdentity(lesson,position,{context:'PROCESS_MEDIA_READY'});
    await this.rememberNavigation(lesson);
    await this.logger.log(\`LESSON \${position}/\${this.total}\`,'Inspecting',{lesson:lesson.lessonTitle,module:lesson.moduleName,mediaType:lesson.mediaType,mediaSourceConfidence:lesson.mediaSourceConfidence||null});

    let paths=this.downloader.buildPaths({root:this.outputRoot,courseName:this.courseName,moduleName:lesson.moduleName,lessonTitle:lesson.lessonTitle,position,total:this.total});
    if(repair && existing?.outputFile){const parsed=path.parse(existing.outputFile);paths={...paths,moduleDir:parsed.dir,baseName:parsed.name,template:path.join(parsed.dir,\`\${parsed.name}.%(ext)s\`) };}
    else {
      const inFlight=this.state.getInFlight(position);
      if(inFlight?.relativeOutputBase){
        const base=this.state.resolveInFlightBase(inFlight);
        const parsed=path.parse(base);
        paths={...paths,moduleDir:parsed.dir,baseName:parsed.base,template:path.join(parsed.dir,\`\${parsed.base}.%(ext)s\`)};
      }
    }
    let attempts=0, status, outputFile=null, validation=null, downloadFailure=null, verifyFailureCode=null;

    if(lesson.drmDetected && (!lesson.videoUrl || ['HLS','DASH'].includes(lesson.mediaType))){status='DRM_PROTECTED';await this.logger.log(\`LESSON \${position}/\${this.total}\`,'DRM marker detected; no bypass attempted');}
    else if(!isSafeDownloadMedia(lesson)) {
      if(this.shouldWaitForMedia(lesson)||lesson.videoUrl){
        status='MEDIA_NOT_READY';verifyFailureCode='MEDIA_NOT_READY';
        await this.state.appendError({scope:'MEDIA',position,status,message:'A página da aula carregou, mas nenhuma mídia comprovada ficou pronta dentro da janela segura.',mediaType:lesson.mediaType||'NONE',mediaSourceConfidence:lesson.mediaSourceConfidence||'UNTRUSTED',mediaDiagnostics:this.browser.mediaDiagnostics?.(this.workPage)||null});
      }else{
        status=lesson.hasMaterialsLinks?'NO_VIDEO':'MEDIA_NOT_FOUND';
      }
      await this.logger.log(\`LESSON \${position}/\${this.total}\`,'No proven downloadable lesson media found',{status,mediaType:lesson.mediaType||'NONE'});
    }
    else {
      await fs.mkdir(paths.moduleDir,{recursive:true});
      if(!repair && !this.state.getInFlight(position)){
        await this.state.setInFlight({position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,lessonUrl:lesson.pageUrl||this.workPage.url,relativeOutputBase:path.relative(this.state.courseDir,path.join(paths.moduleDir,paths.baseName))});
      }
      let existingFile=await this.downloader.findExistingFinal(paths.moduleDir,paths.baseName);
      if(existingFile){
        try{validation=await this.downloader.validateVideo(existingFile,{signal:this.shutdown.signal});status='ALREADY_PRESENT';outputFile=existingFile;await this.logger.log('VERIFY','Existing file valid',{position,duration:validation.duration});}
        catch(error){
          let quarantine;
          if(typeof this.downloader.quarantineCorrupt==='function') quarantine=await this.downloader.quarantineCorrupt(existingFile);
          else {quarantine=\`\${existingFile}.corrupt-\${Date.now()}\`;try{await fs.rename(existingFile,quarantine);}catch(renameError){throw new RunnerError(\`Falha ao isolar arquivo corrompido: \${existingFile}\`,{code:'CORRUPT_FILE_QUARANTINE_FAILED',cause:renameError});}}
          await this.state.appendError({scope:'VERIFY',position,status:'CORRUPT_EXISTING_FILE',failureCode:error?.code||null,message:String(error?.message||error),quarantine});
          existingFile=null;
        }
      }
      if(!status){
        let lastProgressBucket=-1;
        const executeDownload=async({cleanStart=false}={})=>{attempts++;return await this.downloader.download({mediaUrl:lesson.videoUrl,refererUrl:lesson.pageUrl||this.workPage.url,paths,signal:this.shutdown.signal,cleanStart,onProgress:p=>{this.runtimeStats.recordDownloadProgress({speed:p.speedText});const bucket=Math.floor((p.percent||0)/5);if(bucket!==lastProgressBucket){lastProgressBucket=bucket;this.progressSink?.(\`[DOWNLOAD \${position}/\${this.total}] \${Number(p.percent||0).toFixed(1)}%\${p.speedText?\` @ \${p.speedText}\`:''}\${p.eta?\` ETA \${p.eta}\`:''}\`);}}});};
        let refreshAttempts=0;let cleanStart=false;
        while(!status){
          const dl=await executeDownload({cleanStart});cleanStart=false;
          if(!dl.ok){
            downloadFailure=dl;verifyFailureCode=null;
            if(shouldRefreshSignedMedia(dl,lesson)&&refreshAttempts<this.limits.mediaRefreshRetries){
              refreshAttempts++;
              const refreshed=await this.refreshMediaForPosition(position,lesson,{failureCode:dl.failureCode||dl.kind});
              if(refreshed){lesson=refreshed;continue;}
            }
            status=dl.kind==='DRM'?'DRM_PROTECTED':'DOWNLOAD_FAILED';
            await this.state.appendError({scope:'DOWNLOAD',position,status,message:\`yt-dlp: \${dl.kind}\`,failureCode:dl.failureCode||null,exitCode:dl.code??null,diagnosticTail:dl.diagnosticTail||null,mediaDiagnostics:this.browser.mediaDiagnostics?.(this.workPage)||null});
            await this.logger.log('DOWNLOAD','Download failed',{position,status,failureCode:dl.failureCode||null,diagnosticTail:dl.diagnosticTail||null});
            break;
          }

          downloadFailure=null;outputFile=dl.finalPath;
          try{
            validation=await this.downloader.validateVideo(outputFile,{signal:this.shutdown.signal});status='DOWNLOADED';verifyFailureCode=null;
            await this.logger.log('VERIFY',\`ffprobe OK — \${Math.round(validation.duration)}s\`,{position,size:validation.size,codec:validation.codec});
          }catch(error){
            verifyFailureCode=String(error?.code||'VERIFY_FAILED');
            let quarantine=null;try{quarantine=await this.downloader.quarantineCorrupt(outputFile);}catch{}
            await this.state.appendError({scope:'VERIFY',position,status:'VERIFY_FAILED',failureCode:verifyFailureCode,message:String(error?.message||error),outputFile,quarantine,mediaDiagnostics:this.browser.mediaDiagnostics?.(this.workPage)||null});
            outputFile=null;validation=null;
            if(lesson.isSignedDirectMp4&&lesson.mediaType==='DIRECT_MP4'&&refreshAttempts<this.limits.mediaRefreshRetries){
              refreshAttempts++;
              const refreshed=await this.refreshMediaForPosition(position,lesson,{failureCode:verifyFailureCode});
              if(refreshed){lesson=refreshed;cleanStart=true;continue;}
            }
            status='VERIFY_FAILED';
          }
        }
      }
    }

    if(RETRYABLE_FAILURE_STATUSES.has(status)){
      const failureCode=downloadFailure?.failureCode||verifyFailureCode||null;
      await this.state.clearInFlight(position);
      await this.state.setWorkPage(lesson.pageUrl||this.workPage.url);
      await this.logger.log('RETRYABLE',\`Position \${position} remains pending\`,{status,failureCode});
      return {status,skipped:false,retryable:true,retryError:{code:status,failureCode},failureCode,page:this.workPage,lesson,outputFile:null,validation:null};
    }

    if(repair && existing){
      if(status==='DOWNLOADED' || status==='ALREADY_PRESENT'){
        this.repairPositions.delete(position); await this.state.appendError({scope:'STATE',position,status:'FILE_REPAIRED',message:'Arquivo restaurado e validado; manifesto original preservado.'});
      } else {
        throw new RunnerError(\`Reparo da posição \${position} falhou com \${status}.\`,{code:'REPAIR_FAILED'});
      }
    } else {
      await this.state.commit({position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,lessonUrl:lesson.pageUrl||this.workPage.url,status,outputFile,attempts,validation});
    }
    await this.logger.log('COMMIT',\`Position \${position} saved\`,{status});
    return {status,skipped:false,page:this.workPage,lesson,outputFile,validation};
  }
`;

source=source.slice(0,start)+replacement+source.slice(end);
fs.writeFileSync(file,source);
console.log('runner.mjs patched for V4.2.5 media readiness/recovery');
