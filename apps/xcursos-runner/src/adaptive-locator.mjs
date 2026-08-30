function norm(s=''){return String(s).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();}
export function scoreNextCandidate(c={}){
  const text=norm([c.text,c.ariaLabel,c.title].filter(Boolean).join(' '));const role=norm(c.role);const tag=norm(c.tag);
  let score=0;
  if(text==='proxima')score+=0.82;else if(text.startsWith('proxima aula')||text==='proxima aula')score+=0.78;else if(text.includes('proxima'))score+=0.62;
  if(role==='button'||role==='link')score+=0.12;if(tag==='button'||tag==='a')score+=0.08;
  if(c.visible===false)score-=1;if(/anterior|voltar|material|download/.test(text))score-=0.7;
  return Math.max(0,Math.min(1,score));
}
export class AdaptiveLocator {
  constructor({threshold=0.85,ambiguityDelta=0.05}={}){this.threshold=threshold;this.ambiguityDelta=ambiguityDelta;}
  async findNext(page){
    let candidates=[];try{candidates=await page.evaluate(()=>[...document.querySelectorAll('button,a,[role="button"]')].map((el,index)=>({index,tag:el.tagName?.toLowerCase()||'',role:el.getAttribute?.('role')||'',text:(el.innerText||el.textContent||'').trim(),ariaLabel:el.getAttribute?.('aria-label')||'',title:el.getAttribute?.('title')||'',visible:(()=>{const s=getComputedStyle(el),r=el.getBoundingClientRect();return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0;})()})));}catch{return null;}
    if(!Array.isArray(candidates))return null;const ranked=candidates.map(candidate=>({candidate,score:scoreNextCandidate(candidate)})).sort((a,b)=>b.score-a.score);
    const best=ranked[0];if(!best||best.score<this.threshold)return null;if(ranked[1]&&best.score-ranked[1].score<this.ambiguityDelta)return null;
    const locator=page.locator('button,a,[role="button"]').nth(best.candidate.index);return{locator,candidate:best.candidate,score:best.score};
  }
}
