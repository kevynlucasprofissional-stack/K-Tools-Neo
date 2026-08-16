# Diagnóstico científico — navegação Próxima — V4.2.1

## Observação live

O locator encontra o `<button>Próxima</button>`, mas `locator.click()` pode exceder 20 s aguardando actionability. Em outra execução o mesmo runner atravessou dezenas de posições antes de reproduzir o mesmo bloqueio. Portanto, encontrar o elemento e executar a ação são problemas distintos.

## Hipótese 1 — locator errado

**Predição:** o locator não resolveria ou resolveria um elemento semanticamente incorreto.

**Experimento/evidência:** o log live mostra o locator resolvendo um `<button>` e falhando somente em `visible/enabled/stable`. O HTML real também contém a ação Próxima.

**Conclusão:** enfraquecida. O locator correto pode continuar não actionable.

## Hipótese 2 — actionability transitória

**Predição:** `trial:true` e amostras DOM distinguem estabilidade, overlay, disabled e motion sem clicar.

**Experimento:** `ActionabilityProbe` com bounding boxes por animation frames, `elementFromPoint`, style, animations/transitions e trial click.

**Resultado:** testes distinguem elemento estável, movimento, invisibilidade, disabled, overlay, animation e trial timeout.

**Conclusão:** sustentada como classe de falha observável; o próximo live snapshot determinará a causa visual específica no XCursos real.

## Hipótese 3 — TimeoutError cru é mal classificado

**Predição:** `name=TimeoutError`, `code=null`, `message=Timeout ... exceeded` não deveria decidir retry fora de contexto, mas no click de Próxima deve virar erro de domínio.

**Experimento:** teste com TimeoutError cru e RetryPolicy.

**Resultado:** antes da correção o erro semântico era desconhecido; depois `PageController` produz `NEXT_ACTIONABILITY_TIMEOUT` e somente esse código é `TRANSIENT`.

**Conclusão:** confirmada e corrigida.

## Hipótese 4 — fallback pode provocar duplo avanço

**Predição:** se o click normal disparar navegação e ainda assim lançar TimeoutError, chamar `dispatchEvent` imediatamente pode provocar N→N+2.

**Experimento:** click muda 39→40 e em seguida lança TimeoutError.

**Resultado:** a nova navegação observa 40 antes do fallback; `dispatchEvent` permanece em zero chamadas.

**Conclusão:** risco confirmado conceitualmente e fechado por invariant ação→observação.

## Hipótese 5 — dispatchEvent é fallback suficiente

**Predição:** quando click normal falha por actionability e posição permanece N, um único DOM click pode produzir N+1.

**Experimento:** 39 permanece após TimeoutError, `dispatchEvent('click')` muda para 40.

**Resultado:** sucesso; skip para 41 e regressão para 38 são classificados e bloqueados.

**Conclusão:** sustentada pelos testes. Terceiro fallback CDP não foi implementado por falta de evidência de necessidade.

## Hipótese 6 — animations/transitions são sempre a causa

**Predição:** neutralizar motion deveria sempre melhorar o probe.

**Experimento:** cenários instável→estável e instável→continua instável.

**Resultado:** em um cenário melhora; no outro não. Quando não há melhora, o style é removido imediatamente.

**Conclusão:** hipótese global rejeitada. Neutralização permanece apenas evidence-gated, temporária e reversível.

## Hipótese 7 — mojibake causa o click failure

**Predição:** o mesmo timeout desapareceria quando “Próxima” estivesse corretamente codificado.

**Evidência live:** o comando direto mostrou “Próxima” corretamente e teve o mesmo TimeoutError; o mojibake apareceu no wrapper PowerShell.

**Conclusão:** rejeitada como causa de navegação; tratada separadamente como observabilidade/encoding.

## Invariant final

Nenhum caminho pode executar duas ações consecutivas sem observar a posição global entre elas:

```text
AÇÃO
→ observar N/TOTAL
→ SUCCESS / SKIP / REGRESSION / unchanged
→ somente se unchanged e policy permitir: próxima ação
```
