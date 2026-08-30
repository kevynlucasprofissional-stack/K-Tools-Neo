// Compatibility facade. New code should use BrowserSession + PageController directly.
import { BrowserSession, isTargetClosedError } from './browser-session.mjs';
import { PageController, PageRef, isLessonUrl } from './page-controller.mjs';

export class PlaywrightBrowser extends PageController {
  constructor({profileDir=null,cdpEndpoint='http://127.0.0.1:9222',logger=null,limits={},playwrightLoader=null,...rest}={}){
    const session=rest.session||new BrowserSession({cdpEndpoint,logger,limits,playwrightLoader});
    super({session,logger,limits,...rest});this.profileDir=profileDir;this.cdpEndpoint=cdpEndpoint;this.browserSession=session;
  }
  invalidateConnection(){this.session.invalidate();}
  connectionHealthy(){return this.session.isConnected();}
}
export { PageRef, isLessonUrl, isTargetClosedError };
