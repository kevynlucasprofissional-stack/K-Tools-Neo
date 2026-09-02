# ADR-025 — PDF Split V1 uses honest FILE→FILE_SET cardinality and keeps typed members inside FILE_SET

Status: **ACCEPTED / PROVED IN M5 SLICE 3**

## Context

Balanced PDF split takes one source PDF and publishes multiple ordered PDF outputs. Before this slice K-Tools had `files.literal: -> FILE_SET` but no single-file literal node, and PDF Merge already consumed `FILE_SET`.

Two shortcuts were possible:

1. represent one source file as a FILE_SET containing exactly one member;
2. introduce a new `PDF_SET` type for the split output.

Both would add complexity or semantic dishonesty without evidence that the product requires it.

## Decision

### Single-file input

Add `file.literal: -> FILE`, version 1, `CachePolicy.PURE`.

`file.literal` and `files.literal` share the same local-file validation/Artifact construction owner.

`pdf.split.parts` therefore has the honest graph contract:

```text
file.literal -> FILE -> pdf.split.parts
```

Do not encode singular cardinality as "FILE_SET with one element" merely to reuse an existing source node.

### Multi-file output

`pdf.split.parts` outputs `FILE_SET`.

Every member is still a first-class `Artifact` with:

- `type == PDF`;
- MIME `application/pdf`;
- current run/node provenance;
- page-range metadata;
- strong local-file snapshot support.

No `PDF_SET` is introduced in V1.

## Why FILE_SET remains sufficient

The real composition:

```text
file.literal
    ↓ FILE
pdf.split.parts
    ↓ FILE_SET[PDF Artifact, ...]
pdf.merge.files
    ↓ PDF
```

passes hosted Windows/Linux tests and preserves the original page order after recomposition.

This proves the runtime already carries the useful PDF truth at member level. A specialized PDF_SET would add static compatibility rules and conversion pressure without improving V1 runtime evidence.

## Cache/side-effect consequence

`file.literal` is PURE because it has no publication side effect and M4 strongly revalidates the local file before reuse.

`pdf.split.parts` is NEVER because publication of the requested parts is part of its contract. Repeated executions may intentionally create new collision-safe paths; substituting an old FILE_SET would skip required behavior.

## Failure consequence

The FILE_SET is not claimed transactionally. Each PDF part is atomically published, but earlier successful parts may remain if a later part fails. The failed destination is not left partial or represented as a successful Artifact.

## Reopen conditions

Revisit specialized typed collections only when a real capability requires graph-time element-type rejection that member-level Artifact typing/runtime validation cannot safely express, or when UI/catalog ergonomics demonstrate a concrete need that cannot be solved from port metadata.

Do not introduce `PDF_SET`, `IMAGE_SET`, `AUDIO_SET`, etc. merely because domain-specific collections can be named.
