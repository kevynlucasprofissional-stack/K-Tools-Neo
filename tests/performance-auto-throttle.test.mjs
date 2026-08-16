import test from 'node:test';
import assert from 'node:assert/strict';
import { AutoThrottle } from '../src/auto-throttle.mjs';

test('long successful downloads do not create artificial throttle from latency',()=>{
  const t=new AutoThrottle({minDelayMs:0,maxDelayMs:3000});
  assert.equal(t.recordSuccess({latencyMs:120_000}),0);
  assert.equal(t.currentDelayMs,0);
});

test('429 still creates strong backoff and successes decay it quickly',()=>{
  const t=new AutoThrottle({minDelayMs:0,maxDelayMs:3000});
  t.recordFailure({status:429});assert.ok(t.currentDelayMs>=1000);
  const afterFailure=t.currentDelayMs;
  t.recordSuccess({latencyMs:120_000});assert.ok(t.currentDelayMs<afterFailure);
  for(let i=0;i<10;i++)t.recordSuccess({latencyMs:120_000});
  assert.equal(t.currentDelayMs,0);
});

test('403 and 5xx still increase delay instead of being erased',()=>{
  const a=new AutoThrottle({minDelayMs:100,maxDelayMs:3000,initialDelayMs:100});
  a.recordFailure({status:403});assert.ok(a.currentDelayMs>100);
  const b=new AutoThrottle({minDelayMs:100,maxDelayMs:3000,initialDelayMs:100});
  b.recordFailure({status:503});assert.ok(b.currentDelayMs>100);
});

test('Retry-After remains authoritative up to configured max',()=>{
  const t=new AutoThrottle({minDelayMs:0,maxDelayMs:3000});
  t.recordFailure({status:429,retryAfterMs:2500});assert.equal(t.currentDelayMs,2500);
  t.recordFailure({status:429,retryAfterMs:99999});assert.equal(t.currentDelayMs,3000);
});
