function pos(value){const n=Number(value);return Number.isInteger(n)&&n>=1?n:null;}
function usable(ref,target){const p=pos(ref?.position);return Boolean(p&&p<target&&ref?.url);}

export class NavigationPlanner {
  plan({currentPosition=null,targetPosition,total=null,exactTargetUrl=null,checkpoint=null,courseAnchor=null}={}){
    const current=pos(currentPosition),target=pos(targetPosition),max=Number(total)||null;
    if(!target || (max&&target>max))throw new RangeError(`Invalid target position: ${targetPosition}`);
    const base={currentPosition:current,targetPosition:target};
    if(current===target)return{strategy:'ALREADY_AT_TARGET',...base,steps:0};
    if(exactTargetUrl)return{strategy:'EXACT_URL',...base,url:exactTargetUrl,steps:0};
    const candidates=[];
    if(current&&current<target)candidates.push({strategy:'WALK_FROM_CURRENT',...base,fromPosition:current,steps:target-current,rank:0});
    if(usable(checkpoint,target))candidates.push({strategy:'WALK_FROM_CHECKPOINT',...base,checkpoint:{position:Number(checkpoint.position),url:checkpoint.url},steps:target-Number(checkpoint.position),rank:1});
    if(usable(courseAnchor,target)||Number(courseAnchor?.position)===target){
      const anchor={position:Number(courseAnchor.position),url:courseAnchor.url};
      if(anchor.position===target)return{strategy:'EXACT_URL',...base,url:anchor.url,steps:0,source:'COURSE_ANCHOR'};
      candidates.push({strategy:'WALK_FROM_COURSE_ANCHOR',...base,anchor,steps:target-anchor.position,rank:2});
    }
    if(candidates.length){candidates.sort((a,b)=>a.steps-b.steps||a.rank-b.rank);const {rank,...best}=candidates[0];return best;}
    return{strategy:'NO_SAFE_PATH',...base,steps:null,strategiesConsidered:['ALREADY_AT_TARGET','EXACT_URL','WALK_FROM_CURRENT','WALK_FROM_CHECKPOINT','WALK_FROM_COURSE_ANCHOR']};
  }
}
