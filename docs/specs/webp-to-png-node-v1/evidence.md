# Evidence — Image Safety Foundation + WebP→PNG Node V1

Status: **DISCOVERY ACCEPTED / SPEC GATE PENDING**

## Prerequisite gate

Mixed Document Split terminal closure:

- terminal HEAD `3d2d955df71cd65162839a5ac2c1335e5b5a4518`;
- run `33665431920`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

Every Python lane installed `ktools-documents`, passed its suite and passed the real mixed split workflow smoke. Slice 6 discovery therefore starts from a terminal-green Slice 5.

## Fresh discovery facts from the legacy owner

### Shared image boundary already present

The stable GUI currently defines:

- `MAX_IMAGE_TOTAL_PIXELS = 80_000_000`;
- Pillow `Image.MAX_IMAGE_PIXELS` configured to that value;
- `DecompressionBombWarning` promoted to an exception inside guarded decode regions;
- `DecompressionBombError` classified as a user-facing image-safety failure;
- explicit positive-dimension / pixel-count validation;
- `ImageOps.exif_transpose(...)` before final normalization;
- image-format helpers and collision-safe path allocation.

This is sufficient evidence that image safety is existing product behavior to characterize, not a new speculative feature.

### WebP→PNG behavior

The legacy converter:

- filters to existing `.webp` regular files;
- rejects an empty compatible set;
- creates the output directory;
- reserves case-insensitive collision-safe `{stem}.png`, `_1`, `_2`, ... names;
- writes each output through a same-directory temp path;
- opens under bomb-warning protection;
- validates dimensions before and after EXIF transpose;
- detects animation and intentionally seeks/uses only frame 0;
- preserves transparency by converting `RGBA`, `LA` and transparent palette sources to `RGBA`;
- leaves `RGB`/`L` in those modes and normalizes other modes to RGB;
- writes a real PNG, checks it is non-empty, then promotes it;
- cleans the current temp path on handled failure;
- aborts on the first failed compatible source rather than exposing partial success;
- leaves earlier successfully published outputs on disk if a later source fails.

### Images→PDF behavior

The legacy Images→PDF path shares the same safety/EXIF/first-frame foundation but has extra semantics:

- accepts several image formats rather than only WebP;
- converts every prepared page to RGB;
- composites alpha/transparency onto a white background because PDF output does not preserve alpha consistently;
- holds prepared page copies and serializes them as one aggregate PDF;
- publishes one singular destination atomically.

This is a larger contract and benefits from extracting the shared image boundary first.

### Files/Folders behavior

The legacy scan surface walks directories with `os.walk`, mutates `dirnames` to enforce hidden/recursion policy, accumulates permission/OSError records, produces structured entries/stats and has periodic traversal progress. A neighboring listing/report path has overlapping but not identical traversal/result semantics.

Therefore Files/Folders is not a single obvious capability yet; it needs a bounded cross-platform traversal spec before implementation.

## Candidate decision

Selected: **WebP→PNG as Image Safety Foundation**.

Reason: it provides the best ratio of product value to boundary risk while establishing a reusable safety owner needed by the next image capability. It introduces one well-understood third-party dependency but no subprocess/native-tool orchestration.

Deferred:

- Images→PDF until safety/EXIF/frame/mode policy is canonical;
- Files/Folders until traversal/result semantics are bounded.

## Dependency verification

External release verification on 2026-09-02 found Pillow 12.3.0 as the current PyPI release, with `Requires-Python >=3.10` and CPython 3.10+ wheels including Windows. This matches the K-Tools Python 3.10/3.13 hosted matrix.

V1 therefore locks:

```text
Pillow>=12,<13
```

The upper major bound is deliberate dependency governance, not a claim that future Pillow 13 is incompatible. Reopen through evidence when upgrading the image pack.

## Selected architectural hypothesis

Create `packages/ktools-images` with reusable pack-local `safety.py`, pack-local publication helpers and one converter owner.

Workflow contract:

```text
files.literal
   ↓ FILE_SET
image.webp_to_png   (NEVER)
   ↓ FILE_SET containing IMAGE Artifacts
```

No IMAGE_SET is introduced. Current member-level Artifact typing is sufficient for V1.

## Next evidence gate

The next accepted evidence is the exact docs-only spec commit passing the existing five hosted jobs without code changes. Only after that may RED contracts be added.
