"""Paint spray booth shell, fully detailed. The piece the owner called out: the old
booths are grey boxes. A booth is recognised by what a box lacks - glazing showing the
robots inside, a supply plenum with filters and fans on the roof, floor-level extract,
and airlocked entry and exit for the body to pass through.

Robots come from owned content (BodyShopRobotNative) and are placed separately, so the
shell leaves the working volume clear.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          column, cyl, export, material, preview, reset)

GLASS = ("MAT_BoothGlazing", (0.58, 0.72, 0.76, 1.0))

reset()
L, W = 12.0, 5.6          # booth footprint, metres
EAVE = 3.6                # underside of the plenum
OPEN_W = 2.9              # entry and exit opening width

# Foundation, safety outline, and the grated extract strip down the centre.
box("Base", (L + 0.6, W + 0.6, 0.22), (0, 0, 0.11), CHARCOAL)
for sy in (-1, 1):
    box("Outline", (L + 0.6, 0.12, 0.03), (0, sy * (W / 2 + 0.24), 0.23), YELLOW)
box("ExtractGrate", (L - 1.0, 1.7, 0.05), (0, 0, 0.245), STEEL)
for n in range(11):
    box("GrateRib", (0.04, 1.7, 0.06), (-L / 2 + 1.0 + n * 1.0, 0, 0.25),
        CHARCOAL, chamfer=False)

# Columns every 4 m carry the plenum; kit columns bring plates, gussets, trays.
for sx in (-4.0, 0.0, 4.0):
    for sy in (-1, 1):
        column("Col", (sx, sy * (W / 2 - 0.15), 0.22), EAVE - 0.3, GREEN,
               width=0.22)

# Long walls: steel dado, then glazing with mullions - the robots show through.
for sy in (-1, 1):
    y = sy * (W / 2 - 0.03)
    box("Dado", (L - 0.4, 0.08, 1.15), (0, y, 0.8), STEEL)
    box("Glazing", (L - 0.4, 0.05, 2.0), (0, y, 2.45), GLASS)
    for n in range(13):
        box("Mullion", (0.07, 0.09, 2.0), (-L / 2 + 0.2 + n * 0.98, y, 2.45),
            CHARCOAL, chamfer=False)
    box("WallHead", (L - 0.4, 0.1, 0.24), (0, y, 3.52), GREEN)

# Ends: jambs, header, and a yellow airlock lip framing each opening.
for sx in (-1, 1):
    x = sx * (L / 2 - 0.03)
    for sy in (-1, 1):
        box("Jamb", (0.08, (W - OPEN_W) / 2 - 0.1, 3.3),
            (x, sy * (OPEN_W / 2 + (W - OPEN_W) / 4), 1.87), STEEL)
    box("Header", (0.1, W - 0.4, 0.7), (x, 0, 3.28), GREEN)
    box("LipTop", (0.14, OPEN_W + 0.2, 0.1), (x, 0, 2.98), YELLOW)
    for sy in (-1, 1):
        box("LipSide", (0.14, 0.1, 2.9), (x, sy * (OPEN_W / 2 + 0.05), 1.5),
            YELLOW)
    # Strip-curtain slats hanging in the opening: what an airlock looks like.
    for n in range(7):
        box("Curtain", (0.02, 0.34, 2.6),
            (x, -OPEN_W / 2 + 0.25 + n * 0.4, 1.55), WARMWHITE, chamfer=False)

# Roof plenum: filter housings in a row, two supply fans with cowls, main duct.
box("Plenum", (L + 0.3, W + 0.3, 1.05), (0, 0, EAVE + 0.55), CHARCOAL)
box("PlenumBand", (L + 0.34, W + 0.34, 0.12), (0, 0, EAVE + 0.06), GREEN)
for n in range(6):
    box("FilterBox", (1.5, 1.1, 0.5), (-L / 2 + 1.6 + n * 1.85, -1.1,
        EAVE + 1.32), GREEN)
for fx in (-2.6, 2.6):
    cyl("Fan", 0.55, 0.75, (fx, 1.25, EAVE + 1.45), STEEL)
    cyl("FanCowl", 0.68, 0.2, (fx, 1.25, EAVE + 1.85), CHARCOAL)
cyl("SupplyDuct", 0.42, 4.6, (L / 2 - 1.4, 1.25, EAVE + 1.45), STEEL, axis="X")
box("DuctBend", (0.9, 0.9, 0.9), (L / 2 + 1.0, 1.25, EAVE + 1.0), STEEL)

# Floor-level extract ducts along both walls with periodic grilles.
for sy in (-1, 1):
    y = sy * (W / 2 + 0.55)
    box("ExtractDuct", (L - 1.2, 0.6, 0.7), (0, y, 0.6), STEEL)
    for n in range(5):
        box("Grille", (0.8, 0.05, 0.4), (-L / 2 + 1.6 + n * 2.3,
            y - sy * 0.33, 0.6), CHARCOAL, chamfer=False)

# Interior light cornices so the glazing glows from inside.
for sy in (-1, 1):
    box("LightStrip", (L - 1.0, 0.16, 0.1), (0, sy * (W / 2 - 0.45), 3.42),
        WARMWHITE, chamfer=False)

# Controls: cabinet, gauge panel, isolator, e-stop, nameplate.
box("Cabinet", (0.9, 0.4, 1.7), (-L / 2 + 1.2, -(W / 2 + 0.75), 1.07), GREEN)
box("GaugePanel", (0.5, 0.06, 0.4), (-L / 2 + 2.0, -(W / 2 + 0.95), 1.5),
    WARMWHITE)
for n in range(3):
    cyl("Gauge", 0.06, 0.05, (-L / 2 + 1.85 + n * 0.15, -(W / 2 + 0.99), 1.5),
        CHARCOAL, axis="Y", verts=12)
cyl("Isolator", 0.05, 0.07, (-L / 2 + 0.95, -(W / 2 + 0.97), 1.35), YELLOW,
    axis="Y")
cyl("EStop", 0.06, 0.07, (-L / 2 + 1.45, -(W / 2 + 0.97), 1.35), RED, axis="Y")

export("SM_LB_Paint_SprayBoothShell_v001", "PaintShop/SprayBoothShell_v001")
preview("SM_LB_Paint_SprayBoothShell_v001", "PaintShop/SprayBoothShell_v001")
