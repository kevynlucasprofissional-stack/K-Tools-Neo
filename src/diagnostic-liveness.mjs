import { atomicWriteJson, sanitizeForPersistence } from './utils.mjs';

const PROGRESS_EVENT=/(?:RUN_STARTED|PHASE|INSPECT|MEDIA|DOWNLOAD|VERIFY|COMMIT|NAV|POSITION|AUDIT|CHECKPOINT|RETRY)/i;
const SUBPROCESS_END_EVENT=/^SUBPROCESS_(?:END|ERROR|TIMEOUT|ABORTED)$/i;

function numberOrNull(value){const n=Number(value);return Number.isFinite(n)?n:null;}
function positionFrom(value){const n=Number(value);return Number.isInteger(n)?n:null;}
function safeMemory(memoryUsageFn){try{const value=memoryUsageFn?.()||{};return sanitizeForPersistence({rss:numberOrNull(value.rss),heapUsed:numberOrNull(value.heapUsed),heapTotal:numberOrNull(value.heapTotal),external:numberOrNull(value.external)});}catch{return null;}}

export class DiagnosticLiveness {
  constructor({
    runId=null,
    pid=process.pid,
    nowFn=Date.now,
    memoryUsageFn=()=>process.memoryUsage(),
    stallThresholdMs=5*60*1000,
    eventLoopDelayWarnMs=2_000,
    heartbeatIntervalMs=30_000,
    filePath=null,
  }={}){
    this.runId=runId;this.pid=pid;this.nowFn=nowFn;this.memoryUsageFn=memoryUsageFn;
    this.stallThresholdMs=Math.max(1,Number(stallThresholdMs)||5*60*1000);this.eventLoopDelayWarnMs=Math.max(0,Number(eventLoopDelayWarnMs)||2_000);this.heartbeatIntervalMs=Math.max(1_000,Number(heartbeatIntervalMs)||30_000);this.filePath=filePath;
    const now=Number(this.nowFn());this.startedAtMs=now;this.lastEventAtMs=now;this.lastProgressAtMs=now;this.lastHeartbeatAtMs=null;this.lastEventLoopDelayMs=0;
    this.stage=null;this.position=null;this.operation=null;this.waiting=null;this.activeSubprocess=null;this.timer=null;this.nextExpectedAtMs=null;this.lastPersistFailure=null;
  }

  configure({filePath,runId,pid}={}){if(filePath!==undefined)this.filePath=filePath;if(runId!==undefined)this.runId=runId;if(pid!==undefined)this.pid=pid;return this;}

  noteProgress({stage=null,position=null,operation=null}={}){
    const now=Number(this.nowFn());this.lastEventAtMs=now;this.lastProgressAtMs=now;
    if(stage!=null)this.stage=String(stage);if(position!=null&&positionFrom(position)!=null)this.position=positionFrom(position);if(operation!=null)this.operation=String(operation);
    this.waiting=null;return this.snapshot();
  }

  setWaiting(reason,{untilMs=null,data=null}={}){
    this.lastEventAtMs=Number(this.nowFn());this.waiting=sanitizeForPersistence({reason:String(reason||'WAITING'),untilMs:numberOrNull(untilMs),data});return this.snapshot();
  }

  noteSubprocessStart({pid=null,command=null,name=null}={}){
    const now=Number(this.nowFn());this.lastEventAtMs=now;this.lastProgressAtMs=now;this.activeSubprocess=sanitizeForPersistence({pid:positionFrom(pid),command:command?String(command):null,name:name?String(name):null,startedAt:new Date(now).toISOString()});return this.snapshot();
  }

  noteSubprocessEnd({pid=null}={}){
    this.lastEventAtMs=Number(this.nowFn());if(pid==null||this.activeSubprocess?.pid==null||Number(pid)===Number(this.activeSubprocess.pid))this.activeSubprocess=null;return this.snapshot();
  }

  noteEvent(event={}){
    const now=Number(this.nowFn());this.lastEventAtMs=now;const name=String(event?.event||'LOG');const data=event?.data||{};const context=event?.context||{};const position=positionFrom(data.position??context.position);
    if(/^SUBPROCESS_START$/i.test(name))this.noteSubprocessStart({pid:data.pid,command:data.command||data.executable||data.args?.[0],name:data.name});
    else if(SUBPROCESS_END_EVENT.test(name))this.noteSubprocessEnd({pid:data.pid});
    if(/^RETRY$/i.test(name)){
      this.noteProgress({stage:'RETRY',position,operation:'BACKOFF'});const delay=numberOrNull(data.delayMs);this.setWaiting('RETRY_BACKOFF',{untilMs:delay==null?null:now+delay,data:{delayMs:delay}});
    }else if(PROGRESS_EVENT.test(name)){
      this.noteProgress({stage:String(event?.scope||name),position,operation:name});
    }else if(position!=null)this.position=position;
    return this.snapshot();
  }

  classify(now){
    const msSinceProgress=Math.max(0,now-this.lastProgressAtMs);const waitingActive=Boolean(this.waiting&&(this.waiting.untilMs==null||now<=this.waiting.untilMs));
    if(this.activeSubprocess&&msSinceProgress>=this.stallThresholdMs)return'ACTIVE_LONG_OPERATION';
    if(waitingActive)return'EXPECTED_WAIT';
    if(msSinceProgress>=this.stallThresholdMs)return'POSSIBLE_STALL';
    return'HEALTHY';
  }

  snapshot(){
    const now=Number(this.nowFn());return sanitizeForPersistence({
      schemaVersion:1,runId:this.runId,pid:this.pid,timestamp:new Date(now).toISOString(),status:this.classify(now),stage:this.stage,position:this.position,operation:this.operation,
      lastEventAt:new Date(this.lastEventAtMs).toISOString(),lastProgressAt:new Date(this.lastProgressAtMs).toISOString(),msSinceEvent:Math.max(0,now-this.lastEventAtMs),msSinceProgress:Math.max(0,now-this.lastProgressAtMs),
      waiting:this.waiting,activeSubprocess:this.activeSubprocess,eventLoopDelayMs:this.lastEventLoopDelayMs,eventLoopStatus:this.lastEventLoopDelayMs>=this.eventLoopDelayWarnMs?'DELAYED':'NORMAL',memory:safeMemory(this.memoryUsageFn),lastPersistFailure:this.lastPersistFailure,
    });
  }

  async persist(filePath=this.filePath){
    if(!filePath)return{ok:false,skipped:true,reason:'NO_FILE_PATH'};
    try{await atomicWriteJson(filePath,this.snapshot());this.lastPersistFailure=null;return{ok:true,filePath};}
    catch(error){this.lastPersistFailure=sanitizeForPersistence({code:error?.code||'LIVENESS_WRITE_FAILED',message:error?.message||String(error)});return{ok:false,filePath,error:this.lastPersistFailure};}
  }

  async heartbeat({expectedAtMs=null,persist=true}={}){
    const now=Number(this.nowFn());if(expectedAtMs!=null)this.lastEventLoopDelayMs=Math.max(0,now-Number(expectedAtMs));this.lastHeartbeatAtMs=now;const snap=this.snapshot();if(persist)await this.persist();return snap;
  }

  start({filePath=this.filePath,intervalMs=this.heartbeatIntervalMs}={}){
    if(filePath!==undefined)this.filePath=filePath;if(this.timer)return this;
    const every=Math.max(1_000,Number(intervalMs)||this.heartbeatIntervalMs);this.nextExpectedAtMs=Number(this.nowFn())+every;
    this.timer=setInterval(()=>{const expected=this.nextExpectedAtMs;this.nextExpectedAtMs+=every;void this.heartbeat({expectedAtMs:expected,persist:true});},every);this.timer.unref?.();return this;
  }

  async stop({persist=true}={}){if(this.timer){clearInterval(this.timer);this.timer=null;}if(persist)await this.heartbeat({persist:true});return this.snapshot();}
}
