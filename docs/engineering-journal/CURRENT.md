# Engineering Journal — Current

## H-001 — Shared node contracts are the correct integration boundary

Status: VALIDATED FOR PLATFORM DIRECTION
Origin: product goal + repository inspection

### Claim
Ready-made tools and workflows should use the same capability implementation behind node/runtime contracts.

### Evidence / reasoning
The repository already contains overlapping utility behavior, a large integrated GUI and standalone mature apps. Adding workflow-specific copies would create multiple owners for the same operation.

### Refutation attempt
Continuing to add features directly to the legacy GUI is simpler short-term, but does not provide a reusable operational language for visual workflows or future agents and increases duplication.

### Practical implication
New platform work begins outside the legacy monolith; capabilities are migrated behind reusable contracts.

---

## H-002 — Python is the lowest-risk first core runtime

Status: PARTIALLY VALIDATED / ACCEPTED FOR FOUNDATION
Origin: repository inspection

### Claim
A Python workflow core minimizes migration friction for the first stage.

### Evidence
Most root utilities and the legacy K-Tools GUI are Python; YT-DLP TUI is Python. XCursos remains Node.js and can be adapted across a process boundary.

### Refutation boundary
This does not prove Python is the final desktop host or highest-performance scheduler. Reopen with integration/performance evidence.

---

## H-003 — Nested imported workflows do not validate the monorepo

Status: VALIDATED
Origin: repository inspection

### Claim
`.github/workflows` directories inside `apps/...` are not sufficient K-Tools root CI.

### Evidence
The baseline repository had no root `.github/workflows/` directory; imported workflow files exist only below app directories.

### Practical implication
Root CI must explicitly own monorepo validation.

---

## H-004 — Editor/runtime separation is a stable cross-project pattern

Status: VALIDATED
Origin: source study of Node-RED, Activepieces, n8n, Rete.js and xyflow

### Claim
K-Tools should keep workflow semantics/execution independent from the visual canvas.

### Evidence
The independently designed systems studied repeatedly separate graph/editor concerns from runtime/registry/execution concerns. xyflow itself solves interaction/viewport/handles without attempting to be an application workflow runtime.

### Refutation attempt
Using a visual-programming framework as both UI and workflow owner could reduce early code, but would duplicate or displace the already-tested `ktools-core` contracts and make CLI/Tools/agent clients depend on a UI framework.

### Classification
Validated for K-Tools architecture.

### Practical implication
`@xyflow/react` can become a frontend dependency while `ktools-core` remains authoritative.

### Evidence record
`docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md`

---

## H-005 — xyflow is the lowest-lock-in canvas candidate

Status: VALIDATED FOR UI SPIKE / PRODUCT PROMOTION STILL UNPROVED
Origin: xyflow source + Activepieces source

### Claim
`@xyflow/react` is the best first implementation for the K-Tools workflow canvas among the studied projects.

### Confirming evidence
The xyflow source already provides handles, `isValidConnection`, viewport, selection, reconnection and graph-view utilities under MIT. Activepieces uses the same library throughout its real workflow builder with custom nodes/edges, minimap, context menus and selection behavior.

### Refutation boundary
No evidence yet proves K-Tools desktop-host packaging, native bridge or large-graph performance in our target environment.

### Classification
Use in a dedicated UI spike; do not call the editor delivered until that boundary is exercised.

---

## H-006 — Run Journal + Artifact provenance must precede production use of expensive workflows

Status: VALIDATED AS TARGET DIRECTION
Origin: Activepieces durable execution + ComfyUI cache/progress + K-Tools media domain

### Claim
Long-running audio/video/PDF workflows need persistent per-node run state and artifact provenance before restart/resume/cache can be trustworthy.

### Evidence
Activepieces implements replay-and-skip from durable step outputs; ComfyUI uses input signatures/cached node outputs and explicit node progress states. K-Tools workloads can be substantially more expensive than the current deterministic fixture nodes.

### Refutation attempt
A pure in-memory executor is sufficient for the Foundation milestone and remains intentionally simpler. It becomes inadequate only when real expensive workflows require crash recovery/history/cache.

### Practical implication
After the first real Node Pack proves capability composition, persistence/Run Journal should precede a broad visual-workflow rollout.

---

## H-007 — Third-party source must be classified by reuse boundary, not by popularity

Status: VALIDATED
Origin: license/source inspection of all seven study snapshots

### Claim
Some projects are safe candidates for direct dependency/selective reuse while others should remain clean-room references.

### Classification
- xyflow: direct dependency candidate (MIT);
- Activepieces: selective donor code only outside declared Enterprise areas and after per-file/dependency review (MIT area);
- Node-RED: selective donor code possible under Apache-2.0 obligations;
- Rete.js/LiteGraph.js: MIT, but adopting their graph ownership is architecturally unnecessary;
- n8n: conceptual/UX reference under current strategy, not donor code due Sustainable Use restrictions;
- ComfyUI: conceptual reference under current strategy, not donor code unless GPL compatibility is deliberately accepted.

### Anti-repeat lesson
Never copy a useful upstream implementation before classifying its license boundary and proving that direct reuse is better than a small contract-owned implementation.

---

## E-001 — Local editable install could not reach build dependencies

Status: CLASSIFIED / EXTERNAL HARNESS
Environment: isolated execution sandbox

### Fingerprint
pip failed resolving `setuptools` because package-index network/DNS access was unavailable.

### Boundary reached
Packaging dependency acquisition, before K-Tools package/runtime execution.

### Tempting but wrong interpretation
"ktools-core cannot be installed."

### Classification
Harness/environment limitation. Direct source tests and CLI smoke subsequently passed.

### Regression guard
GitHub CI performs the real editable-install boundary once a runner starts.

---

## E-002 — Optional input passed validation but initially crashed execution

Status: RESOLVED
Environment: local candidate before commit

### Fingerprint
Executor indexed every declared input in the incoming-edge map even when `required=False`.

### Root cause
Validation and execution had inconsistent optional-port semantics.

### Correction
Executor now skips absent optional inputs.

### Regression guard
`test_optional_input_may_be_unconnected`.

### Anti-repeat lesson
Any schema distinction introduced in validation must be exercised through execution, not validated only structurally.

---

## E-003 — GitHub Actions jobs failed before a recorded step

Status: RESOLVED / ROOT CAUSE PROVED / REGRESSION BOUNDARY VALIDATED
Environment / refs: PR #1; historical runs `33327645359`, `33327842478`; resolving run `33330660076`

### Historical fingerprint
Every matrix job concluded `failure` almost immediately; API returned no job steps; representative job-log retrieval returned `BlobNotFound`.

### Boundary reached
GitHub Actions orchestration / job startup. Checkout and K-Tools execution were not evidenced in the historical runs.

### Platform evidence that resolved the unknown
The GitHub Actions UI annotation stated that the jobs were not started because recent account payments had failed or the spending limit needed to be increased, directing the account to Billing & plans.

This proved the original red jobs were an account/billing Actions boundary, not a Windows/Linux or `ktools-core` failure.

### Material environment change
The repository was changed from private to public; GitHub repository metadata reported `visibility: public`.

### Resolving experiment
Exact-head run `33330660076` on `1ccffb11af25a8d993ead931183380d354746131`.

Observed:

- Ubuntu 3.10: success;
- Ubuntu 3.13: success;
- Windows 3.10: success;
- Windows 3.13: success;
- all matrix paths reached Checkout, Setup Python, editable install, unit/contract tests and CLI smoke successfully.

### Classification
Historical external blocker closed. The workflow and product boundary are now evidenced on hosted Ubuntu/Windows runners.

### Anti-repeat lesson
A red CI badge is not product evidence unless the failing step reached the relevant code/runtime boundary. Once a platform annotation identifies billing, changing workflow/product code is not a valid fix. After an environmental change, rerun the exact acceptance boundary and classify from the first real failing step.
