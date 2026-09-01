# K-Tools Neo — ChatGPT Solo Development Mode

Status: **ACTIVE UNTIL PROJECT OWNER CHANGES IT**
Primary implementer: **ChatGPT**
Repository: `kevynlucasprofissional-stack/K-Tools-Neo`
Git model: direct-to-`main`, quality-gated

## 1. Why this mode exists

The project owner temporarily does not want to coordinate multiple coding-agent windows. ChatGPT therefore assumes the combined operational role of:

- Conductor / Chief Architect;
- implementation engineer;
- integration engineer;
- test/evidence reviewer;
- documentation/memory maintainer.

OpenCode, Antigravity and Codex are **paused as active writers** unless the project owner explicitly delegates a future task to them.

Their previous work remains valid repository history/evidence where audited. This mode changes who executes new work; it does not erase prior contributions.

## 2. Operating principle

The human should not have to micro-manage tasks.

Given a continuation prompt, ChatGPT should:

1. inspect current `main` and hosted CI;
2. read canonical memory and the active spec;
3. identify the first unresolved roadmap milestone whose prerequisites are satisfied;
4. inspect the real code before deciding implementation details;
5. define acceptance/evidence before material code changes;
6. implement directly in the GitHub repository;
7. add/adjust tests;
8. use GitHub Actions as hosted evidence where applicable;
9. investigate failures to the first meaningful boundary rather than weakening gates;
10. refactor after GREEN where useful;
11. update Current State, Decisions, Known Issues, Testing and Engineering Journal when materially affected;
12. close the milestone only when claims match evidence;
13. if time/tool budget remains, immediately start the next unblocked roadmap item rather than stopping merely because one subtask completed.

Routine implementation choices do **not** require human approval.

Stop/request intervention only when:

- a product decision genuinely requires the owner's preference and multiple options are materially different;
- credentials, private external services, interactive desktop/browser state or physical/local actions are required and unavailable through tools;
- a destructive/irreversible action needs explicit approval;
- a platform/tool limitation prevents further progress;
- new evidence makes the target itself ambiguous or invalid.

## 3. Source of truth order

At the start of every development cycle:

1. current GitHub `main`;
2. current GitHub Actions state for the relevant head;
3. `AGENTS.md`;
4. `docs/CONSTITUTION.md`;
5. `docs/CONSTRAINTS.md`;
6. `docs/CURRENT_STATE.md`;
7. `docs/ROADMAP.md`;
8. `docs/DECISIONS.md`;
9. `docs/KNOWN_ISSUES.md`;
10. `docs/TESTING.md`;
11. this file;
12. active milestone spec/evidence under `docs/specs/`;
13. `docs/engineering-journal/CURRENT.md`;
14. relevant production code/tests.

Chat history is useful context but never overrides a newer repository state.

## 4. Git policy in solo mode

`main` remains the only normal development line.

ChatGPT may create temporary recovery branches only if an operation is destructive or isolation is technically required, but normal work should land directly on `main`.

Before each material write, re-check the current head when concurrent human/local writes are plausible.

Never force-push over human work.

Prefer small coherent commits that leave the repository understandable after every accepted step.

## 5. Quality loop

For each meaningful implementation unit:

```text
Inspect real state
  ↓
Define hypothesis + acceptance evidence
  ↓
RED / failing criterion where practical
  ↓
GREEN implementation
  ↓
REFACTOR / remove duplicate ownership
  ↓
Regression tests
  ↓
Hosted/native evidence at claimed boundary
  ↓
Audit claims vs evidence
  ↓
Memory closure
```

Do not confuse:

- code existing with behavior being proven;
- a local test with cross-platform evidence;
- a mocked boundary with native integration;
- a spike with production architecture;
- a green unrelated CI job with validation of the changed subsystem.

## 6. Roadmap autonomy

ChatGPT is authorized to proceed through `docs/ROADMAP.md` without waiting for approval between routine milestones.

A roadmap item may be:

- split into smaller specs if risk is high;
- reordered if prerequisite evidence demands it;
- deferred if a lower-level boundary must be solved first.

Any material change in ordering/rationale must be documented.

The target is not “write as much code as possible”. It is **maximize validated product progress**.

## 7. Prompt flow for the project owner

### Prompt A — New chat / full bootstrap

Use this when starting a new conversation or when context may be missing:

```text
Assuma sozinho o desenvolvimento do K-Tools Neo como Conductor + Chief Architect + Implementation Engineer + Integration Engineer.

Repositório: kevynlucasprofissional-stack/K-Tools-Neo

Trabalhe diretamente no GitHub e no main. Antes de decidir qualquer coisa, leia o estado real atual do repositório e do CI e siga AGENTS.md, docs/SOLO_DEVELOPMENT_MODE.md, docs/CURRENT_STATE.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/TESTING.md, o spec ativo e o Engineering Journal.

Continue autonomamente a partir do primeiro milestone não resolvido do roadmap cujos pré-requisitos estejam satisfeitos. Não pare em planejamento, primeira hipótese ou primeira implementação: implemente, teste, audite, corrija, refatore, valide no CI e sincronize a memória canônica. Quando um milestone fechar e ainda houver capacidade nesta execução, avance para o próximo trabalho real.

Não use OpenCode, Antigravity ou Codex por enquanto. Não crie branches/PRs como fluxo normal; main é a linha de trabalho. Não peça validação para decisões rotineiras. Pare apenas em bloqueio real, decisão de produto que dependa de mim, ação destrutiva ou limitação externa intransponível.

Ao final, me entregue: estado terminal atingido, commits/SHA relevantes, evidências/testes, o que mudou no produto, riscos conhecidos e o próximo ponto exato de retomada.
```

### Prompt B — Continuação normal no mesmo projeto

Use na maioria das vezes:

```text
Continue o desenvolvimento solo do K-Tools Neo diretamente no main, seguindo o playbook, o estado real do GitHub e o roadmap. Revalide primeiro o head/CI, retome do primeiro trabalho real não resolvido e trabalhe autonomamente até o próximo estado terminal possível. Não pare só em plano ou checkpoint intermediário.
```

### Prompt C — Continuação longa / avance o máximo possível

Use quando quiser autorizar vários ciclos consecutivos na mesma resposta:

```text
Continue o K-Tools Neo em modo solo e avance o máximo que conseguir com qualidade nesta execução. Feche o milestone atual com evidência real e, se ele for resolvido e ainda houver capacidade, inicie e implemente o próximo milestone do roadmap. Trabalhe diretamente no main, mantenha CI e memória canônica sincronizados e só pare em estado terminal ou limitação real.
```

### Prompt D — Auditoria/hardening antes de seguir

Use quando quiser um ciclo focado em robustez:

```text
Faça um Audit Gate profundo do estado atual do K-Tools Neo antes de avançar: procure bugs, inconsistências de contratos, testes fracos, dívida de integração, claims sem evidência, segurança de paths/subprocessos, compatibilidade Windows/Linux e documentação desatualizada. Corrija o que for material, valide no CI, sincronize a memória e depois retome o roadmap se o estado estiver saudável.
```

## 8. Minimal prompt

Within an existing conversation where this repository is already the clear referent, the owner may simply say:

> **Continue o K-Tools.**

ChatGPT should interpret that as Prompt B, re-read GitHub truth and continue autonomously.

## 9. End-of-turn handoff contract

Every development turn should finish with enough information for a future ChatGPT instance to resume from GitHub alone:

- current/last audited main SHA;
- milestone status;
- hosted CI run/status;
- important files/contracts changed;
- what is proven vs still unproven;
- next exact roadmap/spec action;
- any required human intervention.

The repository should contain the durable details; the chat report is a concise navigation layer.
