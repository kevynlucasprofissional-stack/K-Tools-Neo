# Changelog

## V4.2.6 — guia pinada e árvore de módulos/submódulos

- enumeração de abas do Chrome passa a ser passiva: `pages()` não instala mais observers de auth/rede em todas as páginas abertas;
- somente a guia escolhida como work page recebe os observers do XCursos Runner;
- `BrowserSession` passa a obter o CDP Target ID e o `PageController` mantém a identidade da guia de trabalho por target, independentemente da guia/janela que estiver em primeiro plano;
- recovery prefere o target pinado; múltiplas abas com a mesma URL sem identidade recuperável geram `PAGE_RECOVERY_AMBIGUOUS` em vez de escolha arbitrária;
- recovery nunca reutiliza uma aba alheia apenas por estar disponível: somente `about:blank` pode ser reaproveitada, caso contrário uma nova página é criada;
- Chrome dedicado passa a usar `--disable-background-timer-throttling`, `--disable-renderer-backgrounding` e `--disable-backgrounding-occluded-windows` para reduzir desaceleração quando o usuário trabalha em outra guia/janela;
- a metadata de aula passa a carregar `modulePath[]`, preservando hierarquias com profundidade arbitrária e mantendo `moduleName` como leaf compatível;
- inspeção live identifica a aula ativa na sidebar visível e sobe pelos grupos ancestrais de aulas/arquivos para formar a árvore externa → interna;
- downloader espelha a hierarquia no disco como `curso / módulo / submódulo / ... / aula`;
- `modulePath` é persistido em in-flight state e manifesto;
- registros antigos sem `modulePath` continuam válidos por fallback para `moduleName`;
- arquivos antigos não são movidos automaticamente e reparos preservam o caminho de saída já conhecido;
- árvores profundas/títulos longos ganham redução determinística por segmento para respeitar o limite seguro de caminho no Windows;
- regressões V4.2.6 cobrem isolamento de observers, Target ID pinning, flags de background, árvore de três níveis, persistência no manifesto e path guard;
- validação pré-release no GitHub Actions: 273 testes, 271 PASS, 0 FAIL e 2 SKIPPED por ausência de ffmpeg/ffprobe reais no runner Linux;
- nenhuma mudança adiciona bypass de DRM, Cloudflare ou CAPTCHA.

## V4.2.5 — media readiness e recuperação de integridade

- corrige o bug live em que um iframe do Google Tag Manager podia ser promovido a mídia da aula quando o `<video>` ainda não tinha `src` pronto;
- adiciona política semântica para iframe: analytics/tracking são recusados e somente hosts de players reconhecidos podem ser `EXTERNAL_IFRAME`;
- adiciona `mediaSourceConfidence` com `PROVEN`, `SUPPORTED_IFRAME` e `UNTRUSTED`;
- adiciona barreira pré-download: mídia não comprovada nunca é enviada ao yt-dlp;
- adiciona espera limitada de media readiness após navegação/refresh e status transitório `MEDIA_NOT_READY`;
- `YTDLP_FAILED` genérico em direct signed MP4 ganha refresh limitado da mesma aula, mantendo validação de posição/curso/TOTAL e identidade do objeto;
- `VERIFY_FAILED` passa a preservar o código concreto do ffprobe, como `VERIFY_NO_VIDEO_STREAM`;
- arquivo rejeitado pelo ffprobe é isolado e, para signed direct MP4, pode disparar refresh + clean redownload;
- clean redownload usa `--no-continue` e remove somente `.part/.ytdl/.temp` que pertencem à saída da posição atual;
- checkpoint `BLOCKED` de uma execução anterior volta como `READY` com novo orçamento de tentativas, sem apagar manifesto ou arquivos válidos;
- `xcursos-all` detecta `NO_PROGRESS` por cobertura real (`downloaded`, `processed`, `missingPositions`), não por mudanças cosméticas entre `VERIFY_FAILED` e `YTDLP_FAILED`;
- adiciona regressões específicas para GTM, múltiplos trackers, player atrasado, mídia untrusted, refresh de `YTDLP_FAILED`, recovery de ffprobe e retry epoch;
- validação pré-release no GitHub Actions: 264 testes, 262 PASS, 0 FAIL e 2 SKIPPED por ausência de ffmpeg/ffprobe no runner Linux;
- nenhuma mudança adiciona bypass de DRM ou Cloudflare.

## 4.2.1 — estabilização de navegação “Próxima”

- adiciona `ActionabilityProbe` com `trial:true`, estabilidade por frames, hit-test do centro, animations/transitions e diagnóstico sanitizado;
- traduz `TimeoutError` de `locator.click()` na fronteira de Próxima para `NEXT_ACTIONABILITY_TIMEOUT`; timeout Playwright fora dessa fronteira continua sem retry semântico automático;
- adiciona `PageController.navigateNext()` para manter ação → observação N/TOTAL → decisão na mesma fronteira;
- após timeout de actionability, observa a posição antes de qualquer fallback; se N já virou N+1, não envia novo click;
- adiciona fallback único `locator.dispatchEvent('click')`, somente depois de confirmar que a posição continuou N, e valida obrigatoriamente N→N+1;
- bloqueia `dispatchEvent` quando o botão está explicitamente `disabled`/`aria-disabled`;
- `POSITION_SKIP` e `POSITION_REGRESSION` continuam fatais e nunca são mascarados;
- se `dispatchEvent` ou click normal perderem a Page depois da ação, recovery + observação acontecem antes de qualquer nova ação;
- `NEXT_TRANSITION_FAILED` é estrutural e não é repetido pelo retry de navegação externo;
- neutralização de animation/transition é temporária, reversível e só permanece durante a ação se o segundo probe demonstrar melhora;
- endurece UTF-8 no wrapper PowerShell sem deixar de manter os `.ps1` ASCII-only; stdout JSON e stderr de progresso permanecem separados;
- não adiciona `force:true` nem terceiro fallback via CDP/`Runtime.evaluate`: os testes sistêmicos não demonstraram necessidade.

## 4.2.0

- separa `BrowserSession` de `PageController`;
- adiciona saúde de Page e recovery de target/CDP;
- adiciona `NetworkMediaObserver` com prioridade sobre DOM/HTML e cleanup de listeners;
- adiciona `LessonScheduler` com READY/IN_FLIGHT/RETRY_LATER/DONE/BLOCKED;
- adiciona `DurableSchedulerCheckpoint` com escrita temp + fsync + rename e quarentena de JSON corrompido;
- adiciona `RetryPolicy` central com classificação, prioridade e exponential backoff/jitter;
- remove retry genérico `sleep(500)` do loop de download;
- adiciona graceful Ctrl+C e force AbortSignal para yt-dlp/ffprobe;
- adiciona `RuntimeStats`, ETA e progresso yt-dlp para stderr;
- adiciona `AutoThrottle` adaptativo;
- adiciona `safePageContent`;
- adiciona `AdaptiveLocator` conservador para Próxima;
- adiciona snapshots de debug sanitizados e rotacionados;
- adiciona observer de redirects/auth/Cloudflare;
- reforça redaction de Authorization, Cookie, token, apiKey e credentials;
- proíbe novos commits de `DOWNLOAD_FAILED`, `VERIFY_FAILED` e `MEDIA_NOT_FOUND` como progresso;
- corrige cleanup de listeners em Chrome externo persistente;
- corrige stats em resume para começar no número real já validado;
- mantém Chrome humano + CDP, yt-dlp, ffprobe e manifesto existente da V4.1.x.

### Bugs encontrados durante o desenvolvimento

- scheduler `end=null` era coercido para `0`, produzindo fila vazia;
- `NetworkMediaObserver.clear()` trocava o array e o listener continuava escrevendo no array antigo;
- abort de subprocesso podia resolver por `close` antes de rejeitar `PROCESS_ABORTED`;
- retry de `POSITION_STUCK` permitiu tentar posição 3 sem provar posição 2; reclassificado como estrutural após recovery limitado;
- force stop deixava job em RETRY_LATER em vez de READY imediato;
- listeners network/auth poderiam permanecer em páginas do Chrome após desconectar;
- `RuntimeStats` não refletia manifesto existente ao retomar;
- `download-all.ps1` usava `2>&1`, incompatível com progresso stderr + JSON stdout; removido;
- sanitizer de objetos não cobria a chave genérica `token`; corrigido.

## 4.2.2 — reposicionamento seguro e RuntimeStats

- `ensurePageAt()` usa a pagina atual quando ela esta exatamente em `target - 1`, desde que a posicao anterior esteja terminal e sem reparo.
- quando a URL imediatamente anterior nao existe, o runner procura o checkpoint conhecido mais proximo e caminha somente por posicoes ja concluidas, validando cada `N -> N+1`.
- na ausencia de qualquer checkpoint, a pagina atual pode caminhar ate o alvo apenas quando todas as posicoes atravessadas ja estao terminalmente concluidas; qualquer lacuna bloqueia a caminhada.
- novo `_xcursos-runner/lesson-navigation-index.json`: indice duravel `posicao -> URL estavel da aula`, aprendido a cada pagina confirmada e migrado a partir do manifesto antigo.
- indice de navegacao corrompido e colocado em quarentena e reconstruido sem substituir o manifesto como fonte de verdade.
- `RuntimeStats` separa cobertura unica (`coverageProcessed`) de operacoes da sessao (`runOperations`). Reprocessar uma posicao ja coberta nao aumenta cobertura nem ETA.
- ETA passa a usar somente amostras de novas posicoes cobertas nesta execucao, nunca o baseline seedado do resume.
- regressao live adicionada para o caso real: manifesto 1..64, Chrome na 1, `range 64..70`, sem sidebar e sem redownload de 1..64.

## V4.2.3

- Added pure `NavigationPlanner`.
- Separated navigation safety from download health/repair state.
- Reworked forward walk to navigation-only N→N+1 proof.
- Upgraded `lesson-navigation-index.json` to V2 with V1 migration and course anchor.
- Added stale navigation entry invalidation.
- Removed `goToPosition()` from runner reposition fallback.
- Added `POSITION_REPOSITION_NO_SAFE_PATH` diagnostics.
- Stopped masking auth/Cloudflare/course/TOTAL failures during reposition.
- Added `xcursos diagnose-reposition --target N --json`.
- Added `xcursos version`; doctor exposes runner version/install paths.
- Added `lastContiguousCommittedPosition` while preserving legacy `lastCommittedPosition`.
- Added `RuntimeStats.repositionSteps`.
- `login`/`probe` observations now enrich navigation index without manifest commit.
- Added 90-position systemic reposition regression.

## V4.2.4

- NetworkMediaObserver isolado por lesson generation.
- Correlação segura entre network candidate e `video.currentSrc/src` por objeto de mídia sem query.
- DOM atual vence candidato de rede não correlacionado.
- Diagnostics de mídia por fingerprints, sem signed URLs.
- Fixture sanitizada da aula live 108 (`108 / 198`, `e_Aula`, DIRECT_MP4 R2).
- yt-dlp failure classification: HTTP_403/404/429/5XX, NETWORK_RESET/TIMEOUT, DNS, TLS e genérico.
- `diagnosticTail` sanitizado em `errors.jsonl` e logs.
- Refresh limitado para falhas transitórias de direct signed MP4.
- Refresh recusa troca de objeto com `MEDIA_REFRESH_OBJECT_CHANGED`.
- `failureSummary` por causa e posições; falhas resolvidas são removidas do resumo.
- `download-all.ps1` interrompe repetição sem progresso e exibe causas agregadas.
- Contador temporariamente ilegível antes de Próxima usa `POSITION_UNOBSERVABLE`, não regressão falsa.
