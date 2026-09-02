# Plan — Mixed Document Split Orchestrator V1

Status: **RESOLVED / PROMOTION CLOSURE PENDING TERMINAL HEAD CI**

## Executed sequence

1. Preserved the terminal Slice-4 gate `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.
2. Performed fresh discovery against mixed Document Split, Images→PDF, WebP→PNG and bounded Files/Folders work.
3. Locked the mixed orchestration spec in `c3fe4b98bc923eeb02a0b47877262bcbf83620d9`; hosted gate `33661964413` passed 5/5.
4. Added RED contracts before implementation. `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157` reached the new Documents suite after prior Core/JSON/Text/PDF suites passed and failed because `ktools_documents` did not exist.
5. Implemented `packages/ktools-documents` as a thin package over canonical `ktools-text` and `ktools-pdf` splitters.
6. Added structured direct API plus `document.split.files: FILE_SET -> FILE_SET + JSON`, version 1, NEVER.
7. Added root-CI package installation/tests and a real mixed Markdown/PDF workflow smoke.
8. Audited source ownership, partial-success semantics, Artifact preservation/provenance and cached-source/republication behavior.
9. Technical candidate `bde8b3789d86959b1218969510ed68aed14d410e` passed run `33664355218` 5/5 on Ubuntu/Windows Python 3.10/3.13 plus xyflow.
10. Recorded ADR/evidence/final report and canonical project memory. The only remaining gate is the CI of this documentation closure HEAD itself.

## Architectural result

```text
files.literal (PURE)
      ↓ FILE_SET
ktools_documents.batch.split_documents_into_parts
      ├─ .md/.txt → ktools_text.splitter.split_text_file_into_parts
      └─ .pdf     → ktools_pdf.splitter.split_pdf_into_parts
      ↓
ordered successful child Artifacts + structured report
      ↓
direct API / document.split.files (NEVER)
```

`ktools-documents` owns dispatch, batch aggregation, equal-span progress mapping and partial-success reporting only. It owns no Text/PDF primitive algorithm and introduces no generic orchestration framework.

## Audit answers

- Every compatible Text/PDF child call reaches the canonical package owner: **yes**.
- Current workflow provenance is coherent without reconstructing child Artifacts: **yes**.
- Partial-success errors remain product output in `report`: **yes**.
- Zero-output failure is distinct from partial success: **yes**.
- Cached `files.literal` can be reused while Documents executes/republishes: **yes**.
- Root CI runs a real mixed Text/PDF smoke in all four Python lanes: **yes**.
- A generalized fan-out/fan-in or document collection abstraction was introduced: **no**.

## Next sequencing rule

After the closure HEAD is terminal-green, begin a fresh Slice-6 discovery. Do not infer that Images→PDF, WebP→PNG or Files/Folders wins merely from remaining node count. Image work must first lock Pillow/decompression-bomb/EXIF/alpha/animation policy; Files/Folders must first bound traversal and report semantics.
