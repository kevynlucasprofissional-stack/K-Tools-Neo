# OC-001 — Task-local evidence: candidate ranking, decision and proof

Status: TASK-LOCAL EVIDENCE (OpenCode-owned, per OC-001 packet §4/§9)
Task: OC-001 — First Real Capability / Node Pack
Agent: OpenCode (Runtime / Backend Implementation Lead)
Base `main` SHA: `5a8432941e5cd6bf2a3cea13bea1e5a42134a131`

> This file records candidate ranking, the capability decision and the
> evidence produced during OC-001. It is task-local; it is not a canonical
> architecture document. Proposed canonical memory updates are listed in the
> handoff for the Conductor.

## 1. Discovery performed

Repository baseline inspected on the exact base SHA:

- `packages/ktools-core/` source, tests and CLI (`models`, `registry`,
  `builtin`, `engine`, `cli`);
- root `.github/workflows/core-ci.yml`;
- legacy GUI `K Tools Neo - Versão Estável 2.py` (6,912 lines) — full
  business-function inventory (module-level functions separated from the
  CustomTkinter UI, lines 51–2490);
- loose root utilities (`conversor_imagens_pdf.py`, `extrator_audio_video.py`,
  `wav_para_m4a_lossless_gui_v2.py`, `removedor_sibilancia_*.py`, folder/logo
  organizers, `K_Tools_Drive_Streaming_Scanner*.py`, etc.);
- `docs/research/WORKFLOW_PLATFORM_REFERENCE_STUDY.md` (Section 24 defines the
  exact first experiment that OC-001 executes);
- `docs/engineering-journal/CURRENT.md` (entry H-001: shared node contracts
  are the correct integration boundary).

## 2. Candidate ranking

Ranking criteria from the packet: user usefulness, determinism, offline/local
behavior, side-effect risk, testability, dependency complexity, GUI coupling,
typed-port fit, workflow reuse, failure observability, cross-platform
viability.

| Rank | Candidate | Evidence source | Strong points | Weak points |
|---|---|---|---|---|
| 1 | **JSON split** (`split_json_file`, legacy 2002–2042) | legacy GUI JSON section; stdlib-only | Zero external dependency; 100% deterministic; classifiable failures (invalid JSON, no main list, empty list, parts<1, target<=0, output collision, atomic per-file write with post-write validation); produces artifact-shaped part records (uri/size/item count); maps to `DataType.JSON` ports; real recurring tool (GUI has two JSON tools: parts/size) | Text domain, not media; less "flashy" than audio/PDF |
| 2 | Markdown/TXT merge (`merge_text_files`, legacy 1142–1204) | legacy GUI Markdown/TXT section | stdlib-only; offline; deterministic; typed `FOLDER`/`FILE` mapping | Folder-scan semantics add surface; less failure richness; overlaps a domain that a later text node pack would own |
| 3 | Images→PDF (`images_to_pdf`, legacy 1394–1468) | GUI PDF/Imagens + `conversor_imagens_pdf.py` | Highly useful; produces PDF artifact; offline (Pillow) | Requires Pillow (+img2pdf) dependency in root CI; multi-input list semantics need a list type the DataType enum does not yet expose |
| 4 | WebP→PNG (`convert_webp_to_png`, legacy 1470–1534) | GUI PDF/Imagens | Offline; deterministic; `IMAGE` typed | Requires Pillow; narrower usefulness |
| 5 | Folders/file export (`scan_folder_structure`/`export_folder_reports`) | GUI Arquivos/Pastas | stdlib+openpyxl; deterministic | Report-format surface (TXT/JSON/CSV/XLSX) is bigger than the first proof needs; CSV/XLSX deps |
| 6 | Audio/Video transforms (`join_audio_files`, `extract_audio_from_video`, `convert_audio_files_batch`, `split_audio_file`, etc.) | GUI Áudio/Vídeo; `extrator_audio_video.py` | Core K-Tools domain; real recurring use | Requires FFmpeg/FFprobe binary; heavier native smoke; cross-platform CI with FFmpeg is extra machinery — better deferred until the shared FFmpeg bridge boundary is established in a later wave |
| 7 | Sibilance remover / M4A lossless / podcast science / Drive scanner | loose utilities | Real domain value | Some need ffmpeg/DSP or network/streaming state; multiple huge GUI files; worst dependency/side-effect profile |

## 3. Decision

**Selected capability: JSON document split** (parts/size modes), owned by a new
official node pack `packages/ktools-json/`.

Reasons it won (evidence-based):

1. **Already-existing, real recurring K-Tools behavior** — the legacy GUI ships
   a dedicated JSON section (two tools: `parts` and `size`) implemented by
   `split_json_file` and friends. OC-001 therefore extracts and elevates
   existing product behavior instead of inventing a new capability.
2. **Zero-dependency, cross-platform, deterministic** — stdlib only; the same
   input/config yields byte-identical part files; root CI on Ubuntu/Windows ×
   Python 3.10/3.13 can run it with no new machinery.
3. **Rich, classifiable failure boundary** — invalid JSON (line/col), missing
   source, no main list, empty root list, parts<1, target<=0 and output
   collisions are distinguishable error types instead of a generic exception.
4. **Observable artifacts** — each part is reported as a structured record
   (name, `file://` uri, size bytes, item count) that evolves directly into the
   `Artifact` provenance model (ADR-005) once Run Journal lands (Wave 2).
5. **Typed ports map cleanly** — `DataType.JSON` input and outputs; the
   connection contract is validated before execution by `ktools-core`.
6. **Future workflow reuse** — splitting a large JSON dataset is a natural
   upstream step before per-part processing/completion nodes in later media or
   data workflows.

Meaningful rejected alternatives: Markdown/TXT merge (close second; deferred so
a coherent text node pack can be designed later), media/audio extraction (the
strongest "product" candidate but FFmpeg-binary-dependent; deliberately
deferred per packet §2/§4 to give the shared FFmpeg bridge its own boundary),
images→PDF (worthwhile, but wants `list` typing that the DataType enum does not
yet expose).

## 4. Required architecture (single owner)

```text
packages/ktools-json/               official first node pack (OC-001)
  capability.py                     split semantics owner (pure, no I/O)
  writer.py                         shared file-producing orchestration
  api.py                            direct API (thin: read + delegate)
  node.py                           NodeDefinition + handler (thin adapter)
  cli.py / __main__.py              headless workflow smoke boundary
packages/ktools-core/               unchanged node contract / runtime authority
```

Invariant enforced and tested (see `test_workflow_integration.py`):
direct `api.split_json` AND node `json.split` both reach
`writer.split_and_write` → `capability.split_json_document`. No splitting
logic exists in the adapter (`test_node.py` asserts the handler source does
not contain the split algorithms).

## 5. Contract (documented + tested)

- Input: JSON document. Direct: source file path. Node: `json_data` port
  (`DataType.JSON`).
- Config: `mode` (`parts`|`size`, default `parts`), `parts` (int ≥ 1, default 2
  in literals path; required semantics per mode), `target_bytes` (int > 0,
  required in `size` mode).
- Output: `SplitResult` with part records (index, name, uri, sizeBytes,
  itemCount, kind=file, type=json) + summary (rootType, listPath, itemCount,
  partCount, outputSizes, estimatedSizes). Node outputs `parts` (JSON),
  `summary` (JSON).
- Failure boundary: classified `JsonSplitError` subtypes —
  `JsonSourceError`, `InvalidJsonDocumentError`, `InvalidModeError`,
  `InvalidPartsError`, `InvalidTargetSizeError`, `NoMainListError`,
  `EmptyMainListError`, `OutputCollisionError`.
- Destination semantics: `output_dir` is created if absent and must be a
  directory; part file names are deterministic
  `{safe_prefix}_parte_{i}_de_{count}.json`.
- Overwrite semantics: default refuses any pre-existing target part file
  (all-or-nothing collision gate before writing); `overwrite=True` replaces.
- Partial output semantics: per-file atomic temp+`os.replace`; if a mid-write
  failure occurs after earlier parts were emitted, earlier files remain but no
  single part file is ever left incomplete; each written part is re-read and
  JSON-parsed after writing.
- External dependencies: none (stdlib only). Explicitly no FFmpeg/network/GUI.

## 6. Evidence summary (local)

- ktools-core tests re-run green (Foundation regressions intact; core untouched).
- ktools-json unit/contract tests: RED in the sense that the missing capability
  was demonstrated as absent, then GREEN on implementation.
- Direct invocation, workflow-node invocation, shared-owner proof, typed-edge
  validation, failure semantics, CLI smoke — see handoff report for the exact
  test commands and results.

## 7. Deviations recorded for Conductor review

1. **CI change (`.github/workflows/core-ci.yml`)** — OC-001 packet §8
   (Integration-level) requires root CI to reach actual install/test/smoke
   boundaries for the capability, and Phase E requires capability tests and
   CLI smoke through CI. The reserved/`.github/workflows/` ownership map
   normally keeps ChatGPT as the CI writer; this change is additive
   (install + tests + smoke for the new owned package) and was made because
   the task makes it unavoidable to satisfy the stated acceptance boundary.
   Proposed for Conductor review/adjustment.
2. **Canonical memory updates pending** — `docs/CURRENT_STATE.md` still states
   agents must not merge to `main`, contradicting `MAIN_ONLY_POLICY.md`.
   Proposed CURRENT_STATE/DECISIONS updates are listed in the handoff so the
   Conductor can apply them (not edited here).
3. **Legacy behavior deltas** — new overwrite default is refusal (legacy GUI
   overwrote silently); config uses `target_bytes` (legacy GUI used MB). Both
   are deliberate contract improvements recorded for Conductor info.