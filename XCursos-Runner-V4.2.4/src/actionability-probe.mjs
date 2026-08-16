import { BrowserAutomationError } from './errors.mjs';
import { isTargetClosedError } from './browser-session.mjs';

const GEOMETRY_TRANSITION_RE=/(^|,|\s)(all|transform|translate|scale|rotate|width|height|top|right|bottom|left|inset|margin|padding|max-width|max-height|min-width|min-height)(,|\s|$)/i;

function normBox(b){if(!b)return null;return{x:Number(b.x)||0,y:Number(b.y)||0,width:Number(b.width)||0,height:Number(b.height)||0};}
function sameBox(a,b,tolerance=0.25){if(!a||!b)return false;return Math.abs(a.x-b.x)<=tolerance&&Math.abs(a.y-b.y)<=tolerance&&Math.abs(a.width-b.width)<=tolerance&&Math.abs(a.height-b.height)<=tolerance;}
function deriveStable(boxes=[]){const clean=boxes.map(normBox).filter(Boolean);if(clean.length<2)return true;for(let i=1;i<clean.length;i++)if(!sameBox(clean[i-1],clean[i]))return false;return true;}
function safeMessage(error){return String(error?.message||error||'').slice(0,1000);}

export function isPlaywrightTimeoutError(error){
  const name=String(error?.name||'');const code=String(error?.code||'');const msg=String(error?.message||'');
  return name==='TimeoutError'||code==='TIMEOUTERROR'||/\bTimeout\s+\d+ms\s+exceeded\b/i.test(msg)||/locator\.(?:click|hover|tap).*Timeout/i.test(msg);
}

export class ActionabilityProbe {
  constructor({sampleFrames=4,trialTimeoutMs=1500,boxTolerance=0.25}={}){
    this.sampleFrames=Math.max(2,Math.min(12,Math.trunc(Number(sampleFrames)||4)));
    this.trialTimeoutMs=Math.max(50,Math.trunc(Number(trialTimeoutMs)||1500));
    this.boxTolerance=Math.max(0,Number(boxTolerance)||0);
  }

  async probe(locator,{trial=true}={}){
    let dom;
    try{
      dom=await locator.evaluate(async(el,opts)=>{
        const describe=node=>{
          if(!node)return null;
          const text=String(node.innerText||node.textContent||'').trim().replace(/\s+/g,' ').slice(0,120);
          return{same:node===el,contains:Boolean(el.contains?.(node)),tag:String(node.tagName||'').toLowerCase(),role:node.getAttribute?.('role')||null,id:node.id?String(node.id).slice(0,80):null,className:typeof node.className==='string'?node.className.slice(0,160):null,text};
        };
        const box=()=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,width:r.width,height:r.height};};
        const boxes=[];
        for(let i=0;i<opts.sampleFrames;i++){
          boxes.push(box());
          if(i<opts.sampleFrames-1)await new Promise(resolve=>requestAnimationFrame(()=>resolve()));
        }
        const s=getComputedStyle(el);const last=boxes.at(-1)||box();const cx=last.x+last.width/2,cy=last.y+last.height/2;const hit=document.elementFromPoint(cx,cy);
        const animations=(typeof el.getAnimations==='function'?el.getAnimations({subtree:false}):[]).slice(0,20).map(a=>({playState:a.playState||null,currentTime:Number.isFinite(Number(a.currentTime))?Number(a.currentTime):null,name:a.animationName||a.effect?.target?.getAttribute?.('data-animation-name')||null}));
        const disabled=Boolean(el.disabled||el.matches?.(':disabled'));const ariaDisabled=String(el.getAttribute?.('aria-disabled')||'').toLowerCase()==='true';
        return{
          found:true,visible:s.display!=='none'&&s.visibility!=='hidden'&&last.width>0&&last.height>0,enabled:!disabled&&!ariaDisabled,ariaDisabled,
          display:s.display,visibility:s.visibility,opacity:s.opacity,pointerEvents:s.pointerEvents,
          boundingBox:last,boundingBoxes:boxes,viewport:{width:window.innerWidth,height:window.innerHeight},centerPoint:{x:cx,y:cy},centerElement:describe(hit),receivesEvents:Boolean(hit&&(hit===el||el.contains?.(hit))),
          animations,transitions:{property:s.transitionProperty||'',duration:s.transitionDuration||'',delay:s.transitionDelay||''},
        };
      },{sampleFrames:this.sampleFrames});
    }catch(error){
      if(isTargetClosedError(error))throw new BrowserAutomationError('Página fechada durante ActionabilityProbe.',{code:'PAGE_CLOSED',cause:error});
      throw new BrowserAutomationError(`ActionabilityProbe falhou: ${safeMessage(error)}`,{code:'ACTIONABILITY_PROBE_FAILED',cause:error});
    }
    const boxes=(dom?.boundingBoxes||[]).map(normBox).filter(Boolean);
    const stable=typeof dom?.stable==='boolean'?dom.stable:deriveStable(boxes,this.boxTolerance);
    const transitionProperty=String(dom?.transitions?.property||'');
    const hasRunningAnimation=Array.isArray(dom?.animations)&&dom.animations.some(a=>String(a?.playState||'').toLowerCase()==='running');
    const geometryMotion=typeof dom?.geometryMotion==='boolean'?dom.geometryMotion:(!stable||(hasRunningAnimation&&GEOMETRY_TRANSITION_RE.test(transitionProperty)));
    const result={...dom,boundingBoxes:boxes,boundingBox:normBox(dom?.boundingBox||boxes.at(-1)),stable,geometryMotion,trial:{attempted:Boolean(trial),passed:null,errorName:null,errorMessage:null}};
    if(trial){
      try{await locator.click({trial:true,timeout:this.trialTimeoutMs});result.trial.passed=true;}
      catch(error){
        if(isTargetClosedError(error))throw new BrowserAutomationError('Página fechada durante trial click.',{code:'PAGE_CLOSED',cause:error});
        result.trial.passed=false;result.trial.errorName=String(error?.name||'Error');result.trial.errorMessage=safeMessage(error);
      }
    }
    return result;
  }

  shouldNeutralize(probe){
    if(!probe||probe.found===false)return false;
    if(probe.geometryMotion===true||probe.stable===false)return true;
    const prop=String(probe.transitions?.property||'');
    const running=Array.isArray(probe.animations)&&probe.animations.some(a=>String(a?.playState||'').toLowerCase()==='running');
    return running&&GEOMETRY_TRANSITION_RE.test(prop);
  }

  async neutralize(locator){
    const className=`xc-next-motion-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
    try{
      await locator.evaluate((el,args)=>{
        if(args.mode!=='neutralize')return null;
        const nodes=[];let node=el;
        for(let i=0;i<4&&node;i++,node=node.parentElement){node.classList.add(args.className);nodes.push(node);}
        const style=document.createElement('style');style.id=args.styleId;style.textContent=`.${args.className}{transition:none !important;animation:none !important;scroll-behavior:auto !important}`;document.head.appendChild(style);
        return{count:nodes.length,className:args.className};
      },{mode:'neutralize',className,styleId:`${className}-style`});
    }catch(error){
      if(isTargetClosedError(error))throw new BrowserAutomationError('Página fechada ao neutralizar movimento.',{code:'PAGE_CLOSED',cause:error});
      throw new BrowserAutomationError(`Falha ao neutralizar motion: ${safeMessage(error)}`,{code:'ACTIONABILITY_NEUTRALIZE_FAILED',cause:error});
    }
    return async()=>{
      try{
        await locator.evaluate((_el,args)=>{
          document.querySelectorAll(`.${args.className}`).forEach(n=>n.classList.remove(args.className));document.getElementById(args.styleId)?.remove();return true;
        },{mode:'restore',className,styleId:`${className}-style`});
      }catch{}
    };
  }
}
