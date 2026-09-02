# Evidence — Images→PDF Node V1

Status: **RED ACCEPTED / GREEN CANDIDATE PENDING**

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

## Fresh candidate decision

Terminal-main discovery compared Images→PDF and bounded Files/Folders.

Images→PDF was selected because the remaining contract became bounded after Slice 6 established Pillow dependency/safety, EXIF and first-frame behavior. Files/Folders remains deferred because the stable GUI still contains at least two overlapping traversal/report paths with unresolved deterministic ordering, symlink/reparse and result-schema semantics.

## Selected architecture

```text
ktools_images.safety
        ↓
ktools_images.reader  ← guarded decode / frame0 / EXIF
      ↙      ↘
WebP→PNG      Images→PDF
PNG policy    RGB + alpha→white + aggregate PDF policy
```

The second independent consumer is the evidence threshold for extracting the pack-local reader. The reader owns decode/safety/orientation/frame selection only; format-specific mode and publication decisions remain with each capability.

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

The spec changed no product behavior and authorized RED.

## Discriminating RED

RED commit:

- HEAD `9ac1c9bcb2974e8d4daf70844a14198e35fe54db`;
- run `33671061268`.

Ubuntu 3.10 provides the complete discriminating evidence:

- `ktools-images` installed successfully with Pillow 12.3.0;
- 76 Core tests passed;
- 64 JSON tests passed;
- 28 Text tests passed;
- 24 PDF tests passed;
- 7 Documents tests passed;
- all 15 pre-existing WebP→PNG tests passed inside the image suite;
- the 15 new Images→PDF contracts failed on the intended missing product boundary, principally `ModuleNotFoundError: No module named 'ktools_images.reader'`, with `publish_pdf_atomic` also absent.

Ubuntu 3.13 reached the same image-test failure after all prior suites passed. This is product-absence RED, not bootstrap/dependency or Slice-6 regression.

## GREEN implementation hypothesis

The GREEN candidate must add only:

- `reader.py` shared safe first-frame owner;
- refactored WebP converter using the reader;
- `pdf_writer.py` aggregate Images→PDF owner;
- PDF atomic publication in the existing image-pack publication module;
- direct API + `image.files_to_pdf` thin node;
- deterministic hosted Images→PDF workflow smoke using `pypdf` only as an independent test oracle.

The next accepted evidence is exact-head hosted 5/5 with all old WebP behavior still green and all new Images→PDF contracts green.
