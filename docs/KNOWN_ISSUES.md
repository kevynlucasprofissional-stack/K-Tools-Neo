# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications before imported-app adapters are promoted.

## KI-002 — Legacy GUI owns large amounts of business logic

Status: OPEN / REDUCED BY M5 SLICES 1–6

`K Tools Neo - Versão Estável 2.py` remains a large monolithic GUI/application file with capability implementations beside presentation/runtime concerns.

M5 has extracted canonical owners for Markdown/TXT merge/split, PDF merge/split, mixed Text/PDF document-split orchestration and WebP→PNG/image safety. Images→PDF, filesystem and media utilities remain substantially in the monolith.

Invariant: extract capability-by-capability behind tested node contracts rather than performing a broad monolith rewrite.

## KI-003 — No real K-Tools utility node is integrated yet

Status: RESOLVED

Historical foundation condition. Official JSON/Text/PDF/Documents/Images packs now exist alongside `files.literal` and `file.literal` source contracts.

## KI-004 — Workflow/run/artifact persistence is absent

Status: RESOLVED

M2 implements durable run/node history with RunJournal + SQLite. M4 implements persistent Artifact occurrence/validity observations and semantic cache. Automatic continuation of old in-flight RUNNING work remains deliberately ownership-gated.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No production canvas/palette/inspector/run UI exists yet. The audited xyflow spike remains evidence for interaction architecture, not a production editor.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

## KI-007 — Historical GitHub Actions jobs were blocked by billing/spending state

Status: RESOLVED

Historical runs `33327645359` and `33327842478` failed before product steps due account billing/spending state. Later public-repo runs reached and passed actual product steps. Future CI failures must be classified from their real first failing step.

## KI-008 — Legacy stable GUI is not yet wired to canonical Text Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-text` owns Markdown/TXT merge/split evolution. The stable GUI still executes historical copies. New semantics/bug fixes originate in `ktools-text`; later traditional Tool migration must redirect/retire the copies.

## KI-009 — Legacy stable GUI is not yet wired to canonical PDF Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-pdf` owns PDF merge/split evolution. The stable GUI still executes historical copies. New semantics/bug fixes originate in `ktools-pdf`; later traditional Tool migration must redirect/retire the copies.

## KI-010 — Shared temp-then-promote patterns exist across file-producing packs

Status: OPEN / OBSERVE BEFORE ABSTRACTING

Text, PDF and Images now all contain temp→promote publication patterns, but their allocation, writer, aggregate/per-output and failure contracts differ materially. This additional occurrence still does **not** prove a generic core publication API.

Re-evaluate only when multiple independent packs expose a stable common contract for allocation, cleanup, collision policy, promotion and ownership without leaking domain-specific writer semantics.

## KI-011 — Multi-output operations are not globally transactional

Status: OPEN / EXPLICIT V1 BOUNDARY

PDF split, Text split and WebP→PNG publish individual completed outputs atomically but are not all-or-nothing across the full output set. A later failure may leave earlier completed user-visible files.

This is intentional and tested. The failing destination must not be partial or falsely claimed successful. Set-wide rollback requires stronger file ownership/deletion evidence.

## KI-012 — Domain-specialized collection types are intentionally deferred

Status: OPEN / DESIGN WATCH

`FILE_SET` carries Text FILE, PDF and IMAGE Artifacts through current workflows. Hosted PDF/Text composition, mixed Documents and WebP→PNG prove member-level Artifact typing is currently sufficient without `PDF_SET`, text-specific sets, document sets or `IMAGE_SET`.

Revisit only when graph-time element-type rejection or catalog/UI behavior proves a concrete need.

## KI-013 — Mixed Document Split orchestration is still legacy-only

Status: RESOLVED / CANONICAL OWNER EXTRACTED

`packages/ktools-documents` owns mixed `.md/.txt/.pdf` filtering/dispatch/progress/error/report behavior. Primitive PDF/Text split remains in canonical child packs. Stable GUI mixed orchestration is compatibility debt.

Terminal closure: `3d2d955df71cd65162839a5ac2c1335e5b5a4518`, run `33665431920`, 5/5.

## KI-014 — Failed child split may leave unreturned published parts on disk

Status: OPEN / EXPLICIT V1 OWNERSHIP BOUNDARY

A primitive Text/PDF split may publish earlier parts and then raise on a later part. `document.split.files` can continue later source files, but the raised child call cannot return those earlier parts. They may remain on disk but are not falsely claimed in the successful FILE_SET/report. Batch rollback is not attempted without safe ownership/deletion semantics.

## KI-015 — Legacy stable GUI is not yet wired to canonical Image Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-images` is now the canonical evolution owner for the 80M-pixel/Pillow bomb boundary, EXIF orientation policy and WebP→PNG conversion. `K Tools Neo - Versão Estável 2.py` still contains and invokes the historical WebP→PNG implementation and related image helpers.

Impact: direct edits to the legacy path could drift from tested package semantics.

Invariant: WebP→PNG/image-safety semantic changes originate in `ktools-images`; the legacy implementation is a compatibility path only.

Next: traditional image Tool migration should redirect WebP→PNG to the canonical pack. Images→PDF extraction must reuse canonical image safety/orientation rather than copy it.

## KI-016 — Pillow major-version support is intentionally bounded

Status: OPEN / DEPENDENCY GOVERNANCE WATCH

`ktools-images` V1 declares `Pillow>=12,<13`. This does not claim Pillow 13 is incompatible; it prevents an untested major release from silently changing decode/security/format behavior.

Reopen the upper bound only with package tests and hosted image smoke against the proposed major version.
