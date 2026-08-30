# XCursos Runner V4.2.6 — Test Results

## Baseline

V4.2.5 na `main` antes das alterações:

- versão: `4.2.5`;
- CI verde;
- 264 testes, 262 PASS, 0 FAIL, 2 SKIPPED.

## Ciclo RED → GREEN

### 1. Isolamento da guia de trabalho

RED demonstrou que `PageController.pages()` criava refs e instalava observers de auth/rede em todas as páginas enumeradas do Chrome. Também não existia identidade persistente da guia por CDP Target ID.

GREEN:
- enumeração de abas é passiva;
- observers são instalados apenas quando a guia é explicitamente pinada como work page;
- `BrowserSession` obtém `TargetId` via CDP;
- recovery prefere o Target ID pinado, não a aba em foco nem a primeira URL coincidente;
- múltiplas abas com a mesma URL sem Target ID recuperável geram `PAGE_RECOVERY_AMBIGUOUS` em vez de escolha arbitrária;
- fallback reutiliza apenas `about:blank` ou cria uma nova página, nunca sequestra uma aba alheia.

### 2. Responsividade em background

RED verificou ausência de proteção contra throttling do renderer.

GREEN: o Chrome dedicado passa a iniciar com:

- `--disable-background-timer-throttling`;
- `--disable-renderer-backgrounding`;
- `--disable-backgrounding-occluded-windows`.

Essas flags exigem reinício do Chrome dedicado para entrar em vigor; não exigem apagar o perfil.

### 3. Árvore de módulos/submódulos

RED demonstrou que o pipeline só transportava `moduleName`, portanto só conseguia expressar um nível de pasta.

GREEN:
- metadata ganha `modulePath[]` com profundidade arbitrária;
- `moduleName` continua sendo o leaf para compatibilidade;
- inspeção live percorre a ancestralidade da aula ativa na sidebar visível;
- grupos identificados por headers de `aulas`/`arquivos` entram na árvore do mais externo ao mais interno;
- downloader cria `curso / ...modulePath / aula`;
- `modulePath` é preservado em in-flight state e manifesto.

O HTML live usado no desenvolvimento da aula 108 demonstrou uma árvore de três níveis: `2. Regravação VTSD 2026 → 05. Copywriting → 5. Vídeo de vendas - VSL`.

### 4. Compatibilidade e segurança de caminho

GREEN adicional:
- registros antigos sem `modulePath` continuam válidos via fallback para `moduleName`;
- reparo de arquivo existente preserva o caminho antigo;
- novos downloads usam a nova árvore;
- cada segmento é sanitizado para Windows;
- árvores/títulos longos são encurtados deterministicamente até o limite seguro do template;
- caso ainda seja impossível, o runner falha explicitamente com `OUTPUT_PATH_TOO_LONG`.

## Regressão intermediária

Após a implementação funcional e os ajustes de compatibilidade:

- `npm run check`: PASS;
- tests: 271;
- PASS: 269;
- FAIL: 0;
- SKIPPED: 2.

## Validação pré-release V4.2.6

Após remoção da infraestrutura temporária, bump de versão e testes adicionais de persistência/path guard:

- `npm install`: PASS;
- `npm run check`: PASS;
- tests: 273;
- PASS: 271;
- FAIL: 0;
- SKIPPED: 2;
- CANCELLED: 0.

Os 2 skips são integrações dependentes de ffmpeg/ffprobe reais, ausentes no runner Linux usado pelo GitHub Actions.

## Invariants preservados

- N/TOTAL continua fonte principal de posição.
- Ação → observação → decisão na Próxima permanece.
- N→N+2 e N→N-1 não são aceitos silenciosamente.
- Navegação não cria commit.
- Signed URL completa não é persistida.
- Materiais não são mídia.
- DRM não é contornado.
- Cloudflare/login continuam humanos.
- Nenhum perfil, manifesto ou vídeo válido é apagado para aplicar a V4.2.6.
