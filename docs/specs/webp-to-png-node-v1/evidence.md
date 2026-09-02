# Evidence — Image Safety Foundation + WebP→PNG Node V1

Status: **TECHNICAL GREEN / AUDITED / MEMORY CLOSURE GATE**

## Prerequisite

M5 Slice 5 terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` passed run `33665431920` 5/5. Slice 6 therefore began from a terminal-green mixed-document orchestrator.

## Fresh discovery and selection

The exact legacy owner was re-inspected and WebP→PNG, Images→PDF and bounded Files/Folders were compared rather than carrying forward a stale ranking.

WebP→PNG was selected because it establishes a reusable image-safety boundary with lower semantic surface than Images→PDF and lower traversal/platform ambiguity than Files/Folders.

The legacy contract characterized before implementation includes:

- existing `.webp` regular-file filtering and ordered processing;
- 80,000,000-pixel safety ceiling plus Pillow decompression-bomb handling;
- EXIF orientation normalization;
- animated WebP uses frame 0 only;
- alpha/transparency preserved in PNG;
- RGB/L preserved and other non-alpha modes normalized to RGB;
- collision-safe destination allocation;
- same-directory temp publication per PNG;
- abort on first failed compatible source while already-published earlier files remain.

Images→PDF shares the safety/EXIF/frame foundation but additionally aggregates multiple image formats into one PDF, converts pages to RGB and composites alpha onto white. Files/Folders exposes a broader traversal/result-schema problem. Both were deliberately deferred.

## Dependency gate

External release verification on 2026-09-02 established Pillow 12.3.0 as compatible with Python >=3.10 and the hosted Python 3.10/3.13 matrix. V1 locks `Pillow>=12,<13`; the upper bound is dependency governance, not a claim about future Pillow 13 incompatibility.

## Spec gate

Commit `bd454050c182aec74c8f45d529ab2e0377cb3ad3` formalized:

```text
image.webp_to_png
  files: FILE_SET
      -> files: FILE_SET containing IMAGE Artifacts
```

version 1, `CachePolicy.NEVER`, no `IMAGE_SET`.

Run `33666227293` passed all five hosted jobs before RED was introduced.

## Discriminating RED

Commit `311c82a26b5ef64a7c80299b9253829a8e98cfbc` added 15 product contracts and an image-suite CI step while installing Pillow explicitly as a RED fixture dependency.

Run `33667224304` reached the intended missing-product boundary. In the observed Ubuntu 3.13 lane:

- Core: 76 tests passed;
- JSON: 64 tests passed;
- Text: 28 tests passed;
- PDF: 24 tests passed;
- Documents: 7 tests passed;
- `Pillow 12.3.0` installed successfully;
- Image tests failed at `ModuleNotFoundError: No module named 'ktools_images'`.

This is accepted product RED: prior product boundaries and dependency bootstrap were green before the absent Image pack failed.

## GREEN implementation

Commit `670a503d822ba100a66eea3ba0b31cfe39692984` introduced:

- `packages/ktools-images/`;
- package metadata with `ktools-core>=0.1.0` and `Pillow>=12,<13`;
- `safety.py` as the 80M-pixel/decompression/EXIF owner;
- `publication.py` as image-pack collision/temp/promote owner;
- one canonical `converter.convert_webp_files_to_png` owner;
- thin direct API;
- thin `image.webp_to_png` workflow adapter;
- IMAGE Artifacts with PNG MIME, provenance and source/frame/orientation/mode/dimension metadata;
- real generated RGB/RGBA WebP→PNG hosted smoke;
- root CI installation/tests/smoke for the new pack.

Run `33667874076` passed **5/5**:

- Ubuntu Python 3.10 — success;
- Ubuntu Python 3.13 — success;
- Windows Python 3.10 — success;
- Windows Python 3.13 — success;
- xyflow spike — success.

Every Python lane installed `ktools-images`, passed Core/JSON/Text/PDF/Documents/Image suites, preserved all previous smokes and passed the new real WebP→PNG workflow smoke.

## Contract evidence

The Image suite proves:

- filtering/order and IMAGE Artifact output;
- no-compatible-input fail closed;
- real RGB and RGBA pixel/mode preservation;
- EXIF orientation normalization before publication;
- animated WebP frame-0 policy plus metadata;
- bounded progress including animation notice and final 1.0;
- safety ceiling fail closed without a huge fixture;
- collision-safe repeated naming with no overwrite;
- later-source failure retains earlier complete PNG and leaves no current partial/temp output;
- `FILE_SET -> FILE_SET`, version 1, NEVER;
- ArtifactRegistry strong nested-output snapshots and current run/node provenance;
- cached `files.literal` does not suppress re-publication;
- direct/workflow pixel and metadata equivalence;
- API/node structural delegation to one converter owner;
- workflow failure correlation to the conversion node.

## Integration audit

Audit result: **PASS**.

No second WebP transformation owner was introduced. API/node contain no Pillow decode, EXIF, save, bomb or temp-publication algorithm. The image pack did not create a generic cross-domain writer or generalized media abstraction. `FILE_SET` remains sufficient because member IMAGE Artifacts carry the semantic type. M3 subprocess diagnostics are not promoted as evidence here because this capability has no subprocess/native execution boundary.

The stable GUI WebP→PNG implementation now becomes compatibility debt; canonical semantic evolution belongs to `ktools-images`.

## Remaining boundaries

- batch publication remains per output, not set-wide transactional;
- Image pack metadata/persistence does not grant ownership to delete earlier published user outputs;
- Pillow 13+ is not automatically accepted;
- Images→PDF remains a separate aggregate-output contract and must reuse, not recopy, the image-safety foundation;
- production GUI/tool wiring is not part of this slice.

## Promotion gate

Technical implementation is complete and audited. The only remaining evidence required for formal Slice-6 promotion is the synchronized ADR/canonical-memory closure HEAD itself passing the standard five hosted jobs.
