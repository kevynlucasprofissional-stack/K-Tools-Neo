function fmt(ms){if(ms==null)return null;const sec=Math.max(0,Math.round(ms/1000));const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60),s=sec%60;return`${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;}
function ints(values=[]){return new Set((Array.isArray(values)?values:[]).map(Number).filter(Number.isInteger));}

export class RuntimeStats {
  constructor({total=0,nowFn=Date.now}={}){
    this.total=Number(total)||0;this.nowFn=nowFn;this.startedAt=Number(nowFn());this.current=null;this.samples=[];
    this.coveragePositions=new Set();this.healthyPositions=new Set();this.downloadedPositions=new Set();this.identityAware=true;
    this.baseProcessed=0;this.baseHealthy=0;this.baseDownloadsSucceeded=0;this.runOperations=0;
    this.downloadsFailed=0;this.retries=0;this.retryPending=0;this.browserReconnects=0;this.mediaRefreshes=0;this.repositionSteps=0;this.downloadBytes=0;this.lastDownloadSpeed=null;
  }
  setTotal(total){this.total=Number(total)||0;}
  seed({processed=0,healthy=0,downloadsSucceeded=0,downloadBytes=0,completedPositions=null,healthyPositions=null,downloadedPositions=null}={}){
    const hasIdentity=Array.isArray(completedPositions)||Array.isArray(healthyPositions)||Array.isArray(downloadedPositions);
    this.identityAware=hasIdentity;
    if(hasIdentity){
      this.coveragePositions=ints(completedPositions);this.healthyPositions=ints(healthyPositions);this.downloadedPositions=ints(downloadedPositions);
      this.baseProcessed=0;this.baseHealthy=0;this.baseDownloadsSucceeded=0;
    }else{
      this.coveragePositions.clear();this.healthyPositions.clear();this.downloadedPositions.clear();
      this.baseProcessed=Math.max(0,Number(processed)||0);this.baseHealthy=Math.max(0,Number(healthy)||0);this.baseDownloadsSucceeded=Math.max(0,Number(downloadsSucceeded)||0);
    }
    this.downloadBytes=Math.max(0,Number(downloadBytes)||0);return this.snapshot();
  }
  beginLesson(position,title=null){this.current={position:Number(position),title:title||null,startedAt:Number(this.nowFn())};}
  finishLesson({status=null,healthy=false,bytes=0,speed=null}={}){
    const current=this.current;this.runOperations++;
    let isNewCoverage=true;const position=Number(current?.position);
    if(this.identityAware&&Number.isInteger(position)){
      isNewCoverage=!this.coveragePositions.has(position);
      if(isNewCoverage)this.coveragePositions.add(position);
      if(isNewCoverage&&healthy)this.healthyPositions.add(position);
      if(isNewCoverage&&['DOWNLOADED','ALREADY_PRESENT'].includes(status))this.downloadedPositions.add(position);
    }else if(isNewCoverage){
      this.baseProcessed++;if(healthy)this.baseHealthy++;if(['DOWNLOADED','ALREADY_PRESENT'].includes(status))this.baseDownloadsSucceeded++;
    }
    if(current&&isNewCoverage){const d=Math.max(0,Number(this.nowFn())-current.startedAt);this.samples.push(d);if(this.samples.length>100)this.samples.shift();}
    if(isNewCoverage)this.downloadBytes+=Math.max(0,Number(bytes)||0);
    if(speed!=null)this.lastDownloadSpeed=speed;this.current=null;
  }
  recordFailure(){this.downloadsFailed++;}
  recordRetry(){this.retries++;}
  setRetryPending(n){this.retryPending=Math.max(0,Number(n)||0);}
  recordBrowserReconnect(){this.browserReconnects++;}
  recordMediaRefresh(){this.mediaRefreshes++;}
  recordRepositionStep(){this.repositionSteps++;}
  recordDownloadProgress({speed=null}={}){if(speed!=null)this.lastDownloadSpeed=speed;}
  snapshot(){
    const elapsedMs=Math.max(0,Number(this.nowFn())-this.startedAt);
    const coverageProcessed=this.baseProcessed+this.coveragePositions.size;
    const healthy=this.baseHealthy+this.healthyPositions.size;
    const downloadsSucceeded=this.baseDownloadsSucceeded+this.downloadedPositions.size;
    const averageLessonDurationMs=this.samples.length?Math.round(this.samples.reduce((a,b)=>a+b,0)/this.samples.length):null;
    const remaining=Math.max(0,this.total-coverageProcessed);const etaMs=averageLessonDurationMs==null?null:averageLessonDurationMs*remaining;
    return{total:this.total,processed:coverageProcessed,coverageProcessed,runOperations:this.runOperations,healthy,currentPosition:this.current?.position??null,currentTitle:this.current?.title??null,downloadsSucceeded,downloadsFailed:this.downloadsFailed,retries:this.retries,retryPending:this.retryPending,browserReconnects:this.browserReconnects,mediaRefreshes:this.mediaRefreshes,repositionSteps:this.repositionSteps,elapsedMs,elapsed:fmt(elapsedMs),averageLessonDurationMs,downloadBytes:this.downloadBytes,downloadSpeed:this.lastDownloadSpeed,etaMs,ETA:fmt(etaMs)};
  }
  render(){const s=this.snapshot();return`[STATS] ${s.coverageProcessed}/${s.total} | ops=${s.runOperations} | retry=${s.retryPending} | elapsed=${s.elapsed}${s.ETA?` | ETA=${s.ETA}`:''}`;}
}
