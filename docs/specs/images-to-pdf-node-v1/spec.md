# Spec — Images→PDF Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 Slice 7
Canonical implementation target: `packages/ktools-images/`

## Objective

Extract the historical Images→PDF behavior into the canonical Image Node Pack while reusing, rather than copying, the image-safety/EXIF/first-frame foundation proved in Slice 6.

The capability must accept an ordered collection of supported local image files, prepare exactly one PDF page per compatible input, normalize every page to RGB, composite transparency over white, publish one aggregate PDF atomically, and expose the same capability owner through direct API and workflow execution.

## Prerequisite

Slice 6 is terminally promoted at `9b9fc57bd4bfb28d7e23637651a30182ce6f8828`, run `33668942264`, 5/5. `packages/ktools-images` already owns:

- `Pillow>=12,<13`;
- the 80,000,000-pixel ceiling;
- Pillow decompression-bomb classification;
- EXIF orientation normalization;
- first-frame-only animation policy for the current image family;
- image-pack publication helpers for PNG;
- IMAGE Artifact and NEVER/publication evidence.

Slice 7 must extend that owner; it must not recreate a second Pillow safety stack.

## Fresh candidate decision

Terminal-main discovery compared Images→PDF and bounded Files/Folders.

Images→PDF is selected because its remaining contract is now bounded: the shared image decode/safety policy already exists, while the new behavior is primarily supported-format filtering, RGB/alpha preparation, ordered aggregation and singular PDF publication.

Files/Folders remains deferred because the legacy product still exposes at least two overlapping scan/report paths with unresolved cross-platform semantics around deterministic traversal order, hidden items, recursion, symlink/reparse points, permission/OSError aggregation and result schema. That surface needs its own discovery/spec rather than an opportunistic extraction.

## Dependency boundary

No new runtime dependency is introduced.

`ktools-images` keeps:

```text
Pillow>=12,<13
```

Product PDF serialization in this slice uses Pillow's PDF writer, matching the historical owner. `pypdf` may be used by tests/hosted smoke as an independent semantic oracle because it is already present in the monorepo PDF test environment; it is not a runtime dependency of `ktools-images` for Images→PDF execution.

## Supported inputs

The canonical capability accepts an ordered sequence of paths and attempts only existing regular files with these suffixes, case-insensitively:

```text
.jpg .jpeg .png .webp .bmp .tif .tiff
```

Missing paths, directories and unsupported suffixes are filtered before page preparation, preserving historical behavior.

If no compatible source remains, fail with a classified Images→PDF error.

Compatible source order is PDF page order.

## Shared safe first-frame owner

Slice 7 creates the second independent consumer of the same image-open policy. That is sufficient evidence to extract a pack-local shared decode owner.

Introduce one helper boundary such as:

```python
ktools_images.reader.load_safe_first_frame(path)
    -> (detached_image, source_animated, source_format)
```

Exact naming may vary, but ownership may not.

The shared owner must:

1. configure the existing `ktools_images.safety` Pillow limit;
2. treat `DecompressionBombWarning` as an exception;
3. classify Pillow bomb warning/error through the existing safety taxonomy;
4. open the source under the guarded warning scope;
5. validate original dimensions;
6. detect animation/multi-frame state;
7. intentionally select frame 0 only;
8. apply EXIF orientation normalization;
9. validate post-orientation dimensions;
10. fully load and detach the normalized first frame from the source file;
11. return a caller-owned Pillow image that can be safely closed independently.

WebP→PNG must be refactored to consume this same owner. After Slice 7 GREEN, `Image.open(...)`, bomb-warning setup and EXIF transpose must not remain duplicated in both the WebP converter and PDF writer.

The shared reader owns decode/safety/orientation/frame selection only. It does **not** own PNG mode policy or PDF page-mode policy.

## Animation / multi-frame policy

Images→PDF V1 preserves the historical policy: exactly the first frame/page of an animated or multi-frame image source is used as one PDF page.

One input file therefore produces one PDF page. The capability does not expand animated WebP/GIF-like content or multi-page TIFF into multiple PDF pages.

The final PDF Artifact metadata records the frame policy as `first` and may record which source files were detected as animated/multi-frame.

## Page preparation policy

Each safe normalized source becomes one detached RGB page.

### Transparency

For `RGBA`, `LA`, or palette (`P`) images carrying transparency:

1. convert to RGBA;
2. create an RGB image of the same dimensions filled with pure white `(255, 255, 255)`;
3. composite/paste the RGBA image using its alpha channel;
4. use the resulting RGB image as the PDF page.

The output PDF does not preserve alpha.

### Other modes

All other supported decoded modes are converted to `RGB`.

The page passed to Pillow's PDF writer must therefore always be RGB.

### Orientation

EXIF orientation is normalized **before** RGB/alpha preparation. Page dimensions and orientation reflect the normalized pixels.

## Aggregate publication contract

The requested destination is normalized to `.pdf` if necessary.

The capability prepares all pages first, then serializes exactly one PDF:

```python
first.save(temp_pdf, "PDF", save_all=True, append_images=rest)
```

Equivalent implementation is allowed only if semantic behavior remains the same.

Publication is one singular transaction boundary:

- the final destination is not written incrementally;
- a same-directory temporary `.pdf` path is used;
- the temp output must exist and be non-empty before promotion;
- final promotion uses atomic replace where the platform provides the existing `os.replace` semantics;
- a pre-existing destination is replaced only after complete successful serialization;
- on handled decode/preparation/serialization failure, the previous destination remains unchanged;
- temp output is cleaned best-effort;
- all prepared Pillow page objects are closed best-effort on success or failure.

Unlike WebP→PNG, this is not a multi-output partial-success operation. Any compatible-source failure aborts the aggregate result; no new PDF Artifact is returned or newly promoted.

## Canonical capability owner

Introduce one business-logic owner, for example:

```python
ktools_images.pdf_writer.images_to_pdf(
    input_files,
    output_file,
    progress_callback=None,
    *,
    produced_by=None,
) -> Artifact
```

The exact module name may differ if audit evidence finds a clearer pack-local name, but direct API and workflow node must delegate to exactly the same owner.

Direct API target:

```python
ktools_images.api.images_to_pdf(...)
```

## Artifact contract

Successful execution returns one `Artifact`:

- `type = DataType.PDF`;
- local `file://` URI;
- `mime_type = "application/pdf"`;
- `produced_by` supplied by the caller/current workflow node;
- metadata includes at minimum:
  - source count;
  - page count;
  - source names in page order;
  - normalized page pixel sizes in page order;
  - output mode `RGB`;
  - `alphaBackground = "white"`;
  - `orientationNormalized = true`;
  - `framePolicy = "first"`;
  - animated/multi-frame source names or equivalent bounded metadata.

Workflow execution must register a strong local-file snapshot for the singular PDF Artifact.

## Workflow node contract

Node type:

```text
image.files_to_pdf
```

Version `1`.

Ports:

```text
files: FILE_SET -> pdf: PDF
```

The handler accepts local `FILE` or `IMAGE` Artifact members and delegates actual suffix/existence filtering to the capability owner.

`FILE_SET` remains correct. Slice 6 proved member-level IMAGE typing is sufficient, and Slice 7 introduces no graph-time requirement for `IMAGE_SET`.

Cache policy:

```text
NEVER
```

Reason: the contract includes publishing/replacing the requested destination. Reusing a prior Artifact would skip required publication semantics.

A cached PURE `files.literal` source must not suppress Images→PDF execution or destination publication.

## Progress contract

Progress is supplemental.

For N compatible inputs:

- page-preparation events use `(index - 1) / N` before each source;
- animation/first-frame notices may reuse the source position;
- aggregate-save progress may use a bounded value such as `0.95` after all pages are prepared;
- final `1.0` is emitted only after the PDF has been promoted successfully.

All progress values remain within `[0.0, 1.0]`.

## Error taxonomy

Introduce a bounded public capability error such as `ImagePdfError` for:

- invalid ordered-input contract;
- no compatible source;
- unreadable/corrupt supported source;
- page-preparation failure;
- PDF serialization failure;
- destination/publication failure.

`ImageSafetyError` remains the shared fail-closed safety error and should not be hidden as an ordinary format error.

Messages identify the affected source/destination without arbitrary `repr()` leakage.

## Required RED

The RED is committed before implementation.

It must be discriminating on the current package, not on installation:

- Core/JSON/Text/PDF/Documents remain green;
- existing WebP→PNG image tests remain green;
- new Images→PDF tests fail because the new shared-reader/PDF-writer/API/node contracts are absent;
- Pillow installation is already proved by Slice 6 and must not be the failing boundary.

## Required tests

At minimum prove:

1. no compatible sources fails;
2. filtering of missing/unsupported paths and preservation of supported-source order;
3. supported extensions include JPG/JPEG/PNG/WebP/BMP/TIF/TIFF case-insensitively;
4. static RGB images produce one ordered PDF page each;
5. RGBA transparency is composited onto white before PDF serialization;
6. palette transparency follows the same white-background policy where a deterministic fixture is practical;
7. EXIF orientation is normalized before page preparation;
8. animated/multi-frame input contributes exactly one first-frame page and records policy metadata;
9. shared safety ceiling/bomb classification is reused by Images→PDF;
10. shared safe reader is also used by WebP→PNG after refactor;
11. output suffix is normalized to `.pdf`;
12. a pre-existing destination is replaced only on success;
13. forced later-source/decode failure preserves the previous destination and publishes no new aggregate PDF;
14. forced serializer failure preserves previous destination and cleans temp output;
15. all prepared page images are closed on handled failure;
16. PDF Artifact type/MIME/provenance/metadata;
17. `image.files_to_pdf: FILE_SET -> PDF`, version 1, NEVER;
18. ArtifactRegistry strong snapshot for the singular PDF output;
19. cached `files.literal` does not suppress second publication;
20. direct API and workflow produce semantically equivalent PDFs in isolated destinations;
21. API/node contain no Pillow decode/EXIF/RGB/composite/PDF-save/publication algorithm;
22. WebP converter and PDF writer do not duplicate `Image.open`/bomb-warning/EXIF logic after shared-reader extraction;
23. existing WebP→PNG semantics remain green after the refactor.

## Hosted smoke

Every Python CI lane must continue installing `ktools-images`, run the complete image suite, and add a real workflow smoke:

```text
files.literal -> image.files_to_pdf
```

The smoke must generate deterministic source images in-process, including at least one alpha-bearing source, execute the node, and independently reopen the generated PDF with `pypdf` to verify at minimum:

- output is a real non-empty PDF;
- page count equals compatible input count;
- page order is stable using distinguishable page dimensions or another deterministic semantic oracle;
- output Artifact type is PDF and MIME is `application/pdf`;
- metadata reports ordered sources and white-alpha policy.

Hosted matrix remains Ubuntu/Windows × Python 3.10/3.13 plus the existing xyflow job.

## Non-goals

- filesystem traversal/report extraction;
- PDF compression;
- image resize/quality controls;
- all-frame animation expansion;
- OCR;
- ICC/color-management expansion;
- PDF/A or print-production guarantees;
- generalized image pipeline framework;
- `IMAGE_SET`;
- legacy GUI rewiring in this slice.

## Promotion rule

```text
terminal Slice-6 main
  -> docs-only Slice-7 spec gate
  -> discriminating RED
  -> GREEN + shared-reader refactor
  -> integration/ownership audit
  -> exact-head hosted 5/5
  -> ADR + canonical memory closure
  -> terminal closure HEAD CI 5/5
```

No promotion claim before the synchronized closure HEAD itself is green.
