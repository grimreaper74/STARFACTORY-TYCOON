"""Build a concise chronological PR-005 listening-review mix."""

import json
import wave
from pathlib import Path

import numpy as np


RATE = 48_000
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Audio/PR005/Candidate_v001"
OUT = ROOT / "Saved/AudioReviews"
WAV = OUT / "pr005_operational_audio_review_v001.wav"
TIMELINE = OUT / "pr005_operational_audio_review_v001.json"


def load(name):
    with wave.open(str(SOURCE / name), "rb") as handle:
        assert handle.getframerate() == RATE and handle.getnchannels() == 2
        data = np.frombuffer(handle.readframes(handle.getnframes()), dtype="<i2")
    return data.astype(np.float64).reshape((-1, 2)) / 32768.0


events = [
    (0.0, "PR005_HPU_Idle_Loop_v001.wav", 0.28, "Control power and HPU online"),
    (4.0, "PR005_CoilCar_Start_v001.wav", 0.72, "Loaded coil car starts"),
    (6.5, "PR005_CoilCar_Travel_Loop_v001.wav", 0.62, "Coil car travels to mandrel"),
    (10.5, "PR005_CoilCar_Stop_v001.wav", 0.72, "Coil car positions and stops"),
    (12.7, "PR005_Mandrel_Expand_v001.wav", 0.82, "Mandrel expands and locks"),
    (16.0, "PR005_KeeperArm_Engage_v001.wav", 0.88, "Keeper arm engages"),
    (18.4, "PR005_GateInterlock_v001.wav", 0.90, "Guard closes and safety relay confirms"),
    (19.8, "PR005_WarningAlarm_Loop_v001.wav", 0.56, "Automatic-start warning"),
    (22.0, "PR005_RollerDrive_Loop_v001.wav", 0.50, "Pinch rolls and table accelerate"),
    (22.0, "PR005_StripMotion_Loop_v001.wav", 0.54, "Steel strip moves continuously"),
    (26.0, "PR005_RollerDrive_Loop_v001.wav", 0.50, "Sustained automatic roller drive"),
    (26.0, "PR005_StripMotion_Loop_v001.wav", 0.54, "Sustained strip transport"),
    (30.1, "PR005_ControlledStop_v001.wav", 0.78, "Normal controlled stop"),
    (33.2, "PR005_EmergencyStop_v001.wav", 0.90, "Emergency-stop comparison"),
]

duration = 35.2
mix = np.zeros((int(duration * RATE), 2), dtype=np.float64)
timeline = []
for start, filename, gain, label in events:
    audio = load(filename)
    index = int(round(start * RATE))
    end = min(index + len(audio), len(mix))
    mix[index:end] += audio[:end-index] * gain
    timeline.append({"start_seconds": start, "source": filename, "gain": gain, "event": label})

# Maintain a quieter HPU bed after initial energisation.
hpu = load("PR005_HPU_Idle_Loop_v001.wav")
for start in np.arange(6.0, 30.0, 6.0):
    index = int(round(float(start) * RATE))
    end = min(index + len(hpu), len(mix))
    mix[index:end] += hpu[:end-index] * 0.12

peak = float(np.max(np.abs(mix)))
mix *= 0.92 / max(peak, 1e-9)
pcm = (np.clip(mix, -1.0, 1.0) * 32767.0).astype("<i2")
OUT.mkdir(parents=True, exist_ok=True)
with wave.open(str(WAV), "wb") as handle:
    handle.setnchannels(2)
    handle.setsampwidth(2)
    handle.setframerate(RATE)
    handle.writeframes(pcm.tobytes())
TIMELINE.write_text(json.dumps({"duration_seconds": duration, "events": timeline}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_AUDIO_REVIEW_PASS path={WAV} bytes={WAV.stat().st_size}")
