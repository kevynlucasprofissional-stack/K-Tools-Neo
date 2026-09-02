# Evidence — PDF Split Node V1

Status: **DISCOVERY ACCEPTED / RED PENDING**

## Prerequisite gate

PDF Merge V1 terminal closure:

- terminal HEAD `e3a3934aada29e185de7da18cf413ceaa3c299e8`;
- run `33651923578`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 2 is therefore closed before Slice 3 implementation begins.

## Discovery evidence

Remaining bounded owners in the stable monolith include PDF split, Images→PDF, WebP→PNG, mixed Document Split and folder scanning/reporting.

PDF split is selected because:

- it reuses the already accepted `pypdf` dependency and checked-reader/atomic-publication boundary;
- it adds a genuine one-file-input/multi-file-output workflow contract rather than another merge-shaped operation;
- it produces an ordered FILE_SET whose members can remain first-class PDF Artifacts;
- the monolith's mixed Document Split already calls `split_pdf_into_parts(...)`, so extraction removes a prerequisite for a later cross-pack orchestration slice;
- no new native/subprocess or image-security boundary is introduced.

Images→PDF and WebP→PNG remain valuable but introduce Pillow-specific EXIF/alpha/animation/decompression policy. Document Split is better sequenced after PDF and Text primitives are canonical. Files/Folders scan is stdlib-only but has a broader traversal/filter/report contract.

## Characterization facts from legacy owner

Observed legacy PDF split behavior:

- validates one PDF path and `parts >= 2`;
- uses checked PDF reader;
- clamps parts to page count;
- balances contiguous ranges with remaining-pages/remaining-parts ceiling allocation;
- example: 5 pages / 3 parts => 2, 2, 1;
- names parts `{stem}_parte_XX_de_YY.pdf` using actual clamped part count;
- `safe_unique_path` avoids overwrite by selecting `_1`, `_2`, ... suffixes;
- each part uses atomic PDF publication;
- returns ordered output paths;
- Document Split delegates PDF handling to this function.

## Architectural decision pending proof

V1 proposes `pdf.split.parts: FILE -> FILE_SET` plus builtin `file.literal: -> FILE`.

No `PDF_SET` is introduced because individual members retain `Artifact.type == PDF` and direct split→merge composition is more useful than a new collection compatibility layer.

## Next evidence gate

The next accepted evidence is a discriminating RED that reaches product tests and fails because `file.literal` / `pdf.split.parts` / shared split implementation are absent. Packaging, runner or dependency failures do not count as product RED.
