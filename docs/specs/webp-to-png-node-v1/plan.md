# Plan — Image Safety Foundation + WebP→PNG Node V1

Status: **ACTIVE / SPEC LOCKED**

## Sequence

1. Preserve terminal Slice-5 evidence `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / run `33665431920`, 5/5.
2. Record fresh candidate comparison and lock WebP→PNG as the first Image Node Pack slice.
3. Land this spec/plan/tasks/evidence skeleton as a docs-only gate.
4. Require the exact spec HEAD to pass the current five hosted jobs.
5. Add discriminating RED tests before creating `ktools-images` implementation files.
6. Implement Pillow safety policy, image publication and the one canonical WebP→PNG converter owner.
7. Expose thin direct API + `image.webp_to_png` node.
8. Add root CI install/test plus real lossless WebP→PNG workflow smoke.
9. Audit source for duplicated image decode/EXIF/mode/publication logic and prove Artifact/cache/failure boundaries.
10. Require exact-head Ubuntu/Windows Python 3.10/3.13 + xyflow green.
11. Record ADR, evidence, final report and canonical project memory.
12. Require the synchronized closure HEAD itself to pass five hosted jobs before promotion.

## RED strategy

RED test imports the expected `ktools_images` package and contracts while current packs continue to execute first in CI.

Fixtures should be generated deterministically with Pillow rather than stored as opaque binaries where practical:

- lossless RGB WebP;
- lossless RGBA WebP;
- animated WebP with distinguishable first/second frames;
- EXIF-oriented WebP;
- corrupted `.webp` for failure boundary;
- small image combined with a temporarily lowered safety ceiling for bomb/size-policy tests.

The RED is useful only if the current Core/JSON/Text/PDF/Documents boundaries remain green before the image suite fails at missing image product contracts.

## GREEN design

```text
ktools_images.safety
  -> pixel/decompression policy

ktools_images.publication
  -> image-pack path allocation + temp/promote cleanup

ktools_images.converter
  -> canonical convert_webp_files_to_png
       -> safety + Pillow decode/EXIF/mode normalization + publication

ktools_images.api
  -> converter owner

ktools_images.node
  -> converter owner
```

Do not create a generic media/image operation registry or generic cross-domain atomic-writer abstraction.

## Integration audit questions

- Is `Pillow>=12,<13` declared only at package/bootstrap boundary?
- Is the 80M-pixel policy explicit and tested without disabling Pillow's own bomb protection?
- Is first-frame animation behavior deliberate and metadata-visible?
- Is EXIF orientation normalized before mode conversion?
- Is alpha preserved rather than composited?
- Does the converter abort on a bad later source while preserving prior completed PNGs exactly as specified?
- Are outputs IMAGE Artifacts inside FILE_SET, with current workflow provenance and strong snapshots?
- Does cached `files.literal` still lead to new collision-safe outputs?
- Are direct API and node thin callers of one converter owner?
- Does root CI reopen a real generated PNG in every Python lane?
