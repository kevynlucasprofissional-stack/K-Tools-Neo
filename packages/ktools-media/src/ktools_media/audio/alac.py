from __future__ import annotations

import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from ..ffmpeg import run_ffmpeg


def compute_decoded_pcm_hash(audio_path: Path) -> str:
    """
    Decodes audio to a temporary raw PCM stream (s16le) via FFmpeg and computes
    its SHA-256 digest to serve as a bit-exact audio comparison fingerprint.
    """
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    hasher = hashlib.sha256()
    with TemporaryDirectory(prefix="ktools_pcm_hash_") as tmp_dir:
        temp_pcm = Path(tmp_dir) / f"decoded_{uuid4().hex}.pcm"
        res = run_ffmpeg([
            "-y",
            "-i", str(audio_path),
            "-vn", "-sn", "-dn",
            "-f", "s16le",
            str(temp_pcm),
        ])

        if res.returncode != 0 or not temp_pcm.exists():
            raise RuntimeError(f"Failed to decode audio to PCM for hashing: {res.stderr}")

        with open(temp_pcm, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

    return hasher.hexdigest()


def convert_to_alac(
    input_path: Path,
    output_path: Path,
    verify: bool = True,
) -> tuple[Path, str | None]:
    """
    Converts a lossless audio file (WAV/FLAC) to ALAC (.m4a).
    If verify is True, decodes both input and output to raw PCM and verifies
    that their SHA-256 hashes are identical.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    final_output = output_path
    if final_output.suffix.lower() != ".m4a":
        final_output = final_output.with_suffix(".m4a")

    final_output.parent.mkdir(parents=True, exist_ok=True)
    tmp_out = final_output.with_name(f"{final_output.name}.{uuid4().hex}.tmp")

    try:
        # Convert to ALAC
        cmd = [
            "-y",
            "-i", str(input_path),
            "-c:a", "alac",
            str(tmp_out),
        ]
        res = run_ffmpeg(cmd)
        if res.returncode != 0 or not tmp_out.exists():
            raise RuntimeError(f"FFmpeg ALAC conversion failed: {res.stderr}")

        input_hash: str | None = None
        if verify:
            input_hash = compute_decoded_pcm_hash(input_path)
            output_hash = compute_decoded_pcm_hash(tmp_out)
            if input_hash != output_hash:
                raise RuntimeError(
                    f"Lossless verification failed: PCM hashes do not match "
                    f"(input={input_hash}, output={output_hash})"
                )

        os.replace(tmp_out, final_output)
        return final_output, input_hash
    finally:
        if tmp_out.exists():
            try:
                tmp_out.unlink()
            except OSError:
                pass
