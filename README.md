# XCursos Runner

Downloader determinístico para cursos XCursos aos quais o usuário já possui acesso. O Chrome pertence ao usuário; Cloudflare/login são humanos; o runner só se conecta depois via Playwright CDP.

## Versão atual

**V4.2.6**

O projeto está versionado diretamente na raiz do repositório:

- `src/` — código-fonte
- `tests/` — suíte de regressão
- `test-fixtures/` — fixtures sanitizadas e HTML de teste

## Qualidade

Na validação pré-release da V4.2.6, `npm run check` ficou verde e a suíte registrou **273 testes: 271 PASS, 0 FAIL, 2 SKIPPED**. Os 2 skips são integrações que exigem ffmpeg/ffprobe reais no runner Linux do GitHub Actions.

O workflow em `.github/workflows/ci.yml` executa syntax check e suíte completa em pushes e pull requests para `main`.

## Fluxo de desenvolvimento

Mudanças devem seguir:

1. branch de trabalho;
2. teste RED que reproduz o problema;
3. implementação mínima;
4. GREEN + regressão completa;
5. pull request para `main`;
6. nova versão/tag após estabilização.

## Arquitetura

```text
Usuario
  -> CLI xcursos / xcursos-all
  -> XCursosCourseRunner
  -> BrowserSession (CDP + Target ID)
  -> PageController (guia de trabalho pinada + semantica XCursos)
  -> NetworkMediaObserver + DOM/HTML comprovados
  -> media readiness / source confidence
  -> LessonScheduler + DurableSchedulerCheckpoint + RetryPolicy
  -> modulePath[] -> arvore de pastas
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

Extraia o release e rode no Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Abra um terminal novo e confira:

```powershell
xcursos version
xcursos doctor
```

A atualização preserva `%LOCALAPPDATA%\XCursosRunner\chrome-profile`, configuração, manifesto e vídeos já baixados.

Na V4.2.6, reinicie a janela/processo do **Chrome dedicado do XCursos** após instalar para que as novas flags contra throttling em background entrem em vigor. Não é necessário apagar o perfil.

## Autenticação humana

```powershell
xcursos login
```

1. o runner abre/reutiliza Google Chrome com perfil dedicado;
2. Playwright ainda não está conectado;
3. faça Cloudflare/login manualmente;
4. abra uma videoaula;
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
CDP/reconnect ficou separado de título, posição, Próxima e mídia. Page refs possuem saúde `HEALTHY / STALE / RECOVERING / DEAD`. Na V4.2.6, enumerar abas é passivo e somente a guia de trabalho pinada recebe os observers do runner.

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
- falhas retryable não viram novo commit de progresso;
- DRM não é contornado;
- materiais não são vídeo;
- URLs assinadas, Authorization e Cookie não são persistidos em claro;
- sidebar index não é usado como posição global;
- navegação nunca cria commit.

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
  lesson-navigation-index.json
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

## V4.2.2 — reposicionamento seguro

A V4.2.2 introduziu índice durável de navegação e caminhada confirmada `N -> N+1`. A V4.2.3 completou essa arquitetura removendo o fallback arbitrário pela sidebar: `goToPosition()` permanece apenas como guard explícito que recusa indexação não comprovada.

Cada página confirmada alimenta:

```text
<Curso>\_xcursos-runner\lesson-navigation-index.json
```

Esse arquivo não substitui `manifest.jsonl`; ele serve somente para reposicionamento determinístico e é reconstruível.

`RuntimeStats` diferencia:

```text
coverageProcessed = posições únicas cobertas
runOperations      = operações executadas nesta sessão
```

## V4.2.3 — Reposition Engine

Reposicionamento é planejado por `NavigationPlanner` e independente da saúde do download. `repairPositions` e gaps no manifesto podem ser atravessados sem commit. O índice V2 mantém `courseAnchor`, invalida entradas stale e aprende posições observadas. Novos comandos: `xcursos version` e `xcursos diagnose-reposition --target N --json`.

## V4.2.4 — isolamento e diagnóstico de mídia

- respostas de vídeo isoladas por aula/generation;
- resposta antiga de outra aula não ganha do `video.src` atual;
- URL assinada nova só substitui DOM antigo para o mesmo objeto de mídia;
- `probe --json` mostra fingerprints sanitizados;
- `errors.jsonl` registra causa do yt-dlp e tail sanitizado;
- falhas transitórias de MP4 assinado podem renovar mídia da mesma aula;
- refresh recusa troca silenciosa de objeto;
- `failureSummary` agrega causas e posições.

## V4.2.5 — media readiness e recuperação de arquivos inválidos

A V4.2.5 nasce do diagnóstico live das posições 108 e 113–123:

- iframe genérico deixou de ser candidato automático de mídia;
- Google Tag Manager, analytics/tracking e hosts equivalentes são recusados como vídeo;
- iframe só é aceito quando pertence a player reconhecido;
- cada candidato recebe confiança `PROVEN`, `SUPPORTED_IFRAME` ou `UNTRUSTED`;
- o runner aguarda por uma janela limitada o MP4/HLS/DASH comprovado aparecer após navegação;
- estado transitório de player vira `MEDIA_NOT_READY`, não download de iframe irrelevante;
- mídia `UNTRUSTED` nunca chega ao yt-dlp;
- `YTDLP_FAILED` genérico em direct signed MP4 pode receber um refresh seguro da mesma aula;
- `VERIFY_FAILED` preserva o código concreto do ffprobe e, em signed direct MP4, pode fazer refresh + redownload limpo;
- redownload de recuperação usa `--no-continue` e remove somente artefatos parciais correspondentes à posição atual;
- checkpoint `BLOCKED` de execução anterior ganha um novo orçamento de retry sem apagar estado/manifesto;
- `xcursos-all` mede `NO_PROGRESS` por cobertura real (`downloaded + processed + missingPositions`), não pela oscilação do rótulo da falha.

## V4.2.6 — guia de trabalho pinada e árvore real de módulos

A V4.2.6 endurece duas áreas de uso cotidiano:

- `pages()` não instala mais observers em todas as abas do Chrome;
- a aula de trabalho é pinada pela identidade do target CDP quando disponível;
- recovery não depende da aba visualmente ativa e não escolhe arbitrariamente outra aba com a mesma URL;
- o Chrome dedicado é iniciado com flags que reduzem throttling de renderer/timers quando a janela ou guia fica em background;
- o pin é lógico: o runner não precisa forçar `bringToFront()`, então outras abas/janelas podem permanecer em primeiro plano;
- a metadata passa a transportar `modulePath[]` com profundidade arbitrária;
- a inspeção live extrai a ancestralidade da aula ativa na sidebar visível;
- o downloader espelha `curso / módulo / submódulo / ... / aula` no disco;
- `modulePath` é persistido no checkpoint/manifesto, mantendo `moduleName` como folha compatível;
- registros e arquivos antigos não são movidos automaticamente;
- reparo de arquivo já conhecido preserva o caminho original;
- árvores longas recebem sanitização e redução determinística para respeitar o limite seguro de caminho do Windows.

Nenhuma mudança adiciona bypass de DRM ou Cloudflare.
