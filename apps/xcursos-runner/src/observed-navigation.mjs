import { StateStore } from './state.mjs';
import { NavigationIndex } from './navigation-index.mjs';

export async function persistObservedNavigation({outputRoot,lesson,logger=null}={}){
  if(!outputRoot||!lesson?.courseName||!Number.isInteger(Number(lesson?.totalPositions))||!Number.isInteger(Number(lesson?.currentPosition))||!lesson?.pageUrl)return false;
  const store=new StateStore({outputRoot,courseName:lesson.courseName,totalPositions:Number(lesson.totalPositions),logger});
  const index=new NavigationIndex({filePath:store.navigationPath,courseName:lesson.courseName,totalPositions:Number(lesson.totalPositions),logger});
  await index.load();return await index.record(Number(lesson.currentPosition),lesson.pageUrl);
}
