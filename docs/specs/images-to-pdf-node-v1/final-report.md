# Final Report — M5 Slice 7 — Images→PDF Node V1

Status: **RESOLVED / PROMOTED**

## Objective

Extract the historical Images→PDF capability into the canonical Image Node Pack without creating a second Pillow safety stack, while preserving the K-Tools one-owner architecture for direct API and workflow execution.

## Initial state

Slice 7 began only after Image Safety Foundation + WebP→PNG V1 was terminally green at `9b9fc57bd4bfb28d7e23637651a30182ce6f8828`, run `33668942264`, 5/5.

Fresh discovery compared Images→PDF against bounded Files/Folders. Images→PDF won because Slice 6 had already bounded the risky image decode policy, leaving a clear aggregate-output contract. Files/Folders still had unresolved overlapping legacy traversal/report semantics.

## Truth sources

Primary source-of-truth set:

- exact `main` at each gate;
- `AGENTS.md` and Solo Development Mode rules;
- canonical state/roadmap/decisions/constraints/testing/known-issues documents;
- Engineering Journal;
- `docs/specs/images-to-pdf-node-v1/spec.md`, `plan.md`, `tasks.md`, `evidence.md`;
- actual `packages/ktools-images` source/tests;
- hosted CI on exact SHAs.

## Specification result

V1 locks:

- existing regular files with `.jpg/.jpeg/.png/.webp/.bmp/.tif/.tiff`, case-insensitive;
- compatible-source order as page order;
- one first frame/page per input file;
- shared decompression-bomb/80M-pixel and EXIF policy;
- RGB PDF pages;
- RGBA/LA/palette transparency composited over white;
- singular aggregate `.pdf` output;
- same-directory temp + promote publication;
- prior destination preservation on handled failure;
- one PDF Artifact with provenance and bounded metadata;
- `image.files_to_pdf: FILE_SET -> PDF`, v1, `CachePolicy.NEVER`;
- no `IMAGE_SET` and no new runtime dependency.

## Hypotheses and refutations

### H1 — Slice 6's decode/safety path should remain WebP-specific

Refuted by the second independent consumer. Keeping Pillow open/bomb/EXIF/frame selection in both WebP→PNG and Images→PDF would duplicate product-significant safety policy.

Result: pack-local `reader.load_safe_first_frame` became the single shared owner.

### H2 — Images→PDF can reuse the shared reader without forcing one common mode/publication policy

Validated. WebP→PNG still owns PNG-specific alpha/mode/per-output publication; Images→PDF owns RGB/alpha-white/aggregate-PDF semantics.

### H3 — Images→PDF could be PURE because the PDF result is deterministic enough

Rejected for V1. The node contract includes publishing/replacing the requested destination; cache substitution would skip a required side effect. The node is NEVER.

### H4 — Existing `FILE_SET` is sufficient

Validated. Member Artifact types plus capability-level supported-format filtering are sufficient; no graph-time requirement for `IMAGE_SET` emerged.

### H5 — GREEN behavior alone proves reader ownership

Refuted during audit. A stale Slice-6 structural assertion still searched for direct `Image.open`/EXIF tokens in `converter.py`. The test was hardened to follow the true shared owner and the compatibility breadcrumb was removed.

## Implementation result

Delivered in `packages/ktools-images`:

- `reader.py` — guarded first-frame decode owner;
- refactored WebP→PNG converter consuming the shared reader;
- `pdf_writer.py` — Images→PDF business-logic owner;
- singular atomic PDF publication helper;
- direct API route;
- workflow node `image.files_to_pdf`;
- PDF Artifact/provenance/metadata;
- real workflow smoke independently reopened through `pypdf`.

## RED evidence

Spec gate `ae617e948d5549e3dbca1dbe8d5de19c16555535` / `33670517542`, 5/5.

RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db` / `33671061268` proved prior packs plus all 15 existing WebP tests remained green while the 15 new Images→PDF contracts failed at the intended absent shared-reader/PDF-publication boundary.

## GREEN evidence

Implementation `309863ac475330448e6fc44dbdf305482528689e` / `33671740134`, 5/5.

All four Python lanes passed the complete installed-pack suites and all hosted smokes including the new Images→PDF workflow. xyflow remained green.

## Audit / hardening evidence

Ownership-hardening `1d9afc40bb7adbb511a1869d25b18058782bcbad` / `33672387118`, 5/5.

Tests now prove the real `reader.py` ownership while WebP behavior and Images→PDF remain green on Ubuntu/Windows × Python 3.10/3.13.

## Memory-closure evidence

Synchronized closure `c3585f5b7f478f53e1c5ef63f72a7b49fbb0cdea` / run `33674308145` completed 5/5:

- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow — success.

Every Python lane reached and passed all pack suites and all hosted workflow smokes, including both image smokes. This satisfied the explicit terminal promotion rule.

## Regression status

No observed regression in Core runtime/durable execution/diagnostics/cache/artifact suites, JSON, Text merge/split, PDF merge/split, Documents mixed split, WebP→PNG or the audited xyflow spike.

## Architecture consequences

- `ktools-images` now has two production capability consumers over one shared safe reader;
- image safety/frame/orientation policy is no longer tied to a single transformation;
- output-mode and publication semantics remain capability-specific;
- the stable legacy Images→PDF implementation is compatibility debt, not a second canonical owner;
- Files/Folders remains deliberately deferred until its own cross-platform contract is locked.

## Risks / remaining boundaries

- Pillow support remains intentionally bounded to `>=12,<13`;
- first-frame-only is a deliberate V1 policy, not full multi-frame TIFF/animation support;
- PDF/A, ICC/color-management and print-production guarantees are out of scope;
- aggregate PDF publication is atomic at the final destination but does not imply a generic core writer abstraction;
- legacy GUI rewiring is not part of this slice.

## Memory closure

ADR: `docs/decisions/ADR-029-IMAGES-TO-PDF-NODE-V1.md`.
Canonical implementation: `packages/ktools-images/`.
Spec/evidence: `docs/specs/images-to-pdf-node-v1/`.

## Final state

**M5 Slice 7 — RESOLVIDO / RESOLVED / PROMOTED.**

Next state: M5 Slice 8 begins fresh discovery from the terminal mainline; no capability is preselected.
