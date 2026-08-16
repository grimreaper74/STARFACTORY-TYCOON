"""Fail-fast technical audit for original PR-005 WAV candidates."""

import json
import math
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Audio/PR005/Candidate_v001"
MANIFEST = json.loads((SOURCE / "audio_manifest_v001.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "Saved/Audits/pr005_audio_source_quality_v001.json"

records = []
errors = []
for expected in MANIFEST["assets"]:
    path = SOURCE / expected["file"]
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        rate = handle.getframerate()
        frames = handle.getnframes()
        width = handle.getsampwidth()
        pcm = handle.readframes(frames)
    if width != 2:
        errors.append(f"{path.name}: expected 16-bit PCM")
        continue
    audio = np.frombuffer(pcm, dtype="<i2").astype(np.float64) / 32768.0
    audio = audio.reshape((-1, channels))
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio * audio)))
    dc = [float(abs(np.mean(audio[:, channel]))) for channel in range(channels)]
    clipped_samples = int(np.count_nonzero(np.abs(audio) >= 0.999))
    seam = None
    seam_ratio = None
    if expected["loop"]:
        boundary = float(np.sqrt(np.mean((audio[0] - audio[-1]) ** 2)))
        normal_step = float(np.sqrt(np.mean(np.diff(audio, axis=0) ** 2)))
        seam = boundary
        seam_ratio = boundary / max(normal_step, 1e-12)
        if seam_ratio > 2.5:
            errors.append(f"{path.name}: loop seam ratio {seam_ratio:.3f} exceeds 2.5")
    if channels != 2:
        errors.append(f"{path.name}: expected stereo")
    if rate != 48_000:
        errors.append(f"{path.name}: expected 48000 Hz")
    if clipped_samples:
        errors.append(f"{path.name}: {clipped_samples} clipped samples")
    if max(dc) > 0.01:
        errors.append(f"{path.name}: DC offset {max(dc):.5f}")
    rms_db = 20.0 * math.log10(max(rms, 1e-12))
    if not -34.0 <= rms_db <= -7.0:
        errors.append(f"{path.name}: RMS {rms_db:.2f} dBFS outside candidate range")
    records.append({
        "file": path.name,
        "frames": frames,
        "duration_seconds": frames / rate,
        "channels": channels,
        "sample_rate": rate,
        "peak_dbfs": 20.0 * math.log10(max(peak, 1e-12)),
        "rms_dbfs": rms_db,
        "max_dc_offset": max(dc),
        "clipped_samples": clipped_samples,
        "loop": bool(expected["loop"]),
        "loop_boundary_rms": seam,
        "loop_seam_ratio": seam_ratio,
    })

result = {"status": "PASS" if not errors else "FAIL", "errors": errors, "assets": records}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if errors:
    raise RuntimeError("LINE_BOSS_PR005_AUDIO_SOURCE_FAIL " + "; ".join(errors))
print(f"LINE_BOSS_PR005_AUDIO_SOURCE_PASS assets={len(records)} output={OUTPUT}")
