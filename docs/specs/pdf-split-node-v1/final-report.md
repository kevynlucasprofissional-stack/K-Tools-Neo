# Final Report — PDF Split Node V1

Status: **RESOLVED / PROMOTED**
Milestone: M5 — Official local Node Packs, Slice 3

## Objective

Extend the canonical PDF Node Pack with balanced PDF split and prove one-file source, ordered multi-file Artifact output and split→merge workflow composition without duplicating PDF logic or inventing unnecessary collection types.

## Initial state

- PDF Merge V1 was terminal-green and `packages/ktools-pdf` already owned checked PDF reading + atomic PDF publication.
- `FILE_SET` existed, but only a multi-file builtin source was available.
- Legacy `split_pdf_into_parts(...)` remained in the stable monolith and was already called by mixed Document Split.
- M4 could strongly snapshot nested local-file Artifacts and distinguish CACHED from executed success.

## Discovery and decision

Remaining bounded owners were re-inventoried rather than inheriting a favorite candidate. PDF split was selected over Images→PDF, WebP→PNG, Document Split and broad folder scanning because it reused existing PDF dependency/security boundaries, added real cardinality pressure and directly reduced future Document Split coupling.

Two architecture decisions were locked:

1. use honest cardinality `FILE -> FILE_SET`, adding `file.literal`, rather than passing one file inside a FILE_SET by convention;
2. keep FILE_SET with typed PDF members instead of creating PDF_SET without a proved graph-time requirement.

## RED

`e43f01db3473aa693382325e70fc7e1c17d1943d`, run `33653225831`.

Prior Core/JSON/Text and existing PDF Merge behavior remained green. New tests failed at the intended missing product contracts: `file.literal`, `split_pdf_into_parts`, `pdf.split.parts`, and shared-owner structure.

## Implementation

Delivered:

- builtin `file.literal: -> FILE`, version 1, PURE;
- shared local-file Artifact construction used by both single and multi-file literal nodes;
- `ktools_pdf.splitter.split_pdf_into_parts` as the split implementation owner;
- direct API delegation;
- `pdf.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- balanced contiguous partitioning with page-count clamp;
- collision-safe part naming and per-part atomic publication;
- protected/corrupt/empty fail-closed behavior;
- PDF Artifact provenance, MIME and page-range metadata;
- nested ArtifactRegistry strong snapshots;
- explicit partial multi-output failure semantics;
- split→merge typed composition without PDF_SET.

## GREEN and hardening

Initial GREEN:

- commit `88e8c1a37eeb08528bb060b4bdadb5f7b5f6a925`;
- run `33653824159`;
- 5/5 jobs successful.

Hardened technical candidate:

- commit `cb25cad6e6d60377d07a0c4d761700d7785f0c1e`;
- run `33654265424`;
- 5/5 jobs successful;
- hosted split→merge smoke in all four Python lanes.

The hosted smoke generates a deterministic five-page PDF, splits it into three parts, reopens them to verify `2/2/1`, merges the emitted FILE_SET and reopens the recomposed PDF to verify original ordered page dimensions.

## One-owner audit

Canonical split owner:

`packages/ktools-pdf/src/ktools_pdf/splitter.py`

Direct API and workflow node delegate to it. The adapter does not contain page partitioning, page-copy loops, collision selection or publication logic.

`packages/ktools-pdf` is now the canonical evolution owner for both PDF merge and balanced PDF split. The stable GUI copies remain frozen compatibility debt until traditional Tool/UI migration rewires them.

## Cache and side-effect classification

`file.literal` is PURE because it publishes nothing and M4 strongly revalidates its emitted file Artifact.

`pdf.split.parts` is NEVER because creating the requested part files is required behavior. Repeated execution in the same output directory intentionally creates new collision-safe filenames rather than substituting old Artifacts.

## Failure semantics

V1 is atomic per output PDF, not transactional across the entire FILE_SET. If a later part fails, earlier successfully published parts may remain. The failing destination must not contain a partial file or be represented as a successful output. This is explicitly tested and documented rather than implied as all-or-nothing.

## Regressions

No regression was observed in:

- Core runtime/contracts;
- JSON Node Pack;
- Text Node Pack;
- PDF Merge V1;
- xyflow spike.

## Debt carried forward

- legacy stable GUI still invokes historical PDF merge/split implementations;
- mixed Document Split remains in the monolith, but its PDF prerequisite is now canonical;
- Images→PDF/WebP→PNG require a deliberate Pillow/security policy before extraction;
- no PDF_SET is introduced until real graph-time element typing requires it;
- no generic cross-domain atomic publisher is introduced from visual similarity alone.

## Terminal state

**RESOLVED / PROMOTED**, contingent only on the canonical memory-closure commit itself passing the standard terminal `main` CI gate. After that gate, Slice 4 begins from fresh discovery rather than a preselected feature.
