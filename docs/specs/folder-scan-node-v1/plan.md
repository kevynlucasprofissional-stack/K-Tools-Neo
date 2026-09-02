# Plan — Folder Scan Node V1

Status: **ACTIVE / SPEC LOCKED**

## Sequence

1. Preserve terminal Slice-7 main `85985dd2abf9c6251a15332040e44a00def6798f` and run `33675089416`, 5/5.
2. Record fresh comparison of Files/Folders, PNG→ICO, PDF compression and Media and select bounded Folder Scan V1.
3. Reconcile the stale branch-only delivery sentence in `docs/CONSTRAINTS.md` with the active Solo/Main-Only policy.
4. Land spec/plan/tasks/evidence as a docs-only gate.
5. Require the exact docs-only HEAD to pass Ubuntu/Windows Python 3.10/3.13 + xyflow.
6. Add discriminating RED tests for `folder.literal` and `ktools-filesystem` without adding implementation.
7. Require RED to reach the intended missing-product boundary after prior suites/bootstrap remain healthy.
8. Implement `folder.literal` in core and one canonical `ktools-filesystem` scanner/API/node owner.
9. Add no-follow symlink/reparse safety, deterministic ordering, hidden/extension policies and nested error aggregation.
10. Add root CI install/test/smoke and scan→Text composition evidence.
11. Audit path safety, Windows/Linux semantics, cache policy, Artifact provenance/snapshots and one-owner architecture.
12. Refactor only where evidence shows duplicated stable policy; do not create a generic filesystem framework.
13. Require exact-head hosted 5/5.
14. Record ADR, final report, current state, roadmap, testing, known issues and Engineering Journal closure.
15. Require synchronized closure HEAD itself to pass 5/5 before terminal promotion.

## RED strategy

The new package does not exist yet. The useful RED should still prove the platform reaches the new capability boundary rather than failing on an unrelated install step.

Preferred shape:

- add core contract tests expecting `folder.literal`;
- add `packages/ktools-filesystem/tests/test_folder_scan_v1.py` that imports the intended scanner/API/node surface;
- initially do **not** add a CI install command for a nonexistent package if that would cause bootstrap to fail before the tests;
- let the RED fail on absent core/node-pack product contracts after prior suites remain green.

After RED is classified, GREEN adds package metadata and root CI installation/test/smoke.

## GREEN shape

```text
ktools-core
  └─ folder.literal -> FOLDER (NEVER)
                         ↓
               ktools_filesystem.scanner
                 ├─ root validation
                 ├─ hidden/extension policy
                 ├─ no-follow reparse policy
                 ├─ nested error aggregation
                 ├─ deterministic ordering
                 └─ FILE Artifact construction
                    ↑                 ↑
              direct API        workflow node
                                  folder.scan_files
```

Export/report-file writers are not in this ownership tree.

## Security / cross-platform audit

Audit must answer:

- Can a symlink/junction/reparse directory cause traversal outside the selected root?
- Is root reparse status checked without resolving away the evidence first?
- Are metadata calls non-following where relevant?
- Is Windows reparse detection guarded for platforms that lack `FILE_ATTRIBUTE_REPARSE_POINT`?
- Do nested permission failures preserve sibling progress?
- Are all returned regular files actually beneath the root by lexical/traversal construction?
- Does final ordering ignore OS enumeration order?
- Is the dot-component hidden rule identical on Windows/Linux?
- Are extension filters configuration, not globs?
- Is a valid empty scan distinguishable from fatal root failure?

## Cache audit

`folder.literal` and `folder.scan_files` remain NEVER in V1.

Proof must mutate the folder between two equivalent workflow executions and show the second scan observes current files. No scan cache hit is permitted. This explicitly avoids pretending M4's local-file SHA validity is a recursive FOLDER snapshot.

## Integration audit

- exactly one scanner owns traversal/filtering/sorting/error aggregation;
- direct API and node delegate to it;
- report exporters remain outside the package capability;
- FILE_SET remains the correct collection contract;
- ArtifactRegistry recursively observes emitted FILE Artifacts;
- hosted scan output can feed an existing canonical Text node without adapter glue or raw path conventions.
