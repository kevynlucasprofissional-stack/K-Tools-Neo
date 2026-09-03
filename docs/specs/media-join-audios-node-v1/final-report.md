# M5 Slice 12: Media Join Audios Node V1

## What was done
- Implemented media.join_audios in ktools-media.
- Expects a FILE_SET of inputs. Converts each input to WAV locally before joining to prevent formatting/glitching conflicts.
- Creates an internal FFmpeg concat script to combine the audio files.
- Ensures all outputs are correctly mapped back to a DataType.AUDIO output artifact.
- All temporary variables and directories are cleanly disposed of.
- Engine/Behavior tests pass reliably.

## Why it matters
This migrates the legacy _audio_join_run capability into the node ecosystem. By normalizing to WAV internally, it maintains the robust concatenation capability of the original K-Tools logic without propagating format compatibility issues to users.
