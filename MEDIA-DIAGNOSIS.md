# V4.2.5 — Media pipeline diagnosis

## Evidência live

O HTML real da posição 108 mostra uma aula normal do XCursos: `108 / 198`, título `e_Aula`, módulo `5. Vídeo de vendas - VSL`, `<video>` com MP4 direto assinado do Cloudflare R2 e sem evidência de DRM.

Quando a aula 108 foi aberta manualmente e houve tempo para o player ficar pronto, `probe --json` encontrou `DIRECT_MP4` via `live` corretamente.

O `errors.jsonl` posterior revelou a segunda causa: durante navegação automatizada rápida, algumas inspeções aconteciam depois do shell/contador ficar pronto, mas antes de o `<video>` expor o MP4. Nesse intervalo, o parser promovia um iframe genérico da página a `EXTERNAL_IFRAME`. Em várias posições, esse iframe era do Google Tag Manager e chegava ao yt-dlp, que corretamente falhava com `Unsupported URL`.

Outras tentativas chegavam a produzir um arquivo `.mp4`, mas o ffprobe repetidamente o rejeitava por não haver stream de vídeo ou duração positiva.

## Evolução V4.2.4 → V4.2.5

A V4.2.4 continua preservando:
- generation por aula no `NetworkMediaObserver`;
- correlação network × DOM por objeto de mídia;
- proteção contra candidato de outra aula;
- diagnostics sanitizados;
- refresh limitado e identidade de objeto.

A V4.2.5 adiciona uma camada semântica antes do downloader:

1. iframe genérico não é mais mídia por padrão;
2. analytics/tracking, incluindo Google Tag Manager, são rejeitados;
3. iframe só é aceito para hosts de player reconhecidos;
4. confiança da mídia é `PROVEN`, `SUPPORTED_IFRAME` ou `UNTRUSTED`;
5. mídia `UNTRUSTED` nunca chega ao yt-dlp;
6. após navegação/refresh, o runner pode esperar até a janela limitada de media readiness pelo MP4/HLS/DASH comprovado;
7. se o player ainda não ficar pronto, retorna `MEDIA_NOT_READY` retryable em vez de baixar infraestrutura da página.

## Recuperação após download

Para direct signed MP4:
- `YTDLP_FAILED` genérico pode receber refresh seguro da mesma aula;
- falha do ffprobe preserva código específico como `VERIFY_NO_VIDEO_STREAM`;
- arquivo inválido é colocado em quarentena;
- o runner renova a mídia, confirma posição/curso/TOTAL e mesmo objeto;
- o retry de integridade começa limpo com `--no-continue` e remove apenas parciais correspondentes à saída da posição atual.

## Scheduler / wrapper

- `BLOCKED` de execução anterior recebe novo orçamento de tentativas na nova execução;
- `xcursos-all` considera progresso apenas mudança real de cobertura, não troca de rótulo de erro.

## Invariants

- N/TOTAL continua sendo fonte principal de posição;
- nenhum signed query é persistido;
- navegação não é commit;
- mídia não comprovada não chega ao downloader;
- refresh não pode trocar de objeto silenciosamente;
- nenhum DRM é contornado;
- Cloudflare/login permanecem humanos.
