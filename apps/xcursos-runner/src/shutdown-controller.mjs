export class GracefulShutdownController {
  constructor({processRef=process,onCheckpoint=null,onForce=null,onLog=null}={}){this.processRef=processRef;this.onCheckpoint=onCheckpoint;this.onForce=onForce;this.onLog=onLog;this.stopRequested=false;this.forceRequested=false;this.abortController=new AbortController();this.installed=false;this._handler=()=>{void this.requestStop('SIGINT');};this._termHandler=()=>{void this.requestStop('SIGTERM');};}
  get signal(){return this.abortController.signal;}
  async requestStop(signal='SIGINT'){
    if(!this.stopRequested){this.stopRequested=true;this.onLog?.(`[SHUTDOWN] ${signal} received; finishing current atomic step before stopping`);await this.onCheckpoint?.({force:false,signal});return{force:false};}
    this.forceRequested=true;this.onLog?.(`[SHUTDOWN] ${signal} received again; force stop requested`);await this.onCheckpoint?.({force:true,signal});if(!this.abortController.signal.aborted)this.abortController.abort(new Error('FORCE_STOP'));await this.onForce?.({signal});return{force:true};
  }
  install(){if(this.installed)return;this.processRef?.on?.('SIGINT',this._handler);this.processRef?.on?.('SIGTERM',this._termHandler);this.installed=true;}
  uninstall(){if(!this.installed)return;this.processRef?.off?.('SIGINT',this._handler);this.processRef?.off?.('SIGTERM',this._termHandler);this.installed=false;}
}
