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

## E-003 — GitHub Actions jobs fail before a recorded step

Status: BLOCKED / EXTERNAL
Environment / refs: PR #1; runs `33327645359` and `33327842478`

### Fingerprint
Every matrix job concludes `failure` almost immediately; API returns no job steps; representative job-log retrieval returns `BlobNotFound`.

### Boundary reached
GitHub Actions orchestration / job startup. Checkout and K-Tools execution are not evidenced.

### Refutation attempt
The second run materially changed the workflow from Python 3.11/3.13 to 3.10/3.13, removed path-filter ambiguity and added explicit least-privilege contents permission. The first observable failure did not move.

### Tempting but wrong interpretation
"The workflow engine fails on Windows and Ubuntu."

### Current classification
External job-start boundary. Exact runner/account/repository cause is unavailable through the connected API.

### Resolution / next evidence
Inspect the failed run in GitHub Actions UI for the platform-provided reason, resolve that account/repository/runner condition, then rerun the PR. Only after a job reaches checkout/install/test can a product failure be classified.

### Anti-repeat lesson
A red CI badge is not product evidence unless the failing step reached the relevant code/runtime boundary. Do not rerun the same no-step fingerprint without a material environmental change.
