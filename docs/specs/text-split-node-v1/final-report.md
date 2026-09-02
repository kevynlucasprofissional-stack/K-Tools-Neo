# Final Report — Text Split Node V1

Status: **RESOLVED / PROMOTED PENDING TERMINAL CLOSURE CI**

## Objective

Extend canonical `ktools-text` with balanced MD/TXT split so one local FILE produces an ordered FILE_SET of UTF-8 text Artifacts through one shared direct/workflow owner, removing the remaining primitive duplication inside future mixed Document Split.

## Initial state

- Slice 3 terminal closure was green at `a26dfcee626eedc27366dfec93be68503343941a`, run `33656157870`.
- `file.literal` and FILE_SET were already established.
- `ktools-text` canonically owned Text Merge but not Text Split.
- legacy mixed Document Split already delegated PDF to canonical PDF split while keeping separate text decode/balance/publication logic.

## Discovery decision

Text Split was selected ahead of mixed Document Split, Images→PDF, WebP→PNG and Files/Folders because it had the smallest new dependency/security surface and converted a future Document Split slice from primitive migration into orchestration over canonical Text/PDF owners.

## Implementation result

Canonical owner now lives under `packages/ktools-text/src/ktools_text/`:

```text
split_text_balanced
      ↓
split_text_file_into_parts
   ↙               ↘
direct API     text.split.parts
```

Delivered:

- split-specific legacy decoder policy (`utf-8-sig`, `utf-8`, `cp1252`, `latin-1`);
- deterministic line-unit balanced planner;
- UTF-8 output publication;
- collision-safe naming;
- per-part atomic publication;
- explicit partial-set failure behavior;
- direct API + thin node adapter;
- `text.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- FILE Artifact MIME/provenance/chunk metadata;
- nested ArtifactRegistry snapshot proof;
- cached source + required publication proof;
- direct/workflow byte equivalence;
- ordered split→merge composition;
- hosted split→merge smoke in all Python lanes.

Existing Text Merge decode behavior remains unchanged.

## Evidence chain

- spec gate: `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / run `33656954591` — 5/5;
- RED: `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / run `33657352636` — intended Text Split product failure;
- GREEN: `87558e8194692c045bdd95780fe05beb0f436e3a` / run `33657882057` — 5/5;
- hardened technical candidate: `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / run `33660594733` — 5/5 including Text split→merge smoke on Ubuntu/Windows Python 3.10/3.13.

## Audit outcome

No new runtime/native dependency was introduced. The node adapter owns no split algorithm. Publication remains capability-owned inside the Text pack rather than being prematurely generalized into core. FILE_SET remains adequate; no specialized text collection type is justified.

The stable GUI still contains historical Text Split logic. It is now compatibility debt, not the canonical evolution owner.

## Remaining risks / deferred work

- multi-output split remains per-part atomic rather than set-wide transactional;
- mixed Document Split orchestration is not implemented in this slice;
- Pillow/image safety policy remains unimplemented;
- production editor/tool surfaces remain later milestones.

## Terminal state

**RESOLVED / PROMOTED**, subject only to the synchronized memory-closure commit itself passing the normal terminal CI gate.
