import fs from 'node:fs';
function read(p){return fs.readFileSync(p,'utf8');}function write(p,s){fs.writeFileSync(p,s);}
function replaceOnce(p,a,b){const s=read(p);if(!s.includes(a))throw new Error(`anchor missing ${p}: ${a.slice(0,120)}`);write(p,s.replace(a,b));}
function replaceBetween(p,a,b,n){const s=read(p),i=s.indexOf(a),j=s.indexOf(b,i);if(i<0||j<0)throw new Error(`bounds missing ${p}`);write(p,s.slice(0,i)+n+s.slice(j));}

// If an injected/legacy session has getTargetId but no helper, PageController can still recover by target identity.
// If TargetId is unavailable, only recycle an about:blank page; never hijack an unrelated user tab.
replaceBetween('src/page-controller.mjs',
`  async recoverRef(ref,{url=null}={}){`,
`\n  async navigateExact`,
`  async recoverRef(ref,{url=null}={}){\n    const stable=url||ref?.url||this.pinnedUrl||null;const targetId=this.pinnedTargetId||await this.session.getTargetId?.(ref?.handle);this.mark(ref,'STALE');\n    await this.logger?.log('PAGE','Recovering pinned work page',{url:stable,targetPinned:Boolean(targetId)});\n    try{\n      this.mark(ref,'RECOVERING');await this.session.reconnect();const handles=await this.session.getPages();let recovered=null;\n      if(targetId){\n        let exact=null;if(typeof this.session.findPageByTargetId==='function')exact=await this.session.findPageByTargetId(targetId,{pages:handles});\n        else if(typeof this.session.getTargetId==='function'){for(const handle of handles){if(await this.session.getTargetId(handle)===targetId){exact=handle;break;}}}\n        if(exact)recovered=this.ref(exact);\n      }\n      if(!recovered&&stable){const matches=handles.filter(p=>{try{return p.url()===stable;}catch{return false;}});if(matches.length===1)recovered=this.ref(matches[0]);else if(matches.length>1)throw new BrowserAutomationError('Há múltiplas abas com a mesma aula e o target pinado não pôde ser recuperado.',{code:'PAGE_RECOVERY_AMBIGUOUS',details:{url:stable,matches:matches.length}});}\n      if(!recovered&&stable){const blank=handles.find(p=>{try{return p.url()==='about:blank';}catch{return false;}});recovered=this.ref(blank||await this.session.newPage());recovered=await this.navigateExact(recovered,stable);}\n      if(!recovered)throw new BrowserAutomationError('Nenhuma página de aula pôde ser recuperada.',{code:'PAGE_RECOVERY_FAILED'});\n      recovered=await this.pinWorkingPage(recovered);this.mark(recovered,'HEALTHY');return recovered;\n    }catch(error){this.mark(ref,'DEAD');throw error;}\n  }\n`);

// Refresh explicitly operates on the pinned work tab before opening a fresh media generation.
replaceOnce('src/page-controller.mjs',
`      if(!ref?.handle||pageClosed(ref.handle))throw new Error('Target page, context or browser has been closed');\n      this.networkObserver?.attach?.(ref.handle);this.networkObserver?.beginGeneration?.(ref.handle,{reason:'refresh',lessonUrl:originalUrl});\n`,
`      if(!ref?.handle||pageClosed(ref.handle))throw new Error('Target page, context or browser has been closed');\n      ref=await this.pinWorkingPage(ref);this.networkObserver?.beginGeneration?.(ref.handle,{reason:'refresh',lessonUrl:originalUrl});\n`);

// This existing regression intentionally injects a network response before inspection. Under passive enumeration,
// the test must pin the page before it expects network observation.
replaceOnce('tests/network-media-observer.test.mjs',
`  const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);\n  await p.emit('response',response('https://cdn/network.mp4?X-Amz-Signature=LIVE'));\n`,
`  const session=new BrowserSession({playwrightLoader:async()=>({chromium:{connectOverCDP:async()=>browser}})});const controller=new PageController({session});await controller.connect();const ref=controller.ref(p);await controller.pinWorkingPage(ref);\n  await p.emit('response',response('https://cdn/network.mp4?X-Amz-Signature=LIVE'));\n`);
console.log('V4.2.6 fixup applied');
