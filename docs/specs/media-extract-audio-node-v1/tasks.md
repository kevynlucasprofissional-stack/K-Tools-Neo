# Tasks — Media Extract Audio Node V1

Status: **ACTIVE / SPEC GATE**

- [x] S9-001 verify Slice 8 terminal exact-head CI.
- [x] S9-002 inspect remaining legacy features and compare Media against PNG/PDF compress.
- [x] S9-003 select Media Extract Audio V1 to establish FFmpeg boundary.
- [x] S9-004 lock `packages/ktools-media` boundary, `imageio-ffmpeg` dependency, and M3 diagnostics constraint.
- [ ] S9-005 require docs-only spec HEAD CI 5/5.
- [ ] S9-006 add discriminating RED for missing `ktools_media` and `media.extract_audio` contracts.
- [ ] S9-007 implement `ktools_media.ffmpeg` foundation with `record_subprocess`.
- [ ] S9-008 implement `extract_audio_from_video` with atomic temp-to-promote and codec mapping.
- [ ] S9-009 expose direct API + `media.extract_audio: FILE -> AUDIO`, v1 NEVER.
- [ ] S9-010 prove synthetic video creation, extraction success, missing audio stream failure, and invalid video failure.
- [ ] S9-011 prove Artifact metadata, MIME type, and ArtifactRegistry integration.
- [ ] S9-012 add root CI install/test + real FFmpeg smoke test extracting audio.
- [ ] S9-013 exact-head hosted Ubuntu/Windows Python 3.10/3.13 + xyflow green.
- [ ] S9-014 ADR/canonical memory/final-report closure.
- [ ] S9-015 require synchronized terminal closure HEAD CI 5/5 before promotion.
