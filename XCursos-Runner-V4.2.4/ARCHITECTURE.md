# XCursos Runner V4.2.4 — Architecture

## Reposition Engine

`XCursosCourseRunner` usa `NavigationPlanner` antes de qualquer ação. Estratégias:

1. `ALREADY_AT_TARGET`
2. `EXACT_URL`
3. `WALK_FROM_CURRENT`
4. `WALK_FROM_CHECKPOINT`
5. `WALK_FROM_COURSE_ANCHOR`
6. `NO_SAFE_PATH`

O planner escolhe a rota comprovável de menor número de passos. O runner não usa `PageController.goToPosition()` como fallback.

### Invariant de navegação

Segurança é definida por: mesmo curso + mesmo TOTAL + posição N + exatamente uma ação `Próxima` + observação N+1. Estado de download, manifesto e `repairPositions` não determinam se uma página pode ser atravessada.

Navegar por uma posição nunca faz commit. Uma posição MISSING permanece MISSING; uma posição em repair permanece repair.

### Navigation Index V2

`lesson-navigation-index.json` contém posições observadas e `courseAnchor` comprovada (posição 1). V1 é migrado automaticamente. URLs passam por `safePersistUrl`; signed queries/tokens não são persistidos. Entradas stale são removidas após abrir URL e observar posição divergente.

### Error model

Outro curso → `COURSE_IDENTITY_MISMATCH`; TOTAL divergente → `TOTAL_CHANGED`; auth/Cloudflare são propagados; nenhuma rota → `POSITION_REPOSITION_NO_SAFE_PATH` com details. Esses erros são estruturais ou auth, não retry cego.

### Observability

`RuntimeStats.repositionSteps` conta passos de reposicionamento sem alterar `coverageProcessed`, `downloadsSucceeded` ou `runOperations`. Logs usam `[REPOSITION]`.

### CLI

`xcursos version` mostra versão/caminhos reais. `xcursos diagnose-reposition --target N --json` calcula o plano sem navegar, clicar ou baixar.

## V4.2.4 — Lesson-scoped media generations

`PageController` abre uma nova generation no `NetworkMediaObserver` antes de `navigateExact`, `Próxima` e refresh. Eventos antigos continuam disponíveis para diagnóstico, mas não podem ser escolhidos por `best()` fora da generation atual.

A seleção de mídia usa correlação por objeto (hostname + pathname, query ignorada):

1. network response 2xx/3xx da generation atual, se correlacionada ao objeto DOM atual;
2. `video.currentSrc/src` HTTP atual;
3. mídia parseada do HTML;
4. network atual quando DOM não oferece URL HTTP utilizável (ex.: blob).

Mismatches são diagnosticados por fingerprints sem persistir credenciais.
