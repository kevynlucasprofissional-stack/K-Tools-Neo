import { BrowserAutomationError } from './errors.mjs';
import { sleep } from './utils.mjs';
import { isTargetClosedError } from './browser-session.mjs';

function transientContentError(error){return /(?:Execution context was destroyed|Cannot find context|Protocol error|frame was detached|navigation|content.*failed|temporar)/i.test(String(error?.message||error||''));}

export async function safePageContent(page,{maxAttempts=3,delayMs=150,sleepFn=sleep}={}){
  if(!page?.content)throw new BrowserAutomationError('Página não suporta leitura de conteúdo.',{code:'PAGE_CONTENT_UNAVAILABLE'});
  let lastError=null;
  for(let attempt=1;attempt<=Math.max(1,maxAttempts);attempt++){
    try{
      if(page.isClosed?.())throw new BrowserAutomationError('Página fechada durante leitura de conteúdo.',{code:'PAGE_CLOSED'});
      const html=await page.content();
      if(typeof html!=='string'||!html.trim())throw new BrowserAutomationError('Conteúdo HTML vazio.',{code:'PAGE_CONTENT_EMPTY'});
      if(!/<html\b|<body\b/i.test(html))throw new BrowserAutomationError('Conteúdo HTML inesperado.',{code:'PAGE_CONTENT_UNEXPECTED'});
      return html;
    }catch(error){
      lastError=error;
      if(error?.code==='PAGE_CLOSED'||isTargetClosedError(error))throw error?.code?error:new BrowserAutomationError(String(error?.message||error),{code:'PAGE_CLOSED',cause:error});
      if(error?.code==='AUTH_REQUIRED'||!transientContentError(error)||attempt>=maxAttempts)break;
      await sleepFn(delayMs*attempt);
    }
  }
  if(lastError?.code)throw lastError;
  throw new BrowserAutomationError(`Falha ao ler HTML após ${maxAttempts} tentativas: ${String(lastError?.message||lastError)}`,{code:'PAGE_CONTENT_FAILED',cause:lastError});
}
