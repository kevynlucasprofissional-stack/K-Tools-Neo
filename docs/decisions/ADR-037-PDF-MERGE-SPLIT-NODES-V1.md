# ADR 037: PDF Merge and Split Nodes V1

## Date
2026-09-03

## Status
Accepted

## Context
K-Tools legacy included merge and split PDF operations using pypdf. We needed to migrate these as reusable node capabilities.

## Decision
- pdf.merge: Takes FILE_SET input (list of PDF Artifacts), merges via pypdf.PdfWriter, outputs single FILE Artifact.
- pdf.split: Takes single FILE input, splits into N equal parts, outputs FILE_SET of part Artifacts.
- Both modules use top-level pypdf import (with try/except for optional dependency graceful failure).
- Atomic write via .tmp intermediate for each output file.

## Consequences
- PDF document management is now part of the workflow graph.
- pypdf is an additional runtime dependency.
