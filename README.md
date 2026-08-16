# XCursos Runner

Baixador determinístico de cursos do XCursos com Node.js, Playwright/CDP, Chrome, yt-dlp e ffprobe.

## Versão atual

**V4.2.4**

O snapshot inicial está em [`XCursos-Runner-V4.2.4/`](./XCursos-Runner-V4.2.4/).

Principais diretórios:

- `XCursos-Runner-V4.2.4/src/` — código-fonte
- `XCursos-Runner-V4.2.4/tests/` — suíte de regressão
- `XCursos-Runner-V4.2.4/test-fixtures/` — fixtures sanitizadas e HTML de teste

## Qualidade

A V4.2.4 foi empacotada com **251/251 testes passando** e `npm run check` verde.

O workflow em `.github/workflows/ci.yml` executa syntax check e suíte completa em pushes e pull requests para `main`.

## Fluxo de desenvolvimento

Próximas mudanças devem seguir:

1. branch de trabalho;
2. teste RED que reproduz o problema;
3. implementação mínima;
4. GREEN + regressão completa;
5. pull request para `main`;
6. nova versão/tag após estabilização.
