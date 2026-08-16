# XCursos Runner V4.2.4 — Test Results

## Baseline

V4.2.3 intacta antes de qualquer alteração:

- `npm run check`: PASS
- `npm test`: 234/234 PASS
- FAIL: 0

## Método RED → GREEN

### Lesson-scoped media generation

Observação: `NetworkMediaObserver` era por Page e `best()` podia selecionar resposta antiga.

RED: resposta 107.mp4 observada, nova aula 108 iniciada, `best()` ainda via 107.

Correção: `beginGeneration()`, candidates/best filtrados pela generation corrente; `navigateExact`, `navigateNext` e refresh abrem nova generation.

GREEN: resposta da 107 deixa de ser elegível para a 108.

### Correlação network × DOM

Observação: rede tinha prioridade absoluta sobre `video.currentSrc/src`.

RED: DOM aponta 108.mp4 e rede antiga aponta 107.mp4.

Correção: correlação por `hostname + pathname`, query ignorada. Rede só substitui DOM HTTP quando o objeto é o mesmo; mismatch usa DOM atual.

GREEN: 108 selecionada; 107 ignorada.

### Aula 108 real

Foi criada fixture sanitizada derivada do HTML live anexado. Valida 108/198, módulo `5. Vídeo de vendas - VSL`, título `e_Aula`, DIRECT_MP4 R2 assinado, materiais presentes e DRM false.

### yt-dlp diagnostics

RED: 403/network reset retornavam apenas `EXPIRED`/`FAILED` sem causa persistível.

Correção: `failureCode` e `diagnosticTail` sanitizado.

GREEN: HTTP_403 e NETWORK_RESET classificados; signed query não aparece no diagnóstico.

### Signed media refresh

RED: NETWORK_RESET em direct signed MP4 não renovava a mídia antes de devolver falha ao scheduler.

Correção: refresh limitado para 403/429/5xx/network reset/timeout/DNS/TLS/process timeout; posição e objeto de vídeo são revalidados.

GREEN: falha transitória pode ser resolvida no mesmo `processPosition`; objeto diferente é recusado com MEDIA_REFRESH_OBJECT_CHANGED.

### failureSummary

RED: `downloadCourse` BLOCKED não expunha causa agregada; causa antiga permanecia mesmo se a posição fosse resolvida depois.

Correção: resumo por code/count/positions e remoção da posição quando a tentativa posterior termina saudável.

GREEN: somente falhas realmente pendentes permanecem no resumo.

### xcursos-all no-progress

RED: wrapper não tinha detecção de passadas idênticas.

Correção: `NoProgressLimit` (default 3), fingerprint de downloaded+missing+causes e saída `NO_PROGRESS`.

GREEN: script contém proteção sem misturar stderr no JSON.

### Counter temporarily unreadable

RED: `current=null` antes de Próxima virava POSITION_REGRESSION.

Correção: reinspeção curta e `POSITION_UNOBSERVABLE` transient quando o contador continua ilegível.

GREEN: null transitório recupera sem click duplo; null persistente não é regressão falsa.

## Regressão intermediária

Após as mudanças funcionais e antes do bump de release:

- `npm run check`: PASS
- `npm test`: 250/250 PASS

## Final

Após correção da telemetria stale e atualização de release:

- `npm run check`: PASS
- `npm test`: 251/251 PASS
- FAIL: 0
- skipped: 0
- cancelled: 0

## Invariants preservados

- N/TOTAL continua fonte principal de posição.
- Action → observation → decision na Próxima permanece.
- N→N+2 e N→N-1 não são aceitos silenciosamente.
- Navegação não cria commit.
- Signed URL completa não é persistida.
- Materiais não são mídia.
- DRM não é contornado.
