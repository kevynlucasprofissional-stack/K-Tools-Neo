# M5 Slice 15: PDF Merge and Split Nodes V1

## What was done
- Implemented pdf.merge and pdf.split nodes in ktools-media.
- Both use pypdf (imported at module level for mockability).
- pdf.merge takes a FILE_SET of PDF artifacts and produces a single merged PDF FILE artifact.
- pdf.split takes a single PDF FILE and produces a FILE_SET of N part PDFs.
- Both follow atomic .tmp file write patterns.
- All 28 tests passing.

## Why it matters
PDF manipulation is one of the most critical legacy capabilities in K-Tools. Merge and split cover the foundational PDF operations that enable downstream document workflows.
