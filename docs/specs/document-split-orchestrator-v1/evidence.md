# Evidence — Mixed Document Split Orchestrator V1

Status: **DISCOVERY ACCEPTED / RED PENDING**

## Prerequisite gate

Text Split V1 terminal closure:

- terminal HEAD `4a52bef50653aa11878351645d122d0c0ab52343`;
- run `33661273251`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Slice 4 is terminal-green before Slice 5 implementation begins.

## Fresh discovery facts

The historical mixed dispatcher filters compatible `.md/.txt/.pdf` inputs, validates `parts >= 2`, creates the destination, gives every compatible source an equal progress span, delegates PDFs to `split_pdf_into_parts(...)`, delegates Markdown/TXT to `write_text_document_parts(...)`, catches errors per source, continues later files, flattens successful outputs in source order, fails only when no output was produced, and returns a UI-consumed result containing `outputs`, `errors`, `output_folder`, `input_count` and `output_count`.

This is now an orchestration contract because both primitive branches already have canonical package owners.

## Candidate comparison

### Mixed Document Split — selected

No new transformation dependency. New pressure is batch result/report semantics, partial success, progress weighting and cross-pack orchestration. It removes a real legacy owner without duplicating primitive logic.

### Images→PDF

Requires a Pillow policy already visible in the monolith: image-size/decompression-bomb limits, EXIF orientation normalization, alpha/background decisions and animated-image handling. Valuable but a larger security/semantic boundary.

### WebP→PNG

Also requires the Pillow safety boundary plus explicit animation and transparency policy. It should follow a deliberate image-pack foundation rather than an ad-hoc extraction.

### Files/Folders

Stdlib-only but broad: traversal, hidden/subfolder policy, filtering, result schema, error aggregation and report/export semantics. A dedicated bounded spec is required.

## Selected architectural hypothesis

Create `packages/ktools-documents` depending on `ktools-core`, `ktools-text` and `ktools-pdf`.

The pack owns only batch dispatch/aggregation/progress/errors. It must call canonical child splitters and preserve their Artifacts. The node contract is proposed as:

```text
document.split.files
  files: FILE_SET
      -> files: FILE_SET
      -> report: JSON
```

version 1, NEVER.

The JSON report is necessary because legacy partial-success errors are product state, not merely diagnostics.

## Next evidence gate

The next accepted evidence is a hosted discriminating RED that reaches the new Documents tests after existing Core/JSON/Text/PDF boundaries remain green and fails because the documents package/batch owner/node do not yet exist. Packaging/runner failures do not count as product RED.
