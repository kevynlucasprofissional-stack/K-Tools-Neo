# Evidence — Images→PDF Node V1

Status: **RESOLVED / PROMOTED**

## Prerequisite gate

Image Safety Foundation + WebP→PNG terminal closure:

- terminal HEAD `9b9fc57bd4bfb28d7e23637651a30182ce6f8828`;
- run `33668942264`;
- Ubuntu Python 3.10 success;
- Ubuntu Python 3.13 success;
- Windows Python 3.10 success;
- Windows Python 3.13 success;
- xyflow success.

Every Python lane installed `ktools-images`, passed the image suite and executed the real WebP→PNG workflow smoke. Slice 7 therefore started from a terminal-green canonical image foundation.

## Fresh candidate decision

Terminal-main discovery compared Images→PDF and bounded Files/Folders.

Images→PDF was selected because the remaining contract became bounded after Slice 6 established Pillow dependency/safety, EXIF and first-frame behavior. Files/Folders remained deferred because the stable GUI contained overlapping traversal/report paths with unresolved deterministic ordering, symlink/reparse and result-schema semantics.

## Selected architecture

```text
ktools_images.safety
        ↓
ktools_images.reader  ← guarded decode / frame0 / EXIF
      ↙      ↘
WebP→PNG      Images→PDF
PNG policy    RGB + alpha→white + aggregate PDF policy
```

The second independent consumer was the evidence threshold for extracting the pack-local reader. The reader owns decode/safety/orientation/frame selection only; format-specific mode and publication decisions remain with each capability.

Workflow contract:

```text
files.literal
    ↓ FILE_SET
image.files_to_pdf   (NEVER)
    ↓ PDF
```

No `IMAGE_SET` was introduced.

## Spec gate

Docs-only spec commit `ae617e948d5549e3dbca1dbe8d5de19c16555535`, run `33670517542`, passed all five hosted jobs and authorized RED.

## Discriminating RED

RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db`, run `33671061268`.

Ubuntu 3.10 proved:

- `ktools-images` installed successfully with Pillow 12.3.0;
- 76 Core tests passed;
- 64 JSON tests passed;
- 28 Text tests passed;
- 24 PDF tests passed;
- 7 Documents tests passed;
- all 15 pre-existing WebP→PNG tests passed;
- the 15 new Images→PDF contracts failed on the intended missing product boundary, principally absent `ktools_images.reader`, with PDF atomic publication also absent.

Ubuntu 3.13 reached the same intended image-test boundary after prior suites passed. This was product-absence RED, not bootstrap/dependency or Slice-6 regression.

## GREEN implementation

GREEN `309863ac475330448e6fc44dbdf305482528689e`, run `33671740134`, passed 5/5.

Delivered shared reader, WebP refactor, aggregate Images→PDF writer, singular atomic PDF publication, direct API + `image.files_to_pdf`, format/order/frame/EXIF/RGB/alpha-white semantics, PDF Artifact/snapshot, NEVER/cached-source proof, direct/workflow equivalence and hosted PDF reopen smoke.

All prior WebP tests and smoke remained green.

## Integration/ownership audit

The initial GREEN revealed a stale architecture-test assumption: the Slice-6 structural guard still expected direct `Image.open`/EXIF tokens inside `converter.py`. Audit corrected the test rather than retaining a compatibility breadcrumb.

Hardened HEAD `1d9afc40bb7adbb511a1869d25b18058782bcbad`, run `33672387118`, passed all five hosted jobs. The guard now proves `reader.load_safe_first_frame` ownership and rejects duplicated Pillow open/warning/EXIF policy in the WebP converter.

## Memory-closure gate

Synchronized memory closure:

- HEAD `c3585f5b7f478f53e1c5ef63f72a7b49fbb0cdea`;
- run `33674308145`;
- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow spike — success.

Every Python lane installed all official packs, passed every installed-pack suite and completed all hosted smokes, including WebP→PNG and Images→PDF.

This satisfied the explicit promotion condition in the spec and memory-closure candidate.

## Terminal conclusion

M5 Slice 7 — Images→PDF Node V1 is **RESOLVED / PROMOTED**.

Canonical implementation: `packages/ktools-images/`.
ADR: `docs/decisions/ADR-029-IMAGES-TO-PDF-NODE-V1.md`.

The next slice begins only from the terminal mainline and must run fresh candidate discovery.
