# XCursos Runner V4.2.5 — Test Results

## Baseline

V4.2.4 antes das alterações da V4.2.5:

- `npm run check`: PASS
- `npm test`: 251/251 PASS no pacote local de release V4.2.4

## Evidência live que originou a V4.2.5

Os logs da aula 108 mostraram `DIRECT_MP4` correto quando o player estava pronto. O `errors.jsonl` revelou que, durante navegação rápida, algumas tentativas selecionavam o iframe do Google Tag Manager como mídia e entregavam `https://www.googletagmanager.com/ns.html?...` ao yt-dlp. Outras tentativas criavam arquivos que o ffprobe rejeitava por ausência de stream de vídeo/duração positiva.

## Ciclo RED → GREEN

### 1. Semântica de iframe

RED: GTM era `EXTERNAL_IFRAME` e podia chegar ao downloader.

GREEN:
- analytics/tracking deixam de ser candidatos;
- iframe só é aceito para player reconhecido;
- `mediaSourceConfidence`: `PROVEN`, `SUPPORTED_IFRAME`, `UNTRUSTED`;
- múltiplos trackers continuam sem mídia elegível.

### 2. Media readiness

RED: contador/título podiam estar prontos antes do `<video src>` e a aula era processada cedo demais.

GREEN:
- espera limitada padrão de 12 s, poll 250 ms;
- posição, curso e TOTAL são revalidados durante a espera;
- MP4 que aparece depois é escolhido;
- ausência transitória vira `MEDIA_NOT_READY`;
- mídia `UNTRUSTED` não chega ao yt-dlp.

### 3. Recovery de download/verificação

RED: `YTDLP_FAILED` genérico e `VERIFY_FAILED` não recebiam recovery suficiente.

GREEN:
- direct signed MP4 pode renovar a mesma aula em `YTDLP_FAILED` genérico;
- ffprobe failure preserva código concreto como `VERIFY_NO_VIDEO_STREAM`;
- arquivo inválido é colocado em quarentena;
- refresh revalida mesma posição/curso/TOTAL e mesmo objeto de mídia;
- retry de verificação é clean: `--no-continue` e limpeza apenas dos parciais da saída atual.

### 4. Retry epoch

RED: checkpoint `BLOCKED` preservava `attempts` esgotados na execução seguinte.

GREEN: `BLOCKED -> READY` inicia uma nova execução com `attempts=0`, `priority=0` e sem erro antigo. `IN_FLIGHT` de crash continua com semântica própria de resume.

### 5. NO_PROGRESS

RED: a cobertura permanecia 185/198, mas a alternância `VERIFY_FAILED ↔ YTDLP_FAILED` mudava o fingerprint e impedia parada.

GREEN: fingerprint usa somente `downloaded + processed + missingPositions`. As causas continuam exibidas, mas não fingem progresso.

## Validação final pré-release no GitHub Actions

No PR da V4.2.5:

- `npm install`: PASS
- `npm run check`: PASS
- tests: 264
- PASS: 262
- FAIL: 0
- SKIPPED: 2
- CANCELLED: 0

Os 2 skips são testes de integração que dependem de ffmpeg/ffprobe reais e foram pulados no runner Linux porque essas ferramentas não estavam disponíveis naquele ambiente.

## Invariants preservados

- N/TOTAL continua fonte principal de posição.
- Ação → observação → decisão na Próxima permanece.
- N→N+2 e N→N-1 não são aceitos silenciosamente.
- Navegação não cria commit.
- Signed URL completa não é persistida.
- Materiais não são mídia.
- DRM não é contornado.
- Cloudflare/login continuam humanos.
- Estado, manifesto e vídeos válidos não são apagados durante recovery.
