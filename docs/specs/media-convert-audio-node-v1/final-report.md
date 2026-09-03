# M5 Slice 10: Media Convert Audio Node V1

## What was done
- Implemented media.convert_audio inside ktools-media package.
- It acts on an input AUDIO or FILE artifact and converts it into the requested format (e.g. mp3, wav, m4a) using fmpeg.
- Subprocesses are recorded in the DiagnosticsSession to meet M3 requirements.
- Wrote robust tests confirming missing inputs trigger errors, atomic replacement strategy prevents corrupted files, and engine tests verifying contract and graph integrity.
- Identified and fixed a ContextVar leak in ktools-core/engine.py that caused diagnostics tracking to malfunction in unit tests.

## Why it matters
This brings another legacy function from K Tools Neo - Versão Estável 2.py into the Node capability graph, properly tested and auditable.
