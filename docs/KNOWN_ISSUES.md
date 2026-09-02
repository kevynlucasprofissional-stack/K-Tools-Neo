# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications before imported-app adapters are promoted.

## KI-002 — Legacy GUI owns large amounts of business logic

Status: OPEN / REDUCED BY M5 SLICES 1–4

`K Tools Neo - Versão Estável 2.py` remains a large monolithic GUI/application file with many capability implementations embedded beside presentation/runtime concerns.

M5 has now extracted canonical owners for Markdown/TXT merge, balanced Markdown/TXT split, PDF merge and balanced PDF split. Many image, mixed-document, filesystem and media utilities remain in the monolith.

Invariant: extract capability-by-capability behind tested node contracts rather than performing a broad monolith rewrite.

## KI-003 — No real K-Tools utility node is integrated yet

Status: RESOLVED

Historical foundation condition. `packages/ktools-json/` is the first real pack; M5 adds Text/PDF capabilities plus ordered `files.literal` and single `file.literal` source contracts.

## KI-004 — Workflow/run/artifact persistence is absent

Status: RESOLVED

M2 implements durable run/node history with RunJournal + SQLite. M4 implements persistent Artifact occurrence/validity observations and semantic cache.

Automatic continuation of old in-flight RUNNING work remains ownership-gated; this is a deliberate recovery-safety boundary, not missing persistence.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No production canvas/palette/inspector/run UI exists yet.

Research and the audited spike identify `@xyflow/react` as the preferred interaction layer while `ktools-core` remains runtime authority. Desktop-host integration and target-environment performance remain unproved.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

## KI-007 — Historical GitHub Actions jobs were blocked by billing/spending state

Status: RESOLVED

Historical runs `33327645359` and `33327842478` failed before product steps because GitHub UI reported account payment/spending-limit state. After the repository became public, run `33330660076` on `1ccffb11af25a8d993ead931183380d354746131` reached and passed checkout/setup/install/tests/smoke on Ubuntu/Windows.

Future CI failures must be classified from their actual first failing step rather than carried forward from this incident.

## KI-008 — Legacy stable GUI is not yet wired to canonical Text Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-text` is now the canonical evolution owner for both Markdown/TXT merge and balanced Markdown/TXT split. `K Tools Neo - Versão Estável 2.py` still executes historical implementations of both behaviors.

Impact: direct edits to the legacy copies could drift from the tested package semantics.

Invariant: new Text merge/split behavior and bug fixes originate in `ktools-text`; historical implementations are compatibility paths only.

Next: when traditional Text Tool surfaces are migrated to platform workflows, redirect them to `ktools-text` and remove/reduce duplicate owners.

## KI-009 — Legacy stable GUI is not yet wired to canonical PDF Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-pdf` is the canonical evolution owner for both PDF merge and balanced PDF split after M5 Slices 2–3. The stable GUI still contains and invokes historical implementations of both behaviors.

Impact: direct edits to the old copies could drift from the tested package behavior.

Invariant: new PDF merge/split behavior and bug fixes originate in `ktools-pdf`; historical implementations are compatibility paths only.

Next: when traditional PDF Tool surfaces are migrated to platform workflows, redirect them to `ktools-pdf` and remove/reduce duplicate owners.

## KI-010 — Shared temp-then-promote patterns exist across file-producing packs

Status: OPEN / OBSERVE BEFORE ABSTRACTING

Text and PDF writers use temporary output before final publication, and both splitters reuse their pack-specific atomic writers across multiple outputs. Their write/finalization/collision contracts remain materially different across domains.

Do not create a generic core publication abstraction merely because several implementations use temporary files. Re-evaluate only after another file-producing pack proves a stable cross-domain API for allocation, cleanup, collision policy and promotion without leaking writer-specific semantics.

## KI-011 — Multi-output operations are not globally transactional

Status: OPEN / EXPLICIT V1 BOUNDARY

Both `pdf.split.parts` and `text.split.parts` are atomic per produced file but not all-or-nothing across the entire output set. If publication of a later part fails, previously published parts may remain.

This is intentional and tested. The failed destination must not be partial or falsely claimed successful.

Revisit set-wide transaction/rollback only if a real workflow requires it and file ownership/rollback semantics can be made reliable across platforms.

## KI-012 — Domain-specialized collection types are intentionally deferred

Status: OPEN / DESIGN WATCH

`FILE_SET` can contain typed PDF or Text-file Artifacts and already proves PDF split→merge and Text split→merge composition. No `PDF_SET` or text-specific collection type exists.

Revisit only when graph-time element-type rejection or catalog/UI behavior demonstrates a concrete safety/product need that member-level Artifact typing/runtime validation cannot satisfy.

## KI-013 — Mixed Document Split orchestration is still legacy-only

Status: OPEN / NEXT-CANDIDATE BOUNDARY

The historical mixed Document Split now delegates conceptually to two capabilities that both have canonical package owners:

- PDF split -> `ktools-pdf`;
- Markdown/TXT split -> `ktools-text`.

However, the mixed dispatcher/aggregation/progress/error contract itself has not yet been extracted. Do not implement a new mixed node by copying either primitive algorithm; characterize the orchestration boundary first.
