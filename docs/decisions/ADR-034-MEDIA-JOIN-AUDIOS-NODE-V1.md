# ADR 034: Media Join Audios Node V1

## Date
2026-09-02

## Status
Accepted

## Context
As part of the M5 milestone, we need the ability to join multiple audio files. Direct FFmpeg concatenation often fails or glitches if the inputs have varying formats, sample rates, or codec profiles. The legacy K-Tools implementation solved this by performing a 2-pass merge: normalize all inputs to WAV, then concatenate the WAVs into the final desired format.

## Decision
- Built the media.join_audios node which implements the 2-pass merge logic.
- Node takes a FILE_SET of inputs (a list of Artifact instances in runtime).
- A TemporaryDirectory bounds the lifespan of the intermediate .wav files and the generated concat.txt instruction file.
- The fmpeg concatenation output uses .tmp atomic path replacements.

## Consequences
- The orchestration layer handles many-to-one aggregation elegantly.
- FILE_SET proves viable as a generic list transport mechanism for artifact sets.
