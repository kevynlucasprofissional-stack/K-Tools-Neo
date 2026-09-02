# ADR-029 — Shared Image Reader + Images→PDF V1

Status: **ACCEPTED / PROVED / PROMOTED FOR M5 SLICE 7**

## Decision

`packages/ktools-images` remains the canonical image capability owner and now exposes a second production capability, Images→PDF, while moving Pillow decode/safety/orientation/frame-selection policy into one pack-local shared reader.

The accepted V1 workflow contract is:

```text
image.files_to_pdf: FILE_SET -> PDF
version: 1
cache: NEVER
```

Direct API and workflow execution delegate to the same Images→PDF writer owner.

## Shared reader ownership

The second independent consumer proved that guarded image loading is a reusable pack policy rather than WebP→PNG-specific logic.

`ktools_images.reader.load_safe_first_frame()` therefore owns:

- the existing `Pillow>=12,<13` boundary;
- the 80,000,000-pixel ceiling;
- `DecompressionBombWarning` / `DecompressionBombError` classification;
- source opening under the guarded warning scope;
- original and post-orientation dimension validation;
- animated/multi-frame detection;
- intentional frame-0 selection;
- EXIF orientation normalization;
- fully loaded detached caller-owned image output.

WebP→PNG and Images→PDF both consume this reader. Format-specific mode conversion and publication remain with their capability owners.

## Images→PDF V1 semantics

Supported existing regular-file suffixes, case-insensitively:

```text
.jpg .jpeg .png .webp .bmp .tif .tiff
```

Missing paths, directories and unsupported suffixes are filtered while preserving the order of compatible sources. No compatible source fails closed.

Each compatible source contributes exactly one PDF page:

- frame policy is `first`;
- EXIF orientation is normalized before page preparation;
- RGBA, LA and palette transparency are composited over pure white;
- every page given to Pillow's PDF serializer is RGB;
- compatible-source order is page order.

The output is one `DataType.PDF` Artifact with `application/pdf`, current run/node provenance and bounded metadata describing ordered sources, page sizes/count, RGB mode, white alpha background, normalized orientation, first-frame policy and animated/multi-frame sources.

No `IMAGE_SET` is introduced. `FILE_SET` remains sufficient because member Artifact typing and runtime validation already preserve the required collection semantics.

## Aggregate publication boundary

Images→PDF has one singular aggregate transaction boundary, unlike WebP→PNG's per-output batch boundary.

All pages are prepared before serialization. The PDF is written to a same-directory temporary file, verified non-empty and only then promoted with `os.replace` semantics.

On handled decode, preparation, serialization or publication failure:

- a pre-existing destination remains unchanged;
- no new final PDF is claimed;
- temporary output is cleaned best-effort;
- prepared Pillow images are closed best-effort.

## Cache decision

`image.files_to_pdf` is `CachePolicy.NEVER`.

Reason: publishing/replacing the requested destination is part of the capability contract. Substituting an earlier Artifact would skip the required side effect. A cached PURE `files.literal` source therefore must not suppress a fresh Images→PDF execution/publication.

## Dependency decision

No new `ktools-images` runtime dependency is introduced. Product serialization uses Pillow's PDF writer. `pypdf` is used only by tests/hosted smoke as an independent semantic oracle through the already-installed PDF test environment.

## Architecture

```text
                         ktools_images.safety
                                  ↓
                    ktools_images.reader
                  guarded decode / frame0 / EXIF
                         ↙              ↘
            WebP→PNG converter     Images→PDF writer
            PNG mode policy        RGB / alpha→white
            per-output publish     aggregate PDF publish
                    ↑                    ↑
              direct API + node    direct API + node
```

Adapters do not own Pillow decode, EXIF, RGB/composite, PDF-save or temp-publication algorithms.

## Why

Slice 6 intentionally extracted the smaller WebP→PNG capability first to establish a safe decoder policy. Slice 7 provided the second consumer needed to justify shared-reader extraction without creating a generic image framework prematurely.

Images→PDF was selected over bounded Files/Folders after fresh terminal-main discovery because the image contract had become bounded while filesystem traversal still had unresolved cross-platform ordering, symlink/reparse, permission/error aggregation and result-schema semantics.

## Consequences

- image decode/safety/orientation/frame behavior evolves in `reader.py` + `safety.py`, not independently in each image capability;
- WebP→PNG remains behavior-compatible while no longer owning decode policy;
- Images→PDF semantic evolution belongs to `ktools-images`; the stable-GUI copy becomes compatibility debt;
- singular aggregate atomic publication is not evidence for a generic cross-domain writer abstraction;
- Pillow major-version widening still requires explicit compatibility evidence;
- Files/Folders remains a separate future discovery/spec problem.

## Evidence

- Slice-6 terminal prerequisite `9b9fc57bd4bfb28d7e23637651a30182ce6f8828` / run `33668942264`, 5/5;
- Slice-7 spec gate `ae617e948d5549e3dbca1dbe8d5de19c16555535` / run `33670517542`, 5/5;
- discriminating RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db` / run `33671061268`;
- GREEN implementation `309863ac475330448e6fc44dbdf305482528689e` / run `33671740134`, 5/5;
- ownership hardening `1d9afc40bb7adbb511a1869d25b18058782bcbad` / run `33672387118`, 5/5;
- synchronized memory closure `c3585f5b7f478f53e1c5ef63f72a7b49fbb0cdea` / run `33674308145`, 5/5.

The explicit terminal promotion condition is satisfied. M5 Slice 7 is **RESOLVED / PROMOTED**.
