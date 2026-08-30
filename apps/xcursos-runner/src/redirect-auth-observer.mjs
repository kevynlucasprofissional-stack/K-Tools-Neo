import { BrowserAutomationError } from './errors.mjs';
import { redactUrl, sanitizeForPersistence } from './utils.mjs';
import { LESSON_URL_RE, XCURSOS_ORIGIN } from './constants.mjs';

function chainFromRequest(req){
  const chain=[];let cur=req;const guard=new Set();
  while(cur&&typeof cur.url==='function'&&!guard.has(cur)){
    guard.add(cur);chain.unshift(redactUrl(cur.url()));cur=cur.redirectedFrom?.()||null;
  }
  return chain;
}

export function classifyNavigation({url='',title='',bodyText=''}={}){
  const u=String(url||'');const text=`${title||''}\n${bodyText||''}`;
  if(/\/cdn-cgi\/|challenge-platform|challenges\.cloudflare/i.test(u)||/just a moment|verify you are human|verifique se você é humano|cloudflare/i.test(text))return 'CLOUDFLARE_REQUIRED';
  if(/\/(?:login|entrar|signin|auth)(?:[/?#]|$)/i.test(u)||/faça login|entrar na conta|login/i.test(title||''))return 'AUTH_REQUIRED';
  if(LESSON_URL_RE.test(u))return 'LESSON';
  try{const parsed=new URL(u);if(parsed.origin===XCURSOS_ORIGIN&&(parsed.pathname==='/'||/^\/curso\/[^/]+\/?$/.test(parsed.pathname)))return 'LESSON_REDIRECTED';}catch{}
  return 'OTHER';
}

export class RedirectAuthObserver {
  constructor({logger=null,maxEvents=40}={}){this.logger=logger;this.maxEvents=maxEvents;this.events=new WeakMap();this.handlers=new WeakMap();}
  attach(page){
    if(!page||this.handlers.has(page))return;
    const list=[];this.events.set(page,list);
    const push=event=>{list.push(sanitizeForPersistence(event));while(list.length>this.maxEvents)list.shift();};
    const onRequest=req=>{try{if(req.resourceType?.()==='document')push({type:'document-request',url:redactUrl(req.url()),redirectChain:chainFromRequest(req),timestamp:new Date().toISOString()});}catch{}};
    const onFrame=frame=>{try{if(frame===page.mainFrame?.())push({type:'navigation',url:redactUrl(frame.url()),timestamp:new Date().toISOString()});}catch{}};
    page.on?.('request',onRequest);page.on?.('framenavigated',onFrame);
    this.handlers.set(page,{onRequest,onFrame});
  }
  detach(page){const h=this.handlers.get(page);if(!h)return;page.off?.('request',h.onRequest);page.off?.('framenavigated',h.onFrame);this.handlers.delete(page);}
  history(page){return [...(this.events.get(page)||[])];}
  async classifyPage(page){
    const url=page?.url?.()||'';let title='';let bodyText='';
    try{title=await page.title();}catch{}
    if(!LESSON_URL_RE.test(url))try{bodyText=await page.locator?.('body')?.innerText?.({timeout:1500})||'';}catch{}
    return classifyNavigation({url,title,bodyText});
  }
  async assertLesson(page,{requestedUrl=null}={}){
    const classification=await this.classifyPage(page);
    if(classification==='LESSON')return classification;
    const details={requestedUrl:redactUrl(requestedUrl),landedUrl:redactUrl(page?.url?.()||''),history:this.history(page)};
    if(classification==='CLOUDFLARE_REQUIRED')throw new BrowserAutomationError('Cloudflare requer intervenção humana no Chrome. Conclua a verificação e tente novamente.',{code:'CLOUDFLARE_REQUIRED',details});
    if(classification==='AUTH_REQUIRED')throw new BrowserAutomationError('Sessão XCursos exige login. Execute `xcursos login`.',{code:'AUTH_REQUIRED',details});
    if(classification==='LESSON_REDIRECTED')throw new BrowserAutomationError('A navegação da aula foi redirecionada para uma página do curso/home.',{code:'LESSON_REDIRECTED',details});
    throw new BrowserAutomationError('A navegação não terminou em uma videoaula XCursos.',{code:'LESSON_REDIRECTED',details});
  }
}
