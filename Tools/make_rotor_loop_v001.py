"""make_rotor_loop_v001.py - a PLACEHOLDER drone rotor loop.

The spacecraft game is silent. The owner's sound spec asks for a
"quad-rotor buzz, pitch-shiftable, 4 s loop" as the first sound of
Priority 2, and sourcing is his choice per line - generate, buy or
record. This is the blockout equivalent for audio: a synthesised loop so
the pitch-with-rotor-speed behaviour is audible and testable now, to be
replaced by the real thing when he does the audio pass.

Deliberately built from HARMONIC PARTIALS ONLY, no random noise. Every
partial completes a whole number of cycles inside the buffer, so the
loop is seamless by construction rather than by crossfading - a click at
the loop point is the one thing a 4-second buzz cannot get away with.

Pure standard library: no numpy, no audio tooling.
Run: python make_rotor_loop_v001.py
"""

import math
import os
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rotor_loop_v001.wav")

RATE = 44100
SECONDS = 4.0
FRAMES = int(RATE * SECONDS)

# Blade-pass fundamental and its harmonics. Every frequency is a
# multiple of 1/SECONDS (0.25 Hz), so each closes its cycle exactly at
# the buffer end and the loop joins silently.
PARTIALS = [
    # (hz, amplitude)
    (110.0, 0.42),   # body of the buzz
    (220.0, 0.26),
    (330.0, 0.14),
    (440.0, 0.09),
    (660.0, 0.05),
    (880.0, 0.035),  # the thin whine on top
    (1320.0, 0.02),
]

# Slow beating between four rotors that are never quite in sync. Also an
# exact multiple of 1/SECONDS, so it loops too.
BEAT_HZ = 2.5
BEAT_DEPTH = 0.18


def sample(index):
    t = index / RATE
    beat = 1.0 + BEAT_DEPTH * math.sin(2.0 * math.pi * BEAT_HZ * t)
    value = 0.0
    for hz, amp in PARTIALS:
        # Odd partials phase-offset a little so the waveform is not a
        # perfectly symmetrical spike.
        phase = 0.25 * math.pi if int(hz / 110.0) % 2 else 0.0
        value += amp * math.sin(2.0 * math.pi * hz * t + phase)
    return value * beat


def main():
    raw = [sample(i) for i in range(FRAMES)]
    peak = max(abs(v) for v in raw) or 1.0
    # Leave headroom: this gets pitch-shifted and layered across a
    # dozen drones, and clipping is not a placeholder problem.
    scale = 0.72 / peak
    frames = bytearray()
    for value in raw:
        frames += struct.pack("<h", int(max(-1.0, min(1.0, value * scale))
                                        * 32767))
    with wave.open(OUT, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(bytes(frames))

    # Prove the seam. The test is NOT "first sample equals last" - for a
    # periodic signal sample[N] equals sample[0], so sample[N-1] is one
    # ordinary step away from it and always differs. What would click is
    # a wrap step LARGER than the steps either side of it, so that is
    # what gets measured.
    wrap_step = abs(raw[0] - raw[-1])
    steps = [abs(raw[i + 1] - raw[i]) for i in range(0, FRAMES - 1, 97)]
    typical = max(steps)
    print("wrote %s (%.1f s, %d frames)" % (OUT, SECONDS, FRAMES))
    print("wrap step %.5f vs largest ordinary step %.5f"
          % (wrap_step, typical))
    if wrap_step > typical * 1.5:
        raise SystemExit("FAIL CLOSED: loop seam would click")


if __name__ == "__main__":
    main()
