# Known Issues — K-Tools Neo

## KI-001 — Imported app CI is not monorepo root CI

Status: OPEN / CLASSIFIED

`apps/xcursos-runner/.github/workflows/*` and `apps/yt-dlp-tui/.github/workflows/*` live below the repository root. Those imported workflow files do not by themselves validate the K-Tools monorepo.

Impact: upstream/subtree test suites can drift after integration unless root CI explicitly invokes them.

Next: design root jobs/path filters for imported applications before imported-app adapters are promoted.

## KI-002 — Legacy GUI owns large amounts of business logic

Status: OPEN / REDUCED BY M5 SLICES 1–2

`K Tools Neo - Versão Estável 2.py` remains a large monolithic GUI/application file with many capability implementations embedded beside presentation/runtime concerns.

M5 now extracts canonical Markdown/TXT merge and PDF merge package owners, proving the incremental migration pattern, but many utilities remain in the monolith.

Next: continue capability-by-capability extraction behind node contracts rather than broad monolith rewrite.

## KI-003 — No real K-Tools utility node is integrated yet

Status: RESOLVED

Historical foundation condition. `packages/ktools-json/` is the first real pack; M5 adds Text and PDF capabilities plus the ordered `files.literal` source contract.

## KI-004 — Workflow/run/artifact persistence is absent

Status: RESOLVED

M2 implements durable run/node history with RunJournal + SQLite. M4 implements persistent Artifact occurrence/validity observations and semantic cache.

Automatic continuation of old in-flight RUNNING work remains ownership-gated; this is a deliberate recovery-safety boundary, not missing persistence.

## KI-005 — Visual workflow editor is absent

Status: OPEN

No production canvas/palette/inspector/run UI exists yet.

Research and the audited spike identify `@xyflow/react` as the preferred implementation layer while `ktools-core` remains runtime authority. Desktop-host integration and target-environment performance remain unproved.

## KI-006 — No adapter boundary to imported apps yet

Status: OPEN

XCursos and YouTube remain standalone subsystems until adapter contracts are specified and tested.

## KI-007 — Historical GitHub Actions jobs were blocked by billing/spending state

Status: RESOLVED

Historical runs `33327645359` and `33327842478` failed before product steps because GitHub UI reported account payment/spending-limit state. After the repository became public, run `33330660076` on `1ccffb11af25a8d993ead931183380d354746131` reached and passed checkout/setup/install/tests/smoke on Ubuntu/Windows.

Future CI failures must be classified from their actual first failing step rather than carried forward from this incident.

## KI-008 — Legacy stable GUI is not yet wired to canonical Text Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-text` is the canonical evolution owner for Markdown/TXT merge, but `K Tools Neo - Versão Estável 2.py` still executes its historical implementation.

Invariant: new behavior/bug fixes originate in `ktools-text`; the historical copy is frozen until traditional Tool/UI migration redirects/removes it.

## KI-009 — Legacy stable GUI is not yet wired to canonical PDF Node Pack

Status: OPEN / EXPLICIT COMPATIBILITY DEBT

`packages/ktools-pdf` is the canonical evolution owner for PDF merge after M5 Slice 2 final promotion, but the stable GUI still contains and invokes its historical PDF merge implementation.

Impact: direct edits to the old copy could drift from the tested package behavior.

Invariant: new PDF merge behavior/bug fixes originate in `ktools-pdf`; the historical implementation is a compatibility path only.

Next: when the traditional PDF Tool surface is migrated to platform workflows, redirect it to `ktools-pdf` and remove/reduce the duplicate. Do not block bounded capability extraction on a full GUI rewrite.

## KI-010 — Shared temp-then-replace pattern is repeated across file-producing packs

Status: OPEN / OBSERVE BEFORE ABSTRACTING

Text and PDF writers both use same-directory temporary publication followed by final replacement, but their write/finalization contracts differ.

Do not create a generic core abstraction merely because two implementations look similar. Re-evaluate after another file-producing pack shows a stable cross-domain API for temp allocation, cleanup and promotion without leaking writer-specific semantics.
