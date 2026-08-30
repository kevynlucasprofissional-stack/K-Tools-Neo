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
GitHub CI performs the real editable-install boundary.

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

## E-003 — GitHub Actions jobs fail before a recorded step

Status: ACTIVE / EXTERNAL-BOUNDARY SUSPECTED
Environment / ref: PR #1, SHA `3fb12310f531a3754c751116fdc5470ab29ea159`, run `33327645359`

### Fingerprint
Four matrix jobs conclude `failure` almost immediately; API returns no job steps; job-log retrieval returns `BlobNotFound`.

### Boundary reached
GitHub Actions orchestration / job startup. Checkout and K-Tools execution are not evidenced.

### Tempting but wrong interpretation
"The workflow engine fails on Windows and Ubuntu."

### Current classification
The available evidence does not reach the product. Exact account/runner/infrastructure cause is not exposed by the connected API and remains unknown.

### Next discriminating experiment
One materially changed CI definition is allowed: align supported Python versions and make permissions explicit. If the same no-step fingerprint repeats, classify as externally blocked and do not retry unchanged.

### Anti-repeat lesson
A red CI badge is not product evidence unless the failing step reached the relevant code/runtime boundary.
