import fs from 'node:fs';

function read(path){return fs.readFileSync(path,'utf8');}
function write(path,text){fs.writeFileSync(path,text);}
function replaceOnce(path,oldText,newText){
  const source=read(path);
  if(!source.includes(oldText))throw new Error(`anchor not found in ${path}: ${oldText.slice(0,120)}`);
  write(path,source.replace(oldText,newText));
}
function replaceBetween(path,startMarker,endMarker,newBlock){
  const source=read(path);const start=source.indexOf(startMarker);const end=source.indexOf(endMarker,start);
  if(start<0||end<0)throw new Error(`boundaries not found in ${path}: ${startMarker} / ${endMarker}`);
  write(path,source.slice(0,start)+newBlock+source.slice(end));
}

// 1) Keep dedicated XCursos renderer responsive even when another Chrome tab/window is foreground.
replaceOnce('src/chrome-launcher.mjs',
`      '--no-default-browser-check',\n`,
`      '--no-default-browser-check',\n      '--disable-background-timer-throttling',\n      '--disable-renderer-backgrounding',\n      '--disable-backgrounding-occluded-windows',\n`);

// 2) Stable CDP target identity for the work tab.
replaceOnce('src/browser-session.mjs',
`  async newPage(){const context=await this.getContext();return await context.newPage();}\n\n  async recoverSession()`,
`  async newPage(){const context=await this.getContext();return await context.newPage();}\n\n  async getTargetId(page){\n    if(!page)return null;let cdp=null;\n    try{\n      const context=await this.getContext({recover:false});\n      if(typeof context?.newCDPSession!=='function')return page?.targetId||null;\n      cdp=await context.newCDPSession(page);\n      const info=await cdp.send('Target.getTargetInfo');\n      return info?.targetInfo?.targetId||null;\n    }catch{return page?.targetId||null;}\n    finally{if(cdp?.detach)try{await cdp.detach();}catch{}}\n  }\n\n  async findPageByTargetId(targetId,{pages=null}={}){\n    if(!targetId)return null;const candidates=pages||await this.getPages();\n    for(const page of candidates)if(await this.getTargetId(page)===targetId)return page;\n    return null;\n  }\n\n  async recoverSession()`);

// 3) Arbitrary-depth module hierarchy in lesson metadata.
replaceOnce('src/parser.mjs',
`export function isSafeDownloadMedia(meta={}){\n  return mediaSourceConfidence(meta)!=='UNTRUSTED';\n}\n`,
`export function isSafeDownloadMedia(meta={}){\n  return mediaSourceConfidence(meta)!=='UNTRUSTED';\n}\n\nexport function normalizeModulePath(modulePath=[],moduleName=null){\n  const raw=Array.isArray(modulePath)?modulePath:[];const out=[];\n  for(const value of raw){const text=String(value||'').trim();if(text&&out.at(-1)!==text)out.push(text);}\n  const fallback=String(moduleName||'').trim();if(!out.length&&fallback)out.push(fallback);return out;\n}\n`);
replaceOnce('src/parser.mjs',
`    site: 'xcursos',pageUrl,pageTitle,courseName: courseName || 'Curso XCursos',lessonTitle: lessonTitle || 'Aula',moduleName,\n`,
`    site: 'xcursos',pageUrl,pageTitle,courseName: courseName || 'Curso XCursos',lessonTitle: lessonTitle || 'Aula',moduleName,modulePath:normalizeModulePath([],moduleName),\n`);
replaceOnce('src/parser.mjs',
`  const hasUntrustedIframe=Boolean(meta.hasUntrustedIframe||(meta.iframeUrl&&!isTrustedPlayerIframeUrl(meta.iframeUrl)));\n  const result={\n`,
`  const hasUntrustedIframe=Boolean(meta.hasUntrustedIframe||(meta.iframeUrl&&!isTrustedPlayerIframeUrl(meta.iframeUrl)));\n  const modulePath=normalizeModulePath(meta.modulePath,meta.moduleName);\n  const result={\n`);
replaceOnce('src/parser.mjs',
`    courseName: String(meta.courseName || '').trim() || 'Curso XCursos',lessonTitle: String(meta.lessonTitle || '').trim() || 'Aula',moduleName: String(meta.moduleName || '').trim() || null,\n`,
`    courseName: String(meta.courseName || '').trim() || 'Curso XCursos',lessonTitle: String(meta.lessonTitle || '').trim() || 'Aula',moduleName:modulePath.at(-1)||String(meta.moduleName || '').trim()||null,modulePath,\n`);

// 4) Mirror modulePath on disk and keep the Windows path-length guard.
replaceBetween('src/downloader.mjs',
`  buildPaths({ root, courseName, moduleName, lessonTitle, position, total }) {`,
`\n  async findExistingFinal`,
`  buildPaths({ root, courseName, moduleName, modulePath=null, lessonTitle, position, total }) {\n    let course=sanitizeSegment(courseName,'Curso XCursos',90);\n    let modules=(Array.isArray(modulePath)?modulePath:[]).map(x=>String(x||'').trim()).filter(Boolean).map(x=>sanitizeSegment(x,'Modulo desconhecido',80));\n    if(!modules.length)modules=[sanitizeSegment(moduleName || 'Modulo desconhecido','Modulo desconhecido',80)];\n    let title=sanitizeSegment(lessonTitle,'Aula',110);\n    const width=Math.max(3,String(total || 999).length);const prefix=position != null ? String(position).padStart(width,'0') : '000';\n    const templateFor=()=>path.join(root,course,...modules,\`\${prefix} - \${title}.%(ext)s\`);const maxPath=235;let guard=0;\n    while(templateFor().length>maxPath&&guard++<100){\n      if(title.length>32){title=truncateWithHash(title,Math.max(32,title.length-10));continue;}\n      let longest=-1;for(let i=0;i<modules.length;i++)if(modules[i].length>24&&(longest<0||modules[i].length>modules[longest].length))longest=i;\n      if(longest>=0){modules[longest]=truncateWithHash(modules[longest],Math.max(24,modules[longest].length-10));continue;}\n      if(course.length>32){course=truncateWithHash(course,Math.max(32,course.length-10));continue;}break;\n    }\n    if(templateFor().length>maxPath)throw new RunnerError(\`Caminho de saída excede limite seguro (\${templateFor().length} > \${maxPath}). Escolha um outputRoot mais curto.\`,{code:'OUTPUT_PATH_TOO_LONG'});\n    const courseDir=path.join(root,course);const moduleDir=path.join(courseDir,...modules);const baseName=\`\${prefix} - \${title}\`;\n    return{courseDir,moduleDir,modulePath:modules,baseName,template:path.join(moduleDir,\`\${baseName}.%(ext)s\`)};\n  }\n`);

// 5) Persist hierarchy in in-flight checkpoints and manifest without breaking old records.
replaceOnce('src/state.mjs',
`    return {\n      position,\n      lessonTitle:String(value.lessonTitle||'Aula'),\n      moduleName:value.moduleName?String(value.moduleName):null,\n`,
`    const modulePath=(Array.isArray(value.modulePath)?value.modulePath:[]).map(x=>String(x||'').trim()).filter(Boolean);\n    const moduleName=modulePath.at(-1)||(value.moduleName?String(value.moduleName):null);\n    return {\n      position,\n      lessonTitle:String(value.lessonTitle||'Aula'),\n      moduleName,\n      modulePath:modulePath.length?modulePath:(moduleName?[moduleName]:[]),\n`);
replaceOnce('src/state.mjs',
`      lessonTitle:entry.lessonTitle||'Aula',\n      moduleName:entry.moduleName||null,\n`,
`      lessonTitle:entry.lessonTitle||'Aula',\n      moduleName:entry.moduleName||null,\n      modulePath:(Array.isArray(entry.modulePath)?entry.modulePath:[]).map(x=>String(x||'').trim()).filter(Boolean),\n`);

// 6) Page enumeration is passive; only the pinned work tab owns XCursos observers.
replaceOnce('src/page-controller.mjs',
`    this.refs=new WeakMap();this.trackedPages=new Set();this.mediaDiagnosticsByPage=new WeakMap();this.nextId=1;\n`,
`    this.refs=new WeakMap();this.trackedPages=new Set();this.mediaDiagnosticsByPage=new WeakMap();this.nextId=1;this.pinnedRef=null;this.pinnedTargetId=null;this.pinnedUrl=null;\n`);
replaceOnce('src/page-controller.mjs',
`  ref(page){\n    if(!page)return null;let r=this.refs.get(page);\n    if(!r){r=new PageRef(page,this.nextId++);this.refs.set(page,r);this.trackedPages.add(page);this.authObserver.attach(page);this.networkObserver?.attach?.(page);}\n    return r;\n  }\n  mark(ref,health){if(ref)ref.health=health;return ref;}\n`,
`  ref(page,{observe=false}={}){\n    if(!page)return null;let r=this.refs.get(page);if(!r){r=new PageRef(page,this.nextId++);this.refs.set(page,r);}if(observe)this.observeRef(r);return r;\n  }\n  observeRef(ref){const page=ref?.handle;if(!page||this.trackedPages.has(page))return ref;this.trackedPages.add(page);this.authObserver.attach(page);this.networkObserver?.attach?.(page);return ref;}\n  detachRef(ref){const page=ref?.handle;if(!page||!this.trackedPages.has(page))return;this.authObserver?.detach?.(page);this.networkObserver?.detach?.(page);this.trackedPages.delete(page);}\n  async pinWorkingPage(ref){\n    if(!ref?.handle)throw new BrowserAutomationError('Página de trabalho ausente para pin.',{code:'WORK_PAGE_MISSING'});\n    if(this.pinnedRef?.handle&&this.pinnedRef.handle!==ref.handle)this.detachRef(this.pinnedRef);\n    this.observeRef(ref);this.pinnedRef=ref;this.pinnedUrl=ref.url||this.pinnedUrl||null;const target=await this.session.getTargetId?.(ref.handle);if(target)this.pinnedTargetId=target;return ref;\n  }\n  mark(ref,health){if(ref)ref.health=health;return ref;}\n`);
replaceOnce('src/page-controller.mjs',
`  async close(){for(const page of this.trackedPages){this.authObserver?.detach?.(page);this.networkObserver?.detach?.(page);}this.trackedPages.clear();await this.session.disconnect();this.refs=new WeakMap();this.mediaDiagnosticsByPage=new WeakMap();}\n`,
`  async close(){for(const page of this.trackedPages){this.authObserver?.detach?.(page);this.networkObserver?.detach?.(page);}this.trackedPages.clear();this.pinnedRef=null;this.pinnedTargetId=null;this.pinnedUrl=null;await this.session.disconnect();this.refs=new WeakMap();this.mediaDiagnosticsByPage=new WeakMap();}\n`);
replaceOnce('src/page-controller.mjs',
`    if(!page)throw new BrowserAutomationError('Nenhuma aula XCursos está aberta no Chrome dedicado. Abra uma videoaula e tente novamente.',{code:'XC_PAGE_NOT_FOUND'});\n    const lesson=await this.inspectLesson(page);return{page,lesson,cloned:false};\n`,
`    if(!page)throw new BrowserAutomationError('Nenhuma aula XCursos está aberta no Chrome dedicado. Abra uma videoaula e tente novamente.',{code:'XC_PAGE_NOT_FOUND'});\n    page=await this.pinWorkingPage(page);const lesson=await this.inspectLesson(page);return{page,lesson,cloned:false};\n`);
replaceBetween('src/page-controller.mjs',
`  async recoverRef(ref,{url=null}={}){`,
`\n  async navigateExact`,
`  async recoverRef(ref,{url=null}={}){\n    const stable=url||ref?.url||this.pinnedUrl||null;const targetId=this.pinnedTargetId||await this.session.getTargetId?.(ref?.handle);this.mark(ref,'STALE');\n    await this.logger?.log('PAGE','Recovering pinned work page',{url:stable,targetPinned:Boolean(targetId)});\n    try{\n      this.mark(ref,'RECOVERING');await this.session.reconnect();const handles=await this.session.getPages();let recovered=null;\n      if(targetId&&typeof this.session.findPageByTargetId==='function'){const exact=await this.session.findPageByTargetId(targetId,{pages:handles});if(exact)recovered=this.ref(exact);}\n      if(!recovered&&stable){const matches=handles.filter(p=>{try{return p.url()===stable;}catch{return false;}});if(matches.length===1)recovered=this.ref(matches[0]);else if(matches.length>1)throw new BrowserAutomationError('Há múltiplas abas com a mesma aula e o target pinado não pôde ser recuperado.',{code:'PAGE_RECOVERY_AMBIGUOUS',details:{url:stable,matches:matches.length}});}\n      if(!recovered&&stable){recovered=this.ref(await this.session.newPage());recovered=await this.navigateExact(recovered,stable);}\n      if(!recovered)throw new BrowserAutomationError('Nenhuma página de aula pôde ser recuperada.',{code:'PAGE_RECOVERY_FAILED'});\n      recovered=await this.pinWorkingPage(recovered);this.mark(recovered,'HEALTHY');return recovered;\n    }catch(error){this.mark(ref,'DEAD');throw error;}\n  }\n`);
replaceOnce('src/page-controller.mjs',
`    try{\n      this.networkObserver?.attach?.(ref.handle);this.networkObserver?.beginGeneration?.(ref.handle,{reason:'navigate-exact',lessonUrl:url});this.authObserver.attach(ref.handle);\n`,
`    try{\n      ref=await this.pinWorkingPage(ref);this.networkObserver?.beginGeneration?.(ref.handle,{reason:'navigate-exact',lessonUrl:url});\n`);

// 7) Extract visible sidebar ancestry: module -> submodule -> ... -> leaf grouping.
replaceOnce('src/page-controller.mjs',
`          const iframeUrl=[...document.querySelectorAll('iframe[src]')].map(x=>x.src).find(Boolean)||null;\n          return{videoUrl,iframeUrl,pageUrl:location.href,pageTitle:document.title};\n`,
`          const iframeUrl=[...document.querySelectorAll('iframe[src]')].map(x=>x.src).find(Boolean)||null;\n          let modulePath=[];const asides=[...document.querySelectorAll('aside')];const sidebar=asides.find(visible)||asides[0]||null;\n          if(sidebar){\n            const durationRe=/\\b\\d{1,3}:\\d{2}(?::\\d{2})?\\b/;const buttons=[...sidebar.querySelectorAll('button')];\n            const activeButton=buttons.find(b=>{const text=b.innerText||'';if(!durationRe.test(text))return false;const aria=b.getAttribute('aria-current')||b.getAttribute('aria-selected');const state=b.getAttribute('data-state');const cls=String(b.className||'');const p=b.querySelector('p');const pClasses=String(p?.className||'').split(/\\s+/);return aria==='true'||aria==='page'||state==='active'||cls.includes('bg-white/[0.06]')||pClasses.includes('text-white');});\n            if(activeButton){const root=activeButton.closest('aside');const inner=[];let node=activeButton.parentElement;while(node&&node!==root){if(node.tagName==='DIV'){const first=[...node.children][0];if(first?.tagName==='BUTTON'&&/(?:\\b\\d+\\s+aulas?\\b|\\b\\d+\\s+arquivos?\\b)/i.test(first.innerText||'')){const label=(first.querySelector('p')?.innerText||'').trim();if(label&&inner.at(-1)!==label)inner.push(label);}}node=node.parentElement;}modulePath=inner.reverse();}\n          }\n          return{videoUrl,iframeUrl,modulePath,pageUrl:location.href,pageTitle:document.title};\n`);

// 8) Runner passes and persists the hierarchy.
replaceOnce('src/runner.mjs',
`courseName:this.courseName,moduleName:lesson.moduleName,lessonTitle:lesson.lessonTitle,position,total:this.total`,
`courseName:this.courseName,moduleName:lesson.moduleName,modulePath:lesson.modulePath,lessonTitle:lesson.lessonTitle,position,total:this.total`);
replaceOnce('src/runner.mjs',
`position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,lessonUrl:lesson.pageUrl||this.workPage.url,relativeOutputBase`,
`position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,modulePath:lesson.modulePath,lessonUrl:lesson.pageUrl||this.workPage.url,relativeOutputBase`);
replaceOnce('src/runner.mjs',
`await this.state.commit({position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,lessonUrl:lesson.pageUrl||this.workPage.url,status,outputFile,attempts,validation});`,
`await this.state.commit({position,lessonTitle:lesson.lessonTitle,moduleName:lesson.moduleName,modulePath:lesson.modulePath,lessonUrl:lesson.pageUrl||this.workPage.url,status,outputFile,attempts,validation});`);

// Existing observer cleanup test now explicitly pins before expecting listeners.
replaceOnce('tests/browser-session-page-controller.test.mjs',
`test('PageController close detaches network/auth listeners from persistent external Chrome pages',async()=>{\n  const page=new Page();const context=new Context([page]);const session=new BrowserSession({playwrightLoader:loader(context)});const controller=new PageController({session});await controller.pages();assert.ok(page.events.size>0);await controller.close();assert.equal(page.events.size,0);\n});`,
`test('PageController close detaches network/auth listeners from persistent external Chrome pages',async()=>{\n  const page=new Page();const context=new Context([page]);const session=new BrowserSession({playwrightLoader:loader(context)});const controller=new PageController({session});await controller.pages();assert.equal(page.events.size,0);await controller.chooseWorkingPage();assert.ok(page.events.size>0);await controller.close();assert.equal(page.events.size,0);\n});`);

console.log('V4.2.6 implementation applied');
