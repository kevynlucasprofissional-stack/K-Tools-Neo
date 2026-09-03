# K-Tools Neo — Product Roadmap

Status: **ACTIVE / CANONICAL SEQUENCING GUIDE**
Owner: project owner + ChatGPT while Solo Development Mode is active
Execution truth: current `main`, tests and hosted CI

## Product destination

K-Tools Neo becomes one integrated local-first product where every reusable operation is a capability/node, simple Tools and visual Workflows share implementation owners, expensive/local work is observable/durable/diagnosable/conservatively reusable, official Node Packs cover local capability families, imported applications are adapted rather than rewritten, the UI is a client of stable runtime contracts, and later AI agents compose through the same catalog.

The long-horizon extension of that destination is an **agent-native System Capability Layer**: K-Tools exposes deterministic, typed, inspectable computer capabilities to humans, workflows and AI agents through the same canonical owners. K-Tools does not become the conversational agent, planner or product-level orchestrator; it becomes a reliable execution substrate that agent systems can call.

---

## M0 — Platform Foundation
Status: **RESOLVED / PROMOTED**

## M1 — First real Node Pack
Status: **RESOLVED** — `packages/ktools-json/`.

## M2 — Durable Execution V1
Status: **RESOLVED** — optional RunJournal + Memory/SQLite lifecycle history.

## M3 — Diagnostics, Structured Logging + Support Bundle
Status: **RESOLVED / PROMOTED** — structured/share-safe diagnostics, support bundles and native/subprocess evidence boundaries.

Final closure run: `33557338124` on `5e1e46714aaefe0827c96a415d7d58d57790a187`.

## M4 — Artifact Lifecycle + Recovery + Semantic Cache V1
Status: **RESOLVED / PROMOTED** — strong Artifact validity/provenance, explicit PURE/NEVER policy, persistent fail-open cache, CACHED lifecycle and conservative restart reuse.

Formal promotion `b09e6ac62fa74e3e1a22e7cced0a472af50285b1` passed run `33626260487`.

---

## M5 — Official local Node Packs

Status: **RESOLVED / PROMOTED**

Capability families:

- Files/Folders;
- Text;
- Documents/Images/PDF;
- Media.

### Slice 1 — Text Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered ordered FILE_SET, PURE `files.literal`, canonical `packages/ktools-text/`, characterized Markdown/TXT merge, `text.merge.files` NEVER, direct/workflow equivalence, ArtifactRegistry proof, centralized local URI parsing and hosted Text smoke.

Promotion `958d5bf563cda21673d69865d1508831c599c006` / `33630159514`; memory closure `f759e1712d5cf73103cfc37f8a7b7f77ecb6a388` / `33631040505`.

### Slice 2 — PDF Merge Node Pack V1

Status: **RESOLVED / PROMOTED**

Delivered `packages/ktools-pdf/`, `pypdf>=5,<7`, checked reading, ordered page merge, atomic publication, direct API, `pdf.merge.files: FILE_SET -> PDF` v1 NEVER, PDF Artifact provenance/snapshots, cache/publication proof and fail-closed protected/encrypted behavior.

Terminal closure `e3a3934aada29e185de7da18cf413ceaa3c299e8` / `33651923578`, 5/5.

### Slice 3 — PDF Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered `file.literal`, canonical balanced PDF split, `pdf.split.parts: FILE -> FILE_SET` v1 NEVER, contiguous balanced planning, collision-safe per-part atomic publication, explicit partial-set failure, PDF Artifact metadata/snapshots, cache/republication proof and hosted split→merge composition.

Terminal closure `a26dfcee626eedc27366dfec93be68503343941a` / `33656157870`, 5/5.

### Slice 4 — Text Split Node V1

Status: **RESOLVED / PROMOTED**

Delivered split-specific decode policy, balanced line-unit planning, canonical split owner, UTF-8 collision-safe per-output publication, `text.split.parts: FILE -> FILE_SET` v1 NEVER, Artifact metadata/snapshots, cached-source/republication proof, direct/workflow equivalence and hosted split→merge composition.

Evidence: spec `e6b4f5c207a39fe70820939d8c7972833e6cc9fa` / `33656954591`; RED `14a950d8d1b23412d7ba27dace66759d8ae2b37e` / `33657352636`; GREEN `87558e8194692c045bdd95780fe05beb0f436e3a` / `33657882057`; hardened `0630e63d87ae1c452c3d886a2dbab8d994bb3b23` / `33660594733`; terminal closure `4a52bef50653aa11878351645d122d0c0ab52343` / `33661273251`, 5/5.

### Slice 5 — Mixed Document Split Orchestrator V1

Status: **RESOLVED / PROMOTED**

Delivered `packages/ktools-documents` as orchestration-only owner for `.md/.txt/.pdf`: ordered dispatch to canonical Text/PDF splitters, weighted progress, per-source continuation, partial-success JSON report, zero-success failure, child Artifact preservation, current provenance/snapshots, `document.split.files: FILE_SET -> FILE_SET + JSON` v1 NEVER, cache/republication proof and hosted mixed workflow smoke.

Evidence: spec `c3fe4b98bc923eeb02a0b47877262bcbf83620d9` / `33661964413`; RED `3a60b6b4e73cf40d14f3da8b2de9d862402f76db` / `33662320157`; GREEN `bde8b3789d86959b1218969510ed68aed14d410e` / `33664355218`; terminal closure `3d2d955df71cd65162839a5ac2c1335e5b5a4518` / `33665431920`, 5/5.

Canonical batch owner: `packages/ktools-documents`; primitive owners remain `ktools-text`/`ktools-pdf`.

### Slice 6 — Image Safety Foundation + WebP→PNG V1

Status: **RESOLVED / PROMOTED**

Fresh discovery selected WebP→PNG over Images→PDF and Files/Folders because it established the reusable image-safety foundation with the smallest bounded semantic surface.

Delivered canonical `packages/ktools-images`, `Pillow>=12,<13`, 80M-pixel/decompression-bomb policy, EXIF normalization, frame-0 behavior, alpha-preserving PNG normalization, collision-safe per-output temp→promote publication, `image.webp_to_png: FILE_SET -> FILE_SET` v1 NEVER, IMAGE Artifacts, strong snapshots/cache-republication proof and real RGB/RGBA hosted smoke.

Evidence: spec `bd454050c182aec74c8f45d529ab2e0377cb3ad3` / `33666227293`; RED `311c82a26b5ef64a7c80299b9253829a8e98cfbc` / `33667224304`; GREEN `670a503d822ba100a66eea3ba0b31cfe39692984` / `33667874076`; terminal closure `9b9fc57bd4bfb28d7e23637651a30182ce6f8828` / `33668942264`, 5/5.

ADR: `docs/decisions/ADR-028-IMAGE-SAFETY-WEBP-PNG-V1.md`.
Canonical owner: `packages/ktools-images`. Stable-GUI WebP→PNG is compatibility debt.

### Slice 7 — Shared Image Reader + Images→PDF V1

Status: **RESOLVED / PROMOTED**

Fresh terminal-main discovery compared Images→PDF with bounded Files/Folders. Images→PDF won because the Slice-6 safety foundation reduced the remaining surface to a bounded aggregate-image/PDF contract, while Files/Folders still had overlapping legacy traversal/report owners with unresolved cross-platform semantics.

Delivered:

- `ktools_images.reader` as the one guarded Pillow decode / bomb / first-frame / EXIF owner shared by WebP→PNG and Images→PDF;
- WebP→PNG refactor with no observed behavior regression;
- existing JPG/JPEG/PNG/WebP/BMP/TIF/TIFF filtering in compatible-source order;
- one normalized first frame per source;
- RGB pages and alpha/palette transparency composited over white;
- one singular aggregate PDF, same-directory temp-written and promoted only after successful serialization;
- previous destination preservation on handled failure;
- canonical Images→PDF writer shared by direct API and node;
- `image.files_to_pdf: FILE_SET -> PDF`, v1 NEVER;
- one PDF Artifact with ordered metadata/provenance and strong snapshot;
- cached source without skipped publication;
- hosted `files.literal -> image.files_to_pdf` smoke independently reopened with `pypdf`;
- ownership-test hardening proving decode policy resides in the shared reader.

Evidence:

- spec `ae617e948d5549e3dbca1dbe8d5de19c16555535` / `33670517542`, 5/5;
- RED `9ac1c9bcb2974e8d4daf70844a14198e35fe54db` / `33671061268`;
- GREEN `309863ac475330448e6fc44dbdf305482528689e` / `33671740134`, 5/5;
- audited hardening `1d9afc40bb7adbb511a1869d25b18058782bcbad` / `33672387118`, 5/5;
- synchronized terminal memory closure `c3585f5b7f478f53e1c5ef63f72a7b49fbb0cdea` / `33674308145`, 5/5.

ADR: `docs/decisions/ADR-029-IMAGES-TO-PDF-NODE-V1.md`.
Canonical owner remains `packages/ktools-images`; stable-GUI Images→PDF is compatibility debt.

### Slice 8 — Folder Scan Node V1

Status: **RESOLVED / PROMOTED**

Delivered:
- Canonical traversal ownership in `packages/ktools-filesystem`.
- `folder.literal: -> FOLDER`, v1 NEVER.
- `folder.scan_files: FOLDER -> FILE_SET + JSON`, v1 NEVER.
- Security constraints rejecting root symlinks and skipping nested symlinks to prevent escapes.
- Configurable recursion, hidden-item semantics, and extension filtering.
- Deterministic alphabetical order by relative path.
- OSErrors accumulation into a JSON report, allowing partial success.

Evidence:
- spec `a5e65595fa70f7f313d55f61fa7cf643b205d74f`
- RED `df1f94b52f409fd626ec652b3a403092939c9819`
- GREEN `1fd2091` / `33702432021` 5/5

ADR: `docs/decisions/ADR-030-FOLDER-SCAN-NODE-V1.md`.
Canonical owner remains `packages/ktools-filesystem`; legacy stable GUI scanners overlap is compatibility debt.

### Slice 9 — Media Extract Audio Node V1

Status: **RESOLVED / PROMOTED**

Fresh terminal-main discovery compared Media capabilities with document/system utils. Media Extract Audio won to establish the ktools-media package boundary, the imageio-ffmpeg cross-platform dependency, and the diagnostic subprocess wrapper required for M3 compliance.

Delivered:
- packages/ktools-media/ with FFmpeg execution capability (media.extract_audio).
- ContextVar-based `record_subprocess` inside ktools_core.diagnostics to capture subprocess stdout/stderr and exit codes reliably across functional boundaries.
- Atomic artifact publication.
- GitHub Actions CI matrix integration.

### Slice 10 — Media Convert Audio Node V1

Status: **RESOLVED (ADR-032)**

- Developed `media.convert_audio` node in `ktools-media`.
- Atomic `.tmp` to final path replacements.
- Handled ContextVar diagnostics leaks in test engine.

### Slice 11 — Media Split Audio Node V1

Status: **RESOLVED (ADR-033)**

- Implemented `media.split_audio` using `ffprobe` to determine duration and loop `ffmpeg` cuts.
- Returns `FILE_SET` of individual piece artifacts.

### Slice 12 — Media Join Audios Node V1

Status: **RESOLVED (ADR-034)**

- Implemented `media.join_audios`.
- Introduced WAV normalization for disparate inputs.

### Slice 13 — Media Compress Video Node V1

Status: **RESOLVED (ADR-035)**

- Implemented `media.compress_video` using FFmpeg `libx264`.

### Slice 14 — Media WebP to PNG Node V1

Status: **RESOLVED (ADR-036)**

- Implemented `media.webp_to_png` using Pillow.
- Handles animation, EXIF rotation, transparency.

### Slice 15 — PDF Merge and Split Nodes V1

Status: **RESOLVED (ADR-037)**

- Implemented `pdf.merge` (FILE_SET -> FILE) and `pdf.split` (FILE -> FILE_SET) using pypdf.

---

## M5 Extension — Standalone Legacy Utility Migrations

Status: **RESOLVED (ADR-038 to ADR-045)**

All 8 standalone legacy Python utility scripts requested by the project owner have been re-engineered into modular, quality-first Node Packs:

1. **`JV.py` -> `media.join_videos` (ADR-038)**: Video concatenation with stream-copy and fallback normalization.
2. **`wav_para_m4a_lossless_gui_v2.py` -> `media.convert_lossless_alac` (ADR-039)**: Bit-exact WAV to ALAC conversion with decoded PCM SHA-256 validation.
3. **`Audio Merge Studio V2.py` -> `media.merge_audio_studio` (ADR-040)**: Multi-track audio/video merger with natural sorting, loudness normalization, and SHA-256 digest.
4. **`removedor_sibilancia_gui_v2.py` -> `media.deess_audio` (ADR-041)**: Dynamic voice de-esser and spectral noise reduction.
5. **`JA_de_Vários_videos.py` / `subpastas` -> `media.extract_and_join_by_subfolder` (ADR-042)**: Automated batch video-to-audio extraction and joining per subfolder.
6. **`Extrator TLDV.py` -> `text.tldv_extract` (ADR-043)**: Zero-dependency tl;dv HTML transcript extractor emitting Markdown, SRT, and JSON.
7. **`EC.py` -> `filesystem.structure_report` (ADR-044)**: Deep directory audit generating CSV inventory, ASCII tree TXT, and JSON metrics.
8. **`K_Tools_Drive_Streaming_Scanner.py` v1.4 -> `filesystem.drive_stream_scan` (ADR-045)**: Win32 native non-hydrating cloud drive scanner with SQLite checkpoints and CSV export.

---

## Milestone Status Summary

All active milestones (M0 through M5) plus the M5 Standalone Extension defined in this repository are now **RESOLVED / PROMOTED**.
All operations have been extracted into independent, tested, observable, diagnostic-instrumented node packs under `packages/`:
- `packages/ktools-core` (Execution engine, DAG runner, Diagnostics, Run Journal, Artifact lifecycle, Cache)
- `packages/ktools-json` (JSON capability, CLI, nodes)
- `packages/ktools-text` (Text merge, text split, tl;dv transcript extractor nodes)
- `packages/ktools-pdf` (PDF merge, PDF split nodes)
- `packages/ktools-documents` (Mixed document split orchestrator)
- `packages/ktools-images` (WebP to PNG, Images to PDF)
- `packages/ktools-filesystem` (Folder scan, Structure report, Cloud drive streaming scanner)
- `packages/ktools-media` (Audio extract, convert, split, join, ALAC lossless, Studio merge, De-esser, Subfolder audio, video compress, video join)

Repository Test Suite: 298 tests passing across all 8 packages at the M5 closure point. Later product/UI changes must use current `main` tests as execution truth rather than treating this historical count as permanently current.

---

# Next strategic horizon — K-Tools as an Agent-Native System Capability Layer

The next architectural horizon turns the capability catalog already proved by M0–M5 into a stable execution surface for AI agents without changing the product's ownership model.

The intended relationship is:

```text
Human / Tools UI / Workflow Studio / AI Agent
                    ↓
          stable K-Tools capability contract
                    ↓
  typed Node Packs + WorkflowEngine + adapters
                    ↓
 RunJournal + Diagnostics + Artifacts + Cache
                    ↓
       deterministic host-side execution
```

For an agentic workstation, K-Tools should answer **“what can this computer safely and deterministically do, and what happened when it tried?”**. A higher-level agent such as Hermes should answer **“what should be done, why, in what order, and whether another agent should be delegated?”**.

This boundary prevents K-Tools from becoming a second conversational memory, Kanban, planner, LLM router or agent-control plane.

## M6 — Agent Capability Interface V1

Status: **PLANNED / POST-M5 STRATEGIC HORIZON**

**Purpose:** make the same canonical capabilities consumable by AI agents and external automation clients without building a second implementation beside workflow nodes.

### M6.1 — Versioned Capability Manifest

Expose a machine-readable catalog derived from canonical Node Pack/runtime definitions.

Each exposed capability should be able to describe, where applicable:

- stable capability/node identifier and version;
- human description;
- typed inputs and outputs;
- required/local dependencies;
- supported host/platform constraints;
- network requirement;
- side-effect class;
- expected artifact/publication behavior;
- cache policy;
- whether dry-run/planning is supported;
- whether the action is naturally reversible or has an explicit recovery path;
- whether privilege elevation can be required;
- diagnostics/receipt support.

The manifest is a projection of canonical owners, not a second registry manually kept in sync.

### M6.2 — Direct Capability Invocation Contract

Generalize the direct-API pattern already proved by Node Packs into a stable agent/external-client invocation boundary.

Required properties:

- validate the same typed contract used by workflows;
- execute through the same capability owner as Tools/Workflows;
- emit the same Artifact provenance, RunJournal lifecycle and Diagnostics evidence where those concerns apply;
- return structured success/failure rather than requiring an agent to scrape console prose;
- preserve explicit partial-success semantics for batch capabilities;
- never silently substitute a different capability/provider after stateful binding.

### M6.3 — Multiple transport surfaces over one contract

Preferred evolution order:

1. **CLI** — canonical, scriptable local entrypoint;
2. **Skill/playbook** — teaches an agent which capability to use and how to validate/recover;
3. **MCP adapter** — structured agent interoperability where useful;
4. **local HTTP/IPC adapter** — only when a desktop/remote client needs a long-lived service boundary.

Transport adapters must remain thin. None may reimplement media/file/system business logic.

### M6.4 — Agent-facing skills without agent lock-in

Ship or generate capability guidance that can be consumed by Hermes and other compatible harnesses.

Skills should teach:

- capability discovery;
- safe parameter construction;
- path/workspace boundaries;
- validation after execution;
- interpretation of partial success;
- recovery/rollback where supported;
- how to collect diagnostics when execution fails.

K-Tools remains agent-agnostic: Hermes Workstation is a first-class reference consumer, not the only supported caller.

### M6 exit direction

M6 is proved when one canonical K-Tools capability can be invoked through direct API/workflow and at least one agent-facing transport with equivalent observable semantics and without a duplicate implementation owner.

---

## M7 — System Capabilities, Events + Scoped Safety

Status: **PLANNED / AFTER M6 CONTRACT PROOF**

**Purpose:** extend K-Tools from file/media transformation into a bounded computer-capability runtime suitable for agentic work while keeping security and policy responsibilities explicit.

### M7.1 — System Capability Node Packs

Candidate capability families, implemented only when a concrete consumer justifies them:

- filesystem/workspace inspection and bounded mutations;
- process launch/status/termination;
- application launch/focus/open-with operations;
- clipboard read/write with explicit sensitivity policy;
- download/output handoff and location reporting;
- Git and development-environment utilities;
- local job/build/test execution wrappers;
- notifications and user-attention requests;
- machine/application health and diagnostics;
- recoverable user-level configuration operations.

The same one-capability/one-owner rule continues to apply. Do not turn `ktools-core` into a bag of platform-specific commands; host-specific implementation belongs behind capability/provider boundaries.

### M7.2 — Capability scopes and least privilege

Add metadata/runtime enforcement needed for safe agent invocation.

Evaluate explicit scopes such as:

- allowed workspace/path roots;
- read vs write vs destructive mutation;
- network/no-network;
- subprocess/application execution;
- user-interactive vs unattended;
- privilege/elevation requirement;
- secret-bearing input/output handling.

K-Tools must not normalize convenience into blanket administrator/root access. Privilege elevation must be explicit, host-native and narrow.

### M7.3 — Policy handshake, not a second policy brain

K-Tools should expose enough action metadata for a higher-level caller to classify an action as, for example:

```text
allow
constrain / sandbox
require human confirmation
deny
```

K-Tools enforces its own hard safety invariants and caller-provided scopes, but it does **not** own the user's global conversational approval policy. In Hermes Workstation integration, Hermes/Workstation approvals remain authoritative and K-Tools acts as the deterministic executor beneath them.

### M7.4 — System Event → structured event stream

Add the inverse execution direction: meaningful host/runtime changes can be exposed as structured local events.

Candidate event classes:

- process/app crash or abnormal exit;
- local job/build/test completion or failure;
- download/output completion;
- watched file/workspace change where explicitly configured;
- dependency/runtime health transition;
- long-running capability completion;
- user-attention-required state.

Event records should carry stable type/version, timestamp, source/provider, correlation/run identity where available, concise reason/state and evidence references.

K-Tools events do not create an independent agent task database. Consumers such as Hermes Workstation may translate them into or attach them to their own canonical task/session model.

### M7.5 — Execution receipts and local observability

Generalize existing RunJournal/Diagnostics strengths into concise machine-consumable receipts for agent callers.

A receipt may include:

- capability/version/provider;
- validated inputs represented safely;
- start/end/status;
- artifacts and provenance;
- subprocess/native exit information;
- warnings/partial-success details;
- cache/reuse fact;
- recovery/rollback outcome when applicable;
- diagnostic/support-bundle reference when failure requires deeper investigation.

No outbound telemetry is required for this architecture. Local execution evidence is the default; external analytics/usage reporting requires a separate explicit product decision.

### M7 exit direction

M7 is proved when an agent can invoke at least one non-media host capability under an explicit scope, receive a structured receipt, and consume at least one meaningful system event without K-Tools becoming the owner of agent planning/tasks.

---

## M8 — Cross-Platform Host Provider Architecture

Status: **PLANNED / AFTER WINDOWS CONTRACT IS PROVED**

**Purpose:** preserve one semantic K-Tools capability language while allowing the native mechanism to vary by operating system.

### M8.1 — Generic Host Provider Contract

Introduce provider boundaries only after concrete Windows capabilities prove what must vary by host.

The provider contract may cover:

- capability availability/discovery;
- process/application operations;
- workspace/filesystem semantics;
- notifications and user-attention primitives;
- privilege/elevation strategy;
- host health/event sources;
- supported rollback/recovery mechanisms.

Feature negotiation must be explicit. A provider that cannot safely implement a capability reports it unavailable rather than pretending cross-platform parity.

### M8.2 — Windows as canonical first host

Windows remains K-Tools Neo's primary desktop target and the first semantic conformance baseline.

Reuse native Windows mechanisms where they provide materially safer or more correct behavior, while keeping platform-specific code behind the provider/capability owner instead of leaking it into generic workflow semantics.

### M8.3 — Linux / Omarchy reference provider

Treat **Omarchy** as a high-value Linux reference environment and architectural benchmark, not as a mandatory K-Tools dependency or product base.

Relevant patterns to evaluate:

- deterministic public CLI surfaces for system operations;
- skills that teach multiple agents how to operate the host safely;
- explicit agent/tool installation and discovery;
- system-event hooks such as crash diagnosis;
- local health/usage observability;
- user-level configuration boundaries rather than direct edits to packaged system files.

Where an Omarchy integration is built, prefer its documented CLI/config/skill contracts over distro-specific filesystem hacks. Generic Linux support must not be artificially defined as “whatever Omarchy does”; Omarchy is the first reference provider, not the semantic owner.

### M8.4 — Cross-host conformance suite

For every capability advertised by more than one host provider, test the semantic contract rather than implementation identity.

Conformance should prove, where relevant:

- equivalent input validation;
- side-effect and safety classification;
- artifact/result shape;
- error/partial-success semantics;
- event/receipt contract;
- path/scope isolation;
- privilege behavior;
- recovery behavior.

A host may legitimately expose fewer capabilities. Unsupported is preferable to unsafe emulation.

### M8 exit direction

M8 is proved when at least one meaningful capability family can run through the same external contract on Windows and a Linux reference host while preserving typed semantics, safety metadata, receipts and evidence.

---

## M9 — Agentic Workstation Integration + Capability Ecosystem

Status: **LONG-HORIZON / AFTER M6–M8 FOUNDATIONS**

**Purpose:** make K-Tools a reusable capability runtime for the broader agent ecosystem while preserving its independent product value for humans and workflows.

### Hermes Workstation integration

Hermes Workstation is the primary ecosystem integration to design against because the projects are complementary:

```text
Hermes Workstation
  owns user intent, chat, tasks, memory, agent orchestration and approvals
        ↓
K-Tools Capability Adapter
  translates bounded requested operations into canonical K-Tools contracts
        ↓
K-Tools Neo
  owns deterministic capability/workflow execution, artifacts, diagnostics and receipts
```

The integration must not introduce:

- a second Hermes SessionDB/Kanban/Memory inside K-Tools;
- a K-Tools LLM planner that competes with Hermes orchestration;
- duplicate implementations of K-Tools nodes inside Workstation;
- silent approval bypass because execution is local;
- hidden fallback between stateful providers.

### Reusable workflow-as-capability for agents

Build on ADR-007 so a saved, validated workflow with explicit typed public inputs/outputs can itself become an agent-callable capability.

This is strategically important: an agent should be able to call a tested local procedure such as a media/document pipeline without regenerating the low-level sequence every time.

The workflow remains the one owner of orchestration semantics; the agent-facing projection is an adapter over it.

### Capability discovery and compatibility

Evolve toward:

- stable capability IDs/versions;
- provider/host availability negotiation;
- backward-compatible manifest evolution;
- workflow/capability dependency declarations;
- local installation/readiness checks;
- conformance tests for external adapters;
- explicit deprecation/migration rules.

### Agentic capability reference tracking

Maintain lightweight research on projects that solve adjacent agent↔computer interface problems. Current references should include:

- Omarchy — OS skills, default-agent abstraction, system events and agent-native desktop affordances;
- Hermes / Hermes Workstation — orchestration, skills, memory, task identity and approvals;
- MCP ecosystem — structured tool interoperability;
- agent harnesses such as Codex, Claude Code, OpenCode and Antigravity — expectations of machine-operable local tools;
- relevant Windows/Linux automation runtimes where they can improve deterministic host providers.

The question is not “which project should K-Tools copy?” but “which stable contract would let all of them consume K-Tools capabilities without K-Tools becoming coupled to one agent?”

### Long-horizon target experience

```text
user asks Hermes for an outcome
  → Hermes plans and owns the task
  → Hermes selects a K-Tools capability or reusable workflow
  → caller policy scopes/approves the requested side effect
  → K-Tools executes deterministically on the host
  → RunJournal/Diagnostics/Artifacts produce structured evidence
  → K-Tools returns a receipt
  → host events can wake/enrich the upstream task when appropriate
  → the same K-Tools capability remains usable directly by a human or Workflow Studio
```

The success criterion is composability without identity loss: **Tools, Workflows and Agents are three clients of the same capability owners, not three K-Tools implementations.**
