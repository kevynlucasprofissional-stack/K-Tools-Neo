# Spec — Image Safety Foundation + WebP→PNG Node V1

Status: **ACTIVE / SPEC LOCKED**
Milestone: M5 Slice 6
Canonical implementation target: `packages/ktools-images/`

## Objective

Extract the historical WebP→PNG behavior into the first official Image Node Pack while formalizing a reusable image-safety boundary that a later Images→PDF slice can consume.

The slice must preserve the established legacy product behavior where it is deliberate, remove GUI/runtime coupling, use first-class Artifacts, and avoid broad image-framework abstractions not yet proved by a second capability.

## Why this slice was selected

Fresh discovery on terminal Slice-5 `main` compared:

1. WebP→PNG;
2. Images→PDF;
3. bounded Files/Folders operations.

### WebP→PNG — selected

It is a bounded local transformation with no native subprocess boundary, but already exercises the image decisions that must become explicit before broader image work:

- Pillow dependency/versioning;
- decompression-bomb protection;
- maximum decoded dimensions/pixel count;
- EXIF orientation normalization;
- animated/multi-frame handling;
- transparency and color-mode conversion;
- collision-safe multi-output naming;
- temp-then-promote publication;
- first-class IMAGE Artifact output.

This creates a real reusable safety/policy owner before Images→PDF.

### Images→PDF — deferred behind the image foundation

It reuses the same Pillow safety/orientation/frame rules but additionally accepts many image formats, aggregates N sources into one PDF, converts transparency onto white, manages a list of prepared page objects and relies on Pillow PDF serialization. It is more valuable after the common image boundary is proved independently.

### Files/Folders — deferred

Its apparent stdlib simplicity hides a larger cross-platform traversal contract: hidden-file semantics, recursion, symlink/reparse handling, deterministic ordering, permission/OSError aggregation, result/report schema and PURE-vs-publication distinctions. It deserves a separately bounded spec rather than being chosen merely because it has no third-party dependency.

## Dependency boundary

V1 declares:

```text
Pillow>=12,<13
```

External verification at specification time found Pillow 12.3.0 as the current release, requiring Python >=3.10 and providing wheels compatible with the project matrix. The upper major bound prevents unreviewed major-version behavior changes from entering the image safety boundary.

No runtime auto-install is allowed inside capability execution. Dependency installation belongs to package/bootstrap/CI boundaries.

## Package shape

```text
packages/ktools-images/
  pyproject.toml
  README.md
  src/ktools_images/
    __init__.py
    safety.py
    publication.py
    converter.py
    api.py
    node.py
  tests/
  examples/
```

This structure is intentionally small. `safety.py` may be reused by later image capabilities inside the same pack. No generic cross-domain publication abstraction is introduced.

## Supported source behavior

The direct capability accepts an ordered sequence of paths and attempts only existing regular files whose suffix is `.webp` case-insensitively.

Unsupported paths, missing paths and directories are filtered before conversion, matching the historical tool. If no compatible input remains, fail with a classified error.

Input order determines output order.

## Image safety policy

### Pixel limit

Preserve the historical V1 ceiling:

```text
MAX_IMAGE_TOTAL_PIXELS = 80_000_000
```

Before decoding, configure Pillow's `Image.MAX_IMAGE_PIXELS` to the same ceiling. Treat Pillow `DecompressionBombWarning` as an exception during image open/decode and classify both the warning and `DecompressionBombError` as image-safety failures.

Also explicitly validate decoded width/height and `width * height`:

- width/height must be positive;
- total pixels must not exceed 80,000,000;
- validate the opened frame and the EXIF-transposed image.

Do not silently disable Pillow's protection.

### EXIF orientation

Apply `ImageOps.exif_transpose(...)` to the selected frame before final mode normalization and publication. Output pixel dimensions reflect the normalized orientation.

### Animation / multi-frame policy

V1 intentionally converts **only the first frame** of an animated WebP.

The capability must seek frame 0 where possible and must not silently expand one animated source into multiple PNG Artifacts.

Output Artifact metadata records that the source was animated and that the V1 frame policy was `first`.

A future all-frames mode is a separate contract, not an implicit extension of V1.

### Transparency / color modes

Preserve the historical normalization policy:

- `RGBA` or `LA` → `RGBA`;
- palette (`P`) with transparency → `RGBA`;
- `RGB` remains `RGB`;
- `L` remains `L`;
- any other decoded mode converts to `RGB`.

PNG preserves alpha; WebP→PNG must not composite transparency onto a background.

## Publication contract

For each compatible source, allocate:

```text
{source_stem}.png
```

in the requested output directory.

If the candidate already exists or has already been reserved earlier in the same batch, allocate `_1`, `_2`, ... until free. Collision identity is case-insensitive in V1 to remain Windows-safe.

Each output is written to a same-directory temporary `.png` path and promoted to the final destination only after a non-empty PNG exists.

The requested final destination is never partially written by a handled failure.

### Multi-output transaction boundary

The batch is **not set-wide transactional**.

Conversion proceeds in source order. If source N fails after sources 1..N-1 were successfully published, those earlier successful PNG files remain. The call raises and does not return a successful output collection.

Do not attempt rollback/deletion without stronger file-ownership evidence.

This behavior must be explicitly tested rather than inferred from single-output atomicity.

## Direct capability contract

Canonical owner:

```python
ktools_images.converter.convert_webp_files_to_png(
    input_files,
    output_dir,
    progress_callback=None,
    *,
    produced_by=None,
) -> list[Artifact]
```

Direct API:

```python
ktools_images.api.convert_webp_to_png(...)
```

must delegate to the same canonical owner.

## Artifact contract

Every successful PNG is an `Artifact` with:

- `type = DataType.IMAGE`;
- local `file://` URI;
- `mime_type = "image/png"`;
- supplied/current `produced_by`;
- metadata sufficient to describe source/output semantics without reopening the legacy GUI path, including at minimum:
  - source name;
  - source format `webp`;
  - output format `png`;
  - width;
  - height;
  - output mode;
  - whether source was animated;
  - frame policy `first`.

ArtifactRegistry must strongly snapshot nested outputs when used through the workflow engine.

## Workflow node contract

Node type:

```text
image.webp_to_png
```

Version `1`.

Ports:

```text
files: FILE_SET -> files: FILE_SET
```

`FILE_SET` remains the collection contract because no IMAGE_SET exists and member-level Artifact typing is already proved sufficient. The handler accepts local FILE/IMAGE Artifacts and lets the capability filter actual source suffix/existence semantics.

Output members are IMAGE Artifacts.

Cache policy:

```text
NEVER
```

Reason: the node contract includes publishing new requested files. Reusing prior outputs would skip required publication and collision behavior.

An upstream `files.literal` may be PURE/cached. That cache hit must not suppress conversion or re-publication.

## Progress contract

Progress is supplemental and must not affect output semantics.

For N compatible inputs:

- emit per-source preparation/conversion progress using `(index - 1) / N` before each item;
- animation notices may reuse the current source position;
- emit final `1.0` only after every output is successfully published.

All emitted values must remain in `[0.0, 1.0]`.

## Error taxonomy

Introduce a bounded public taxonomy such as:

- `ImageConversionError` — invalid source/config/publication/decode conversion failure;
- `ImageSafetyError(ImageConversionError)` — decompression-bomb or decoded-size safety rejection.

Messages should identify the affected source without leaking arbitrary object representations.

No diagnostics subsystem integration is required merely for ordinary in-process Pillow exceptions; M3 diagnostics continues to capture workflow failures at the engine boundary. If future image work introduces native subprocesses/plugins, that decision is reopened.

## Required RED

The RED must be committed before implementation and must be discriminating:

- existing Core/JSON/Text/PDF/Documents suites stay green first;
- new image suite fails because `ktools_images` / its expected contracts do not yet exist;
- Pillow may be installed explicitly for the RED fixture boundary if tests need it, but a dependency/bootstrap failure does not count as product RED.

## Required tests

At minimum prove:

1. no compatible inputs fails;
2. supported-path filtering and source order;
3. static RGB WebP → RGB PNG;
4. alpha WebP → RGBA PNG with alpha preserved;
5. EXIF orientation normalization changes dimensions/pixel orientation as expected;
6. animated WebP uses first frame only and records metadata;
7. palette/transparency and grayscale normalization behavior where Pillow fixtures can represent it deterministically;
8. safety ceiling and Pillow bomb warning/error are classified fail-closed without requiring huge fixtures;
9. clean names and `_1` collision behavior;
10. same-directory temp publication and no partial failed destination;
11. later-source failure leaves earlier completed output but raises/no returned collection;
12. output IMAGE Artifact type/MIME/provenance/metadata;
13. `image.webp_to_png: FILE_SET -> FILE_SET`, v1 NEVER;
14. ArtifactRegistry nested strong snapshots;
15. cached `files.literal` does not suppress repeated conversion and second run allocates new names;
16. direct API and workflow delegate to the same converter owner and are pixel/metadata equivalent in isolated destinations;
17. adapter source contains no decode/EXIF/mode/publication algorithm.

## Hosted smoke

Every Python CI lane must install `ktools-images`, run its full tests and execute a real workflow smoke:

```text
files.literal -> image.webp_to_png
```

The smoke must create at least one deterministic lossless WebP with alpha, execute the node, reopen the PNG with Pillow and verify:

- report-free ordered output count;
- IMAGE Artifact type and `image/png` MIME;
- expected dimensions/mode;
- alpha/pixel semantics;
- non-empty real PNG publication.

Hosted matrix remains Ubuntu/Windows × Python 3.10/3.13, plus the existing xyflow job.

## Non-goals

- Images→PDF;
- JPEG/PNG/BMP/TIFF conversion;
- resize/compression/quality controls;
- all-frame animation extraction;
- ICC color-management expansion;
- generalized image-processing pipeline abstraction;
- IMAGE_SET or covariance changes to FILE_SET;
- GUI rewiring in this slice.

## Promotion rule

Sequence is:

```text
terminal Slice-5 main
  -> spec gate
  -> discriminating RED
  -> GREEN
  -> architecture/integration audit
  -> hosted exact-head evidence
  -> ADR + canonical memory closure
  -> terminal closure HEAD CI
```

No promotion claim before the final closure HEAD is green.
