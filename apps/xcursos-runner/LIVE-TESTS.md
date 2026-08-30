# V4.2.6 — Live tests no Windows

## 1. Confirmar instalação

```powershell
xcursos version
xcursos doctor
```

Esperado: `4.2.6` e dependências disponíveis.

> As novas flags contra throttling de aba em background só entram em vigor quando o Chrome dedicado do XCursos for iniciado novamente. Feche apenas essa janela/processo do Chrome XCursos e abra de novo com `xcursos login`/`xcursos browser`. Não apague perfil, manifesto, configuração ou vídeos.

## 2. Validar pin da guia de trabalho

```powershell
xcursos login
```

Abra a videoaula que será usada pelo runner e conclua o gate humano normalmente. Depois inicie um range, por exemplo:

```powershell
xcursos range --start 108 --end 123 --json
```

Enquanto o range estiver trabalhando:

- alterne para outra guia;
- abra outra janela do Chrome;
- navegue normalmente em outros sites;
- não feche a guia de aula que o XCursos Runner está usando.

Esperado: o runner continua trabalhando na guia pinada por CDP Target ID; enumerar outras abas não instala observers nelas e trocar o foco visual não deve fazer o runner seguir a guia ativa.

## 3. Validar hierarquia de pastas

Para aulas cuja sidebar exponha módulos/submódulos aninhados, novos downloads devem espelhar a árvore no disco.

O HTML live usado durante o desenvolvimento da aula 108 mostrou esta hierarquia:

```text
2. Regravação VTSD 2026
└── 05. Copywriting
    └── 5. Vídeo de vendas - VSL
        └── 108 - e_Aula.mp4
```

A pasta raiz do curso continua acima dessa árvore. A implementação aceita profundidade arbitrária via `modulePath[]`; não está limitada a somente “módulo + submódulo”.

Arquivos antigos já validados não são movidos nem apagados automaticamente. Reparo de um arquivo já conhecido preserva seu caminho anterior; a nova árvore vale para novos downloads e novas posições cuja hierarquia seja observada.

## 4. Validar mídia e recuperação

Na aula 108:

```powershell
xcursos probe --json
```

Esperado:
- posição correta `108 / 198`;
- `DIRECT_MP4` quando a mídia estiver pronta;
- Google Tag Manager/analytics nunca selecionado como vídeo;
- signed URLs não persistidas em claro.

## 5. Auditoria

```powershell
xcursos audit --json
```

Meta:
- `missingPositions: []` ao final do curso;
- `duplicatePositions: []`;
- `invalidFilePositions: []`;
- DRM, se houver, permanece somente classificado e não é contornado.

Se houver lentidão mesmo depois de reiniciar o Chrome dedicado com a V4.2.6, guardar `runner.log` e informar o que estava sendo feito nas outras abas no momento; isso permitirá separar gargalo de renderer/CDP de gargalo de disco/rede/yt-dlp.
