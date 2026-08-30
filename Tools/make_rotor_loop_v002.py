"""make_rotor_loop_v002.py - a PLACEHOLDER drone rotor loop, with air in it.

Supersedes v001, which is kept as evidence. v001 was built from harmonic
partials only and is therefore seamless but WRONG in character: a rotor
is mostly broadband air noise with a blade-pass tone riding on it, and a
pure harmonic stack sounds like a small organ. Greg cannot judge whether
pitch-follows-rotor-speed feels right against an organ.

Noise was left out of v001 because random noise does not loop - the
buffer end would not join its start and the four-second click would be
worse than the wrong timbre. The fix is to build the WHOLE signal in the
frequency domain and transform it once: every component then lives on an
exact FFT bin, so it completes a whole number of cycles inside the
buffer and the loop is seamless BY CONSTRUCTION. Noise included.

The buffer length is a power of two (2^18 = 262144 frames, 5.94 s at
44.1 kHz) because that is what a radix-2 transform needs, and the exact
duration does not matter for a loop.

Pure standard library: no numpy, no audio tooling. Deterministic - the
phases come from a fixed seed, so re-running reproduces the asset
byte-for-byte, which is what makes the manifest hash meaningful.

Run: python make_rotor_loop_v002.py
"""

import cmath
import math
import os
import random
import struct
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rotor_loop_v002.wav")

RATE = 44100
LOG2N = 18
FRAMES = 1 << LOG2N
SECONDS = FRAMES / RATE
BIN_HZ = RATE / FRAMES  # ~0.168 Hz; every component snaps to a multiple

SEED = 20260827

# Blade-pass tone and its harmonics. Snapped to the nearest bin below,
# which is what guarantees the loop joins.
PARTIALS = [
    (110.0, 0.30),
    (220.0, 0.19),
    (330.0, 0.10),
    (440.0, 0.065),
    (660.0, 0.036),
    (880.0, 0.025),
    (1320.0, 0.014),
]

# The air. A rotor's noise is broadband with most energy low down and a
# long hiss tail; this envelope is a pink-ish rolloff with a broad hump
# where the blades chop, which is the part that reads as "rotor" rather
# than "fan".
NOISE_LOW_HZ = 90.0
NOISE_HIGH_HZ = 9000.0
NOISE_GAIN = 0.85
HUMP_CENTRE_HZ = 900.0
HUMP_WIDTH_OCT = 1.4
HUMP_GAIN = 1.8

# Four rotors never quite in sync. Snapped to a bin so the envelope's
# period divides the buffer and cannot break the seam either.
BEAT_HZ = 2.5
BEAT_DEPTH = 0.16


def noise_envelope(hz):
    """Relative magnitude of the noise floor at a frequency."""
    if hz < NOISE_LOW_HZ or hz > NOISE_HIGH_HZ:
        return 0.0
    # Pink-ish: energy falls as 1/f. Rotor noise is not white.
    tilt = math.sqrt(NOISE_LOW_HZ / hz)
    # Broad resonant hump around the blade-chop band, in octaves so it
    # is symmetric to the ear rather than to the number line.
    octaves = math.log(hz / HUMP_CENTRE_HZ, 2.0)
    hump = 1.0 + (HUMP_GAIN - 1.0) * math.exp(
        -(octaves / HUMP_WIDTH_OCT) ** 2)
    # Roll the very top off so the hiss does not sound like tape.
    rolloff = 1.0 / (1.0 + (hz / 5200.0) ** 2)
    return tilt * hump * rolloff


def inverse_fft(spectrum):
    """In-place iterative radix-2 inverse FFT. Pure stdlib on purpose."""
    n = len(spectrum)
    # Bit-reversal permutation.
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            spectrum[i], spectrum[j] = spectrum[j], spectrum[i]
    length = 2
    while length <= n:
        # +2i pi for the INVERSE transform.
        step = cmath.exp(2j * math.pi / length)
        half = length >> 1
        for start in range(0, n, length):
            w = 1.0 + 0.0j
            for offset in range(half):
                a = spectrum[start + offset]
                b = spectrum[start + offset + half] * w
                spectrum[start + offset] = a + b
                spectrum[start + offset + half] = a - b
                w *= step
        length <<= 1
    for i in range(n):
        spectrum[i] /= n
    return spectrum


def main():
    rng = random.Random(SEED)
    spectrum = [0j] * FRAMES
    half = FRAMES // 2

    def place(bin_index, magnitude, phase):
        """Set a bin and its conjugate, so the transform comes out real."""
        if bin_index <= 0 or bin_index >= half:
            return
        value = cmath.rect(magnitude, phase)
        spectrum[bin_index] += value
        spectrum[FRAMES - bin_index] += value.conjugate()

    for hz, amp in PARTIALS:
        # Snapping to the nearest bin is the whole seam guarantee: an
        # off-bin component would not close its cycle at the buffer end.
        place(int(round(hz / BIN_HZ)), amp * half,
              0.25 * math.pi if int(hz / 110.0) % 2 else 0.0)

    low_bin = max(1, int(NOISE_LOW_HZ / BIN_HZ))
    high_bin = min(half - 1, int(NOISE_HIGH_HZ / BIN_HZ))
    for bin_index in range(low_bin, high_bin + 1):
        magnitude = noise_envelope(bin_index * BIN_HZ)
        if magnitude <= 0.0:
            continue
        # Random PHASE, fixed magnitude envelope: that is what noise is.
        # Every bin is still an exact whole number of cycles, so this
        # hiss loops as cleanly as the tone does.
        place(bin_index, magnitude * NOISE_GAIN * half,
              rng.uniform(0.0, 2.0 * math.pi))

    raw = [value.real for value in inverse_fft(spectrum)]

    # Beat envelope, snapped to a bin so its period divides the buffer.
    beat_hz = round(BEAT_HZ / BIN_HZ) * BIN_HZ
    for index in range(FRAMES):
        raw[index] *= 1.0 + BEAT_DEPTH * math.sin(
            2.0 * math.pi * beat_hz * index / RATE)

    peak = max(abs(value) for value in raw) or 1.0
    # Headroom: this is pitch-shifted and layered across a dozen drones,
    # and clipping is not a placeholder problem.
    scale = 0.72 / peak
    frames = bytearray()
    for value in raw:
        frames += struct.pack("<h", int(
            max(-1.0, min(1.0, value * scale)) * 32767))
    with wave.open(OUT, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(bytes(frames))

    # Seam proof, as in v001: NOT "first sample equals last" - for a
    # periodic signal sample[N] equals sample[0], so sample[N-1] is one
    # ordinary step away and always differs. What clicks is a wrap step
    # LARGER than the steps either side of it.
    wrap_step = abs(raw[0] - raw[-1])
    typical = max(abs(raw[i + 1] - raw[i])
                  for i in range(0, FRAMES - 1, 97))
    print("wrote %s (%.2f s, %d frames)" % (OUT, SECONDS, FRAMES))
    print("wrap step %.5f vs largest ordinary step %.5f"
          % (wrap_step, typical))
    if wrap_step > typical * 1.5:
        raise SystemExit("FAIL CLOSED: loop seam would click")


if __name__ == "__main__":
    main()
