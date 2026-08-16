# V4.2.4 — Media pipeline diagnosis

## Evidência live

O HTML real da posição 108 mostra uma aula normal do XCursos: `108 / 198`, título `e_Aula`, módulo `5. Vídeo de vendas - VSL`, um único `<video>` e um MP4 direto assinado do Cloudflare R2 com `X-Amz-Expires=14400`. Não há HLS, DASH, iframe de player ou evidência de DRM nessa aula.

## Causa arquitetural encontrada

Na V4.2.3 o `NetworkMediaObserver` guardava respostas por `Page`, e `inspectLesson()` dava prioridade global à melhor resposta 2xx/3xx da aba. Uma resposta bem-sucedida de uma aula anterior podia sobreviver à navegação e competir com o `video.currentSrc/src` da aula atual.

## V4.2.4

- mídia de rede agora pertence a uma `generation` de aula;
- `navigateExact`, `Próxima` e refresh abrem nova generation;
- `best()` considera somente a generation corrente;
- URLs de rede e DOM são correlacionadas pelo objeto `host + pathname`, ignorando query assinada;
- rede só substitui uma URL HTTP atual quando aponta para o mesmo objeto;
- se os objetos divergem, a URL DOM atual vence;
- diagnostics usam fingerprints SHA-256 truncados, nunca signed URL completa;
- erros de yt-dlp recebem `failureCode` e `diagnosticTail` sanitizado;
- falhas transitórias de MP4 assinado podem provocar refresh limitado da mesma aula;
- refresh que aponta para outro objeto é recusado com `MEDIA_REFRESH_OBJECT_CHANGED`;
- `failureSummary` agrega causas/posições pendentes;
- `xcursos-all` detecta repetição sem progresso e interrompe cedo;
- contador `null` antes de Próxima vira `POSITION_UNOBSERVABLE` transient, não regressão falsa.

## Invariants

- N/TOTAL continua sendo fonte principal de posição;
- nenhum signed query é persistido;
- rede antiga nunca deve sobrepor silenciosamente mídia HTTP da aula atual;
- atravessar/navegar não é commit;
- nenhum refresh pode trocar de objeto de vídeo sem erro explícito;
- nenhum DRM é contornado.
