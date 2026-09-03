# M5 Slice 11: Media Split Audio Node V1

## What was done
- Implemented media.split_audio in ktools-media.
- Uses fprobe to accurately determine media duration.
- Dispatches multiple fmpeg instances to partition audio into N equal files.
- Outputs FILE_SET compliant pieces as multiple Artifact outputs.
- Subprocesses recorded within DiagnosticsSession.
- All RED tests brought to GREEN status.

## Why it matters
This migrates the legacy _audio_split_run capability into the node ecosystem. We can now construct batch pipelines that cut long audio tracks into short segments for subsequent LLM processing (e.g. Whisper API limits).
