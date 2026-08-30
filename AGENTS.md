# AGENTS.md — K-Tools Neo

All agents working in this repository must follow the project's quality-first engineering protocol.

## Read-before-work order

1. `docs/README.md`
2. `docs/CONSTITUTION.md`
3. `docs/CONSTRAINTS.md`
4. `docs/CURRENT_STATE.md`
5. `docs/DECISIONS.md`
6. `docs/KNOWN_ISSUES.md`
7. `docs/TESTING.md`
8. the active spec under `docs/specs/`
9. `docs/engineering-journal/CURRENT.md`
10. relevant code and tests on the exact current ref

## Core rules

- Treat code/runtime/tests on the exact ref as evidence of current state; docs describe intent and memory, not magic.
- Do not add new product behavior to the legacy monolith when it can instead become a reusable node capability.
- A capability used by a traditional tool screen and by a workflow must have one implementation owner, not duplicated business logic.
- Keep the workflow runtime independent from the visual editor.
- Preserve imported upstream applications under `apps/`; integrate them through adapters unless evidence proves a deeper fork is required.
- Revalidate the branch/head before material changes.
- Use RED → GREEN → REFACTOR when practical and define evidence before implementation.
- Update canonical docs and the Engineering Journal when architecture, invariants, failures, or evidence boundaries change.
- Never commit credentials, cookies, tokens, secrets, or sensitive runtime payloads.
