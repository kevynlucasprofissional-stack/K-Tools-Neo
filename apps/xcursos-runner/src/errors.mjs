export class RunnerError extends Error {
  constructor(message,{code='RUNNER_ERROR',cause=null,details=null}={}){
    super(message,cause?{cause}:undefined);this.name='RunnerError';this.code=code;this.details=details;
  }
}
export class BrowserAutomationError extends RunnerError {
  constructor(message,opts={}){super(message,{code:opts.code||'BROWSER_ERROR',...opts});this.name='BrowserAutomationError';}
}
export class TransitionError extends RunnerError {
  constructor(message,{kind='TRANSITION_ERROR',...opts}={}){super(message,{code:kind,...opts});this.name='TransitionError';this.kind=kind;}
}
