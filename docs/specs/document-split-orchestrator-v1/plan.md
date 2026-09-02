# Plan — Mixed Document Split Orchestrator V1

Status: **ACTIVE / SPEC LOCKED**

## Sequence

1. Preserve terminal Slice-4 evidence and exact `main` head.
2. Land Slice-5 spec/plan/tasks/evidence skeleton as a docs-only gate.
3. Add discriminating RED tests before package implementation.
4. Implement `ktools-documents` package with no primitive split logic.
5. Reuse canonical `ktools_text.splitter` and `ktools_pdf.splitter` owners directly so returned Artifacts preserve domain semantics.
6. Expose structured direct API and `document.split.files` workflow node.
7. Add root CI install/test/smoke for the new pack.
8. Audit source for duplicated text/PDF algorithms and validate partial-success/report semantics.
9. Require exact-head Windows/Linux Python 3.10/3.13 + xyflow green.
10. Close ADR/memory/final report and require terminal closure CI.

## RED strategy

The initial RED should import the expected package/API/node symbols dynamically where practical so the first product failure is the absence of `ktools-documents`, not a malformed test harness.

The RED fixture should include:

- one valid `.md` source;
- one valid `.pdf` source;
- one unsupported path to prove filtering;
- one compatible but deliberately bad source for partial-success behavior;
- later valid source after the failure to prove continuation.

## GREEN design

Keep the package thin:

```text
batch.py
  DocumentSplitBatchError
  DocumentSplitBatchResult
  split_documents_into_parts

api.py
  split_document_files_into_parts

node.py
  DOCUMENT_SPLIT_NODE_TYPE_ID
  register_nodes
```

`batch.py` is allowed to know only:

- supported suffix dispatch;
- child callback weighting;
- per-source exception aggregation;
- ordered Artifact flattening;
- batch result/report construction.

Text/PDF primitive algorithms remain forbidden in this package.

## Integration audit questions

- Does every Text/PDF child call go through canonical owners?
- Is provenance current-run/current-node without reconstructing Artifacts?
- Are partial-success errors exposed as product output rather than swallowed?
- Does zero-output failure remain distinguishable from partial success?
- Does repeated execution republish because the node is NEVER?
- Does root CI exercise a real mixed Text/PDF batch in every Python lane?
- Did the new package accidentally create a generic orchestrator abstraction not justified by this one use case?
