# M5 Slice 14: Media WebP to PNG Node V1

## What was done
- Implemented media.webp_to_png in ktools-media.
- Uses Pillow (PIL) to open WebP files and save them as PNG.
- Handles animated WebPs (first frame extraction), EXIF rotation, and RGBA transparency.
- Atomic write via .tmp file.
- Tested with mocked PIL so no runtime Pillow dependency needed in CI for unit tests.

## Why it matters
WebP conversion is a legacy capability in K-Tools that allows converting web-optimized images back to the universally compatible PNG format.
