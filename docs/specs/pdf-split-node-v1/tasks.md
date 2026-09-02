# Tasks — PDF Split Node V1

Status: **ACTIVE / PRE-RED**

- [x] S3-001 re-inventory remaining bounded owners after PDF Merge V1 terminal green.
- [x] S3-002 compare PDF split, Images→PDF, WebP→PNG, Document Split and Files/Folders scan.
- [x] S3-003 select PDF Split V1 and lock scope/cardinality/FILE_SET decision.
- [ ] S3-004 add characterization + contract RED tests.
- [ ] S3-005 add shared single-file `file.literal` source contract.
- [ ] S3-006 implement `splitter.split_pdf_into_parts` using shared PDF reader/publication boundaries.
- [ ] S3-007 expose direct API and `pdf.split.parts` thin adapter.
- [ ] S3-008 prove PDF Artifact metadata/provenance + ArtifactRegistry nested snapshots.
- [ ] S3-009 prove NEVER semantics with cached file literal and repeated collision-safe publication.
- [ ] S3-010 prove direct/workflow equivalence and split→merge composition.
- [ ] S3-011 extend root CI with hosted split/composition smoke.
- [ ] S3-012 integration audit/refactor and debt classification.
- [ ] S3-013 exact-head hosted evidence on Ubuntu/Windows Python 3.10/3.13 + xyflow.
- [ ] S3-014 canonical memory closure and terminal `main` verification.
