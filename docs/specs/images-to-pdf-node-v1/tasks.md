# Tasks — Images→PDF Node V1

Status: **ACTIVE / RED**

- [x] S7-001 verify Slice 6 terminal closure exact-head CI.
- [x] S7-002 fresh-compare Images→PDF vs bounded Files/Folders from exact terminal `main`.
- [x] S7-003 select Images→PDF and lock scope/non-goals.
- [x] S7-004 preserve existing `Pillow>=12,<13` dependency/safety boundary; add no runtime dependency.
- [x] S7-005 specify supported formats, order, frame, EXIF, RGB/alpha-white, aggregate publication and Artifact contracts.
- [x] S7-006 require docs-only spec HEAD CI 5/5 — `ae617e948d5549e3dbca1dbe8d5de19c16555535` / run `33670517542`.
- [x] S7-007 add discriminating RED tests while keeping existing WebP suite available to the same image-test step.
- [ ] S7-008 extract shared safe first-frame reader from Slice-6 policy.
- [ ] S7-009 refactor WebP→PNG to the shared reader with zero semantic regression.
- [ ] S7-010 implement canonical Images→PDF writer owner.
- [ ] S7-011 add singular atomic PDF publication helper with prior-destination preservation.
- [ ] S7-012 expose direct API + `image.files_to_pdf` thin node.
- [ ] S7-013 prove supported-format filtering and ordered pages.
- [ ] S7-014 prove EXIF normalization + first-frame behavior.
- [ ] S7-015 prove RGB normalization and alpha→white composition.
- [ ] S7-016 prove safety ceiling/bomb failures use shared image policy.
- [ ] S7-017 prove serializer/decode failure preserves previous destination and cleans temp/prepared pages.
- [ ] S7-018 prove PDF Artifact metadata/provenance + ArtifactRegistry snapshot.
- [ ] S7-019 prove NEVER semantics with cached upstream `files.literal`.
- [ ] S7-020 prove direct/workflow semantic equivalence + one writer owner.
- [ ] S7-021 add hosted real Images→PDF workflow smoke and independent PDF reopen oracle.
- [ ] S7-022 integration audit/refactor + compatibility debt classification.
- [ ] S7-023 exact-head hosted evidence Ubuntu/Windows 3.10/3.13 + xyflow.
- [ ] S7-024 ADR/canonical memory closure + terminal closure CI.
