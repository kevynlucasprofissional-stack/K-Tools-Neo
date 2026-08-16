# XCursos Runner V4.2.4

Downloader determinístico para cursos XCursos aos quais o usuário já possui acesso. O Chrome pertence ao usuário; Cloudflare/login são humanos; o runner só se conecta depois via Playwright CDP.

## Arquitetura

```text
Usuario
  -> CLI xcursos / xcursos-all
  -> XCursosCourseRunner
  -> BrowserSession (CDP)
  -> PageController (semantica XCursos)
  -> NetworkMediaObserver -> DOM/HTML fallback
  -> LessonScheduler + DurableSchedulerCheckpoint + RetryPolicy
  -> yt-dlp
  -> ffprobe
  -> manifest/state/audit
```

Não usa OpenCode, LLM, MCP, BrowserClaw, proxy rotation, CAPTCHA automático ou bypass de Cloudflare.

## Requisitos

- Windows 11
- Node.js 22.x, 24.x ou 26.x (24 LTS recomendado)
- Google Chrome Stable
- `yt-dlp` no PATH ou `YTDLP_PATH`
- `ffprobe` no PATH ou `FFPROBE_PATH`

## Instalação / atualização

Extraia o ZIP e rode no Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Abra um terminal novo e confira:

```powershell
xcursos doctor
```

A instalação por cima da V4.1.x preserva `%LOCALAPPDATA%\XCursosRunner\chrome-profile`, configuração, manifesto e vídeos já baixados.

## Autenticação humana

```powershell
xcursos login
```

1. o runner abre/reutiliza Google Chrome com perfil dedicado;
2. Playwright ainda não está conectado;
3. faça Cloudflare/login manualmente;
4. abra uma videoaula (para um curso novo completo, posição `1 / TOTAL`);
5. pressione ENTER no terminal;
6. só então Playwright conecta via CDP.

## Uso

```powershell
xcursos probe --json
xcursos current --json
xcursos range --start 1 --end 5 --json
xcursos download --json
```

Para retomar/baixar tudo com passes externos adicionais:

```powershell
xcursos-all
```

`xcursos-all` não apaga estado nem repete posições já validadas.

## O que há de novo na V4.2

### NetworkMediaObserver
Escuta requests/responses antes de navegação/reload e prioriza MP4/HLS/DASH HTTP(S) realmente requisitados pelo player. 403 é observado mas não é selecionado. `/api/materials/download` nunca é mídia. URLs assinadas ficam somente em memória e são redigidas quando persistidas.

### LessonScheduler + DurableSchedulerCheckpoint
Cada posição é um job `READY / IN_FLIGHT / RETRY_LATER / DONE / BLOCKED`. Manifesto é a verdade de DONE; checkpoint contém trabalho pendente/in-flight e é gravado com temp + fsync + rename. Job in-flight de processo morto volta a ser recuperável.

### RetryPolicy
Backoff exponencial com limite, jitter e penalidade de prioridade. Download/media temporariamente problemáticos voltam ao fim da fila; auth, DRM e erros estruturais de sequência não entram em retry cego.

### BrowserSession / PageController
CDP/reconnect ficou separado de título, posição, Próxima e mídia. Page refs possuem saúde `HEALTHY / STALE / RECOVERING / DEAD`. Listeners são removidos ao desconectar do Chrome externo.

### Graceful Ctrl+C
Primeiro Ctrl+C pede parada segura: não inicia nova aula, termina a etapa atômica, commita e salva checkpoint. Segundo Ctrl+C salva checkpoint e aborta subprocessos; a posição em andamento volta a ser recuperável.

### RuntimeStats + progresso
Progresso normal vai para stderr, inclusive percentual/velocidade do yt-dlp; `--json` mantém somente o JSON final em stdout. Estatísticas incluem progresso, retries, reconnects, bytes, tempo médio e ETA quando já existem amostras.

### safePageContent
Leitura do HTML tem retries pequenos para erros transitórios, mas page closed/auth são delegados à recuperação correta e não entram em loop.

### AdaptiveLocator
É somente fallback. Seletores determinísticos têm prioridade; o fallback exige score alto e ambiguidade baixa. Qualquer clique em Próxima continua sujeito à pós-condição obrigatória `N -> N+1`.

### Debug snapshots
Erros importantes podem criar `_xcursos-runner/debug/<posição>-<timestamp>/` com HTML, metadata, network, screenshot e erro sanitizados. Há rotação por quantidade, idade e tamanho. Falha ao criar snapshot nunca substitui o erro original.

### Redirect/Auth Observer
Distingue aula, login, home/curso e Cloudflare e preserva cadeia de redirects sanitizada. Cloudflare nunca é resolvido automaticamente.

### AutoThrottle
Ritmo aumenta sob 403/429/5xx/timeouts e cai gradualmente após sucessos, sempre entre limites finitos.

## Invariants preservados

- posição global `N / TOTAL` é a fonte principal de progresso;
- nenhum salto `N -> N+2` é aceito silenciosamente;
- commit durável acontece antes de Próxima;
- uma posição concluída não é baixada novamente;
- `DOWNLOAD_FAILED`, `VERIFY_FAILED` e `MEDIA_NOT_FOUND` não podem virar novo commit de progresso;
- DRM não é contornado;
- materiais não são vídeo;
- URLs assinadas, Authorization e Cookie não são persistidos em claro;
- sidebar index não é usado como posição global.

## Estado por curso

```text
<Curso>\_xcursos-runner\
  course.identity.json
  state.json
  manifest.jsonl
  errors.jsonl
  runner.log
  run.lock
  scheduler.checkpoint.json
  debug\
```

## Desenvolvimento

```powershell
npm run check
npm test
```

A suíte automatizada não requer seu XCursos real; o teste live deve seguir `LIVE-TESTS.md`.

## V4.2.1 — estabilização de Próxima

A V4.2.1 mantém toda a arquitetura V4.2 e substitui a navegação frágil por uma fronteira segura `navigateNext()`:

```text
posição N
→ ActionabilityProbe
→ uma ação
→ observar N/TOTAL
→ só então decidir fallback
```

Quando o click físico excede o timeout de actionability, o runner primeiro verifica se a posição já mudou. Somente se continuar em N e o botão não estiver explicitamente desabilitado é enviado um único `dispatchEvent('click')`; depois a posição é validada novamente. `N+2` e `N-1` continuam bloqueios estruturais.

Animations/transitions só são neutralizadas temporariamente quando o probe detecta instabilidade geométrica/motion e um segundo probe comprova melhora. O style é sempre removido no final.

Falhas de Próxima geram snapshot sanitizado com actionability, bounding boxes, hit-test, animations/transitions e estratégia utilizada.

No Windows PowerShell, o wrapper configura UTF-8 explicitamente para comunicação com o processo Node, mantendo os arquivos `.ps1` em ASCII para compatibilidade com PowerShell 5.1. JSON final continua em stdout; progresso continua em stderr.

Para validar especificamente o bug live depois da atualização, use o procedimento de `LIVE-TESTS.md`, especialmente o range 38→42.

## V4.2.2 — reposicionamento seguro

O runner nao depende mais de `goToPosition()` para retomar um range quando o Chrome esta longe da primeira posicao pendente.

A ordem de reposicionamento e:

```text
1. pagina atual ja e o alvo
2. pagina atual = alvo - 1 e a anterior esta concluida -> uma unica Proxima validada
3. URL exata conhecida no indice/manifesto
4. checkpoint conhecido mais proximo abaixo do alvo -> caminhada N -> N+1 validada
5. pagina atual -> caminhada somente se todas as posicoes atravessadas ja estao concluidas
6. somente depois disso o fallback legado goToPosition(), que continua recusando sidebar indexing nao comprovado
```

Cada pagina confirmada alimenta:

```text
<Curso>\_xcursos-runner\lesson-navigation-index.json
```

Esse arquivo nao substitui `manifest.jsonl`; ele serve somente para reposicionamento deterministico e e reconstruivel.

`RuntimeStats` agora diferencia:

```text
coverageProcessed = posicoes unicas cobertas
runOperations      = operacoes executadas nesta sessao
```

Assim, executar `xcursos current` sobre uma aula ja concluida nao cria progresso ficticio nem ETA de poucos segundos para centenas de aulas.


## V4.2.3 — Reposition Engine

Reposicionamento agora é planejado por `NavigationPlanner` e independente da saúde do download. `repairPositions` e gaps no manifesto podem ser atravessados sem commit. O índice V2 mantém `courseAnchor`, invalida entradas stale e aprende posições observadas. Novos comandos: `xcursos version` e `xcursos diagnose-reposition --target N --json`.

## V4.2.4 — estabilização das aulas restantes

A V4.2.4 endurece especificamente o pipeline de mídia observado nas aulas `e_Aula` restantes:

- respostas de vídeo são isoladas por aula/generation;
- uma resposta antiga de outra aula não pode ganhar do `video.src` atual;
- URLs assinadas novas podem substituir URLs DOM antigas somente para o mesmo objeto R2;
- `probe --json` mostra `mediaDiagnostics` com fingerprints seguros;
- `errors.jsonl` registra a causa do yt-dlp e um tail sanitizado;
- falhas 403/rede em MP4 assinado podem renovar a mídia por refresh da mesma aula;
- `xcursos-all` para após repetição comprovada sem progresso, em vez de desperdiçar passadas idênticas.
