from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Sequence
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def join_audios(
    input_paths: Sequence[Path],
    output_path: Path,
    output_format: str = "m4a",
    bitrate: str | None = None,
) -> Path:
    '''
    Joins multiple audio files into a single output.
    Normalizes inputs to WAV to prevent concat glitches from differing codecs.
    '''
    if len(input_paths) < 2:
        raise ValueError("At least 2 audio files are required to join.")
        
    for p in input_paths:
        if not p.exists():
            raise FileNotFoundError(f"Input file not found: {p}")

    out_fmt = output_format.strip(".").lower()
    final_output = output_path
    if final_output.suffix.strip(".").lower() != out_fmt:
        final_output = final_output.with_suffix(f".{out_fmt}")
        
    final_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = final_output.with_name(f"{final_output.name}.{uuid4().hex}.tmp")

    with TemporaryDirectory(prefix="ktools_media_join_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        wav_paths: list[Path] = []
        
        # 1. Convert to WAV
        for i, src in enumerate(input_paths):
            wav_file = tmp_path / f"part_{i:04d}.wav"
            cmd_wav = ["-y", "-i", str(src), "-vn", "-ar", "44100", "-ac", "2", "-f", "wav", str(wav_file)]
            res_wav = run_ffmpeg(cmd_wav)
            if res_wav.returncode != 0:
                raise RuntimeError(f"Failed to normalize {src} to WAV: {res_wav.stderr}")
            wav_paths.append(wav_file)
            
        # 2. Build concat file
        concat_txt = tmp_path / "concat.txt"
        lines = []
        for w in wav_paths:
            # properly escape the path for ffmpeg concat
            # or just use relative path since they are in the same dir
            lines.append(f"file '{w.name}'")
        concat_txt.write_text("\n".join(lines), encoding="utf-8")
        
        # 3. Concat
        cmd_concat = ["-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt)]
        if bitrate:
            cmd_concat.extend(["-b:a", bitrate])
            
        cmd_concat.append(str(tmp_out))
        
        # run concat inside the temp dir so relative paths in concat.txt work
        try:
            cwd_before = os.getcwd()
            os.chdir(str(tmp_path))
            try:
                res_concat = run_ffmpeg(cmd_concat)
            finally:
                os.chdir(cwd_before)
                
            if res_concat.returncode != 0:
                raise RuntimeError(f"Failed to concat audios: {res_concat.stderr}")
                
            os.replace(tmp_out, final_output)
        finally:
            if tmp_out.exists():
                try:
                    tmp_out.unlink()
                except OSError:
                    pass

    return final_output
