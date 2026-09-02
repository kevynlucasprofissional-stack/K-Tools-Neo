# Evidence — Text Node Pack V1

Status: **DISCOVERY / RED NOT STARTED**

## Candidate selection evidence

The stable monolith contains a bounded `merge_text_files(...)` operation for `.md`/`.txt`, with validation, decoding fallback, separator modes, output/input collision guard and temporary publication.

Alternative first slices were rejected for now:

- WebP → PNG requires Pillow plus image decompression safety, EXIF transpose, alpha-mode handling, animated-image first-frame policy and output collision logic;
- generic folder scanning is currently an instance/UI helper parameterized by callbacks and is less clean as the first standalone capability owner.

## M4 prerequisite

M4 is promoted before M5 implementation starts.

Formal promotion HEAD:

`b09e6ac62fa74e3e1a22e7cced0a472af50285b1`

Promotion run:

`33626260487`

Result: all five hosted jobs success.

## Pending evidence

No Text Node Pack behavior is claimed yet. Characterization RED tests are the next evidence boundary.
