# ktools-images

Official K-Tools Neo image Node Pack.

V1 establishes the shared Pillow safety boundary and exposes lossless WebP → PNG conversion through one canonical owner.

Workflow node:

- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1, `CachePolicy.NEVER`.

V1 policy:

- Pillow `>=12,<13`;
- 80,000,000 pixel safety ceiling plus Pillow decompression-bomb protection;
- EXIF orientation normalization before publication;
- animated WebP uses frame 0 only;
- alpha/transparency is preserved in PNG;
- outputs are collision-safe `IMAGE` Artifacts;
- each PNG publishes atomically, while the whole batch is not transactional.
