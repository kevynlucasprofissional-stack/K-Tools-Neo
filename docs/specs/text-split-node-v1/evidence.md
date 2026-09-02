# Evidence — Text Split Node V1

Status: **DISCOVERY ACCEPTED / RED PENDING**

## Prerequisite gate

PDF Split V1 canonical closure:

- terminal HEAD `a26dfcee626eedc27366dfec93be68503343941a`;
- run `33656157870`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 3 is therefore terminal-green before Slice 4 implementation begins.

## Fresh discovery

The legacy mixed Document Split is not one primitive owner. It dispatches:

- `.pdf` -> `split_pdf_into_parts(...)`;
- `.md` / `.txt` -> `write_text_document_parts(...)`.

PDF split is already canonical in `packages/ktools-pdf`. The remaining primitive duplication is the text path.

The text path is built from:

- `read_text_document_with_fallback(...)` using `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`;
- pure `split_text_balanced(...)` using line units with preserved line endings and character-target balancing;
- `write_text_document_parts(...)` using actual chunk count in names, collision-safe paths and UTF-8 per-part publication.

This makes Text Split a prerequisite extraction for a clean future Document Split orchestrator.

## Competing candidate evidence

### Images→PDF

The monolith already carries a Pillow safety boundary: `MAX_IMAGE_TOTAL_PIXELS = 80_000_000`, decompression-bomb warnings/errors, EXIF transpose, animation-first-frame behavior and alpha flattening to white before PDF. This is a valuable slice but materially larger than stdlib-only Text Split.

### WebP→PNG

Also depends on the Pillow safety boundary, EXIF transpose, animated-first-frame policy and alpha preservation. It should share an image package/safety policy rather than being extracted ad hoc.

### Files/Folders scan

Uses traversal/filter/report/error aggregation with hidden/subfolder options and multiple export forms. The capability boundary is broader than one simple scan node and needs a dedicated traversal/result-schema spec.

### Mixed Document Split

Now has one canonical branch (PDF) and one noncanonical branch (Text). Implementing it before Text Split would either duplicate or hide the text owner inside orchestration. Defer until this slice closes.

## Legacy Text Split characterization facts

Observed:

- supported extensions are `.md` and `.txt` in the mixed document flow;
- decode order is `utf-8-sig`, `utf-8`, `cp1252`, `latin-1`;
- empty text fails;
- units are `splitlines(keepends=True)`;
- parts clamp to line-unit count;
- chunk target starts at total chars / parts and is recomputed after each chunk;
- lines remain indivisible;
- whitespace-only chunks are removed;
- output name is `{stem}_parte_XX_de_YY{lower_suffix}` using actual chunk count;
- safe unique naming avoids overwrite;
- output content is written as UTF-8 with `newline=""`;
- each output uses temp-then-replace publication;
- output order follows chunk order.

## Important compatibility distinction

Existing canonical Text Merge currently decodes in the order `utf-8-sig`, `utf-8`, `latin-1`.

The legacy split path inserts `cp1252` before `latin-1`. Therefore a refactor that blindly makes both call one fixed decoder would change existing Merge behavior for some byte sequences. V1 must preserve both policies independently or use a policy-driven helper proved by regression tests.

## Next evidence gate

The next accepted evidence is a hosted discriminating RED that reaches the Text suite after Core/JSON/PDF regressions remain green and fails because `split_text_balanced`, `split_text_file_into_parts` and `text.split.parts` are absent. CI/bootstrap/package failures do not count as product RED.
