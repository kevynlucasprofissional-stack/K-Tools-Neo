# Final Report — M4 Artifact Lifecycle + Recovery + Semantic Cache V1

Status: **RESOLVED / PROMOTED**

## Objective

Add a conservative reusable-execution layer to K-Tools without lying about execution history, returning stale files, or skipping required side effects.

## Initial state

Before M4, M2 retained durable run/node lifecycle history and M3 produced support-grade diagnostics, but Artifact had no strong persistent validity lifecycle, repeated deterministic work always recomputed, there was no semantic node cache, and previous success was insufficient for safe reuse.

## Implemented contracts

- local file Artifact strong validity using size, mtime-ns and SHA-256;
- versioned NodeDefinition with explicit `CachePolicy.NEVER` default / `PURE` opt-in;
- deterministic semantic signatures over type/version/config/inputs/content identity;
- persistent optional `SQLiteNodeCache`;
- explicit `NODE_CACHED` / `NodeRunStatus.CACHED` lifecycle truth;
- persistent `SQLiteArtifactRegistry` per run/node/output/value-path occurrence;
- core and JSON CLI `--cache` / `--artifact-registry` integration;
- real cacheable `json.split.plan` over the existing pure `split_json_document` owner;
- preserved side-effect semantics for `json.split` as NEVER;
- conservative restart boundary: new run + validated PURE reuse, never automatic old-RUNNING continuation.

## Refuted shortcuts

- prior SUCCEEDED means reusable — refuted;
- size + mtime prove file equality — refuted;
- deterministic-looking code may be cached implicitly — refuted;
- cached reuse can masquerade as ordinary SUCCEEDED execution — refuted;
- cache failure should fail the workflow — refuted;
- matching signature alone proves cached file output is reusable — refuted;
- recovery requires continuing the old RUNNING row — refuted for V1 safety.

## Significant audit fixes

- corrected a pre/post Artifact-signature regression that initially compared only post-mutation state;
- changed cache serialization to container envelopes so user JSON cannot impersonate internal markers;
- required string mapping keys to prevent canonicalization collisions;
- normalized SQLite errors to CacheError so cache storage fails open;
- converted hashing I/O failures into explicit validity/bypass evidence;
- removed false double-reporting of cache read error as ordinary miss;
- kept `json.split` non-cacheable rather than weakening publication semantics.

## Real workload proof

A 2,000-record, 8-part `json.split.plan` workload ran twice with SQLite cache close/reopen between runs. The real pure implementation owner was called once total; the second run reused validated outputs and projected CACHED.

A separate CLI integration proves `json.literal -> json.split` may cache the source while the splitter still executes and republishes files, with diagnostics explaining both decisions.

## Artifact lifecycle proof

The Artifact registry persists historical observations and can independently revalidate current file state. A cached second run creates a new current-run occurrence marked CACHED without rewriting original Artifact production provenance.

## Hosted evidence

Accepted code SHA `c7ae2fa3953099d0bd9377da7c2c0195e96f6175` passed run `33560041360`, all five jobs.

Representative Ubuntu/Python 3.13 lane: 63 core tests, 64 JSON tests, CLI smokes, generated JSON artifact verification and PowerShell diagnostic regression all OK.

The synchronized canonical-memory candidate `d61ddfe139855b1fe9bf310fcbcc698524f3b444` then passed the complete hosted matrix in run `33625955613`.

## Explicit non-claims

M4 does not claim automatic resume of old in-flight work, `RECOVERED`, distributed/shared cache, strong remote/directory Artifact validity, safe replay of arbitrary side effects, automatic user-file deletion or cacheability of opaque Python objects.

## Final state

```text
WorkflowEngine
  ├─ RunJournal          -> what executed / lifecycle truth
  ├─ DiagnosticsSession  -> why / forensic support evidence
  ├─ NodeCache           -> validated reusable PURE results
  └─ ArtifactRegistry    -> persistent Artifact occurrence + validity provenance
```

These remain optional injected concerns rather than hidden globals.

## Promotion decision

M4 is resolved and promoted. M5 may begin from the first real legacy capability whose ownership and acceptance evidence are explicitly characterized before extraction.
