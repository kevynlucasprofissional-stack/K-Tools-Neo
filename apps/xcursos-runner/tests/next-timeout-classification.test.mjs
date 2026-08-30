import test from 'node:test';
import assert from 'node:assert/strict';
import { RetryPolicy, RetryClass } from '../src/retry-policy.mjs';
import { TransitionError } from '../src/errors.mjs';

const rawTimeout=Object.assign(new Error('locator.click: Timeout 20000ms exceeded.\n - waiting for element to be visible, enabled and stable'),{name:'TimeoutError',code:null});

test('raw Playwright TimeoutError is not globally treated as retryable without semantic context',()=>{const p=new RetryPolicy();assert.equal(p.classify({error:rawTimeout}),RetryClass.UNKNOWN);});

test('NEXT_ACTIONABILITY_TIMEOUT is explicitly transient even when original Playwright code is null',()=>{const p=new RetryPolicy();const e=new TransitionError('Próxima não ficou actionable',{kind:'NEXT_ACTIONABILITY_TIMEOUT',cause:rawTimeout});const d=p.decide({attempt:1,error:e});assert.equal(d.classification,RetryClass.TRANSIENT);assert.equal(d.retry,true);});

test('NEXT_TRANSITION_FAILED is structural and does not requeue blindly',()=>{const p=new RetryPolicy();const e=new TransitionError('Próxima não alterou posição',{kind:'NEXT_TRANSITION_FAILED'});const d=p.decide({attempt:1,error:e});assert.equal(d.classification,RetryClass.STRUCTURAL);assert.equal(d.retry,false);});

test('auth and position structural errors remain non-retryable',()=>{const p=new RetryPolicy();for(const code of ['AUTH_REQUIRED','CLOUDFLARE_REQUIRED','POSITION_SKIP','POSITION_REGRESSION','COURSE_IDENTITY_MISMATCH'])assert.notEqual(p.classify({error:{code}}),RetryClass.TRANSIENT,code);});

import { PageController } from '../src/page-controller.mjs';
test('PageController translates raw locator TimeoutError into NEXT_ACTIONABILITY_TIMEOUT at the Next boundary',async()=>{
  const locator={filter(){return this;},first(){return this;},count:async()=>1,click:async()=>{throw rawTimeout;}};
  const page={getByRole(role){return role==='button'?locator:{filter(){return this;},count:async()=>0};},getByText(){return{filter(){return this;},count:async()=>0};}};
  const observer={attach(){},detach(){}};
  const controller=new PageController({session:{capabilities:{},disconnect:async()=>{}},authObserver:{...observer},networkObserver:{...observer}});
  await assert.rejects(()=>controller.clickNext({handle:page}),e=>e.code==='NEXT_ACTIONABILITY_TIMEOUT'&&e.cause===rawTimeout);
});
