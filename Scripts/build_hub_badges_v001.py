"""Draw the site hub's state badges.

The first padlock was four rectangles assembled in widget code. It read
correctly, which was all it aimed for, but against a painted site it
looked exactly like what it was. These are drawn properly: a rounded
plate, a padlock with a real arc shackle, and a plus for a place the
player can build right now.

SHAPES, NEVER LETTERS. A padlock and a plus carry no language, which is
the whole reason for choosing them over the words LOCKED and BUILD - no
artwork in this game may contain text, because it ships translated.

Interface colours, not world colours, because these are the game
talking to the player rather than part of the picture:
  plate  #0B0B0B at 88%   (Panel.Edge, near-black)
  face   #EDEDEC          (Text.Body)

Run with any Python that has Pillow:
  python build_hub_badges_v001.py <outdir>
"""
import os
import sys

from PIL import Image, ImageDraw

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

S = 256                      # drawn large, mip-ed down by the engine
SS = 4                       # supersample, then downsample for clean edges
PLATE = (11, 11, 11, 224)
FACE = (237, 237, 236, 255)


def canvas():
    return Image.new('RGBA', (S * SS, S * SS), (0, 0, 0, 0))


def plate(d):
    """The rounded plate every badge sits on, inset so the rounding is
    not clipped when the engine pads to a power of two."""
    m = 10 * SS
    d.rounded_rectangle([m, m, S * SS - m, S * SS - m],
                        radius=44 * SS, fill=PLATE)


def save(img, name):
    img = img.resize((S, S), Image.LANCZOS)
    path = os.path.join(OUT, name + '.png')
    img.save(path)
    print('WROTE', path)


def padlock():
    img = canvas()
    d = ImageDraw.Draw(img)
    plate(d)
    cx = S * SS // 2
    # Body: a rounded block in the lower half.
    bw, bh = 108 * SS, 84 * SS
    by = 150 * SS
    d.rounded_rectangle([cx - bw // 2, by - bh // 2,
                         cx + bw // 2, by + bh // 2],
                        radius=16 * SS, fill=FACE)
    # Shackle: a real arc, open at the bottom, drawn as a thick arc so
    # it reads as a loop rather than two posts and a bar.
    r = 38 * SS
    top = 78 * SS
    d.arc([cx - r, top - r, cx + r, top + r], start=180, end=360,
          fill=FACE, width=18 * SS)
    # The uprights that meet the body.
    for sx in (-1, 1):
        x = cx + sx * r
        d.rounded_rectangle([x - 9 * SS, top, x + 9 * SS, by - bh // 2 + 6 * SS],
                            radius=5 * SS, fill=FACE)
    # Keyway: a slot, not a letter.
    d.rounded_rectangle([cx - 7 * SS, by - 20 * SS,
                         cx + 7 * SS, by + 22 * SS],
                        radius=7 * SS, fill=PLATE)
    save(img, 'T_LB_Icon_HubLocked_v001')


def plus():
    img = canvas()
    d = ImageDraw.Draw(img)
    plate(d)
    cx = S * SS // 2
    arm, thick = 76 * SS, 24 * SS
    d.rounded_rectangle([cx - arm, cx - thick // 2, cx + arm, cx + thick // 2],
                        radius=thick // 2, fill=FACE)
    d.rounded_rectangle([cx - thick // 2, cx - arm, cx + thick // 2, cx + arm],
                        radius=thick // 2, fill=FACE)
    save(img, 'T_LB_Icon_HubBuild_v001')


padlock()
plus()
print('HUB BADGES DONE')
