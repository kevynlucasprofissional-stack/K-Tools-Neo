# ADR-028 — Image Safety Foundation + WebP→PNG V1

Status: **ACCEPTED / PROVED FOR M5 SLICE 6**

## Decision

`packages/ktools-images` is the canonical evolution owner for the K-Tools image-safety boundary and WebP→PNG conversion.

V1 locks the following policy:

- Python >= 3.10;
- `Pillow>=12,<13` declared at the package/bootstrap boundary;
- `MAX_IMAGE_TOTAL_PIXELS = 80_000_000` plus Pillow decompression-bomb warning/error handling;
- positive dimensions and explicit pixel-count validation before and after orientation normalization;
- EXIF orientation normalized through Pillow before final mode publication;
- animated/multi-frame WebP intentionally publishes frame 0 only;
- RGBA/LA/transparent palette inputs preserve transparency as RGBA PNG;
- RGB and L remain valid PNG modes; other modes normalize to RGB;
- collision-safe `{stem}.png`, `_1`, `_2`, ... allocation avoids overwrite;
- every PNG is temp-written and promoted independently; the batch is not globally transactional;
- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1, `CachePolicy.NEVER`;
- returned members are `DataType.IMAGE` Artifacts with `image/png`, current run/node provenance and image-policy metadata;
- no `IMAGE_SET` is introduced in V1.

## Architecture

```text
Direct API (`ktools_images.api.convert_webp_to_png`)
                    \
                     -> `converter.convert_webp_files_to_png`
                        ├─ `safety`
                        └─ `publication`
                    /
Workflow node (`image.webp_to_png`)
```

API and workflow adapters do not own Pillow decode, EXIF, frame, color-mode, collision or publication algorithms.

## Why

The legacy WebP→PNG path already contained product-significant safety and normalization behavior. Extracting that bounded capability first establishes one image foundation before Images→PDF adds its separate aggregate-PDF and alpha-to-white semantics.

The node remains NEVER because publishing a fresh collision-safe PNG is an externally required side effect. A cached `files.literal` source must not suppress conversion/publication.

`FILE_SET` remains the collection contract because member-level IMAGE typing, MIME, metadata and ArtifactRegistry snapshots are sufficient for the current graph/runtime. A specialized image collection would add type surface without a demonstrated graph-time need.

## Failure / transaction boundary

A failed source aborts the conversion call. A PNG already published for an earlier source remains on disk. The current failing source must not leave a partial final destination or temp file. K-Tools does not delete earlier user-visible outputs without stronger ownership/rollback evidence.

## Consequences

- new WebP→PNG semantics and bug fixes originate in `ktools-images`;
- the stable GUI implementation is compatibility debt and should be redirected/retired when traditional Tools migrate to platform workflows;
- Images→PDF should reuse the canonical safety/orientation foundation instead of copying it, while specifying its own supported formats, white-background alpha composition, page order and singular PDF publication semantics;
- Pillow major-version upgrades require explicit compatibility evidence rather than silent widening of the range;
- the package-local PNG publication helper is not evidence for a generic cross-domain atomic writer.

## Evidence

- spec gate `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / run `33666227293`, 5/5;
- discriminating RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / run `33667224304`;
- GREEN/audited technical candidate `670a503d822ba100a66eea3ba0b31cfe39692984` / run `33667874076`, 5/5.

Terminal promotion requires the synchronized memory-closure HEAD to pass the same five hosted jobs.
