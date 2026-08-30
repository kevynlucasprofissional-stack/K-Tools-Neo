# V4.2.3 — Reposition diagnosis

A causa arquitetural da V4.2.2 era a dependência de `state.hasTerminal()` e `repairPositions` dentro de `canWalkSafely()`. Isso fazia saúde do download bloquear navegação. Quando a regra recusava o walk, `ensurePageAt()` chamava `goToPosition()`, que é propositalmente indisponível porque sidebar DOM não prova posição global.

A V4.2.3 remove essa cadeia. Reposition é independente do download state e usa exclusivamente referências comprovadas + N/TOTAL + identidade do curso + transições N→N+1.
