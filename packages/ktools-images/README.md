# ktools-images

Official K-Tools Neo image Node Pack.

The pack owns the shared Pillow image-safety/decode foundation plus canonical WebP→PNG and Images→PDF capabilities.

Workflow nodes:

- `image.webp_to_png: FILE_SET -> FILE_SET`, version 1, `CachePolicy.NEVER`;
- `image.files_to_pdf: FILE_SET -> PDF`, version 1, `CachePolicy.NEVER`.

Shared V1 image policy:

- Pillow `>=12,<13`;
- 80,000,000 pixel safety ceiling plus Pillow decompression-bomb protection;
- one shared safe first-frame reader;
- EXIF orientation normalization before capability-specific mode preparation;
- animated/multi-frame inputs use frame 0 only.

WebP→PNG policy:

- existing `.webp` files are converted in input order;
- alpha/transparency is preserved in PNG;
- outputs are collision-safe `IMAGE` Artifacts;
- each PNG publishes atomically, while the whole batch is not transactional.

Images→PDF policy:

- compatible existing JPG/JPEG/PNG/WebP/BMP/TIF/TIFF files are filtered in input order;
- each compatible source contributes one PDF page;
- all PDF pages are RGB;
- RGBA/LA/palette transparency is composited over white;
- one aggregate `PDF` Artifact is published through a same-directory temp file and final replace;
- a handled source/serializer/publication failure does not replace a pre-existing destination.

Direct API and workflow adapters delegate to the same capability owners. Pillow decode/safety/EXIF/frame policy belongs to the shared reader rather than being duplicated by individual image capabilities.
