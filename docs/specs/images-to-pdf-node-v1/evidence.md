# Evidence — Images→PDF Node V1

Status: **TECHNICAL GREEN / MEMORY-CLOSURE CANDIDATE**

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

Ubuntu 3.13 reached the same image-test failure after all prior suites passed. This was product-absence RED, not bootstrap/dependency or Slice-6 regression.

## GREEN implementation

GREEN implementation:

- HEAD `309863ac475330448e6fc44dbdf305482528689e`;
- run `33671740134`;
- Ubuntu Python 3.10 success;
- Ubuntu Python 3.13 success;
- Windows Python 3.10 success;
- Windows Python 3.13 success;
- xyflow success.

Delivered:

- `reader.py` as the shared safe first-frame owner;
- WebP→PNG refactored to consume the reader;
- `pdf_writer.py` as the aggregate Images→PDF owner;
- singular same-directory atomic PDF publication;
- direct API + `image.files_to_pdf` thin node;
- supported JPG/JPEG/PNG/WebP/BMP/TIF/TIFF filtering in preserved order;
- EXIF-normalized first-frame semantics;
- RGB page normalization and alpha/palette transparency composited over white;
- PDF Artifact metadata/provenance and strong ArtifactRegistry snapshot;
- NEVER semantics with cached upstream `files.literal` still re-publishing;
- direct/workflow semantic equivalence;
- real hosted `files.literal -> image.files_to_pdf` smoke independently reopened with `pypdf`.

The same run kept the existing WebP→PNG suite and hosted smoke green in all Python lanes.

## Integration/ownership audit

The first GREEN exposed one test-design debt: the older Slice-6 structural guard still required literal `Image.open` and `safety.normalize_orientation` tokens inside `converter.py`. A temporary migration comment could satisfy that old assertion while the real owner had already moved to `reader.py`; this would make the architecture test less truthful than the architecture.

The audit therefore changed the guard rather than weakening the new owner:

- HEAD `1d9afc40bb7adbb511a1869d25b18058782bcbad`;
- run `33672387118`;
- all five hosted jobs completed success.

The hardened test now requires `reader.load_safe_first_frame` from the WebP converter, rejects Pillow open/warning/EXIF ownership there, and verifies those responsibilities in `reader.py`. The artificial breadcrumb was removed from production code.

## Exact-head technical gate

Run `33672387118` on `1d9afc40bb7adbb511a1869d25b18058782bcbad` completed:

- Ubuntu / Python 3.10 — success;
- Ubuntu / Python 3.13 — success;
- Windows / Python 3.10 — success;
- Windows / Python 3.13 — success;
- xyflow spike — success.

Every Python lane installed all official packs, passed Core/JSON/Text/PDF/Documents/Images suites, and passed the existing and new hosted workflow smokes, including Images→PDF.

## Remaining promotion gate

The technical capability is green and audited. Promotion is not yet claimed by this evidence file alone.

The synchronized memory-closure commit containing ADR-029, canonical state/roadmap/testing/issues/journal updates, completed task accounting and final report must itself pass the same five hosted jobs. Only then may Slice 7 be terminally marked **RESOLVED / PROMOTED**.
