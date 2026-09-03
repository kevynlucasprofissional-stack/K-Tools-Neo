# Discovery: Media Convert Lossless ALAC Node V1

## Context and Problem
The workspace contains `wav_para_m4a_lossless_gui_v2.py`, a utility that converts WAV files to ALAC (Apple Lossless Audio Codec, `.m4a`) and guarantees bit-exact fidelity by comparing the SHA-256 hash of decoded raw PCM streams from both the input WAV and the resulting ALAC M4A file.

While `media.convert_audio` performs lossy/general conversions (e.g. AAC, MP3, general WAV), audio engineers and archive workflows require an uncompromising, bit-verifiable lossless audio conversion to ALAC for high-fidelity playback in Apple ecosystems without generation loss.

## Candidate Node Definition
- Node Type: `media.convert_lossless_alac`
- Inputs: `audio: FILE` (WAV, FLAC or compatible lossless audio artifact)
- Outputs: `audio: AUDIO`
- Config:
  - `verify_bit_exact` (bool, default True): compute and verify decoded PCM SHA-256
  - `output_name` (optional str)
  - `output_dir` (optional str)

## Technical Architecture
1. Module: `packages/ktools-media/src/ktools_media/audio/alac.py`
2. Functions:
   - `convert_to_alac(input_path: Path, output_path: Path, verify: bool = True) -> tuple[Path, str | None]`
   - `compute_decoded_pcm_hash(audio_path: Path) -> str`
3. Subprocess tracking via `run_ffmpeg` (M3 compliant).
4. Atomic file promotion via `.tmp`.
