# Evidence — Images→PDF Node V1

Status: **SPEC GREEN / RED PUBLISHED**

## Prerequisite gate

Image Safety Foundation + WebP→PNG terminal closure:

- terminal HEAD `9b9fc57bd4bfb28d7e23637651a30182ce6f8828`;
- run `33668942264`;
- Ubuntu Python 3.10 success;
- Ubuntu Python 3.13 success;
- Windows Python 3.10 success;
- Windows Python 3.13 success;
- xyflow success.

Every Python lane installed `ktools-images`, passed the image suite and executed the real WebP→PNG workflow smoke. Slice 7 therefore starts from a terminal-green canonical image foundation.

## Current canonical image owner

`packages/ktools-images` currently proves:

- `Pillow>=12,<13` as package dependency;
- `MAX_IMAGE_TOTAL_PIXELS = 80_000_000`;
- fail-closed Pillow decompression-bomb handling;
- EXIF normalization through `ImageOps.exif_transpose`;
- explicit first-frame policy for animated WebP;
- per-PNG collision-safe atomic publication;
- direct API + workflow use sharing one converter owner;
- `image.webp_to_png` version 1 NEVER;
- IMAGE Artifact provenance and strong snapshots.

Current implementation still places guarded `Image.open`, frame selection and EXIF orchestration directly in `converter.py`, which was correct with one consumer. Images→PDF becomes the second independent consumer and therefore supplies the evidence threshold for a pack-local shared reader extraction.

## Fresh legacy Images→PDF facts

The stable GUI Images→PDF owner:

- filters to existing regular image files with `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tif`, `.tiff`;
- rejects an empty compatible set;
- preserves input order as page order;
- normalizes destination to `.pdf`;
- uses the same Pillow safety ceiling/bomb-warning policy as WebP→PNG;
- validates size before and after EXIF transpose;
- detects animated/multi-frame input and deliberately uses frame 0 only;
- fully loads the selected normalized image;
- converts transparent `RGBA`, `LA`, or transparent palette input through RGBA and composites it onto an RGB white background;
- converts non-transparent inputs to RGB;
- stores prepared page images until the aggregate save;
- serializes one PDF through Pillow with `save_all=True` and ordered `append_images`;
- writes a same-directory temporary PDF first;
- requires a non-empty temporary result before final promotion;
- atomically replaces the requested destination only after complete success;
- closes prepared images and cleans the temporary output in `finally`.

This is a singular aggregate publication boundary: there is no partial successful PDF result if a compatible source fails.

## Files/Folders comparison

The stable GUI still exposes at least two partially overlapping traversal paths:

- `scan_folder_structure(...)` for file/dir entries, errors and stats;
- `scan_simple_file_names(...)` for simpler file-name/path export semantics.

Both walk with `os.walk` and support hidden/subfolder options, but current discovery does not prove one canonical deterministic ordering policy, Windows reparse/symlink behavior or a single result schema suitable for a Node Pack contract.

Therefore Files/Folders remains the next major candidate family, but not the safer Slice-7 extraction.

## Candidate decision

Selected: **Images→PDF Node V1**.

Reason: Slice 6 deliberately created the foundation this capability needs. The second consumer now justifies a shared safe-reader refactor, while PDF-specific behavior is bounded and directly characterizable.

Deferred: bounded Files/Folders until traversal semantics are explicitly locked.

## Architectural hypothesis

```text
ktools_images.safety
        ↓
ktools_images.reader  ← shared guarded decode / frame0 / EXIF
      ↙      ↘
WebP→PNG      Images→PDF
PNG policy    RGB + alpha→white + aggregate PDF policy
```

Workflow contract:

```text
files.literal
    ↓ FILE_SET
image.files_to_pdf   (NEVER)
    ↓ PDF
```

No `IMAGE_SET` is introduced.

## Spec gate

Docs-only spec commit:

- HEAD `ae617e948d5549e3dbca1dbe8d5de19c16555535`;
- run `33670517542`;
- Ubuntu 3.10 success;
- Ubuntu 3.13 success;
- Windows 3.10 success;
- Windows 3.13 success;
- xyflow success.

The spec therefore changed no product behavior and the RED gate is authorized.

## RED contract

`packages/ktools-images/tests/test_images_to_pdf_v1.py` defines the full target contract against the already-installable image package. The intended failure boundary is absence of the new shared reader, PDF writer, API and `image.files_to_pdf` node—not Pillow/bootstrap or prior-pack regression.

The next accepted evidence is a hosted RED where prior Core/JSON/Text/PDF/Documents steps pass and the image test step fails on the missing Slice-7 product contract. After that, GREEN implementation is authorized.
