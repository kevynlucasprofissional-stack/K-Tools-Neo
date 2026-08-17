# XCursos Runner

Downloader determinístico para cursos XCursos aos quais o usuário já possui acesso. O Chrome pertence ao usuário; Cloudflare, CAPTCHA e login continuam humanos; o runner só se conecta ao Chrome dedicado depois, via Playwright CDP.

## Versão atual

**V4.3.0**

A V4.3.0 consolida a evolução realizada depois da V4.2.6: download nativo do XCursos via CDP, melhorias de performance e resiliência para execuções longas e um sistema de diagnóstico completo, autocontido e validado também no Windows.

Não há breaking change intencional em relação à linha 4.x. Estado, manifesto, checkpoint, vídeos já baixados e perfil dedicado do Chrome continuam compatíveis.

## Estado de qualidade

A validação final da base que originou a V4.3.0 foi executada em **Ubuntu e Windows**.

- **389 testes por lane**;
- Ubuntu: **387 PASS, 0 FAIL, 2 SKIPPED** — os skips dependem de ffmpeg/ffprobe reais ausentes naquele runner;
- Windows: **389 PASS, 0 FAIL**;
- syntax check: PASS nos dois sistemas;
- Windows PowerShell 5.1 smoke: PASS;
- `diagnostics-check`: PASS;
- validação de caminhos com espaços e caracteres portugueses: PASS;
- geração e correlação de report/events/metadata/liveness: PASS.

O workflow em `.github/workflows/ci.yml` executa syntax check e a suíte completa em Ubuntu e Windows para pushes e pull requests em `main`.

## O que a V4.3.0 consolida

### 1. Download nativo do XCursos primeiro

Quando a aula expõe o endpoint nativo confiável de download, o runner prefere esse caminho antes do yt-dlp.

Fluxo normal:

```text
botão nativo XCursos
  -> Browser.setDownloadBehavior via CDP
  -> staging isolado por GUID
  -> conclusão confirmada
  -> ffprobe
  -> rename para o nome final determinístico
  -> manifesto/commit
```

No caminho CDP normal, o arquivo não precisa ficar duplicado em `Downloads` do Windows. `download.path()` é fallback; `saveAs()` é último recurso. Se o download nativo não estiver disponível ou falhar e houver uma URL de mídia segura, o yt-dlp continua como fallback.

`validation.downloadMethod` registra `XCURSOS_NATIVE` ou `YTDLP`.

### 2. Performance sem enfraquecer validação

- cache curto de inspeção para metadata já comprovadamente baixável;
- estados sem mídia pronta nunca entram no cache;
- `AutoThrottle` reage a instabilidade real, não à duração normal de um download longo;
- validação ffprobe do download nativo pode ser reaproveitada uma única vez imediatamente após a promoção do arquivo;
- resume pode reutilizar validação persistida somente quando o fingerprint `size + mtimeMs` continua idêntico;
- arquivo alterado força nova validação;
- `audit` explícito continua executando validação completa.

### 3. Recuperação de rede e retry observável

Erros transitórios de navegação, incluindo `net::ERR_NETWORK_ACCESS_DENIED`, podem receber recuperação limitada de CDP/page e nova tentativa.

Erros permanentes e `net::ERR_*` desconhecidos não entram em retry cego.

O log de retry informa causa concreta, posição, orçamento e atraso, por exemplo:

```text
[RETRY] 80/144 | NAV_NETWORK_ERROR | ERR_NETWORK_ACCESS_DENIED | tentativa 2/3 | retry em 500ms
```

### 4. Fast-path para páginas somente de materiais

A classificação é estrutural, não baseada no título da aula. Uma página comprovadamente composta apenas por materiais pode avançar sem esperar inutilmente por media readiness.

Páginas com vídeo, botão nativo de vídeo ou iframe não reconhecido continuam no caminho conservador.

### 5. ETA robusto

O ETA só aparece depois de amostras suficientes e usa estimativa resistente a outliers. Retries e falhas não são contados como novas aulas concluídas e não inflacionam artificialmente a previsão.

### 6. Pacote de diagnóstico por execução

Cada comando relevante produz uma sessão diagnóstica em:

```text
<outputRoot>\_xcursos-diagnostics\<runId>\
  diagnostic-report.json
  diagnostic-report.md
  events.jsonl
  run-meta.json
  liveness.json
  emergency-crash.json      # somente quando necessário
```

`diagnostic-report.json` é o artefato principal para investigação e compartilhamento. Ele inclui uma timeline estruturada e bounded com as evidências mais relevantes sem exigir, na maioria dos casos, o envio imediato de todos os arquivos brutos.

O relatório correlaciona, quando disponíveis:

- versão/build/commit do XCursos Runner;
- comando e configuração efetiva;
- curso, módulo, aula e posição;
- fases e decisões;
- navegação e confiança/ambiguidade;
- retries e causas;
- subprocessos, PID, duração, exit code, timeout/abort;
- método de download;
- arquivo produzido;
- validação ffprobe;
- commit/manifesto/checkpoint;
- erros persistidos;
- findings derivados das evidências;
- liveness e último progresso real;
- falhas do próprio sistema de diagnóstico.

O diagnóstico não tenta inventar causa-raiz. Ele preserva evidências para que a causa possa ser investigada posteriormente.

### 7. Observabilidade fail-soft

A persistência foi separada em dois domínios:

**Persistência funcional — fail-hard**

- `state.json`;
- `manifest.jsonl`;
- scheduler checkpoint;
- dados necessários para integridade/resume.

Falhas nesses arquivos não são silenciosamente engolidas.

**Persistência diagnóstica — fail-soft**

- `runner.log`;
- `events.jsonl`;
- relatórios;
- liveness;
- artefatos auxiliares de observabilidade.

Falhas como `ENOSPC`, `EACCES`, arquivo bloqueado ou diretório inacessível tentam fallback e não devem transformar o próprio diagnóstico na causa principal de uma execução que estaria saudável.

### 8. Consistência entre report, events e metadata

A finalização grava o evento terminal antes de calcular o relatório. Depois de uma execução encerrada normalmente:

```text
report.eventSummary.count
==
quantidade física de eventos em events.jsonl
```

`run-meta.json`, o relatório e o evento terminal convergem para o contexto efetivo da execução, inclusive alterações de output, curso, resume e CDP ocorridas depois do bootstrap.

### 9. Identidade exata da build

O diagnóstico registra:

- `packageVersion`;
- `runnerVersion`;
- commit SHA quando comprovável;
- branch/build identifier quando confiável;
- `cliPath`;
- `installRoot`;
- Node;
- plataforma/arquitetura no contexto de ambiente.

Quando a instalação não possui identidade Git confiável, nenhum SHA é inventado. O relatório usa fallback explícito como `PACKAGE_VERSION_ONLY`.

### 10. Snapshot seguro da configuração efetiva

O relatório preserva os parâmetros seguros que realmente influenciaram aquela execução — retries, timeouts, media readiness, download, navigation, throttle, scheduler, CDP, resume e limites — permitindo comparar duas execuções com configurações diferentes.

Cookies, Authorization, tokens, API keys, credenciais, URLs assinadas e dados de sessão não entram nesse snapshot.

### 11. Recuperação de runs interrompidos

Uma queda de energia, `taskkill /F`, crash nativo ou reinício da máquina pode impedir `finalize()` de rodar. O XCursos Runner não promete capturar o impossível no instante da queda; em vez disso, a próxima execução procura runs anteriores sem finalização válida.

Quando o processo anterior está realmente órfão, o sistema pode reconstruí-lo como `INTERRUPTED`, usando o que já havia sido persistido:

- último evento conhecido;
- última posição;
- último subprocesso;
- metadata;
- timeline;
- manifesto/checkpoint existentes.

PID e host são considerados para não confundir uma execução ainda ativa com uma execução abandonada.

### 12. Liveness e possível travamento silencioso

Um heartbeat leve acompanha:

- PID;
- etapa;
- posição;
- operação atual;
- último progresso real;
- duração sem progresso;
- memória do processo;
- event-loop delay;
- subprocesso ativo;
- retry/backoff ou espera deliberada.

O diagnóstico diferencia, entre outros:

- `POSSIBLE_STALL` — ausência de progresso não explicada;
- `ACTIVE_LONG_OPERATION` — operação longa legítima, como subprocesso/download ainda ativo;
- `EXPECTED_WAIT` — espera deliberada, como backoff.

### 13. Self-test do diagnóstico

Execute sem Chrome e sem credenciais:

```powershell
xcursos diagnostics-check --json
```

O comando cria uma sessão controlada e não destrutiva, testa evento, contexto, sanitização, erro simulado, subprocesso Node, JSON, Markdown, timeline, metadata, liveness, identidade e consistência interna.

Resultado saudável:

```text
diagnosticsHealthy: true
```

### 14. Privacidade de paths

O software continua conhecendo os caminhos reais necessários à operação local, mas o relatório compartilhável anonimiza a home do usuário:

```text
C:\Users\Nome\Downloads\Cursos
```

vira, quando apropriado:

```text
$HOME\Downloads\Cursos
```

`run-meta.json` e `events.jsonl` são artefatos locais e podem preservar caminhos operacionais reais. Para compartilhar uma investigação, comece por `diagnostic-report.json`.

### 15. Retenção e rotação

Artefatos de diagnóstico não crescem indefinidamente. A limpeza é conservadora e considera idade, quantidade e tamanho total.

Prioridades:

- preservar runs recentes;
- preservar falhas/crashes por mais tempo que sucessos equivalentes;
- nunca remover run detectado como ativo;
- limitar limpeza a artefatos diagnósticos reconhecidos;
- transcripts PowerShell só entram quando seguem `xcursos-all-*.log`;
- arquivos do curso nunca são candidatos.

Falha de cleanup é fail-soft.

### 16. Windows CI e PowerShell 5.1

A CI mantém Linux e adiciona um lane Windows real. No Windows são verificados:

- Node;
- paths Windows;
- filesystem;
- UTF-8;
- nomes com espaços e caracteres portugueses;
- Windows PowerShell 5.1;
- `download-all.ps1`;
- `%LOCALAPPDATA%`;
- transcript;
- `diagnostics-check`;
- subprocessos;
- sanitização de `$HOME`;
- JSON/Markdown/events/metadata/liveness.

A CI não autentica no XCursos. O smoke com sessão real continua sendo uma etapa local.

## Arquitetura atual

```text
Usuário
  -> CLI xcursos / xcursos-all
  -> diagnostics lifecycle + liveness
  -> XCursosCourseRunner
  -> LessonScheduler + DurableSchedulerCheckpoint + RetryPolicy
  -> BrowserSession (CDP + Target ID)
  -> PageController (guia pinada + semântica XCursos)
  -> NetworkMediaObserver + DOM/HTML comprovados
  -> media readiness / source confidence
  -> modulePath[] -> árvore de pastas
  -> download nativo XCursos via CDP
       -> fallback download.path()/saveAs quando necessário
       -> fallback yt-dlp quando existe mídia segura
  -> ffprobe
  -> manifest/state/audit
  -> diagnostic-report + events + metadata + liveness
```

Não usa LLM para decidir navegação. Também não depende de OpenCode, BrowserClaw ou MCP para o fluxo principal.

Não existe bypass automático de DRM, Cloudflare ou CAPTCHA.

## Requisitos

- Windows 11 para o ambiente principal de produção;
- Node.js 22.x, 24.x ou 26.x — 24 LTS recomendado;
- Google Chrome Stable;
- `yt-dlp` no PATH ou `YTDLP_PATH`;
- `ffprobe` no PATH ou `FFPROBE_PATH`.

A suíte também é validada em Ubuntu para regressão e portabilidade do núcleo Node.

## Instalação / atualização

No Windows PowerShell, dentro da cópia mais recente do projeto:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Depois abra um terminal novo e confira:

```powershell
xcursos version
xcursos diagnostics-check --json
xcursos doctor
```

A atualização preserva `%LOCALAPPDATA%\XCursosRunner\chrome-profile`, configuração, manifesto e vídeos já baixados.

## Autenticação humana

```powershell
xcursos login
```

1. o runner abre/reutiliza o Google Chrome com perfil dedicado;
2. Playwright ainda não está conectado;
3. faça Cloudflare/login manualmente;
4. abra uma videoaula;
5. pressione ENTER no terminal;
6. só então Playwright conecta via CDP.

## Comandos principais

```powershell
xcursos browser
xcursos login
xcursos probe --json
xcursos current --json
xcursos range --start 1 --end 5 --json
xcursos download --json
xcursos status
xcursos audit --json
xcursos diagnostics-check --json
xcursos doctor
xcursos version
xcursos diagnose-reposition --target 65 --json
```

Configuração:

```powershell
xcursos config --output "D:\Cursos"
xcursos config --chrome "C:\caminho\chrome.exe"
xcursos config --port 9222
```

Para retomar/baixar tudo com passes externos adicionais:

```powershell
xcursos-all
```

`xcursos-all` não apaga estado nem repete posições já validadas e cria transcript próprio em `%LOCALAPPDATA%\XCursosRunner\logs`.

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

Os diagnósticos globais da execução ficam separados em:

```text
<outputRoot>\_xcursos-diagnostics\<runId>\
```

## Invariantes preservados

- posição global `N / TOTAL` continua sendo a fonte principal de progresso;
- nenhum salto `N -> N+2` é aceito silenciosamente;
- commit durável acontece antes de Próxima;
- uma posição concluída não é baixada novamente;
- falhas retryable não viram novo commit de progresso;
- DRM não é contornado;
- Cloudflare/CAPTCHA continuam humanos;
- materiais nunca são tratados como vídeo;
- mídia `UNTRUSTED` nunca chega ao downloader;
- URLs assinadas, Authorization, Cookie e tokens não são persistidos em claro;
- sidebar index não é usado como posição global;
- navegação nunca cria commit;
- auditoria explícita continua usando validação real;
- falha diagnóstica não pode mascarar falha funcional;
- manifesto/state/checkpoint continuam sendo persistência funcional fail-hard.

## Smoke test operacional no Windows

Depois de instalar a versão mais recente:

```powershell
xcursos diagnostics-check --json
xcursos doctor
xcursos login
xcursos probe --json
xcursos current --json
```

Quando for apropriado executar curso completo:

```powershell
xcursos-all
```

O procedimento detalhado está em `docs/diagnostics-smoke-test-windows.md`.

Para reavaliar uma execução problemática, envie primeiro apenas:

```text
diagnostic-report.json
```

Se a timeline bounded não for suficiente, envie também `events.jsonl`, `run-meta.json`, `liveness.json` e o transcript correspondente do PowerShell.

## Desenvolvimento

Mudanças devem seguir:

1. branch de trabalho;
2. teste RED/reprodução quando houver mudança funcional ou bug;
3. implementação mínima;
4. testes direcionados;
5. `npm run check`;
6. suíte completa;
7. validação Ubuntu + Windows quando aplicável;
8. revisão do diff;
9. pull request para `main`.

Comandos locais:

```powershell
npm run check
npm test
```

A suíte automatizada não requer acesso à conta XCursos. Testes autenticados/live devem seguir `LIVE-TESTS.md` e o smoke Windows documentado.

## Histórico

A história detalhada das versões V4.2.0–V4.2.6 e das mudanças consolidadas na V4.3.0 está em `CHANGELOG.md`.
