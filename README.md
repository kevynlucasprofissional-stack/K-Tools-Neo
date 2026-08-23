# YT-DLP TUI

TUI resiliente para baixar áudio, vídeo e playlists do YouTube usando `yt-dlp`, com retomada, autenticação renovável, retry limitado e auditoria final de playlists.

## Estado da release

Versão atual: **0.6.6**.

A versão é definida em `pyproject.toml`; o pacote lê a metadata instalada em runtime. A release fixa as dependências de runtime em `yt-dlp[default]==2026.8.19` e `imageio-ffmpeg==0.6.0` para que uma instalação futura não mude silenciosamente de comportamento. Atualizações dessas dependências devem ser deliberadas e testadas em uma nova release.

Requer **Python 3.10+**. Deno precisa estar disponível no `PATH` e o preflight exige FFmpeg funcional antes de iniciar downloads, pois a auditoria completa de playlists depende dele.

## Comportamento principal

- **Pasta obrigatória a cada execução:** o seletor de pasta é aberto em toda run. Não existe pasta padrão ou persistida para downloads.
- **Somente TUI:** não existe GUI ou entrypoint gráfico.
- **Sem auto-update:** o aplicativo não consulta nem instala versões novas por conta própria.
- **Sem cookies distribuídos:** nenhum `cookies.txt` acompanha fonte, wheel, ZIP ou EXE.
- **Sessão renovável:** somente erros classificados como `AUTH_EXPIRED` acionam o fluxo de renovação.
- **Cache privado:** o export selecionado é apenas lido e filtrado para uma cópia gerenciada em `%LOCALAPPDATA%\YT-DLP-TUI\cookies.txt` no Windows.
- **Retry de rede/CDN limitado:** apenas `TRANSIENT_NETWORK` e `RATE_LIMIT` entram no retry automático.
- **Indisponibilidade permanente separada:** vídeos inequivocamente removidos/privados ficam `unavailable` e não gastam retry de rede.
- **Controle persistente de playlist:** `YT-DLP-TUI-controle.json` registra progresso, tentativas, falhas, auditoria e retomada.
- **Staging isolado:** itens em andamento usam `.yt-dlp-tui-tmp`; parciais são removidos antes de uma repetição completa.
- **Auditoria final:** FFmpeg decodifica os arquivos disponíveis para detectar truncamento/corrupção; itens reprovados entram no mesmo fluxo de reparo/retry.
- **Entradas não resolvidas não viram falsos “indisponíveis”:** falhas de metadata na extração flat permanecem `unresolved`, mantendo a tarefa incompleta até uma extração futura resolver o item.
- **Playlist nunca conclui como 0/0:** se o yt-dlp retornar metadata de playlist com zero entradas, a TUI trata o resultado como extração inválida, tenta novamente de forma limitada e nunca cria/conclui uma tarefa vazia por engano.
- **Deno + EJS local:** utiliza `yt-dlp-ejs` instalado por `yt-dlp[default]`; não existe fetch de `ejs:github` em runtime.

## Como usar

Execute `INICIAR_YT-DLP-TUI.bat` no Windows.

1. Na primeira execução, o launcher cria `.venv` e instala as dependências fixadas pela release.
2. Em toda run, escolha a pasta-base de destino.
3. Cole um vídeo/playlist ou use os comandos da TUI.
4. Se não houver sessão configurada, pressione **Enter** quando solicitado e selecione um export Netscape `cookies.txt`.
5. Em playlist, a subpasta da tarefa recebe o arquivo de controle e passa por auditoria final antes de a tarefa ser declarada concluída.

## Comandos da TUI

- `[link]` — baixar vídeo ou playlist.
- `s:<busca>` — pesquisar e baixar o primeiro resultado.
- `s3:<busca>` / `s5:<busca>` — pesquisar e escolher entre resultados.
- `audio` / `video` — alternar formato.
- `res` — escolher `480p`, `720p`, `1080p` ou `best`.
- `rename` — habilitar renomeação manual para downloads **individuais**. Por padrão, os arquivos usam o título do vídeo no YouTube como nome, preservando espaços e acentos; caracteres que o Windows não permite em nomes de arquivo são ajustados pelo yt-dlp. Em caso raro de dois vídeos com exatamente o mesmo título na mesma playlist, o segundo recebe apenas um sufixo numérico para evitar sobrescrita.
- `cache` — importar manualmente um novo `cookies.txt`.
- `open` — abrir a pasta escolhida para a run atual.
- `?` — ajuda.
- `q` — sair.

## Autenticação e cookies

O export precisa estar em formato Netscape e conter pelo menos um cookie de autenticação Google/YouTube ainda válido por data. O arquivo escolhido nunca é alterado.

O importador mantém apenas cookies dos domínios raiz necessários ao fluxo Google/YouTube. No Windows, a cópia ativa fica em:

```text
%LOCALAPPDATA%\YT-DLP-TUI\cookies.txt
```

No POSIX, diretório e arquivo são endurecidos para `0700` e `0600`. No Windows, o programa tenta adicionalmente restringir a ACL com `icacls` quando disponível. Essa proteção é best-effort porque políticas de domínio podem impedir alteração de ACL.

Se a sessão expirar durante um item:

```text
⚠ Sua sessão do YouTube expirou.

Exporte um novo cookies.txt.
Pressione ENTER para selecionar o arquivo.
```

O staging do item é apagado, o estado da playlist fica `waiting_auth`, o cache é substituído atomicamente após validação e exatamente o mesmo item é reiniciado. O número de renovações rejeitadas pelo servidor é limitado por operação para impedir loop infinito.

Se o usuário cancelar, a tarefa permanece retomável. Um export inválido não sobrescreve o cache anterior.

## Classificação de falhas

Há uma única taxonomia central:

- `AUTH_EXPIRED`
- `TRANSIENT_NETWORK`
- `RATE_LIMIT`
- `PERMANENT_UNAVAILABLE`
- `JS_RUNTIME`
- `LOCAL_IO`
- `FORMAT_CONFIG`
- `UNKNOWN`

A classificação prioriza tipo da exceção, causa preservada, status HTTP e só depois texto. A mensagem ambígua `The page needs to be reloaded` não é suficiente para classificar autenticação; evidência de challenge/EJS tem precedência.

O logger do `yt-dlp` é capturado para diagnóstico e controle, mas o erro bruto não é despejado na TUI antes da classificação.

## Retry de rede/CDN

Somente `TRANSIENT_NETWORK` e `RATE_LIMIT` são repetidos automaticamente.

Orçamento da release:

- yt-dlp: 1 retry HTTP, 2 de fragmento, 1 de extractor e 1 de acesso a arquivo;
- socket timeout: 15 s;
- TUI: no máximo 3 tentativas completas por fase;
- backoff externo de rede: 3 s e 6 s;
- backoff de rate limit: 10 s e 20 s.

`AUTH_EXPIRED`, `PERMANENT_UNAVAILABLE`, `JS_RUNTIME`, `LOCAL_IO` e `FORMAT_CONFIG` não entram no retry de rede. Um `403` puro permanece conservadoramente não classificado; contexto explícito de CDN/signed-media permite apenas reextração limitada.

Antes de uma tentativa externa completa, o staging do item é limpo. Se o orçamento acabar, não existe `.part` promovido a arquivo final.


### Proteção contra playlist falsamente vazia

O YouTube/yt-dlp pode ocasionalmente devolver o nome e o ID de uma playlist, mas uma lista de entradas vazia. A v0.6.2 trata isso como falha de extração, não como playlist concluída.

Fluxo aplicado:

1. a primeira leitura preserva a URL original;
2. se ela retornar zero entradas, novas tentativas usam o endpoint direto `playlist?list=...`, removendo contexto de vídeo/índice;
3. a extração flat é repetida de forma limitada e a última tentativa usa metadata completa com `skip_download`, sem baixar mídia;
4. se as três tentativas continuarem vazias, nenhum controle novo é criado e a TUI informa que nenhum download foi iniciado;
5. a auditoria possui uma segunda barreira: um estado com `items=[]` é bloqueado e jamais pode resultar em `✓ 0/0`.

Um controle antigo criado pelo bug `0/0` não perde o caminho da tarefa: quando uma extração futura volta a trazer os itens, o estado é repopulado e retorna a `in_progress`.

## Controle, retomada e recuperação

Cada playlist usa:

```text
YT-DLP-TUI-controle.json
```

Schema atual: **3**. O controle registra, entre outros:

- ID, posição, título e URL;
- `available` e status (`pending`, `unresolved`, `downloading`, `processing`, `waiting_auth`, `retry_wait`, `completed`, `failed`, `unavailable`);
- `attempts`, `retry_count`, `last_retry_at`;
- progresso/bytes;
- arquivo final;
- timestamps;
- `last_error_kind` e diagnóstico técnico;
- estado da auditoria.

A escrita é atômica. Controles v2 válidos são migrados preservando progresso. JSON inválido ou semanticamente inconsistente é tratado como controle corrompido, preservado como `.corrupt.json` e reconstruído com metadata fresca e mídia local.

Arquivos encontrados durante reconstrução só viram `completed` após verificação de integridade. Caminhos vindos do controle são confinados à pasta da tarefa; staging e deleções não seguem symlink/junction para fora da área permitida.

## Auditoria final de playlist

A tarefa não é declarada concluída somente porque o `yt-dlp` retornou sucesso. O FFmpeg percorre integralmente a mídia dos itens ainda disponíveis.

- íntegro → `audit_status=ok`;
- ausente/corrompido → arquivo é removido com proteção de caminho, item volta a `pending` e usa a mesma política de download/retry;
- `PERMANENT_UNAVAILABLE` durante download/reparo → sai do conjunto obrigatório e é reportado separadamente;
- `unresolved` → continua faltando; não é falsamente convertido em indisponível;
- FFmpeg ausente → auditoria fica `blocked`; o programa não declara aprovação por uma checagem fraca.

## Deno, EJS e FFmpeg

O preflight verifica, antes de pedir cookies:

1. Deno disponível e versão >= 2.3;
2. `yt-dlp-ejs` importável;
3. versão de `yt-dlp-ejs` igual ao pin exigido pela metadata do `yt-dlp` instalado;
4. FFmpeg disponível pelo sistema ou por `imageio-ffmpeg`.

Falha nessa camada é apresentada como `JS_RUNTIME` ou erro de FFmpeg; não abre o seletor de cookies.

## Build Windows

`GERAR_EXE_WINDOWS.bat`:

1. prepara/valida a `.venv`;
2. reaplica a instalação da release;
3. instala PyInstaller;
4. executa `python -m pytest`;
5. executa `compileall`;
6. gera `dist\yt-dlp-tui.exe` usando `yt-dlp-tui.spec`.

O spec inclui módulos/dados de `yt_dlp`, `yt_dlp_ejs` e `imageio_ffmpeg`, além de metadata de `yt-dlp-tui`, `yt-dlp` e `yt-dlp-ejs`.

## Segurança

- nenhum cookie/segredo é empacotado;
- `.gitignore` cobre cookies, `.env`, credentials, secrets, tokens e sessions;
- cookies nunca são impressos;
- deleções e caminhos de arquivos finais são confinados às pastas da tarefa;
- symlinks/junctions de staging não são percorridos recursivamente;
- o seletor de cookies só lê o export original;
- não há auto-update nem fetch remoto automático de EJS.

---

Baseado em projeto open source de NamikazeAsh, com alterações locais substanciais de TUI, autenticação, classificação de falhas, retomada, retry, segurança e auditoria.
