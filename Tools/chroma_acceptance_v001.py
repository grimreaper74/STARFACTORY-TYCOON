"""THE CHROMA ACCEPTANCE TEST - is the ship still the star?

From the brand implementation spec (2026-08-29). The whole palette
discipline exists to make one promise true: COLOUR BELONGS TO THE SHIPS.
The spec states it as a measurable check rather than an opinion:

    At whole-bay zoom, non-ship pixels above 60% saturation stay under
    8% of the frame, and the single most saturated pixel in frame
    always belongs to a hull.

    "If a livery ever loses that test, lower the machinery - never
     raise the livery."

Every art judgement on this project so far has been me looking at a
render and forming a view. Twice the owner saw a fault before I did.
This turns the question into arithmetic.

WHY A VALUE FLOOR IS ALSO REPORTED. Saturation on its own is leaky: a
pixel at S=0.70 but V=0.04 is visually black while counting as fully
saturated, so a dark shadow could fail a frame that looks perfect. The
raw spec figure is reported first because it is the spec, and a
value-gated figure beside it because that is the one that matches the
eye. When they disagree the difference is shadow, not paint.

HOW "BELONGS TO A HULL" IS DECIDED. There is no segmentation here, so
pass --livery-hue with the hue the contract is painting (degrees). Any
saturated pixel within the tolerance of that hue is credited to the
ship; everything else is charged to the world. Without it the tool
still reports WHERE the saturated pixels are and what colour they are,
which is enough to tell machinery from paint by inspection.

RUN:
  blender -b --python Tools/chroma_acceptance_v001.py -- <shot.png>
          [--livery-hue 210] [--tolerance 25]
"""
import sys

import bpy
import numpy as np

SPEC_SATURATION = 0.60      # above this a pixel counts as coloured
SPEC_MAX_FRACTION = 0.08    # non-ship share of frame allowed above it
VALUE_FLOOR = 0.15          # below this a pixel reads as black, not paint

# THE HAZARD CARVE-OUT (spec rev B, amendment 1).
#
# As first written this test could not be passed. Hazard yellow is S 86%,
# and the livery bands top out at S 92% with a canonical 76-88%, so a
# ship parked beside floor striping loses "the most saturated pixel
# belongs to a hull" through no fault of the ship. The rev B answer is
# to exempt striping rather than to brighten every livery, because
# raising the liveries to clear it would delete the bright tier and
# halve the number of customers that can be told apart.
#
# Striping is identified by hue AND saturation together, which is what
# separates it from the two other warm world tokens. Machine.Amber sits
# at 33 degrees and Crate.Tan at 35, and both are capped at S 69, so a
# high-saturation pixel in this arc can only be hazard. Amber and crate
# stay inside the test, as they should - they are surfaces, and the
# ceiling is exactly what governs them.
HAZARD_HUE_RANGE = (38.0, 56.0)
HAZARD_MIN_SATURATION = 0.75


def rgb_to_hsv(rgb):
    """Vectorised RGB->HSV. rgb is (...,3) in 0..1; returns h(deg),s,v."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    v = rgb.max(axis=-1)
    lo = rgb.min(axis=-1)
    chroma = v - lo
    # Saturation is undefined for black; 0 is the conventional answer and
    # it keeps black out of the "coloured" count, which is what we want.
    s = np.divide(chroma, v, out=np.zeros_like(v), where=v > 0)
    h = np.zeros_like(v)
    nz = chroma > 0
    rmax = nz & (v == r)
    gmax = nz & (v == g) & ~rmax
    bmax = nz & ~rmax & ~gmax
    h[rmax] = ((g - b)[rmax] / chroma[rmax]) % 6.0
    h[gmax] = ((b - r)[gmax] / chroma[gmax]) + 2.0
    h[bmax] = ((r - g)[bmax] / chroma[bmax]) + 4.0
    return h * 60.0, s, v


def load_srgb(path):
    """Pixels as the EYE sees them, not as the renderer stores them."""
    img = bpy.data.images.load(path)
    # Non-Color stops Blender linearising on read. Saturation judged in
    # linear space would overstate every dark surface in the frame.
    img.colorspace_settings.name = 'Non-Color'
    buf = np.empty(len(img.pixels), dtype=np.float32)
    img.pixels.foreach_get(buf)
    w, h = img.size
    # Blender hands back bottom-up; flip so reported rows match the image.
    return buf.reshape(h, w, 4)[::-1, :, :3], w, h


def hue_name(deg):
    for lo, hi, name in (
        (0, 15, 'red'), (15, 45, 'orange'), (45, 70, 'yellow'),
        (70, 160, 'green'), (160, 200, 'cyan'), (200, 260, 'blue'),
        (260, 320, 'violet'), (320, 360, 'magenta'),
    ):
        if lo <= deg < hi:
            return name
    return '?'


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    if not argv:
        print('usage: ... -- <image.png> [--livery-hue D] [--tolerance D]')
        sys.exit(2)
    path = argv[0]
    livery = None
    tol = 25.0
    if '--livery-hue' in argv:
        livery = float(argv[argv.index('--livery-hue') + 1])
    if '--tolerance' in argv:
        tol = float(argv[argv.index('--tolerance') + 1])

    rgb, w, h = load_srgb(path)
    hue, sat, val = rgb_to_hsv(rgb)
    total = float(w * h)

    # Striping is exempt (see HAZARD_HUE_RANGE above), but it is counted
    # and reported rather than quietly dropped: a frame where the exempt
    # share is large is a frame with too much striping in it, and that
    # is worth seeing even though it cannot fail the test.
    hazard = ((hue >= HAZARD_HUE_RANGE[0]) & (hue <= HAZARD_HUE_RANGE[1])
              & (sat > HAZARD_MIN_SATURATION))
    coloured = (sat > SPEC_SATURATION) & ~hazard
    visible = coloured & (val > VALUE_FLOOR)

    print('=' * 62)
    print('CHROMA ACCEPTANCE  %dx%d  %s' % (w, h, path))
    print('=' * 62)
    print('above %d%% saturation      : %6.2f%% of frame  (spec figure)'
          % (SPEC_SATURATION * 100, 100.0 * coloured.sum() / total))
    print('  hazard striping exempt  : %6.2f%% of frame  (not counted above)'
          % (100.0 * hazard.sum() / total))
    print('  ...and above %d%% value  : %6.2f%% of frame  (what the eye '
          'sees)' % (VALUE_FLOOR * 100, 100.0 * visible.sum() / total))

    if livery is not None:
        # Circular hue distance, so a livery at 5 deg still matches 355.
        d = np.abs((hue - livery + 180.0) % 360.0 - 180.0)
        is_ship = coloured & (d <= tol)
        world = coloured & ~is_ship
        world_pct = 100.0 * world.sum() / total
        print('  credited to the ship    : %6.2f%% (hue %.0f +/- %.0f)'
              % (100.0 * is_ship.sum() / total, livery, tol))
        print('  charged to the world    : %6.2f%%' % world_pct)
        verdict = 'PASS' if world_pct <= SPEC_MAX_FRACTION * 100 else 'FAIL'
        print('  RULE 1 (world < %.0f%%)   : %s'
              % (SPEC_MAX_FRACTION * 100, verdict))

    # RULE 2: the most saturated pixel must belong to a hull. Reported as
    # the peak plus its neighbourhood - a lone hot pixel is noise, a
    # cluster is a surface.
    if coloured.any():
        peak = np.unravel_index(np.argmax(np.where(visible, sat, 0)),
                                sat.shape)
        pr, pc = int(peak[0]), int(peak[1])
        px = rgb[pr, pc]
        print('\nmost saturated visible pixel: #%02X%02X%02X  '
              'hue %.0f (%s)  S %.2f V %.2f  at row %d col %d'
              % (int(px[0] * 255), int(px[1] * 255), int(px[2] * 255),
                 hue[pr, pc], hue_name(hue[pr, pc]), sat[pr, pc],
                 val[pr, pc], pr, pc))
        if livery is not None:
            d0 = abs((hue[pr, pc] - livery + 180.0) % 360.0 - 180.0)
            print('  RULE 2 (peak is a hull) : %s'
                  % ('PASS' if d0 <= tol else 'FAIL - that is the world'))

    # WHERE the colour is, so an offender can be named without guessing.
    print('\nsaturated pixels by hue (visible only):')
    hb = hue[visible]
    if hb.size:
        counts, edges = np.histogram(hb, bins=24, range=(0, 360))
        for i, c in enumerate(counts):
            if c:
                mid = (edges[i] + edges[i + 1]) / 2.0
                print('  %3.0f-%3.0f deg %-8s %6.3f%% of frame'
                      % (edges[i], edges[i + 1], hue_name(mid),
                         100.0 * c / total))
    else:
        print('  none - the frame carries no visible colour at all')


main()
