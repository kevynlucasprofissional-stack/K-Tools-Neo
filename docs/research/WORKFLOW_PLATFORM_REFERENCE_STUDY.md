# Estudo de Referências para a Plataforma de Workflows do K-Tools Neo

Status: **RESEARCH-VALIDATED / ARQUITETURA DE REFERÊNCIA**  
Data do estudo: 2026-08-30  
Escopo: arquitetura, runtime, modelo de nodes, extensibilidade, persistência, execução, cache, UX do canvas e viabilidade de reutilização de código.

> Este documento registra aprendizado de engenharia. Ele não transforma recomendações futuras em funcionalidades já implementadas. As decisões canônicas continuam em `docs/DECISIONS.md`, e o estado real continua em `docs/CURRENT_STATE.md`.

---

## 1. Objetivo

O K-Tools Neo está deixando de ser uma coleção de utilitários isolados para se tornar um único produto local-first em que:

1. funcionalidades como converter, juntar, analisar, baixar, organizar e processar arquivos sejam capacidades reutilizáveis;
2. as mesmas capacidades apareçam tanto em **Ferramentas** prontas quanto em um **editor visual de workflows**;
3. workflows possam ser salvos, versionados, reutilizados e, mais tarde, encapsulados como ferramentas/subworkflows;
4. Python, Node.js e aplicações importadas possam coexistir sem reescritas desnecessárias;
5. no futuro, um agente de IA possa construir workflows usando a mesma linguagem operacional do usuário.

A pergunta deste estudo é:

> O que projetos maduros de programação visual e automação já resolveram, o que podemos reutilizar diretamente, o que devemos adaptar conceitualmente e o que devemos evitar copiar?

---

## 2. Materiais analisados e identidade dos snapshots

Foram analisados os arquivos-fonte anexados, não apenas READMEs ou páginas de marketing.

| Projeto | Snapshot observado | Licença observada | SHA-256 do ZIP estudado |
|---|---:|---|---|
| n8n | `2.37.0` | Sustainable Use License + áreas Enterprise | `7ace9090e37be75f3c006094e064ccf580de4b750eb65620f45abe644bd9fc77` |
| Activepieces | `0.88.3` | MIT fora das áreas Enterprise declaradas | `8b869df3140e2d035a57477e5c0dd818b4a49a31c7b36762bd164cda13b2711e` |
| LiteGraph.js | `0.7.14` | MIT | `e5633b5f8a475ff7e28b64cff59879f531739f932ec1d228035d32c5b87d9cfc` |
| Rete.js | `2.0.6` | MIT | `84ad57ec17c7a7420b6ee8309c50a5012851beb1daa25c5fd988edbb3158216d` |
| ComfyUI | `0.34.0` | GPL-3.0 | `4563f1a2fc8d27b946ac019b436b6920817698a76a9adc615da9bc058696a26c` |
| Node-RED | `5.0.4` | Apache-2.0 | `88cace110541eb96490c790372e9adb07c6d1f942b21503a6610bf5c10c1378c` |
| xyflow / React Flow | snapshot monorepo anexado | MIT | `f54308bba93e49ce8b7bb28f3b53daba2daa156bde62ca310554fc2f6ba1700c` |

Os hashes existem para impedir que um estudo futuro seja tratado como evidência do mesmo código quando o snapshot tiver mudado.

### Arquivos/famílias examinados em profundidade

Entre outros:

- n8n: `packages/workflow/src/workflow.ts`, `interfaces.ts`, `packages/cli/src/node-types.ts`, `packages/core/src/execution-engine/workflow-execute.ts` e componentes do editor/NDV/canvas;
- Activepieces: documentação de arquitetura, durable execution, waitpoints e sandboxing; engine, execution journal, piece framework e canvas React;
- Node-RED: runtime, registry, flow lifecycle, flow diff/deploy e subflows;
- ComfyUI: `nodes.py`, `execution.py`, `comfy_execution/caching.py`, `comfy_execution/progress.py`;
- Rete.js: `editor.ts`, `scope.ts`, preset clássico de socket/input/output/node/connection;
- LiteGraph.js: registry, execução, serialização/configuração e canvas;
- xyflow: React store, handles/conexões e utilitários de grafo.

---

# 3. Conclusão principal

Nenhum dos sete projetos deve ser transformado no “novo K-Tools” por fork direto.

A combinação que melhor atende ao produto é:

```text
K-Tools Runtime próprio (Python)
        │
        ├── contratos tipados de Node / Port / Workflow / Artifact
        ├── execução, journal, cache e persistence próprios
        ├── Node Packs próprios
        └── adapters para runtimes externos

Frontend React/TypeScript
        │
        └── @xyflow/react como infraestrutura do canvas

Referências arquiteturais
        ├── Node-RED      → registry, subflows, revision/diff deploy, runtime/editor split
        ├── Activepieces → pieces, durability, checkpoints, executor strategies, sandbox tiers
        ├── ComfyUI      → typed validation, cache signatures, progress/event model
        ├── n8n          → rich node contracts, partial execution, tool wrappers, NDV UX
        ├── Rete.js      → socket/control abstractions and event middleware concepts
        └── LiteGraph    → serialization resilience and missing-node placeholders
```

A implicação mais importante é:

> **O canvas é um cliente do K-Tools Core. Ele não é o engine e não é a fonte de verdade do workflow.**

Isso protege o produto contra lock-in visual e permite que CLI, ferramentas tradicionais, automações agendadas e agentes usem a mesma infraestrutura.

---

# 4. Matriz de reutilização

## 4.1. Classificação

| Projeto | Reutilização recomendada | Papel no K-Tools | Copiar código? |
|---|---|---|---|
| **xyflow** | **Dependência direta** | Canvas visual React | Preferir pacote oficial a copiar source |
| **Activepieces** | **Adaptação seletiva** | Node Packs, durability, journal, security tiers | Pode ser considerado em trechos MIT, após revisão de cada arquivo/dependência |
| **Node-RED** | **Adaptação seletiva** | Registry, subflows, revision/diff, lifecycle | Apache-2.0 permite reutilização com obrigações de licença/atribuição |
| **Rete.js** | Conceitos + reutilização seletiva | Sockets, controls, middleware/event pipeline | MIT, mas evitar adotar um segundo graph model junto de xyflow + ktools-core |
| **LiteGraph.js** | Conceitos pontuais | Compatibilidade de serialização e placeholder de node ausente | MIT; não recomendado como base do frontend |
| **n8n** | **Inspiração clean-room** | UX, rich node schema, partial execution, tool wrappers | **Não incorporar source ao produto** sob a estratégia atual |
| **ComfyUI** | **Inspiração clean-room** | Cache, validation, progress, lazy/incremental execution | **Não incorporar source** sem decisão consciente de compatibilidade GPL |

### Nota de licenciamento

Isto é triagem de engenharia, não aconselhamento jurídico. Antes de reutilizar código de terceiros em release distribuído, deve existir revisão de licença do arquivo e de suas dependências. Em especial:

- n8n limita uso/modificação/distribuição no Sustainable Use License; por isso é referência, não donor code;
- ComfyUI é GPL-3.0; copiar/adaptar código pode trazer obrigações copyleft relevantes;
- Activepieces declara MIT fora de `packages/ee/` e `packages/server/api/src/app/ee`; essas áreas Enterprise devem ficar fora da reciclagem;
- Node-RED é Apache-2.0;
- xyflow, Rete.js e LiteGraph.js são MIT nos snapshots estudados.

---

# 5. O que aprendemos com cada projeto

## 5.1. Node-RED — a referência mais forte para boundaries arquiteturais

### O que o source demonstra

O monorepo separa explicitamente:

```text
@node-red/runtime
@node-red/registry
@node-red/editor-api
@node-red/editor-client
@node-red/nodes
@node-red/util
```

O runtime não precisa possuir a UI. O `registry` carrega módulos de node, registra construtores, resolve tipos e consegue habilitar/desabilitar node sets. O `Flow` possui lifecycle próprio de criação/start/stop e contexto. A camada de flows mantém revision, calcula diferenças entre a configuração antiga e nova e pode reiniciar apenas a parte afetada.

Outra ideia extremamente valiosa é o **subflow como node**: um subflow recebe um type próprio (`sf:<id>`) e passa a aparecer como unidade reutilizável.

### O que adaptar

1. **Registry independente do canvas**.
2. **Node Pack / Node Set** carregável sem editar o engine central.
3. **Subworkflow como node de primeira classe**.
4. **Workflow revision** explícita.
5. **Diff de versão** para descobrir nodes adicionados, removidos, reconfigurados e rewired.
6. Lifecycle separado: `load → validate → start/run → stop/cancel → cleanup`.
7. Contextos com ownership claro em vez de um grande estado global.

### O que não copiar

Não precisamos reproduzir toda a arquitetura de deploy de um servidor event-driven. O K-Tools é primeiro um produto desktop/local. Revision/diff são úteis para cache, hot reload do editor e execução incremental, mas não justificam portar o runtime do Node-RED.

---

## 5.2. Activepieces — melhor referência para extensibilidade + execução durável

### Componentização

A documentação e o source separam:

```text
UI
App/API
Worker
Sandbox
Engine
Pieces
Shared
Postgres
Redis
```

A escala cloud não deve ser copiada literalmente para um desktop, mas a separação de responsabilidades é valiosa.

### Pieces

`createPiece(...)` reúne metadata, autenticação, categories, actions e triggers. A principal lição é que uma integração não precisa modificar o engine. Ela se registra através de um contrato estável.

Para K-Tools:

```text
NodePack
├── manifest
├── nodes/actions
├── metadata/categories/icons
├── runtime requirements
├── optional adapter
└── tests
```

### Durable execution

A arquitetura de **replay-and-skip** é particularmente relevante para operações longas do K-Tools.

O run log registra output dos steps concluídos. Após crash/restart, o engine percorre o fluxo novamente e:

```text
step já concluído → reutiliza output
step não concluído → executa
```

Isso evita reprocessar horas de vídeo/áudio depois de uma queda.

### Execution journal

O source mantém step outputs em uma estrutura capaz de representar caminhos dentro de loops. Para K-Tools, uma primeira versão pode ser mais simples, mas o princípio deve ser preservado:

```text
Run
└── NodeRun
    ├── status
    ├── inputs/provenance
    ├── outputs/artifacts
    ├── timestamps/duration
    ├── progress
    └── error
```

### Executor strategies

O engine despacha diferentes action types para executores diferentes (`CODE`, `LOOP_ON_ITEMS`, `PIECE`, `ROUTER`) em vez de concentrar todas as semânticas em um switch gigantesco.

K-Tools deve evoluir para runners/strategies explícitos, por exemplo:

```text
PythonInProcessRunner
PythonSubprocessRunner
NodeSubprocessRunner
CliAdapterRunner
LongRunningMediaRunner
FutureSandboxedPluginRunner
```

### Sandbox tiers

Activepieces diferencia níveis de isolamento. Para K-Tools isso não é prioridade na V1 porque nossos nodes oficiais são confiáveis/local-first, mas é uma advertência arquitetural importante:

> no momento em que aceitarmos Node Packs de terceiros ou código gerado por usuários/IA, plugin execution deixa de ser apenas extensibilidade e passa a ser uma fronteira de segurança.

### Prova adicional para xyflow

O frontend real do Activepieces usa `@xyflow/react` extensivamente no builder. Isso é evidência forte de que xyflow não serve apenas para demos: é adequado como infraestrutura de canvas para um produto de automação completo.

---

## 5.3. ComfyUI — melhor referência para pipelines locais pesados

ComfyUI é especialmente relevante porque o K-Tools trabalha com artefatos locais e tarefas caras, não apenas chamadas rápidas a APIs.

### Validação antes da execução

`validate_inputs` verifica, entre outras coisas:

- required inputs;
- links malformados;
- type mismatch;
- dependency cycle.

Isso reforça a decisão atual do `ktools-core`: workflow inválido deve falhar **antes** de executar operações caras.

### Cache por assinatura de input

A implementação de cache constrói assinatura a partir de:

- class/type do node;
- indicador de mudança;
- inputs ordenados;
- ancestry ordenada;
- exceções para nodes não idempotentes.

A lição para K-Tools é forte:

> cache não deve depender simplesmente do `node_id` visual.

Uma futura chave deveria ser aproximadamente:

```text
hash(
  node_type
  + node_version
  + normalized_config
  + upstream_artifact_hashes
  + relevant_runtime_version
)
```

Nodes declarados `non_idempotent` ou com efeitos externos devem poder desabilitar cache.

### Progress como contrato, não callback de UI

ComfyUI define estado de node (`Pending`, `Running`, `Finished`, `Error`) e handlers de progress separados para CLI e WebUI.

K-Tools deve fazer o mesmo conceitualmente:

```text
Node handler
   ↓ emits
ExecutionEvent / ProgressEvent
   ↓
Event bus
   ├── CLI subscriber
   ├── Desktop UI subscriber
   ├── diagnostics subscriber
   └── persistence subscriber
```

O node nunca deveria chamar diretamente um widget React/CustomTkinter.

### Cache visível ao usuário

ComfyUI também diferencia node executado de node servido por cache. Essa distinção deve aparecer no K-Tools (`CACHED`) para explicar por que um workflow terminou rapidamente e facilitar diagnóstico.

### Limite de reutilização

A licença GPL-3.0 torna o source uma excelente referência técnica, mas a recomendação é **reimplementar conceitos** no K-Tools em vez de copiar código.

---

## 5.4. n8n — melhor referência para contrato rico + UX do editor

### Contrato de node

O source separa `description` das funções que executam comportamento. A descrição inclui metadata rica como:

- versões;
- inputs/outputs;
- required inputs;
- properties/config schema;
- credentials;
- hints;
- webhooks;
- grupos/categories;
- connection filters;
- maximum connections;
- capacidade de uso como tool.

Isso mostra o caminho natural do `NodeDefinition` atual: ele deve crescer por camadas, sem colocar UI manual dentro de cada node.

### Connection types além de “dado genérico”

n8n possui tipos de conexão diferentes, inclusive para ferramentas/modelos/memória de IA. Para K-Tools, vale separar ao menos:

```text
DATA      → arquivo/texto/json/etc.
CONTROL   → sequência/branch/event
ERROR     → erro/continue-on-error
```

Nossos tipos de dados (`AUDIO`, `VIDEO`, `PDF`...) continuam existindo dentro de DATA.

Isso evita confundir “um PDF saiu deste node” com “agora execute o próximo branch”.

### Synthetic tools sem implementação própria

Um achado especialmente importante: o resolver do n8n possui o conceito de **synthetic tool** sem implementação própria; ele deriva a variante a partir do node-base.

Isso valida diretamente o princípio do K-Tools:

> uma Tool pronta não deve duplicar a implementação do Node.

No K-Tools, uma ferramenta tradicional pode ser:

```text
ToolDefinition
├── workflow/template base
├── preset de parâmetros
├── UI simplificada
└── zero business logic duplicada
```

### Partial execution

O executor possui caminhos para executar até um destination node e trabalhar com subgrafo/parents. Isso é extremamente útil durante edição.

K-Tools deve futuramente suportar:

- Run Workflow;
- Run Node;
- Run Until Here;
- Run From Here, quando inputs anteriores estiverem materializados;
- reuso de cached/artifact outputs anteriores.

### NDV — Node Details View

A UI separa claramente:

```text
Input Panel | Node Settings | Output Panel
```

Há ainda pinned data, run data, erros, validação e diferentes estados de execução.

É uma referência forte para o inspector do K-Tools.

### Status visual do node

O canvas representa estados como:

- selected;
- disabled;
- success;
- error;
- running;
- pinned;
- warning/configuration.

A lição é que node não pode ser apenas um retângulo com nome: ele deve explicar o estado do runtime.

### Limite de reutilização

O Sustainable Use License impõe restrições incompatíveis com tratar o n8n como donor code genérico. Usar padrões conceituais e UX; não incorporar seus arquivos ao K-Tools.

---

## 5.5. Rete.js — melhor referência para abstrações de editor e middleware

O core de Rete é pequeno e instrutivo.

### NodeEditor como modelo, não engine de produto

`NodeEditor` mantém nodes/connections e emite eventos antes/depois de create/remove. O processamento do workflow não precisa estar misturado à manipulação do canvas.

### Scope / Signal / Pipe

Rete implementa um pipeline tipado de eventos/middleware. A ideia pode inspirar hooks do K-Tools:

```text
before_node_execute
node_progress
node_completed
node_failed
artifact_created
run_completed
```

Subscribers conseguem observar/transformar eventos sem acoplar todas as partes do produto.

### Socket / Input / Output / Control

O preset clássico distingue:

- Socket;
- Input;
- Output;
- Control;
- Node;
- Connection.

Um input também pode possuir control inline. Isso é uma ideia de UX importante:

```text
sem conexão no input → mostrar campo/config control
com conexão          → valor vem do upstream
```

Exemplo: o node `Converter áudio` pode oferecer um select “Formato: M4A” localmente, mas aceitar esse valor por conexão no futuro.

### Por que não usar Rete + xyflow juntos como dois engines de UI

Rete tem seu próprio modelo/plugin ecosystem. O K-Tools já possui um modelo de workflow próprio e xyflow oferece a camada visual necessária. Introduzir Rete como segundo graph owner criaria duas fontes de verdade.

Recomendação: absorver os conceitos e, se algum pequeno módulo MIT for excepcionalmente útil, avaliar isoladamente — não adotar Rete como runtime paralelo.

---

## 5.6. LiteGraph.js — uma boa fonte de resiliência de formato

LiteGraph concentra grafo e canvas em um grande runtime JS, uma arquitetura menos alinhada ao K-Tools atual. Ainda assim há uma ideia excelente.

### Missing-node placeholder

Ao carregar um workflow cujo node type não existe, LiteGraph cria um node de substituição, preserva sua serialização original e marca erro em vez de destruir os dados.

K-Tools deve adotar isso.

Exemplo:

```text
Workflow usa: community.audio.super-denoise@2
Pack não instalado

NÃO:
  falhar parse e perder o node

SIM:
  MissingNodePlaceholder
  ├── mantém type/version/config/position/edges
  ├── mostra “Node Pack ausente”
  ├── bloqueia execução daquele caminho
  └── oferece localizar/instalar/migrar pack
```

Isso se torna essencial quando workflows sobrevivem a upgrades ou são compartilhados entre máquinas.

### Serialização versionada

O grafo serializado possui nodes, links, groups, config, extra e version. O K-Tools também deve possuir `schemaVersion` explícito e migration pipeline.

### O que não adotar

O engine de execução do LiteGraph tolera ciclos de maneira que não corresponde à semântica DAG atual do K-Tools. Não devemos importar esse comportamento. Cycles só entram quando tivermos semântica explícita de loop/control-flow, não como acidente topológico.

---

## 5.7. xyflow / React Flow — melhor base concreta para o canvas

xyflow é diferente dos demais: não tenta ser nosso workflow engine. Isso é justamente sua vantagem.

### O que ele resolve

O source já cuida de problemas de UI complexos:

- viewport/pan/zoom;
- seleção;
- node lookup;
- parent/subflow lookup;
- connection lookup;
- handles;
- conectar/reconectar;
- drag interactions;
- bounds;
- incomers/outgoers;
- connected edges;
- fit view;
- custom nodes e edges.

### Handles e typed validation

`Handle` aceita `isValidConnection` e mantém visual state de connection/validity.

Isso encaixa perfeitamente em nosso `ktools-core`:

```text
usuário arrasta AUDIO output → PDF input
       ↓
frontend chama validator compatível com core
       ↓
edge fica inválido imediatamente
       ↓
core continua sendo a autoridade no save/run
```

A UI pode dar feedback instantâneo sem duplicar a verdade do runtime.

### Decisão recomendada

Usar `@xyflow/react` **como dependência**, não vendorizar/forkar source agora.

O K-Tools deve controlar:

- tipos semânticos;
- node schema;
- layout de node;
- palette;
- inspector;
- persistence;
- validation;
- runtime;
- run state.

xyflow controla apenas a interação gráfica.

### Evidência de adequação

Além do próprio source, o Activepieces estudado usa `@xyflow/react` no builder real, com custom nodes, edges, minimap, context menu, selection e widgets. Isso reduz o risco da escolha para nossa classe de produto.

---

# 6. Padrões que aparecem repetidamente

Quando arquiteturas independentes convergem, a convergência é uma evidência forte de design.

## 6.1. Editor separado do runtime

Observado em graus diferentes em Node-RED, Activepieces, n8n, Rete e xyflow.

**Decisão para K-Tools: manter.**

```text
Frontend/editor
     ↓ contracts/API
ktools-core
     ↓
runners/adapters
```

## 6.2. Registry/plugin contract

Node-RED registry, Activepieces Pieces, ComfyUI custom nodes e n8n node types mostram que extensibilidade deve entrar pelo registry, não por `if/elif` central infinito.

## 6.3. Metadata e runtime separados

O editor precisa saber título, category, ports e config schema sem importar toda implementação pesada do node.

## 6.4. Validation antes de trabalho caro

ComfyUI/n8n/Rete e nossa fundação apontam para fail-fast de graph/type/config.

## 6.5. Run state é um domínio próprio

Activepieces, ComfyUI e n8n não tratam execução como simples `for node in graph`. Existe run identity, node state, output, status, duration e error.

## 6.6. Subflow/workflow reutilizável

Node-RED é a referência mais explícita. K-Tools deve permitir workflow → reusable node/tool.

## 6.7. Cache/checkpoint é necessário para cargas caras

ComfyUI e Activepieces tornam isso especialmente evidente. Vídeo/áudio/PDF de K-Tools têm custo suficiente para justificar a fundação desde cedo.

## 6.8. UI precisa mostrar runtime state

n8n, Activepieces e ComfyUI apresentam execução como algo observável, não como um spinner global.

---

# 7. Arquitetura alvo refinada do K-Tools Neo

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         K-TOOLS DESKTOP                              │
│                                                                     │
│  Tools     Workflows     Runs     Artifacts     Node Packs          │
│                    React + TypeScript                               │
│                       @xyflow/react                                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ typed API / local bridge
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         K-TOOLS CORE                                │
│                                                                     │
│ Workflow Model / Schema                                             │
│ Registry / Node Pack Registry                                       │
│ Validation / Compiler                                               │
│ Execution Scheduler                                                 │
│ Run Journal                                                         │
│ Artifact Store + Provenance                                         │
│ Cache / Signatures                                                  │
│ Event + Progress Bus                                                │
│ Persistence / Migrations                                            │
└─────────────┬───────────────────┬─────────────────────┬─────────────┘
              │                   │                     │
              ▼                   ▼                     ▼
     Python official nodes   Node.js runners       CLI/adapters
              │                   │                     │
              │                   │               ┌─────┴─────────┐
              │                   │               │               │
              ▼                   ▼               ▼               ▼
      file/audio/video       future JS packs   XCursos       yt-dlp-tui

Persistence local sugerida para V1/V2:
SQLite + Artifact filesystem store
```

---

# 8. Evolução recomendada dos contratos atuais

O `NodeDefinition` atual é propositalmente mínimo. Não deve virar um objeto gigante de uma vez. Evoluir somente quando cada campo possuir consumidor real.

## 8.1. Próximos campos de alto valor

Conceitualmente:

```yaml
id: audio.extract
version: 1
name: Extrair áudio
category: Audio

inputs:
  video:
    dataType: video
    required: true

outputs:
  audio:
    dataType: audio
    required: true

configSchema:
  format:
    type: enum
    values: [wav, flac, m4a]
    default: wav

execution:
  runner: python
  idempotency: deterministic
  cache: auto
  sideEffects: false
  cancellable: true
  progress: true

requirements:
  - ffmpeg
```

### Não colocar prematuramente

Não adicionar autenticação, webhook, AI tool, sandbox, retry e 40 flags antes de existir um node que realmente precise delas. n8n mostra o destino de maturidade, não o tamanho correto da V1.

---

# 9. Data Flow e Control Flow devem ser separados

A primeira fundação é um DAG de dados. Isso é correto.

Mais tarde, a linguagem precisa diferenciar:

## Data Flow

```text
Video --video--> ExtractAudio --audio--> Denoise
```

## Control Flow

```text
Start → If
        ├─ true  → A
        └─ false → B
```

Não devemos representar branch apenas fingindo que `EVENT` é um arquivo/dado comum. Recomenda-se uma camada explícita de edge/port kind:

```text
PortKind.DATA
PortKind.CONTROL
PortKind.ERROR    # futuro
```

`DataType` continua descrevendo o payload dentro de DATA.

---

# 10. Modelo de execução recomendado

## 10.1. Fase de compile/validation

Antes de executar:

1. workflow schema version válido;
2. nodes únicos;
3. node types + versions disponíveis;
4. ports existem;
5. types compatíveis;
6. required inputs conectados/preenchidos;
7. cardinalidade de connections válida;
8. ciclo acidental ausente;
9. config schema válido;
10. runtime requirements disponíveis.

## 10.2. Fase de run

Cada execução ganha `run_id` e cada node ganha estado persistível.

Estados recomendados:

```text
PENDING
READY
RUNNING
CACHED
SUCCEEDED
FAILED
SKIPPED
CANCELLED
PAUSED       # quando waitpoints existirem
```

## 10.3. Partial execution

Planejar desde cedo, implementar depois da persistence/cache:

- node selecionado + ancestors necessários;
- `run until here`;
- outputs cached/materializados como boundary de reuso.

## 10.4. Cancelamento

Media processing pode durar minutos/horas. Runner API deve evoluir para cancelamento cooperativo e cleanup de temporários.

---

# 11. Run Journal + Artifact: a combinação central para confiabilidade

O `Artifact` atual já é uma boa semente. Ele deve ser complementado por um run journal.

## Artifact futuro

```text
Artifact
├── id
├── semantic type
├── uri/path
├── content hash
├── size
├── mime
├── metadata
├── produced_by_node
├── run_id
├── created_at
└── lifecycle/cache flags
```

## NodeRun futuro

```text
NodeRun
├── node_id
├── node_type/version
├── status
├── started_at
├── finished_at
├── duration
├── progress
├── input artifact refs
├── output artifact refs
├── cache_key
├── cached_from
└── error
```

Com isso, “retomar workflow” deixa de ser uma heurística baseada na existência de arquivos e passa a ser uma operação audível.

---

# 12. Cache incremental

Inspirado conceitualmente em ComfyUI, mas implementado no nosso domínio.

## Cache key sugerida

```text
sha256(
  node.type
  + node.version
  + canonical_json(config)
  + ordered(input artifact hashes / scalar values)
  + relevant engine/runtime signature
)
```

## Regras

- node determinístico: cache permitido;
- node com side effects: cache desabilitado por default;
- node marcado `always_run`: nunca cache;
- mudança de node version invalida cache;
- alteração de upstream content invalida downstream;
- mover node visualmente não invalida cache;
- trocar `node_id` sem mudar semântica não deveria necessariamente invalidar cache.

---

# 13. Workflows como nodes e Tools

Unificar duas ideias observadas:

- Node-RED: subflow vira node;
- n8n: tool sintética não possui implementação própria.

## K-Tools

Um workflow salvo pode ganhar uma interface pública:

```text
WorkflowDefinition
  + exposed inputs
  + exposed outputs
  + metadata
        ↓
ReusableWorkflowNode
```

O mesmo workflow pode ganhar uma experiência simplificada:

```text
WorkflowDefinition
  + presets
  + form simplificado
        ↓
ToolDefinition
```

Logo:

```text
Capability Node(s)
      ↓ compose
Workflow
      ├── usado no canvas
      ├── encapsulado como Node
      └── apresentado como Tool
```

**Business logic continua em um só lugar.**

---

# 14. Node Packs

Estrutura recomendada para o médio prazo:

```text
node-packs/
├── core-files/
│   ├── manifest.yaml
│   ├── nodes/
│   └── tests/
├── audio/
├── video/
├── image/
├── pdf/
└── integrations/
```

Manifest conceitual:

```yaml
id: ktools.audio
version: 1.0.0
apiVersion: 1
name: K-Tools Audio
runtime: python
nodes:
  - audio.extract
  - audio.merge
  - audio.normalize
requirements:
  - ffmpeg
```

### Compatibilidade

`node type + node version + Node Pack API version` deve ser tratado como contrato. Workflows antigos não podem silenciosamente mudar de semântica quando um pack é atualizado.

---

# 15. Workflow schema e migrations

Aprendizado de LiteGraph + sistemas maduros:

Todo workflow persistido deve conter `schemaVersion`.

Exemplo:

```json
{
  "schemaVersion": 1,
  "id": "mega-podcast",
  "revision": 7,
  "nodes": [],
  "edges": [],
  "ui": {}
}
```

Separar:

- **semantic workflow state** — executável;
- **UI state** — posição, zoom, groups, notes.

O engine não deveria rejeitar workflow apenas porque metadata visual é desconhecida.

## Missing node preservation

Loader deve preservar node desconhecido integralmente e produzir placeholder. Nunca descartar config/edges de um node apenas porque o pack não está presente.

---

# 16. Revision e diff

Inspirado em Node-RED:

Cada save relevante incrementa `revision`.

O sistema consegue classificar:

```text
added nodes
removed nodes
config-changed nodes
rewired nodes
UI-only changes
```

Uso no K-Tools:

- dirty state do editor;
- autosave;
- cache invalidation;
- incremental validation;
- migration audit;
- future collaborative/agent edits;
- histórico e rollback.

---

# 17. UX recomendada

A síntese de n8n, Activepieces, Node-RED e xyflow sugere quatro regiões estáveis.

```text
┌──────────────────────────────────────────────────────────────┐
│ K-Tools Neo           Workflow name          Save     ▶ Run │
├──────────────┬─────────────────────────────┬─────────────────┤
│ Palette      │                             │ Inspector       │
│ Search       │           Canvas            │                 │
│ Categories   │                             │ Config          │
│ Nodes        │                             │ Inputs          │
│ Templates    │                             │ Outputs         │
│              │                             │ Validation      │
├──────────────┴─────────────────────────────┴─────────────────┤
│ Run / Timeline / Logs / Artifacts / Errors / Performance    │
└──────────────────────────────────────────────────────────────┘
```

## 17.1. Palette

- search-first;
- categories;
- recentes/favoritos futuramente;
- drag-to-canvas;
- missing dependencies marcadas antes da inserção.

## 17.2. Node

Deve mostrar pouco quando idle e mais quando existe estado relevante.

Idle:

```text
┌──────────────────┐
│ 🎵 Extrair áudio │
└──────────────────┘
```

Running:

```text
┌──────────────────┐
│ 🎵 Extrair áudio │
│ 73% · 00:21      │
└──────────────────┘
```

Finished/cache/error devem ser distinguíveis.

## 17.3. Inspector

A ideia Input / Settings / Output do n8n deve ser adaptada.

Para um node selecionado:

- Settings;
- Inputs e origem dos values;
- Outputs/artifacts da última execução;
- Logs;
- Timing;
- Cache provenance;
- Validation issues.

## 17.4. Handle validation

Usar `isValidConnection` de xyflow para feedback instantâneo e revalidar no core ao salvar/executar.

## 17.5. Context menu e keyboard

Activepieces/n8n mostram valor de:

- context menu;
- multi-select;
- delete/duplicate;
- fit view;
- minimap;
- Escape para fechar creator/panels;
- drag/drop claro;
- read-only run/history view.

---

# 18. Separar editor graph de execution graph

A UI precisa de elementos que não executam:

- notes;
- groups;
- comments;
- selection;
- collapsed containers;
- viewport.

Portanto:

```text
EditorDocument
├── WorkflowDefinition     # semantic/executable
└── PresentationState      # xyflow/UI only
```

Nunca deixar posição X/Y alterar cache/execution semantics.

---

# 19. Integração com XCursos e yt-dlp-tui

O estudo reforça que não devemos portar seus internals para nodes gigantes.

## Primeiro boundary

```text
NodeDefinition
    ↓
Adapter
    ↓ process/API contract
Imported application
```

Exemplos futuros:

```text
xcursos.download_course
youtube.download
```

A primeira integração pode expor operações grandes e estáveis. Só decompor em nodes menores quando existir valor de composição e contrato nativo seguro.

Isso preserva retry, diagnostics, auth e lifecycle já maduros nos subsistemas.

---

# 20. Segurança e confiança de Node Packs

## Fase inicial

Somente:

```text
OFFICIAL_TRUSTED
```

Node Packs entram no repositório/release e passam pela mesma suíte.

## Futuro

Possíveis tiers:

```text
OFFICIAL_TRUSTED
LOCAL_TRUSTED
COMMUNITY_SANDBOXED
UNTRUSTED_CODE
```

Um futuro marketplace de plugins não deve executar código arbitrário no mesmo processo que gerencia arquivos do usuário sem uma threat model explícita.

---

# 21. O que explicitamente não devemos fazer

1. **Não forkear n8n para transformá-lo em K-Tools.** Licença e domínio arquitetural criariam dependência desnecessária.
2. **Não copiar ComfyUI engine/cache.** Reimplementar os conceitos por causa da GPL e do domínio diferente.
3. **Não usar React Flow como engine.** xyflow é presentation/interaction.
4. **Não usar Rete e xyflow simultaneamente como dois owners do grafo.**
5. **Não migrar todas as ferramentas antes da fundação de packs/persistence.**
6. **Não colocar persistence dentro do frontend.**
7. **Não passar apenas path string entre todos os nodes para sempre.** Artifact provenance precisa crescer.
8. **Não tratar loops como cycles acidentais do DAG.** Control flow deve ganhar semântica própria.
9. **Não criar cada Tool tradicional com uma implementação paralela.**
10. **Não habilitar plugins comunitários arbitrários antes de isolamento/permission model.**
11. **Não inventar um canvas do zero.** O custo está resolvido por xyflow.
12. **Não copiar um sistema cloud distribuído inteiro para um desktop local.** Absorver boundaries, não a infraestrutura desnecessária.

---

# 22. Decisões recomendadas após este estudo

## DR-01 — Manter `ktools-core` como autoridade de workflow/runtime

**Recomendação: ACCEPT.**

Nenhum third-party editor/engine se torna fonte de verdade.

## DR-02 — xyflow como leading canvas implementation

**Recomendação: ACCEPT FOR UI SPIKE.**

Usar `@xyflow/react` no primeiro editor real. O desktop host ainda precisa de spike próprio.

## DR-03 — Node Pack contract antes de marketplace/plugin loading

**Recomendação: ACCEPT.**

Primeiro provar packs oficiais estáticos. Dynamic/community install depois.

## DR-04 — Introduzir Run Journal + persistence antes de workflows caros em produção

**Recomendação: ACCEPT.**

Sem isso, crash/retry pode repetir processamento caro e tornar Run history pouco confiável.

## DR-05 — Cache de artifacts por assinatura semântica

**Recomendação: ACCEPT AS TARGET, IMPLEMENT AFTER JOURNAL/PERSISTENCE.**

## DR-06 — Workflow → reusable node e Workflow → Tool

**Recomendação: ACCEPT AS PRODUCT INVARIANT.**

A implementação vem depois que exposed input/output contracts existirem.

---

# 23. Sequência de implementação recomendada

A pesquisa modifica a ordem ótima de algumas etapas.

## Milestone A — Foundation atual

```text
Node/Port types
Registry
DAG validation/execution
Artifact seed
CLI
CI
```

Status: candidate PR #1.

## Milestone B — Primeiro Node Pack real

Objetivo: provar que uma capacidade existente pode sair do legado e operar tanto diretamente quanto dentro de workflow.

Preferência: uma capacidade local, determinística e de baixo risco antes de integrações web complexas.

Entregas:

- Node Pack manifest mínimo;
- 2–4 nodes reais;
- config schema mínimo;
- Artifact real;
- testes de integração com filesystem/runtime.

## Milestone C — Run Journal + SQLite + Artifact Store

Antes de transformar pipelines pesados em UX principal.

Entregas:

- Workflow persistence;
- Run/NodeRun persistence;
- Artifact content hash/provenance;
- crash-safe checkpoints básicos;
- schema migrations.

## Milestone D — Cache incremental

Implementar signature + cache policy em nodes determinísticos.

## Milestone E — UI spike React + xyflow

Não construir o produto inteiro. Provar:

- carregar schema do core;
- palette;
- custom node;
- typed handles;
- invalid edge feedback;
- inspector;
- run event/progress;
- save/load;
- 100/500 nodes como benchmark visual básico;
- packaging dentro do desktop-host candidato.

## Milestone F — Desktop shell

Escolher host somente com spike:

- Tauri;
- Electron;
- ou outra solução que preserve integração local e subprocessos.

## Milestone G — Imported app adapters

- yt-dlp-tui;
- XCursos Runner.

## Milestone H — Tools as workflow projections

Criar primeiras telas simples sobre workflows/templates e aposentar lógica duplicada do monólito incrementalmente.

## Milestone I — Control flow

- branch;
- loop;
- error path;
- wait/delay quando houver caso real.

## Milestone J — Agent-first authoring

Somente depois que Node schemas, validation e workflow format estiverem estáveis o bastante para IA produzir grafos verificáveis.

---

# 24. Primeiro experimento recomendado após a Foundation

Criar o primeiro `Node Pack` oficial e provar a invariável:

> **a mesma capability é executável por chamada direta e por workflow sem duplicação de business logic.**

Critério mínimo:

```text
Capability real
   ├── API direta / future Tool surface
   └── Node handler
          ↓
      mesma função de domínio
```

O experimento deve incluir Artifact real e integration test no filesystem.

Não começar pela UI porque ela esconderia a pergunta arquitetural mais importante: o runtime é realmente composável sem depender do canvas?

---

# 25. Hipóteses futuras que ainda exigem spikes

## H-UI-01 — React + xyflow funciona bem dentro do desktop host escolhido

Ainda não provado no ambiente final.

**Experimento:** desktop shell mínimo + canvas de 100/500 nodes + drag/connect/inspector.

## H-PERSIST-01 — SQLite é suficiente como owner local de workflow/run state

Altamente plausível, ainda não validado no K-Tools.

**Experimento:** restart test com workflow, run, node journal e artifacts.

## H-RUNNER-01 — Python orchestration + subprocess adapters é suficiente para workloads mistos

Aceito para fundação, não provado sob vários jobs longos/concurrent.

**Experimento:** pipeline com Python + FFmpeg + Node subprocess, cancel/restart/error propagation.

## H-PACK-01 — Um manifest único consegue descrever nodes Python e adapters Node.js

Precisa ser testado antes de fixar schema público.

---

# 26. Checklist para qualquer reciclagem futura de source externo

Antes de copiar/adaptar um trecho:

1. identificar arquivo exato + snapshot/hash;
2. verificar licença daquele arquivo/diretório;
3. verificar se depende de código com licença diferente;
4. provar que adaptar é melhor do que implementar um módulo pequeno próprio;
5. preservar notices/atribuição exigidos;
6. registrar origem no arquivo e em `THIRD_PARTY_NOTICES` quando aplicável;
7. criar teste que descreva nosso contrato, não o comportamento acidental do upstream;
8. evitar internal APIs sem estabilidade;
9. preferir dependency package quando existe API pública estável;
10. manter K-Tools contract independente para permitir troca do fornecedor.

---

# 27. Ranking prático para o K-Tools

## Em valor arquitetural

1. **Node-RED** — boundaries e lifecycle.
2. **Activepieces** — extensibilidade + durability.
3. **ComfyUI** — execução local pesada + cache/progress.
4. **n8n** — contract richness + UX.
5. **xyflow** — implementação concreta do canvas.
6. **Rete.js** — abstrações elegantes de visual programming.
7. **LiteGraph.js** — resiliência de serialization/legacy patterns.

## Em código que faz sentido incorporar como dependência

1. **xyflow** — sim, forte candidato.
2. demais — não como fundamento inteiro; usar contratos próprios e seleção pontual.

## Em donor code potencialmente reutilizável

1. Activepieces MIT areas — seletivamente.
2. Node-RED Apache areas — seletivamente.
3. Rete/LiteGraph MIT — somente quando um módulo específico superar nossa implementação própria.
4. n8n / ComfyUI — inspiração, não donor code sob a estratégia atual.

---

# 28. Síntese final

O estudo reforça, em vez de derrubar, a arquitetura iniciada na Foundation PR.

A decisão mais importante já estava correta:

> **Runtime primeiro, canvas depois.**

Mas agora temos uma visão mais precisa do que esse runtime deverá se tornar:

```text
Typed Graph
  + Versioned Node Registry
  + Node Packs
  + Run Journal
  + Artifact Provenance
  + Semantic Cache
  + Event/Progress Bus
  + Runners/Adapters
  + Workflow Revisions/Migrations
           ↓
      múltiplos clientes
           ├── Visual Workflow Editor (@xyflow/react)
           ├── Simple Tools
           ├── CLI
           ├── Scheduler
           └── AI Agent
```

O K-Tools não deve copiar n8n, ComfyUI, Node-RED ou Activepieces. Ele deve **absorver as soluções que sobreviveram em vários desses sistemas e implementá-las de acordo com seu próprio domínio local-first de arquivos e mídia**.

O resultado almejado deixa de ser “um programa com muitas ferramentas” e passa a ser:

> **uma linguagem operacional visual e programática para transformar arquivos, mídia, informação e ações locais, em que cada capacidade é componível e cada execução é observável, recuperável e reutilizável.**

---

# 29. Source map para futuras auditorias

Use estes caminhos dentro dos snapshots estudados para reabrir decisões com evidência:

### n8n
- `packages/workflow/src/workflow.ts`
- `packages/workflow/src/interfaces.ts`
- `packages/cli/src/node-types.ts`
- `packages/core/src/execution-engine/workflow-execute.ts`
- `packages/frontend/editor-ui/src/features/shared/nodeCreator/components/NodeCreator.vue`
- `packages/frontend/editor-ui/src/features/ndv/shared/views/NodeDetailsView.vue`
- `packages/frontend/editor-ui/src/features/workflows/canvas/components/elements/nodes/render-types/CanvasNodeDefault.vue`
- `packages/frontend/editor-ui/src/features/workflows/canvas/components/elements/nodes/render-types/parts/CanvasNodeStatusIcons.vue`

### Activepieces
- `docs/install/architecture/overview.mdx`
- `docs/install/architecture/durable-execution.mdx`
- `docs/install/architecture/waitpoints.mdx`
- `docs/install/architecture/sandboxing.mdx`
- `packages/pieces/framework/src/lib/piece.ts`
- `packages/core/execution/src/lib/flow-run/execution/execution-journal.ts`
- `packages/server/engine/src/lib/handler/flow-executor.ts`
- `packages/web/src/app/builder/flow-canvas/index.tsx`
- `packages/web/src/app/builder/flow-canvas/nodes/step-node/index.tsx`

### Node-RED
- `packages/node_modules/@node-red/runtime/lib/nodes/index.js`
- `packages/node_modules/@node-red/registry/lib/index.js`
- `packages/node_modules/@node-red/runtime/lib/flows/Flow.js`
- `packages/node_modules/@node-red/runtime/lib/flows/index.js`
- `packages/node_modules/@node-red/runtime/lib/flows/util.js`
- `packages/node_modules/@node-red/registry/lib/subflow.js`

### ComfyUI
- `nodes.py`
- `execution.py`
- `comfy_execution/caching.py`
- `comfy_execution/progress.py`

### Rete.js
- `src/editor.ts`
- `src/scope.ts`
- `src/presets/classic.ts`

### LiteGraph.js
- `src/litegraph.js`

### xyflow
- `packages/react/src/types/store.ts`
- `packages/react/src/components/Handle/index.tsx`
- `packages/system/src/utils/graph.ts`

---

# 30. Reopening rules

Reabrir recomendações deste estudo quando houver mudança material, por exemplo:

- novo snapshot/licença relevante;
- xyflow não atender performance ou desktop packaging no spike;
- ktools-core demonstrar incompatibilidade com o modelo de Node Packs;
- runtime Python se tornar bottleneck provado;
- distribuição/licenciamento do K-Tools mudar;
- necessidade concreta de community code sandboxing;
- control flow exigir modelo incompatível com o DAG atual.

Não reabrir apenas porque um novo agente prefere outra biblioteca sem evidência nova.
