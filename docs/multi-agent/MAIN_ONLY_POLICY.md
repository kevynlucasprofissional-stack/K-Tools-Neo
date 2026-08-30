# K-Tools Neo — Main-Only Development Policy

Status: ACTIVE
Authority: project owner decision

## Purpose

K-Tools Neo now uses a simplified **single-main development model**.

The goal is to remove coordination overhead from many task branches, draft branches and staging PRs while preserving quality through ownership discipline, rebasing before push, tests and evidence.

## Source of truth

`main` is the only active source of development and integration truth.

Unless the project owner explicitly says otherwise:

- new work starts from current `main`;
- new work lands directly on `main`;
- agents do not create task branches merely for normal implementation;
- PRs are not required as an intermediate staging mechanism;
- old branch names in historical Work Packets are informational only.

This policy overrides older instructions that require OpenCode or Antigravity to work on separate branches or avoid direct writes to `main`.

## Safe multi-agent operation on one main

Parallelism is still allowed, but it is based on **disjoint ownership**, not branch isolation.

Example safe wave:

```text
OpenCode      -> packages/ktools-core / node packs
Antigravity   -> spikes/xyflow-editor or apps/desktop
ChatGPT       -> architecture/spec/integration docs
```

Unsafe parallelism:

```text
OpenCode      -> edits node contract X
Antigravity   -> edits the same node contract X
```

When two tasks need the same file or compatibility-sensitive contract, serialize them.

## Required write protocol

Before changing files:

1. fetch current `main`;
2. pull/rebase to current `origin/main`;
3. record the starting SHA;
4. read the required canonical docs and current task packet;
5. confirm ownership does not overlap another active writer.

Before pushing:

1. fetch again;
2. `git pull --rebase origin main`;
3. inspect any upstream changes that landed during the task;
4. rerun task-local tests and relevant regressions;
5. push directly to `main` only when the owned change remains valid.

If the push is rejected because `main` moved, do not force-push. Pull/rebase, revalidate and push normally.

## Conflict rule

Never force through a semantic conflict just to preserve parallelism.

If another agent changed the same file/contract:

- stop the overlapping edit;
- re-read current `main`;
- preserve already-valid upstream work;
- ask the Conductor to assign one writer or define an explicit dependency order.

## CI and evidence

Direct-to-main does not mean unvalidated.

After material commits:

- run the relevant local tests before push;
- let root GitHub Actions validate `main` where configured;
- if `main` turns red, the agent responsible for the triggering change owns the first investigation;
- classify the first failing boundary before changing unrelated code;
- do not weaken tests to regain green.

## Roles

### ChatGPT — Conductor / Chief Architect / Integration Engineer

Owns architecture, shared contracts, milestone sequencing, integration decisions, canonical memory and conflict arbitration.

### OpenCode — Runtime / Backend Implementation Lead

Owns delegated backend/runtime/node-pack work on non-overlapping paths.

### Antigravity — Frontend / UX / Product Prototype Lead

Owns delegated frontend/editor/UX work on non-overlapping paths.

### Codex

Not part of the K-Tools agent pool until the project owner changes that decision.

## Work Packets

Versioned Work Packets remain the preferred way to give agents full local instructions.

However, any packet text that says:

- `Working branch: ...`;
- `Do not write directly to main`;
- `Open a PR`;
- `Do not merge your own PR`;

is overridden by this policy unless the project owner explicitly re-enables branch isolation for that specific task.

## Exceptions

A temporary branch may be created only when one of these is true:

- the project owner explicitly requests it;
- a destructive migration/recovery experiment needs isolation;
- an external contribution mechanism requires a PR;
- GitHub permissions prevent direct `main` writes.

The default remains: **work on `main`, keep ownership disjoint, rebase before push, test, and keep moving.**
