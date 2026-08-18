"""Paint shop ED dip tank: one 18 m open tank of the treatment line.

The ED line must read as open dip tanks under an overhead carrier (owner
brief). A tank is recognised by its stiffened walls, the dark liquid surface
just below the rim, the anode bus rails running the length of both inner
walls, the circulation pipework with pump pods along one side, and the weir
box and level mast at the outlet end.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

L, W, H = 18.0, 5.0, 3.0

# Tank shell with external stiffeners and rim capping.
for sy in (-W * 0.5, W * 0.5):
    box("WallLong", (L, 0.12, H), (0, sy, H * 0.5), GREEN)
    for n in range(13):
        box("Stiffener", (0.14, 0.22, H - 0.2), (-L * 0.5 + 0.7 + n * 1.4,
            sy * 1.02, (H - 0.2) * 0.5), CHARCOAL)
for sx in (-L * 0.5, L * 0.5):
    box("WallEnd", (0.12, W, H), (sx, 0, H * 0.5), GREEN)
    box("EndStiffX", (0.22, 0.14, H - 0.2), (sx * 1.005, 0, (H - 0.2) * 0.5),
        CHARCOAL)
box("RimN", (L + 0.2, 0.30, 0.10), (0, W * 0.5, H + 0.03), CHARCOAL)
box("RimS", (L + 0.2, 0.30, 0.10), (0, -W * 0.5, H + 0.03), CHARCOAL)
box("RimE", (0.30, W, 0.10), (L * 0.5, 0, H + 0.03), CHARCOAL)
box("RimW", (0.30, W, 0.10), (-L * 0.5, 0, H + 0.03), CHARCOAL)

# Liquid surface just below the rim.
box("Liquid", (L - 0.3, W - 0.3, 0.03), (0, 0, H - 0.25), CHARCOAL,
    chamfer=False)

# Anode bus rails along both inner walls with insulator studs.
for sy in (-W * 0.5 + 0.35, W * 0.5 - 0.35):
    box("AnodeRail", (L - 1.0, 0.08, 0.16), (0, sy, H - 0.05), STEEL)
    for n in range(9):
        cyl("Insulator", 0.05, 0.12, (-L * 0.5 + 1.0 + n * 2.0, sy, H + 0.02),
            WARMWHITE, verts=10)

# Bus bars and rectifier connection boxes on the north rim.
for n in range(4):
    bx = -L * 0.5 + 2.5 + n * 4.4
    box("BusBox", (0.5, 0.4, 0.35), (bx, W * 0.5 + 0.35, H + 0.20), CHARCOAL)
    box("BusBar", (0.32, 0.5, 0.06), (bx, W * 0.5 + 0.05, H + 0.06), STEEL,
        chamfer=False)

# Circulation pipework with pump pods and valve wheels along the south side.
for pz, pr in ((0.5, 0.14), (0.95, 0.14)):
    cyl("CircPipe", pr, L - 1.4, (0, -W * 0.5 - 0.45, pz), STEEL, axis="X",
        verts=14)
for n in range(3):
    px = -L * 0.5 + 3.2 + n * 5.6
    cyl("PumpBody", 0.30, 0.75, (px, -W * 0.5 - 0.45, 0.55), GREEN, axis="X",
        verts=16)
    cyl("PumpMotor", 0.22, 0.45, (px + 0.6, -W * 0.5 - 0.45, 0.55), CHARCOAL,
        axis="X", verts=16)
    box("PumpBase", (0.9, 0.6, 0.12), (px + 0.2, -W * 0.5 - 0.45, 0.06),
        CHARCOAL)
    cyl("ValveWheel", 0.11, 0.05, (px - 0.7, -W * 0.5 - 0.45, 1.12), YELLOW,
        axis="X", verts=14)
    cyl("RiserPipe", 0.10, 1.6, (px - 1.3, -W * 0.5 - 0.30, 1.6), STEEL,
        verts=12)

# Weir box, level mast and beacon at the outlet end.
box("WeirBox", (0.8, 1.4, 0.9), (L * 0.5 + 0.45, 0, 2.7), GREEN)
box("WeirLip", (0.06, 1.3, 0.08), (L * 0.5 + 0.06, 0, 2.98), STEEL,
    chamfer=False)
cyl("LevelMast", 0.035, 1.4, (L * 0.5 + 0.7, 1.2, 3.6), STEEL, verts=10)
box("LevelBox", (0.18, 0.14, 0.22), (L * 0.5 + 0.7, 1.2, 4.35), GREEN)
cyl("Beacon", 0.045, 0.10, (L * 0.5 + 0.7, 1.2, 4.55), RED)
box("IDPlate", (0.02, 0.6, 0.3), (-L * 0.5 - 0.07, 0, 2.2), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_EDDipTank_v001", "PaintShop/EDDipTank_v001")
preview("SM_LB_Paint_EDDipTank_v001", "PaintShop/EDDipTank_v001")
