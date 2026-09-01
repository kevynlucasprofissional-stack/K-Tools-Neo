# OC-001 — Conductor Audit

Status: **RESOLVED / FIRST OFFICIAL NODE PACK PROVED**
Conductor: ChatGPT
Implementation commit: `a41aa8beaef0d22269f9ac387c972438986902f8`
Integrated `main` checkpoint: `c9cdffdc6b6502b07f3546db7e3e3fafe3407068`
Hosted CI run: `33551124229` — success

## 1. Objective audited

OC-001 existed to prove the central K-Tools Neo invariant with real product behavior:

> one useful existing capability has one implementation owner and is reusable through both a direct invocation path and a workflow node.

The objective is achieved with the first official Node Pack: `packages/ktools-json/`.

## 2. Capability selected

The selected capability is JSON document splitting, extracted from the legacy K-Tools JSON tools.

The task-local candidate ranking compared JSON split against text merge, Images→PDF, WebP→PNG, folder/report tools, FFmpeg-based media transformations and heavier standalone utilities. JSON split was chosen because it is useful, deterministic, stdlib-only, cross-platform, easy to fixture safely, maps cleanly to typed JSON ports and exposes meaningful failure semantics without introducing a native/runtime dependency in the first production proof.

This was an appropriate first capability. It does not imply JSON is the highest-value long-term K-Tools domain; it was the strongest first architectural proof.

## 3. Single-owner architecture verified

The production path is:

```text
Direct API (`ktools_json.api.split_json`)
                 \
                  -> `writer.split_and_write`
                         -> `capability.split_json_document`
                  /
Workflow node (`json.split`)
```

Repository evidence supports this separation:

- `capability.py` owns split planning/transformation semantics and performs no file I/O;
- `writer.py` is the shared file-producing orchestration and atomic-write boundary;
- `api.py` is a thin source-reading/direct API layer;
- `node.py` is a thin K-Tools workflow adapter;
- both API and node import/use the same `writer.split_and_write` function;
- integration tests assert identity/reachability of the shared owner and byte-identical part outputs between direct and node paths.

The anti-pattern of separate direct/workflow implementations was not introduced.

## 4. Contract verified

The Node Pack provides:

- node type `json.split`;
- typed required input `json_data: JSON`;
- outputs `parts: JSON` and `summary: JSON`;
- fixture/source node `json.literal` for typed composition/smoke workflows;
- `parts` and `size` split modes;
- deterministic output naming;
- classified configuration/source/document/collision errors;
- default refusal to overwrite pre-existing part files;
- per-file temp-write + `os.replace` atomic publication;
- post-write JSON parsing validation;
- artifact-shaped part metadata (`uri`, byte size, item count, type).

The current artifact-shaped dictionaries are an intentional bridge, not yet the final durable `Artifact` lifecycle.

## 5. Hosted evidence

Run `33551124229` on `main@c9cdffdc6b6502b07f3546db7e3e3fafe3407068` completed successfully.

The Python matrix covered:

- Ubuntu / Python 3.10;
- Ubuntu / Python 3.13;
- Windows / Python 3.10;
- Windows / Python 3.13.

On the matrix jobs GitHub Actions successfully reached:

1. checkout;
2. Python setup;
3. editable install of `ktools-core`;
4. editable install of `ktools-json`;
5. core unit/contract tests;
6. JSON Node Pack unit/contract tests;
7. core CLI smoke;
8. JSON workflow smoke;
9. verification that smoke artifacts were produced and parse as JSON.

The xyflow spike job also remained green in the same repository CI, so OC-001 did not regress the already-audited frontend spike.

## 6. Collision-smoke observation

The OpenCode handoff noted that an initial local smoke hit the output-collision guard because a previous `%TEMP%/oc001-split-out` remained. This is expected behavior under the new default `overwrite=False`, not a product failure.

The hosted CI uses a fresh runner temp directory and independently proves the smoke on clean state. Future local smoke helpers should prefer unique run directories or explicit cleanup so a correct safety guard is not mistaken for a test failure.

## 7. Evidence boundaries / follow-up debt

OC-001 proves the capability/node architecture. It does **not** yet prove:

- durable workflow/run persistence;
- restart/resume after process interruption;
- semantic cache or selective re-execution;
- final `Artifact` persistence/provenance semantics;
- dynamic Node Pack discovery/version compatibility;
- production UI consumption of Node Pack schemas;
- native media boundaries such as FFmpeg.

Minor hardening opportunities for `ktools-json` may be addressed opportunistically, but they do not block closure of the architectural milestone.

## 8. Architectural conclusion

The central platform thesis is now supported by real code rather than only synthetic Foundation nodes:

```text
Capability implementation
       ↑          ↑
 direct API    workflow node
```

This validates continuing migration through official Node Packs instead of adding behavior to the legacy monolith.

## 9. Next milestone

Proceed to **Durable Execution V1** using a real Node Pack workload as evidence.

The next milestone should establish:

- Run and node lifecycle states;
- appendable/inspectable Run Journal events;
- SQLite persistence;
- durable run/node records and outputs metadata;
- crash/interruption observability;
- a clean event contract that a future editor can consume.

Resume/cache semantics should only be promoted after the journal/persistence model is proven first.

## 10. Terminal state

**OC-001 RESOLVED.**

The first official K-Tools Node Pack is proven on hosted Windows/Linux CI and is accepted into the product architecture.