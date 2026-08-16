import { sleep } from './utils.mjs';
export class AutoThrottle {
  constructor({minDelayMs=0,maxDelayMs=3000,initialDelayMs=null,sleepFn=sleep}={}){this.minDelayMs=Math.max(0,Number(minDelayMs)||0);this.maxDelayMs=Math.max(this.minDelayMs,Number(maxDelayMs)||this.minDelayMs);this.currentDelayMs=Math.min(this.maxDelayMs,Math.max(this.minDelayMs,initialDelayMs==null?this.minDelayMs:Number(initialDelayMs)||0));this.sleepFn=sleepFn;this.successStreak=0;}
  recordFailure({status=null,retryAfterMs=null}={}){this.successStreak=0;const code=Number(status);let next=Math.max(this.minDelayMs,this.currentDelayMs||Math.max(100,this.minDelayMs));next=Math.max(next, code===429?Math.max(1000,next*2):code===403||code>=500?next*1.75:next*1.4);if(Number.isFinite(Number(retryAfterMs)))next=Math.max(next,Number(retryAfterMs));this.currentDelayMs=Math.min(this.maxDelayMs,Math.round(next));return this.currentDelayMs;}
  recordSuccess({latencyMs=null}={}){this.successStreak++;const floor=Number.isFinite(Number(latencyMs))?Math.max(this.minDelayMs,Math.min(this.maxDelayMs,Number(latencyMs)*0.15)):this.minDelayMs;const factor=this.successStreak>=3?0.75:0.9;this.currentDelayMs=Math.max(this.minDelayMs,Math.round(Math.max(floor,this.currentDelayMs*factor)));return this.currentDelayMs;}
  async wait(){if(this.currentDelayMs>0)await this.sleepFn(this.currentDelayMs);}
}
