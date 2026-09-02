# Plan — Images→PDF Node V1

Status: **ACTIVE / SPEC LOCKED**

## Sequence

1. Preserve terminal Slice-6 evidence `9b9fc57bd4bfb28d7e23637651a30182ce6f8828` / run `33668942264`, 5/5.
2. Record fresh comparison against bounded Files/Folders and select Images→PDF.
3. Land this spec/plan/tasks/evidence set as a docs-only gate.
4. Require the exact spec HEAD to pass all five hosted jobs.
5. Add discriminating RED tests to the existing `ktools-images` package.
6. Extract one shared safe first-frame reader from the already-proved Slice-6 decode policy.
7. Refactor WebP→PNG to consume the shared reader without changing its semantics.
8. Implement one canonical Images→PDF writer owner using ordered RGB pages, alpha→white and singular atomic PDF publication.
9. Expose thin direct API + `image.files_to_pdf` node.
10. Add a real hosted Images→PDF workflow smoke and semantic PDF reopen verification.
11. Audit single ownership, cleanup/failure boundaries, Artifact/cache behavior and absence of duplicate Pillow-open policy.
12. Require exact-head Ubuntu/Windows Python 3.10/3.13 + xyflow green.
13. Record ADR, evidence, final report, current-state/roadmap/testing/issues/journal closure.
14. Require the synchronized closure HEAD itself to pass all five hosted jobs before promotion.

## RED strategy

The package already exists, so a useful RED must isolate missing Slice-7 contracts rather than repeat Slice-6 package absence.

Add `test_images_to_pdf_v1.py` that imports the expected shared-reader/PDF-writer/node surface. Existing WebP tests must still run and pass first. The new suite should fail on missing `ktools_images.reader`, `ktools_images.pdf_writer`, `api.images_to_pdf` or `image.files_to_pdf` contracts.

No bootstrap failure counts as RED.

## GREEN shape

```text
ktools_images.safety
  -> bomb/pixel/orientation primitives already proved

ktools_images.reader
  -> guarded Image.open + first-frame + EXIF + detach
       ↑                         ↑
       |                         |
ktools_images.converter     ktools_images.pdf_writer
  -> PNG mode + publish       -> RGB/alpha-white + aggregate PDF publish
       ↑                         ↑
       |                         |
      API/node callers remain thin adapters
```

`publication.py` may gain PDF-specific same-directory temp/promote helpers, but only pack-local helpers whose behavior is proved by this slice. Do not move publication into core.

## Refactor gate

The Slice-6 architecture test currently expects `Image.open` in the WebP converter because only one consumer existed then. Slice 7 intentionally changes that invariant: after GREEN, `Image.open`, decompression-warning setup and EXIF transpose belong to the shared reader. Update the old architecture regression to enforce the new owner while preserving every WebP behavioral test.

## Integration audit questions

- Is Pillow still declared only at the package boundary?
- Is there exactly one guarded `Image.open`/first-frame/EXIF owner used by both capabilities?
- Does Images→PDF add only PDF-specific RGB/alpha/aggregate behavior?
- Does WebP→PNG preserve alpha and collision semantics after the reader refactor?
- Does the PDF writer hold/close prepared pages safely on all paths?
- Does a failure before final promotion preserve an existing destination?
- Is the singular PDF output a PDF Artifact with strong registry snapshot?
- Does `image.files_to_pdf` stay NEVER while cached upstream literals remain reusable?
- Are API and node adapters algorithm-free?
- Does hosted CI independently reopen the generated PDF rather than trusting only the writer return value?
