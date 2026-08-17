# Smoke test de diagnóstico no Windows

Este procedimento separa a **Validação automatizada** da CI do **Smoke test operacional** que depende do Windows real, Chrome humano e uma sessão autenticada no XCursos.

## Validação automatizada

A CI executa a suíte completa em Ubuntu e Windows. A validação automatizada roda sem credenciais do XCursos e não tenta fazer login, contornar Cloudflare, CAPTCHA ou acessar conteúdo autenticado.

No Windows, o workflow confirma Windows PowerShell 5.1, executa `diagnostics-check` em um caminho com espaços e caracteres portugueses, valida JSON/Markdown/eventos/metadata/liveness, testa a criação de transcript em `%LOCALAPPDATA%\XCursosRunner\logs` e verifica que o relatório compartilhável não contém o segredo do self-test.

## Smoke test operacional

Use este fluxo depois de atualizar a cópia local para a `main` mais recente e reinstalar o CLI a partir dessa cópia.

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Abra um novo PowerShell e execute, nesta ordem:

```powershell
xcursos version
xcursos diagnostics-check --json
xcursos doctor
xcursos login
xcursos probe --json
xcursos current --json
```

O `xcursos diagnostics-check --json` deve retornar `diagnosticsHealthy: true` sem abrir o Chrome e sem exigir credenciais. O `doctor` deve comprovar as dependências reais da máquina. `login`, `probe` e `current` constituem o smoke autenticado e devem usar apenas o fluxo humano normal do XCursos.

Para validar também a orquestração PowerShell de curso completo, quando for apropriado executar downloads reais:

```powershell
.\download-all.ps1
```

O wrapper deve indicar o caminho do transcript, cujo nome segue o padrão `xcursos-all-<timestamp>-<PID>.log`, normalmente em `%LOCALAPPDATA%\XCursosRunner\logs`.

## O que verificar depois de `xcursos current --json`

Use o objeto `diagnostics` retornado pelo comando para localizar o run. Confirme a existência dos seguintes artefatos:

- `diagnostic-report.json` — artefato principal e compartilhável;
- `diagnostic-report.md` — versão legível;
- `events.jsonl` — timeline integral local;
- `run-meta.json` — metadata operacional da execução;
- `liveness.json` — último heartbeat/liveness persistido.

No `diagnostic-report.json`, confira:

- `runId` igual ao run indicado pelo resultado do comando;
- `codeIdentity` com a versão e a melhor identidade de código disponível;
- `effectiveConfig` coerente com a execução;
- `eventSummary.count` coerente com `events.jsonl`;
- timeline incorporada;
- posição/aula processada quando aplicável;
- método de download em `validation.downloadMethod` quando houve download;
- evidência de validação do arquivo por ffprobe;
- `liveness` final;
- ausência de cookies, Authorization, tokens, URLs assinadas e outros segredos;
- caminhos pessoais anonimizados como `$HOME` no relatório compartilhável.

## O que me encaminhar para reavaliação

Na maioria dos casos, envie primeiro apenas:

```text
diagnostic-report.json
```

Se eu precisar reconstruir detalhes que ficaram fora da timeline bounded, envie também o diretório do run contendo:

```text
diagnostic-report.md
events.jsonl
run-meta.json
liveness.json
```

Se a execução foi feita por `download-all.ps1`, inclua também o transcript `xcursos-all-<timestamp>-<PID>.log` correspondente.

Se houver snapshots estruturais referenciados no relatório, só envie esses arquivos quando forem necessários para a investigação; o relatório principal não incorpora HTML, screenshot ou vídeo bruto por padrão.

## Resultado esperado

O smoke está aprovado quando o self-test retorna saudável, o `doctor` identifica corretamente o ambiente, `probe` reconhece a aula aberta, `current` termina com resultado coerente e os artefatos da execução permitem correlacionar código, configuração, timeline, posição, subprocessos, validação e resultado final sem expor segredos.
