# Spec — Text Split Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 — Official local Node Packs, Slice 4
Owner/implementer: ChatGPT Solo Development Mode

## Objective

Extend canonical `packages/ktools-text/` with the legacy balanced MD/TXT split capability so one local text document can be divided into an ordered FILE_SET of safely published text Artifacts through one shared direct-API/workflow implementation owner.

Historical characterization sources in `K Tools Neo - Versão Estável 2.py`:

- `read_text_document_with_fallback(...)`;
- `split_text_balanced(...)`;
- `write_text_document_parts(...)`;
- mixed `split_document_files_into_parts(...)`, which already delegates PDF work to `split_pdf_into_parts(...)` and MD/TXT work to `write_text_document_parts(...)`.

## Slice selection

Fresh discovery after terminal PDF Split V1 compared the actual remaining boundaries:

| Candidate | Dependency/security boundary | New contract pressure | Duplicate-owner reduction | Slice-4 fit |
|---|---|---|---|---:|
| Text split | stdlib only; existing Text pack | FILE -> FILE_SET, pure planner + publication | removes the last primitive embedded in mixed Document Split | **selected** |
| Mixed Document Split | no new dependency | dispatch + aggregation across Text/PDF | would still own text split unless Text Split is extracted first | after this slice |
| Images→PDF | new Pillow boundary | EXIF, alpha flattening, animation, decompression-bomb policy | standalone | later |
| WebP→PNG | new Pillow boundary | alpha/animation + image FILE_SET | standalone | later |
| Files/Folders scan | stdlib | traversal/filter/error/report semantics | broad surface | later bounded slice |

Text Split is selected because it has the smallest new dependency/security surface, a clear legacy oracle, reuses `file.literal`/FILE_SET from Slice 3, and turns future mixed Document Split into an orchestration problem instead of another capability-owner migration.

## Legacy behavior to characterize

### Decode boundary

The document-split path tries encodings in this order:

1. `utf-8-sig`;
2. `utf-8`;
3. `cp1252`;
4. `latin-1`.

This differs from the existing Text Merge decoder (`utf-8-sig`, `utf-8`, `latin-1`). Do **not** silently change merge decoding in this slice merely to share a helper.

### Balanced split

- `parts >= 2`;
- empty source text fails;
- split units are `content.splitlines(keepends=True)`;
- requested parts clamp to the number of line units;
- target size starts from total character count / remaining parts;
- lines are indivisible units;
- a chunk closes after reaching/exceeding the current target only when enough units remain for later parts;
- target is recomputed from remaining characters after each closed chunk;
- whitespace-only chunks are filtered;
- if no non-whitespace chunk remains, fail;
- actual output count may therefore be less than requested/clamped count for degenerate whitespace layouts.

### Publication

- output folder is created when absent;
- output names use `{stem}_parte_{index:02d}_de_{actual_count:02d}{source_suffix_lower}`;
- existing or same-batch reserved paths are not overwritten: select `_1`, `_2`, ... before the suffix;
- every chunk is written as UTF-8 regardless of detected source encoding;
- existing line endings inside the chunk are preserved by writing with `newline=""`;
- each output is temp-then-replace published;
- output order follows chunk order;
- progress is supplemental and owns no split semantics.

V1 may normalize error wording but must not silently change decode order, line-unit split behavior, output UTF-8 normalization, chunk order, collision avoidance or per-part publication semantics.

## Package boundary

Extend `ktools-text`; do not create a second text package:

```text
packages/ktools-text/src/ktools_text/
  capability.py     # existing merge renderer
  writer.py         # existing merge writer + reusable atomic text-content publication
  splitter.py       # split decoder/planner/publication owner
  api.py            # thin direct APIs
  node.py           # thin workflow adapters
```

One-owner path:

```text
split decoder + balanced planner + atomic text publisher
                      ↓
         splitter.split_text_file_into_parts
             ↙                    ↘
        direct API             text.split.parts
```

The node adapter must not contain decode fallback, line balancing, chunking, collision naming or file-publication logic.

## Pure planner boundary

`splitter.split_text_balanced(content, parts)` is a pure deterministic function and should be directly unit tested. It does not need a separate public workflow node in V1; the user-facing migrated capability is file split.

A future planner node may be added only if a real workflow needs in-memory TEXT→collection planning independently of file publication.

## Text split node contract

Type id: `text.split.parts`

Input:

- `file: FILE` — runtime-validated as local `.md` or `.txt`.

Output:

- `files: FILE_SET` — ordered output Artifacts, each `type == FILE`.

Config:

- `output_dir`: required destination directory string;
- `parts`: required integer >= 2; bool is rejected.

Version: `1`.
Cache policy: `NEVER`.

Reason: publishing the requested chunk files is required behavior. Repeated runs in the same directory intentionally choose new collision-safe names rather than substituting old Artifact references.

## Artifact semantics

Every output Artifact:

- `type == FILE`;
- local normalized `file://` URI;
- `produced_by = {run_id}/{node_id}` for workflow execution;
- MIME `text/markdown` for `.md`, `text/plain` for `.txt`;
- JSON-safe metadata including `sourceName`, `sourceEncoding`, `partIndex`, `partCount`, `charCount`, `lineCount`, and `format`.

No domain-specific TEXT_FILE_SET type is introduced. Existing FILE_SET + member metadata/type is sufficient for V1.

## Atomic publication and partial-set failure

Add/reuse a Text-pack atomic text-content publication helper without generalizing it into `ktools-core`.

V1 is atomic per part, not transactional across the whole FILE_SET:

- a successfully completed earlier part may remain if a later publication fails;
- the failing destination must not contain a partial file;
- temp residue for the failed output must be cleaned where practical;
- no Artifact is returned/recorded for an output that did not publish successfully.

## Decode-policy non-unification decision

Do not change existing Text Merge decoding merely to remove visual duplication. Text Merge and legacy Document Split currently have different fallback orders. Sharing a helper is only correct if the helper can preserve caller-specific policy without changing bytes/characters.

A small policy-driven internal helper is acceptable if tests prove both existing Merge behavior and Split legacy behavior remain unchanged; otherwise keep the split decoder local in `splitter.py` for V1.

## Direct/workflow equivalence

In independent clean directories, the direct API and workflow node must emit byte-identical UTF-8 parts for equivalent source/config.

## Composition proof

Use the real workflow:

```text
file.literal -> text.split.parts -> text.merge.files
```

This is a type/composition proof, **not** a claim that Text Merge is an inverse of Text Split. `text.merge.files` has its own separator contract. With `separator_mode="nenhum"`, the expected merged bytes are the ordered emitted chunk texts with the merge node's documented `\n\n` suffix behavior.

Also prove separately that concatenating clean split chunk text values in order reproduces the decoded source text for a normal non-degenerate fixture.

## Acceptance

### A — characterization RED

- [ ] missing/directory/non-text source rejected;
- [ ] parts < 2, bool and non-integer rejected;
- [ ] decode order distinguishes cp1252 from latin-1 where bytes make that observable;
- [ ] empty/whitespace-only content fails closed;
- [ ] requested parts clamp to line-unit count;
- [ ] balanced line-preserving split characterized on uneven line lengths;
- [ ] clean-folder naming and actual part count characterized;
- [ ] collision-safe `_1`, `_2`, ... naming characterized;
- [ ] outputs are UTF-8 and preserve in-chunk line endings;
- [ ] progress reaches completion without owning semantics.

### B — package owner

- [ ] pure `split_text_balanced` owner exists;
- [ ] `split_text_file_into_parts` owns decode + plan + publication orchestration;
- [ ] direct API delegates to splitter;
- [ ] node adapter delegates to splitter;
- [ ] adapter contains no decode/chunk/collision/publication algorithm;
- [ ] existing Text Merge decoding/bytes remain regression-green.

### C — workflow/Artifact contract

- [ ] `text.split.parts: FILE -> FILE_SET`, version 1, NEVER;
- [ ] every output is a FILE Artifact with MIME/provenance/chunk metadata;
- [ ] ArtifactRegistry records/snapshots nested outputs;
- [ ] cached `file.literal` may be reused while split still executes;
- [ ] repeated split collision-safely republishes rather than overwriting/cache-skipping.

### D — failure semantics

- [ ] forced later-part failure preserves earlier completed part;
- [ ] failed destination is absent/unchanged and temp residue is cleaned;
- [ ] no successful output list is returned for the failed operation.

### E — equivalence/composition

- [ ] direct API/workflow emit byte-identical parts in clean independent directories;
- [ ] ordered clean chunks concatenate to decoded normal source text;
- [ ] `file.literal -> text.split.parts -> text.merge.files` executes successfully with documented merge separator behavior.

### F — hosted regression

- [ ] Core/JSON/PDF suites remain green;
- [ ] Text suite passes Ubuntu/Windows Python 3.10/3.13;
- [ ] hosted Text split→merge workflow smoke verifies emitted chunks and downstream merge on all Python lanes if inexpensive;
- [ ] xyflow remains green.

## Non-goals

- mixed Document Split orchestration in this slice;
- paragraph/Markdown-heading semantic splitting beyond the characterized line-based algorithm;
- byte-preserving original encoding output (V1 normalizes parts to UTF-8 as legacy Document Split does);
- arbitrary character/byte-size split mode;
- TEXT_FILE_SET or specialized collection types;
- all-or-nothing transaction across the entire output set;
- Images→PDF/WebP work;
- production editor/UI changes;
- broad stable-GUI rewrite.

## Promotion rule

Promote only after discriminating RED, GREEN, integration audit, exact-head Windows/Linux + xyflow hosted evidence, explicit canonical ownership/debt classification, memory closure and green terminal `main` HEAD.
