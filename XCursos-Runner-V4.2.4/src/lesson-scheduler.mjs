export const LessonTaskStatus=Object.freeze({READY:'READY',IN_FLIGHT:'IN_FLIGHT',RETRY_LATER:'RETRY_LATER',DONE:'DONE',BLOCKED:'BLOCKED'});
const VALID=new Set(Object.values(LessonTaskStatus));
function clone(v){return v==null?v:JSON.parse(JSON.stringify(v));}
function int(v,fallback=null){if(v==null||v==='')return fallback;const n=Number(v);return Number.isInteger(n)?n:fallback;}

export class LessonScheduler {
  constructor({total,start=1,end=null,nowFn=Date.now,schedulerVersion=1}={}){
    this.total=Math.max(0,int(total,0));this.start=Math.max(1,int(start,1));this.end=Math.min(this.total,int(end,this.total));this.nowFn=nowFn;this.schedulerVersion=schedulerVersion;this.tasks=new Map();
  }
  _base(position){return{position,lessonUrl:null,attempts:0,priority:0,status:LessonTaskStatus.READY,nextAttemptAt:null,lastError:null};}
  _merge(base,raw){if(!raw||int(raw.position)!==base.position)return base;return{...base,lessonUrl:raw.lessonUrl||base.lessonUrl,attempts:Math.max(0,int(raw.attempts,0)),priority:Number(raw.priority)||0,status:VALID.has(raw.status)?raw.status:base.status,nextAttemptAt:Number.isFinite(Number(raw.nextAttemptAt))?Number(raw.nextAttemptAt):null,lastError:clone(raw.lastError)||null};}
  reconcile({donePositions=[],repairPositions=[],checkpoint=null}={}){
    this.tasks.clear();const done=new Set([...donePositions].map(Number));const repair=new Set([...repairPositions].map(Number));
    const cpByPos=new Map();
    if(checkpoint&&Number(checkpoint.schedulerVersion)===this.schedulerVersion){
      for(const bucket of ['ready','retryLater','inFlight','blocked'])for(const raw of (Array.isArray(checkpoint[bucket])?checkpoint[bucket]:[])){const p=int(raw?.position);if(p!=null&&!cpByPos.has(p))cpByPos.set(p,raw);}
    }
    for(let p=this.start;p<=this.end;p++){
      let task=this._merge(this._base(p),cpByPos.get(p));
      if(done.has(p)&&!repair.has(p))task={...task,status:LessonTaskStatus.DONE,nextAttemptAt:null,lastError:null};
      else if(task.status===LessonTaskStatus.IN_FLIGHT||task.status===LessonTaskStatus.BLOCKED)task={...task,status:LessonTaskStatus.READY,nextAttemptAt:null};
      else if(task.status===LessonTaskStatus.DONE)task={...task,status:LessonTaskStatus.READY,nextAttemptAt:null};
      this.tasks.set(p,task);
    }
    return this;
  }
  get(position){const t=this.tasks.get(Number(position));return t?clone(t):null;}
  _getMutable(position){const t=this.tasks.get(Number(position));if(!t)throw new Error(`LessonTask ${position} not found`);return t;}
  setPriority(position,priority){this._getMutable(position).priority=Number(priority)||0;return this.get(position);}
  updateLessonUrl(position,lessonUrl){const t=this._getMutable(position);if(lessonUrl)t.lessonUrl=lessonUrl;return this.get(position);}
  _promoteDue(){const now=Number(this.nowFn());for(const t of this.tasks.values())if(t.status===LessonTaskStatus.RETRY_LATER&&(t.nextAttemptAt??0)<=now){t.status=LessonTaskStatus.READY;t.nextAttemptAt=null;}}
  _sortedReady(){this._promoteDue();return [...this.tasks.values()].filter(t=>t.status===LessonTaskStatus.READY).sort((a,b)=>(b.priority-a.priority)||(a.position-b.position));}
  claim(position){const t=this._getMutable(position);if(t.status===LessonTaskStatus.IN_FLIGHT)throw new Error(`LessonTask ${position} already IN_FLIGHT; duplicate claim rejected`);if(t.status!==LessonTaskStatus.READY)throw new Error(`LessonTask ${position} cannot be claimed from ${t.status}`);t.status=LessonTaskStatus.IN_FLIGHT;t.attempts+=1;t.nextAttemptAt=null;return clone(t);}
  claimNext(){const ready=this._sortedReady();if(ready.length)return{task:this.claim(ready[0].position),waitMs:0};const now=Number(this.nowFn());const future=[...this.tasks.values()].filter(t=>t.status===LessonTaskStatus.RETRY_LATER&&Number.isFinite(Number(t.nextAttemptAt))).sort((a,b)=>a.nextAttemptAt-b.nextAttemptAt);return{task:null,waitMs:future.length?Math.max(0,future[0].nextAttemptAt-now):null};}
  release(position,{lessonUrl=null,lastError=null}={}){const t=this._getMutable(position);if(t.status!==LessonTaskStatus.IN_FLIGHT)throw new Error(`LessonTask ${position} cannot release from ${t.status}`);t.status=LessonTaskStatus.READY;t.nextAttemptAt=null;t.lastError=clone(lastError);if(lessonUrl)t.lessonUrl=lessonUrl;return this.get(position);}
  markDone(position,{lessonUrl=null}={}){const t=this._getMutable(position);t.status=LessonTaskStatus.DONE;t.nextAttemptAt=null;t.lastError=null;if(lessonUrl)t.lessonUrl=lessonUrl;return this.get(position);}
  markBlocked(position,{lastError=null,lessonUrl=null}={}){const t=this._getMutable(position);t.status=LessonTaskStatus.BLOCKED;t.nextAttemptAt=null;t.lastError=clone(lastError);if(lessonUrl)t.lessonUrl=lessonUrl;return this.get(position);}
  requeue(position,{delayMs=0,priorityPenalty=0,lastError=null,lessonUrl=null}={}){const t=this._getMutable(position);if(t.status!==LessonTaskStatus.IN_FLIGHT&&t.status!==LessonTaskStatus.READY)throw new Error(`LessonTask ${position} cannot requeue from ${t.status}`);t.status=LessonTaskStatus.RETRY_LATER;t.nextAttemptAt=Number(this.nowFn())+Math.max(0,Number(delayMs)||0);t.priority-=Math.max(0,Number(priorityPenalty)||0);t.lastError=clone(lastError);if(lessonUrl)t.lessonUrl=lessonUrl;return this.get(position);}
  statusCounts(){const out={READY:0,IN_FLIGHT:0,RETRY_LATER:0,DONE:0,BLOCKED:0};for(const t of this.tasks.values())out[t.status]=(out[t.status]||0)+1;return out;}
  pending(){return[...this.tasks.values()].filter(t=>t.status!==LessonTaskStatus.DONE).map(clone);}
  snapshot(){
    const arr=status=>[...this.tasks.values()].filter(t=>t.status===status).sort((a,b)=>a.position-b.position).map(clone);
    return{schedulerVersion:this.schedulerVersion,updatedAt:new Date(Number(this.nowFn())).toISOString(),ready:arr(LessonTaskStatus.READY),retryLater:arr(LessonTaskStatus.RETRY_LATER),inFlight:arr(LessonTaskStatus.IN_FLIGHT),blocked:arr(LessonTaskStatus.BLOCKED)};
  }
}
