# Tasks — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

- [x] T-001 compare first M5 candidates and select Markdown/TXT merge slice.
- [x] T-002 identify stable legacy owner `merge_text_files(...)` and decoding helper.
- [x] T-003 characterize exact separator/output/overwrite behavior with tests.
- [x] T-004 add FILE_SET core RED tests.
- [x] T-005 implement FILE_SET contract and regress core.
- [x] T-006 create `packages/ktools-text` skeleton and RED behavior tests.
- [x] T-007 implement shared merge capability/writer/direct API.
- [x] T-008 implement `text.merge.files` thin node adapter.
- [x] T-009 prove direct/node byte equivalence and no duplicated merge logic.
- [x] T-010 prove M4 ArtifactRegistry and NEVER/cache semantics.
- [x] T-011 extend root CI + text workflow smoke.
- [x] T-012 hosted Windows/Linux/xyflow evidence on code candidate.
- [x] T-013 integration audit; remove duplicated local-file URI parser; decide canonical owner.
- [x] T-014 canonical-memory exact-head CI, promotion PR merge and post-merge `main` verification.

## Promotion closure

Final pre-merge candidate: `31b02467cac9c9dc59733d32325728792eb83b22`.

Final pre-merge hosted run: `33629673452` — 5/5 success.

Draft PR #8 was closed administratively after the connector could not transition it to Ready. Replacement non-draft PR #9 used the same candidate and was merged.

Promotion merge commit: `958d5bf563cda21673d69865d1508831c599c006`.

Post-merge `main` run: `33630159514` — success.