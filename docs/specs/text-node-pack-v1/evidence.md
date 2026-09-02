# Evidence — Text Node Pack V1

Status: **CODE ACCEPTED / CANONICAL MEMORY CI PENDING**

## Candidate selection

The stable monolith contains a bounded `merge_text_files(...)` operation for `.md`/`.txt`, with validation, decoding fallback, separator modes, output/input collision guard and temporary publication.

Alternative first slices were deferred:

- WebP → PNG requires Pillow plus image decompression safety, EXIF transpose, alpha-mode handling, animated-image first-frame policy and output collision logic;
- generic folder scanning is currently an instance/UI helper parameterized by callbacks and is less clean as the first standalone capability owner.

## M4 prerequisite

M4 was promoted before M5 code began.

Formal promotion HEAD: `b09e6ac62fa74e3e1a22e7cced0a472af50285b1`.

Promotion run: `33626260487` — all five jobs success.

## RED evidence

Characterization commit: `1660a4dbac7efc7f21d7a96bfdebde8ffc13edd2`.

Run: `33626957901`.

The harness/package boundary succeeded: checkout, Python setup and editable installs of core/JSON/Text were reached. The first product boundary failed in core tests exactly because the new contracts did not yet exist:

- three errors: `DataType.FILE_SET` absent;
- one error: `files.literal` absent.

Existing pre-M5 core tests remained green before those four new RED errors. xyflow remained green. This is accepted as a discriminating RED rather than a packaging/platform failure.

## GREEN and hardening

Initial implementation commit: `a7cbcbe408939187bcb15514e6b6ca2ad0585206`.

It established FILE_SET, `files.literal`, `ktools-text`, the shared writer/direct API and `text.merge.files`.

Hardening added direct↔workflow byte equivalence, real source-file cache invalidation and a hosted Text workflow smoke.

Integration review then found a real duplication not exposed by green behavior tests: both M4 cache identity and the Text adapter independently parsed `file://` URIs. The duplicate was removed by `dbd39a1119ce1557d802a115404f01a3f797d93e`, introducing `ktools_core.local_files.path_from_file_uri()` as the shared owner.

## Accepted code candidate

HEAD: `dbd39a1119ce1557d802a115404f01a3f797d93e`.

Hosted run: `33627879876`.

All five jobs succeeded:

- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow spike — success.

Representative Ubuntu/Python 3.10 evidence:

- `ktools-core`: 72 tests, OK;
- `ktools-json`: 64 tests, OK;
- `ktools-text`: 15 tests, OK;
- core CLI smoke — success;
- JSON workflow smoke + artifact verification — success;
- Text workflow smoke generated a FILE Artifact and `merged.md` with exact `Alpha\n\nBeta\n\n` content — success.

The corresponding Text install/tests/smoke also passed in both Windows lanes and Ubuntu/Python 3.13.

## Behavior evidence

Tests prove:

- FILE_SET is a distinct exact typed collection port;
- `files.literal` preserves order and returns FILE Artifacts;
- `files.literal` can be cached while files remain strongly valid;
- changing source content invalidates cached output and executes source again;
- BOM/UTF-8/latin-1 reading order matches characterized behavior;
- `completo`, `simples` and `nenhum` formatting bytes match the legacy contract;
- publication uses temp output and preserves a previous destination on a handled pre-replacement failure;
- direct API and workflow route are byte-identical;
- both direct API and workflow adapter delegate to `writer.merge_text_files`;
- `text.merge.files` is `NEVER` and republishes on equivalent repeated runs;
- output Artifact carries current run/node provenance;
- ArtifactRegistry records the executed output occurrence with strong snapshot;
- M4 and Text use one local-file URI interpretation owner after refactor.

## Ownership evidence/boundary

Canonical merge owner after promotion: `packages/ktools-text/src/ktools_text/`.

`K Tools Neo - Versão Estável 2.py` remains an old stable GUI/runtime path and still contains historical merge logic. It is explicitly frozen as compatibility debt for this capability: new semantics/bug fixes originate in `ktools-text`. A later GUI-adapter slice must redirect/remove the historical copy.

This is not presented as physical code deletion; it is an explicit owner boundary with remaining debt tracked in `KNOWN_ISSUES.md`.

## Pending promotion evidence

The synchronized canonical-memory commit created from this evidence must itself pass the same five-job hosted matrix before PR #8 can be marked ready/merged.
