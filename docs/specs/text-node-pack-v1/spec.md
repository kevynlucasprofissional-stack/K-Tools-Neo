# Spec — Text Node Pack V1

Status: **ACTIVE**
Milestone: M5 — first local Node Pack slice
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Migrate the existing Markdown/TXT merge behavior out of the legacy CustomTkinter monolith into a reusable, testable Text Node Pack without duplicating business logic and without weakening M0-M4 runtime contracts.

The first delivered behavior is the real legacy operation currently owned by `merge_text_files(...)` in `K Tools Neo - Versão Estável 2.py`.

## Why this slice first

Discovery compared three real candidates:

| Candidate | Existing owner | Native/external coupling | Contract complexity | First-slice fit |
|---|---|---:|---:|---:|
| Markdown/TXT merge | bounded function `merge_text_files` | stdlib only | low/moderate | **preferred** |
| WebP → PNG | bounded `convert_webp_to_png` | Pillow + image safety/EXIF/alpha/animation | moderate/high | later Image pack |
| folder scan | `_scan_files_in_folder` UI method | UI callback/filter coupling | moderate | later Files pack |

Markdown/TXT merge is useful product behavior, deterministic at its transformation core, has simple filesystem side effects, already uses temporary output replacement, and is the smallest slice that exercises typed multiple-file inputs plus first-class Artifact output.

## Legacy behavior source of truth

For supported usage, the stable monolith currently establishes:

- inputs are ordered `.md` / `.txt` files;
- empty input is rejected;
- each input must exist, be a file and use a supported extension;
- text decoding tries `utf-8-sig`, then `utf-8`, then `latin-1`;
- output extension is `.md` when caller supplies a non-`.md`/`.txt` suffix;
- output may not be one of the input files;
- output parent is created;
- writing occurs through a temporary file in the destination directory before final replacement;
- separator mode `completo` adds per-file start/end provenance markers;
- separator mode `simples` adds a Markdown heading with the source filename;
- separator mode `nenhum` concatenates content without provenance headings;
- input order is preserved;
- progress callback is supplementary and must not own semantics.

The new package may classify invalid unsupported direct-API values more explicitly, but valid legacy UI behavior must remain byte-equivalent unless an intentional difference is documented and tested.

## Package boundary

Create:

```text
packages/ktools-text/
  pyproject.toml
  README.md
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

The workflow node must not reimplement merge/render/encoding/publication logic.

## Typed multi-file contract

M5 introduces `DataType.FILE_SET` in `ktools-core`.

V1 semantics:

- a FILE_SET runtime value is an **ordered** list/tuple of `Artifact` values;
- order is semantic and must be preserved in cache signatures and merge output;
- FILE_SET is not interchangeable with JSON or ANY merely for convenience;
- no new collection object is required in V1 because M4 cache identity and Artifact registry already traverse list/tuple containers recursively;
- static compatibility is exact FILE_SET → FILE_SET in this slice; subtype-collection covariance is deferred until there is a real need.

Runtime validation of the text node must reject non-sequences, empty sequences, non-Artifact items, non-local-file Artifacts and unsupported extensions.

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

Reason: the node publishes/replaces a requested filesystem result. A cached metadata result is not a substitute for performing the required publication side effect. A later pure render node may be added only if it improves real composition without duplicating the transformation owner.

Node version starts at `1`.

## Artifact semantics

The node returns a first-class `Artifact` for the published output, not a naked path string.

Required output Artifact fields:

- type `FILE`;
- normalized `file://` URI;
- `produced_by` identifies the current `run_id/node_id`;
- useful metadata may include source count, separator mode and text format, but must stay JSON-safe and non-sensitive.

With an injected ArtifactRegistry, the normal M4 runtime must persist the output occurrence as `EXECUTED` and strong-snapshot it when possible.

## Publication safety

The writer must:

- never use an input path as output;
- create output parent when needed;
- write UTF-8 text;
- use same-directory temporary output;
- replace final output only after successful complete write;
- clean partial temporary output after failure where possible;
- not silently overwrite a destination unless the direct/node contract explicitly allows the legacy replacement behavior being characterized.

The exact overwrite behavior of legacy `replace_temp_output(...)` must be characterized before locking acceptance.

## Diagnostics

No subprocess boundary exists in this slice.

When a DiagnosticsSession is present, engine lifecycle already records node start/success/failure. The Text pack may emit domain-specific diagnostics only when they add operational facts not already represented, such as decoding fallback used or source-count/output-size metrics.

Do not add noisy duplicate logging merely to satisfy a checklist.

## Acceptance

### A — core FILE_SET contract

- [ ] `DataType.FILE_SET` exists;
- [ ] FILE_SET typed edge validates;
- [ ] FILE cannot feed FILE_SET;
- [ ] FILE_SET cannot feed FILE;
- [ ] existing type compatibility remains green;
- [ ] ordered list/tuple Artifact values already remain semantically ordered in M4 signature behavior.

### B — pure/characterized merge behavior

- [ ] empty input rejected;
- [ ] missing/non-file/unsupported input rejected;
- [ ] input order preserved;
- [ ] UTF-8 BOM is removed through `utf-8-sig` behavior;
- [ ] UTF-8 content round-trips;
- [ ] latin-1 fallback works;
- [ ] `completo` output matches characterized legacy bytes;
- [ ] `simples` output matches characterized legacy bytes;
- [ ] `nenhum` output matches characterized legacy bytes;
- [ ] destination suffix normalization matches legacy valid behavior.

### C — filesystem publication safety

- [ ] output cannot be one of the inputs;
- [ ] destination parent is created;
- [ ] incomplete write does not replace a previously valid destination;
- [ ] successful write is atomically/safely promoted through same-directory temp replacement;
- [ ] no orphan temp output remains after handled failure where cleanup is possible.

### D — one-owner package architecture

- [ ] direct API reaches the shared writer/capability owner;
- [ ] workflow node reaches the same owner;
- [ ] structural regression rejects merge algorithm duplication inside node adapter;
- [ ] direct API and node produce byte-identical output for equivalent input/config.

### E — workflow / Artifact integration

- [ ] node accepts ordered FILE_SET;
- [ ] node returns FILE Artifact;
- [ ] output Artifact uses current run/node provenance;
- [ ] ArtifactRegistry records output occurrence/strong snapshot;
- [ ] node remains NEVER and executes on repeated equivalent runs even when cache is injected;
- [ ] upstream FILE_SET source may later be cached independently without causing merge publication to be skipped.

### F — hosted regression

- [ ] root CI installs `ktools-text`;
- [ ] Text pack suite runs on Ubuntu/Windows Python 3.10/3.13;
- [ ] existing core/JSON tests remain green;
- [ ] existing JSON CLI smoke remains green;
- [ ] new text workflow smoke proves a real merged file;
- [ ] xyflow spike remains green.

## Non-goals

- broad Text toolbox in one change;
- rich Markdown parsing/reformatting;
- PDF/image/media operations;
- automatic folder scanning UI changes;
- FFmpeg/FFprobe;
- dynamic plugin loading;
- production visual editor;
- cache replay of file-publication side effects;
- replacing the entire legacy GUI in this slice.

## Promotion rule

The legacy owner is not considered migrated merely because a new copy exists. V1 is promoted only after the new package/node is proved equivalent for supported behavior and the remaining legacy ownership is explicitly redirected/deprecated or otherwise documented so two independent implementations are not treated as canonical.
