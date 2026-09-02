# Evidence — PDF Merge Node Pack V1

Status: **DISCOVERY ACCEPTED / RED PENDING**

## Slice selection evidence

After Text Node Pack V1 promotion, current `main` was re-inventoried against the stable monolith rather than carrying forward a preselected feature.

Observed bounded owners include:

- `merge_pdf_files(...)`;
- `split_pdf_into_parts(...)`;
- `images_to_pdf(...)`;
- `convert_webp_to_png(...)`;
- `split_document_files_into_parts(...)`.

The legacy PDF merge path already has:

- `.pdf` path validation;
- checked `pypdf.PdfReader(..., strict=False)` opening;
- explicit protected/corrupt/no-readable-page handling;
- output `.pdf` normalization;
- output/input collision protection;
- ordered page append behavior;
- atomic/same-directory temporary publication.

PDF merge is selected because it opens the PDF capability family with one bounded Python dependency and one output Artifact. PDF split adds multi-output naming/partition policy; Pillow-based candidates add image decompression/EXIF/alpha/animation policy; media/FFmpeg remains later and diagnostics-gated.

## Prerequisite evidence

Text Node Pack V1 promotion merge: `958d5bf563cda21673d69865d1508831c599c006`.

Post-merge run: `33630159514` — success.

Final Text memory closure: `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388`.

Closure run: `33631040505` — five of five jobs success.

## Pending evidence

The next accepted evidence must be a discriminating characterization RED for PDF merge behavior and contracts. Packaging/runner failures do not count as product RED.