# Spec — Text Node Pack V1

Status: **IMPLEMENTATION COMPLETE / CANONICAL MEMORY CI PENDING**
Milestone: M5 — first local Node Pack slice
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Migrate the existing Markdown/TXT merge behavior out of the legacy CustomTkinter monolith into a reusable, testable Text Node Pack without duplicating business logic and without weakening M0-M4 runtime contracts.

The first delivered behavior is the real legacy operation historically implemented by `merge_text_files(...)` in `K Tools Neo - Versão Estável 2.py`.

After successful promotion, that legacy function remains a **characterization/compatibility source**, not the canonical place to evolve behavior. The canonical implementation owner becomes `packages/ktools-text/`.

## Why this slice first

Discovery compared three real candidates:

| Candidate | Existing owner | Native/external coupling | Contract complexity | First-slice fit |
|---|---|---:|---:|---:|
| Markdown/TXT merge | bounded function `merge_text_files` | stdlib only | low/moderate | **preferred** |
| WebP → PNG | bounded `convert_webp_to_png` | Pillow + image safety/EXIF/alpha/animation | moderate/high | later Image pack |
| folder scan | `_scan_files_in_folder` UI method | UI callback/filter coupling | moderate | later Files pack |

Markdown/TXT merge is useful product behavior, deterministic at its transformation core, has simple filesystem side effects, already uses temporary output replacement, and is the smallest slice that exercises typed multiple-file inputs plus first-class Artifact output.

## Legacy behavior source of truth

For supported usage, the stable monolith establishes:

- inputs are ordered `.md` / `.txt` files;
- empty input is rejected;
- each input must exist, be a file and use a supported extension;
- text decoding tries `utf-8-sig`, then `utf-8`, then `latin-1`;
- output extension is `.md` when caller supplies a non-`.md`/`.txt` suffix;
- output may not be one of the input files;
- output parent is created;
- writing occurs through a temporary file in the destination directory before final replacement;
- successful final publication uses `os.replace` and therefore replaces an existing non-input destination;
- failure before final replacement preserves the previous destination and cleans the temporary output where possible;
- separator mode `completo` adds per-file start/end provenance markers;
- separator mode `simples` adds a Markdown heading with the source filename;
- separator mode `nenhum` concatenates content without provenance headings;
- every non-`completo` source is followed by two newline characters;
- input order is preserved;
- progress callback is supplementary and must not own semantics.

The new package may classify invalid unsupported direct-API values more explicitly, but valid legacy behavior must remain byte-equivalent unless an intentional difference is documented and tested.

## Package boundary

Created:

```text
packages/ktools-text/
  pyproject.toml
  README.md
  examples/
  src/ktools_text/
    __init__.py
    capability.py
    writer.py
    api.py
    node.py
  tests/
```

One-owner flow:

```text
pure formatting owner
        ↓
text file writer/orchestrator
   ↙                 ↘
direct API        workflow node
```

Concretely:

```text
render_document_block
        ↓
writer.merge_text_files
   ↙                 ↘
api.merge_text_files   text.merge.files
```

`render_merged_text` remains a deterministic higher-level rendering/characterization surface. The filesystem writer deliberately streams `render_document_block(...)` one source at a time rather than loading every file into one large in-memory string.

The workflow node must not reimplement merge/render/encoding/publication logic.

## Typed multi-file contract

M5 introduces `DataType.FILE_SET` in `ktools-core`.

V1 semantics:

- a FILE_SET runtime value is an **ordered** list/tuple of `Artifact` values;
- order is semantic and must be preserved in cache signatures and merge output;
- FILE_SET is not interchangeable with JSON or ANY merely for convenience;
- FILE and FILE_SET are not implicitly interchangeable;
- no new collection object is required in V1 because M4 cache identity and Artifact registry already traverse list/tuple containers recursively;
- static compatibility is exact FILE_SET → FILE_SET in this slice; subtype-collection covariance is deferred until there is a real need.

`files.literal` is the minimum built-in source that makes this contract composable before production UI work. It accepts configured local paths, validates them, preserves configured order and emits FILE Artifacts through a FILE_SET output.

`files.literal` is explicitly `PURE` because it publishes no external side effect. This is safe only together with M4 output-Artifact validation: cached results are strongly revalidated, and a missing/changed source file invalidates the cache candidate and causes normal execution.

Runtime validation of the Text node rejects non-sequences, empty sequences, non-Artifact items, non-local-file Artifacts and unsupported text-file inputs.

## Node contract

Initial node type:

`text.merge.files`

Inputs:

- `files: FILE_SET` — required, ordered source Artifacts.

Outputs:

- `file: FILE` — required output Artifact.

Config:

- `output_path` — required destination path/string;
- `separator_mode` — `completo`, `simples`, or `nenhum`; default `completo`.

Cache policy:

- `NEVER` in V1.

Reason: the node publishes/replaces a requested filesystem result. A cached metadata result is not a substitute for performing the required publication side effect. The fact that formatting is deterministic does not make the publication node safe to skip.

A later pure render node may be added only if it improves real composition without duplicating the transformation owner.

Node version starts at `1`.

## Artifact semantics

The node returns a first-class `Artifact` for the published output, not a naked path string.

Required output Artifact fields/semantics:

- type `FILE`;
- normalized local `file://` URI;
- `produced_by` identifies the current `run_id/node_id`;
- metadata remains JSON-safe and may include source count, separator mode and text format;
- MIME type reflects Markdown versus plain text output.

With an injected ArtifactRegistry, the normal M4 runtime persists the output occurrence as `EXECUTED` and strong-snapshots it when supported.

## Shared local-file URI boundary

Integration review discovered a platform-level duplication after behavior had already gone GREEN: M4 cache identity and the new Text adapter each contained independent `file:// URI → Path` parsing.

That duplication is removed before promotion.

`ktools_core.local_files.path_from_file_uri()` is now the single V1 owner for local file URI interpretation:

- ordinary local `file://` URIs are supported;
- `file://localhost/...` is treated as local;
- remote/UNC authorities fail closed in V1;
- Windows drive-letter URI normalization is handled centrally.

Platform/capability-specific callers translate `LocalFileUriError` into their own public taxonomy (`UnsupportedArtifactError` for Artifact validity, `TextMergeError` for the Text capability).

## Publication safety

The writer must and now does:

- never use an input path as output;
- create output parent when needed;
- write UTF-8 text;
- use same-directory temporary output;
- replace final output only after successful complete write;
- replace an existing non-input destination on success, matching characterized legacy `os.replace` behavior;
- clean partial temporary output after handled failure where possible;
- preserve a previously valid destination when failure occurs before final replacement.

## Diagnostics

No subprocess/native boundary exists in this slice.

When a DiagnosticsSession is present, engine lifecycle already records node start/success/failure. The Text pack does not add noisy duplicate logging merely to satisfy a checklist.

Domain-specific diagnostics may be added later only when they add operational facts not already represented, such as decoding fallback usage or source-count/output-size metrics that prove useful in real support cases.

## Canonical ownership and legacy compatibility debt

After promotion, canonical Markdown/TXT merge evolution belongs to:

`packages/ktools-text/src/ktools_text/`

The old stable GUI still contains and invokes its historical implementation. This is deliberately **not** described as physically removed or redirected in V1.

Instead:

- the old implementation is frozen as compatibility debt;
- new behavior and bug fixes originate in `ktools-text`;
- a later traditional Tool/UI migration must redirect the old GUI surface to the canonical package/runtime and remove or reduce the historical duplicate;
- this debt is explicitly tracked in `docs/KNOWN_ISSUES.md`.

This satisfies the one-owner architecture at the evolution/contract level without disguising the fact that a legacy compatibility path still exists.

## Acceptance

### A — core FILE_SET contract

- [x] `DataType.FILE_SET` exists;
- [x] FILE_SET typed edge validates;
- [x] FILE cannot feed FILE_SET;
- [x] FILE_SET cannot feed FILE;
- [x] existing type compatibility remains green;
- [x] ordered list/tuple Artifact values remain semantically ordered in M4 signature behavior;
- [x] `files.literal` emits ordered FILE Artifacts through FILE_SET;
- [x] `files.literal` rejects missing/empty configured paths;
- [x] source-file mutation invalidates a cached `files.literal` result rather than returning stale Artifacts.

### B — pure/characterized merge behavior

- [x] empty input rejected;
- [x] missing/non-file/unsupported input rejected;
- [x] input order preserved;
- [x] UTF-8 BOM is removed through `utf-8-sig` behavior;
- [x] UTF-8 content round-trips;
- [x] latin-1 fallback works;
- [x] `completo` output matches characterized legacy bytes;
- [x] `simples` output matches characterized legacy bytes;
- [x] `nenhum` output matches characterized legacy bytes;
- [x] destination suffix normalization matches legacy valid behavior.

### C — filesystem publication safety

- [x] output cannot be one of the inputs;
- [x] destination parent is created;
- [x] incomplete write does not replace a previously valid destination;
- [x] successful write is atomically/safely promoted through same-directory temp replacement;
- [x] existing non-input destination is replaced on successful publication, matching the legacy contract;
- [x] no orphan temp output remains after handled failure where cleanup is possible.

### D — one-owner package architecture

- [x] direct API reaches the shared writer/capability owner;
- [x] workflow node reaches the same owner;
- [x] structural regression rejects merge algorithm duplication inside node adapter;
- [x] direct API and node produce byte-identical output for equivalent input/config;
- [x] local file URI parsing is centralized in `ktools-core` rather than duplicated in Text;
- [x] canonical evolution ownership is documented and the remaining GUI copy is explicitly classified as compatibility debt.

### E — workflow / Artifact integration

- [x] node accepts ordered FILE_SET;
- [x] node returns FILE Artifact;
- [x] output Artifact uses current run/node provenance;
- [x] ArtifactRegistry records output occurrence/strong snapshot;
- [x] node remains NEVER and executes on repeated equivalent runs even when cache is injected;
- [x] upstream FILE_SET source may be cached independently without causing merge publication to be skipped;
- [x] changed source content invalidates cached source Artifacts.

### F — hosted regression

- [x] root CI installs `ktools-text`;
- [x] Text pack suite runs on Ubuntu/Windows Python 3.10/3.13 on the accepted code candidate;
- [x] existing core/JSON tests remain green;
- [x] existing JSON CLI/workflow smoke remains green;
- [x] new Text workflow smoke proves a real merged file and exact content;
- [x] xyflow spike remains green;
- [ ] final synchronized canonical-memory HEAD passes the same hosted matrix before PR #8 merge.

## Accepted code evidence

Accepted code candidate:

`dbd39a1119ce1557d802a115404f01a3f797d93e`

Hosted run:

`33627879876`

Result: five of five jobs succeeded.

Representative Ubuntu/Python 3.10 evidence:

- core suite: 72 tests, OK;
- JSON Node Pack: 64 tests, OK;
- Text Node Pack: 15 tests, OK;
- core CLI smoke: success;
- JSON workflow + generated Artifact verification: success;
- Text workflow: success;
- generated `merged.md` exact content `Alpha\n\nBeta\n\n`: success.

Equivalent package/test/smoke boundaries also passed on Ubuntu/Python 3.13 and Windows/Python 3.10/3.13; xyflow remained green.

Full evidence: `docs/specs/text-node-pack-v1/evidence.md`.

## Non-goals

- broad Text toolbox in one change;
- rich Markdown parsing/reformatting;
- PDF/image/media operations;
- automatic folder scanning UI changes;
- FFmpeg/FFprobe;
- dynamic plugin loading;
- production visual editor;
- cache replay of file-publication side effects;
- replacing the entire legacy GUI in this slice;
- physically deleting the historical GUI merge implementation before the traditional surface is migrated.

## Promotion rule

The legacy owner is not considered migrated merely because a new copy exists.

V1 is promoted only after:

1. supported behavior is characterized and proved equivalent;
2. direct API and workflow use the same canonical package owner;
3. remaining historical GUI ownership is explicitly redirected, deprecated or otherwise classified so it is not treated as a second canonical evolution path;
4. exact accepted code passes hosted Windows/Linux evidence;
5. synchronized canonical state/decision/journal/evidence documentation passes the same exact-head hosted gate;
6. PR #8 is merged with exact-head protection and post-merge `main` CI is green.
