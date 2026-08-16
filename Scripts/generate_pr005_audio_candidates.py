"""Generate deterministic original PR-005 machine-audio source candidates.

These are clean, layered starting points for Unreal attenuation, modulation and
state-driven mixing. They contain no third-party recordings.
"""

import json
import math
import wave
from pathlib import Path

import numpy as np


RATE = 48_000
OUT = Path(__file__).resolve().parents[1] / "SourceAssets/Audio/PR005/Candidate_v001"
RNG = np.random.default_rng(5005)


def timebase(seconds):
    return np.arange(int(round(seconds * RATE)), dtype=np.float64) / RATE


def smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def env(t, attack=0.03, release=0.08):
    length = max(float(t[-1]), 1.0 / RATE)
    return smoothstep(t / attack) * smoothstep((length - t) / release)


def periodic_noise(seconds, low_hz, high_hz, seed, slope=0.0):
    n = int(round(seconds * RATE))
    rng = np.random.default_rng(seed)
    spectrum = np.zeros(n // 2 + 1, dtype=np.complex128)
    freqs = np.fft.rfftfreq(n, 1.0 / RATE)
    mask = (freqs >= low_hz) & (freqs <= high_hz)
    count = int(mask.sum())
    phase = rng.uniform(0.0, 2.0 * np.pi, count)
    magnitude = rng.uniform(0.35, 1.0, count)
    if slope:
        magnitude *= np.maximum(freqs[mask], 1.0) ** slope
    spectrum[mask] = magnitude * np.exp(1j * phase)
    signal = np.fft.irfft(spectrum, n=n)
    return signal / max(np.max(np.abs(signal)), 1e-9)


def filtered_noise(n, low_hz, high_hz, seed):
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    spectrum = np.fft.rfft(noise)
    freqs = np.fft.rfftfreq(n, 1.0 / RATE)
    spectrum[(freqs < low_hz) | (freqs > high_hz)] = 0.0
    signal = np.fft.irfft(spectrum, n=n)
    return signal / max(np.max(np.abs(signal)), 1e-9)


def sweep(t, f0, f1, phase=0.0):
    duration = max(float(t[-1]), 1.0 / RATE)
    k = (f1 - f0) / duration
    return np.sin(2.0 * np.pi * (f0 * t + 0.5 * k * t * t) + phase)


def transient(t, at, decay, frequencies, amplitudes=None):
    local = t - at
    gate = local >= 0.0
    amplitudes = amplitudes or [1.0] * len(frequencies)
    result = np.zeros_like(t)
    for frequency, amplitude in zip(frequencies, amplitudes):
        result += amplitude * np.sin(2.0 * np.pi * frequency * np.maximum(local, 0.0))
    return gate * np.exp(-np.maximum(local, 0.0) / decay) * result


def stereo(left, right=None):
    if right is None:
        right = np.roll(left, 13) * 0.985
    return np.column_stack((left, right))


def write(name, audio, loop, description):
    audio = np.nan_to_num(audio)
    peak = float(np.max(np.abs(audio)))
    if peak > 0.0:
        audio = audio * (0.92 / peak)
    rms = float(np.sqrt(np.mean(audio * audio)))
    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype("<i2")
    path = OUT / f"{name}.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(pcm.tobytes())
    return {
        "file": path.name,
        "duration_seconds": round(len(audio) / RATE, 4),
        "sample_rate": RATE,
        "channels": 2,
        "loop": loop,
        "peak_dbfs": round(20.0 * math.log10(max(float(np.max(np.abs(audio))), 1e-9)), 2),
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-9)), 2),
        "description": description,
    }


def make_candidates():
    results = []

    t = timebase(6.0)
    pump = 0.38 * np.sin(2*np.pi*50*t) + 0.18*np.sin(2*np.pi*100*t) + 0.08*np.sin(2*np.pi*150*t)
    ripple = (0.72 + 0.28*np.sin(2*np.pi*7*t)) * periodic_noise(6.0, 180, 1450, 501, -0.25)
    results.append(write("PR005_HPU_Idle_Loop_v001", stereo(0.72*pump + 0.20*ripple), True, "Hydraulic power-unit motor, pump ripple and cabinet resonance."))

    t = timebase(4.0)
    gear = 0.34*np.sin(2*np.pi*36*t) + 0.17*np.sin(2*np.pi*180*t) + 0.08*np.sin(2*np.pi*360*t)
    rail = periodic_noise(4.0, 70, 1800, 502, -0.15) * (0.35 + 0.15*np.sin(2*np.pi*5*t))
    results.append(write("PR005_CoilCar_Travel_Loop_v001", stereo(gear + 0.24*rail), True, "Geared coil-car drive with rail and wheel vibration."))

    t = timebase(2.5)
    start = env(t, .02, .18) * (0.48*sweep(t, 16, 40) + 0.20*sweep(t, 95, 210) + 0.16*filtered_noise(len(t), 80, 1800, 503))
    start += 0.30*transient(t, .08, .035, [180, 720, 1650], [1, .55, .25])
    results.append(write("PR005_CoilCar_Start_v001", stereo(start), False, "Contactor engagement and loaded drive acceleration."))

    t = timebase(2.1)
    stop = env(t, .01, .12) * (0.45*sweep(t, 40, 12) + 0.16*sweep(t, 210, 70) + 0.12*filtered_noise(len(t), 60, 1200, 504))
    stop += 0.32*transient(t, 1.48, .06, [95, 420, 1200], [1, .5, .22])
    results.append(write("PR005_CoilCar_Stop_v001", stereo(stop), False, "Loaded drive coast-down, brake and rail-settle impact."))

    t = timebase(3.2)
    hydraulic = filtered_noise(len(t), 350, 6200, 505) * env(t, .12, .28) * (0.18 + .32*smoothstep(t/1.3))
    strain = 0.26*sweep(t, 42, 68) * env(t, .18, .35)
    latch = 0.48*transient(t, 2.67, .12, [115, 690, 1380], [1, .65, .28])
    results.append(write("PR005_Mandrel_Expand_v001", stereo(hydraulic + strain + latch), False, "Hydraulic expansion, steel strain and final lock."))

    t = timebase(2.2)
    cylinder = 0.24*filtered_noise(len(t), 450, 4800, 506)*env(t, .05, .45)
    arm = 0.22*sweep(t, 58, 38)*env(t, .08, .32)
    impact = 0.62*transient(t, 1.62, .11, [82, 430, 1120, 2440], [1, .72, .36, .16])
    results.append(write("PR005_KeeperArm_Engage_v001", stereo(cylinder + arm + impact), False, "Keeper-arm cylinder travel and damped contact with the coil."))

    t = timebase(4.0)
    motor = .32*np.sin(2*np.pi*28*t)+.16*np.sin(2*np.pi*56*t)+.10*np.sin(2*np.pi*224*t)
    bearings = periodic_noise(4.0, 240, 4200, 507, -.15)*(0.25+.08*np.sin(2*np.pi*8*t))
    results.append(write("PR005_RollerDrive_Loop_v001", stereo(motor + .28*bearings), True, "Pinch-roll and threading-table motor, gearbox and bearings."))

    t = timebase(4.0)
    sheet = periodic_noise(4.0, 700, 9500, 508, .05)*(0.26+.10*np.sin(2*np.pi*6*t))
    contact = .10*np.sin(2*np.pi*420*t)*(0.5+0.5*np.sin(2*np.pi*12*t))
    flutter = .14*np.sin(2*np.pi*74*t)*(0.55+0.45*np.sin(2*np.pi*3*t))
    results.append(write("PR005_StripMotion_Loop_v001", stereo(sheet + contact + flutter), True, "Continuous steel-strip hiss, roller contacts and restrained flutter."))

    t = timebase(1.15)
    latch = .58*transient(t, .12, .055, [140, 760, 1700], [1, .75, .3])
    relay = .38*transient(t, .54, .025, [950, 2100], [1, .42])
    results.append(write("PR005_GateInterlock_v001", stereo(latch + relay), False, "Mechanical guard latch followed by safety-relay confirmation."))

    t = timebase(2.0)
    alarm_env = smoothstep(np.sin(2*np.pi*1*t)*3.0 + .5)
    alarm = alarm_env*(.55*np.sin(2*np.pi*880*t)+.23*np.sin(2*np.pi*1760*t))
    results.append(write("PR005_WarningAlarm_Loop_v001", stereo(alarm, np.roll(alarm, 7)), True, "Two-pulse industrial pre-start/fault warning."))

    t = timebase(2.7)
    coast = env(t, .01, .18)*(.42*sweep(t, 34, 7)+.18*sweep(t, 210, 45)+.14*filtered_noise(len(t), 100, 2500, 509))
    vent = .32*transient(t, 1.75, .24, [70, 310, 980], [1, .46, .18])
    results.append(write("PR005_ControlledStop_v001", stereo(coast + vent), False, "Controlled roller coast-down and pneumatic pressure release."))

    t = timebase(1.6)
    drop = .74*transient(t, .04, .07, [92, 520, 1450], [1, .7, .28])
    brake = .38*filtered_noise(len(t), 120, 4200, 510)*env(t, .015, .45)
    slap = .60*transient(t, .48, .13, [64, 240, 810], [1, .65, .3])
    results.append(write("PR005_EmergencyStop_v001", stereo(drop + brake + slap), False, "Contactor drop, drive brake and tensioned-strip slap."))

    return results


OUT.mkdir(parents=True, exist_ok=True)
manifest = {
    "status": "CANDIDATE_NOT_PROMOTED",
    "license": "Original procedural synthesis generated for Line Boss; no third-party recordings.",
    "assets": make_candidates(),
}
(OUT / "audio_manifest_v001.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_AUDIO_GENERATION_PASS assets={len(manifest['assets'])} output={OUT}")
