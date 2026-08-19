"""Paint UF membrane skid: ultrafiltration recovering ED paint from rinse.

Recognised by the rack of four horizontal membrane housings with domed end
caps, the feed pump, the permeate manifold with its small valves and
gauges, and the skid frame with control box.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

box("Skid", (2.6, 1.1, 0.12), (0, 0, 0.06), CHARCOAL)
for sx in (-1.15, 1.15):
    box("SkidRail", (0.10, 1.1, 0.16), (sx, 0, 0.20), GREEN)

# Rack of four membrane housings with domed caps.
for n in range(4):
    hz = 0.55 + n * 0.38
    cyl("Housing", 0.13, 2.2, (0, 0.15, hz), STEEL, axis="X", verts=18)
    for ex in (-1.1, 1.1):
        cyl("EndCap", 0.145, 0.10, (ex, 0.15, hz), GREEN, axis="X", verts=18)
    for rx in (-0.7, 0.7):
        box("HousingClamp", (0.06, 0.10, 0.30), (rx, 0.15, hz - 0.12),
            CHARCOAL, chamfer=False)
for rx in (-0.7, 0.7):
    box("RackPost", (0.10, 0.10, 1.85), (rx, 0.15, 0.97), GREEN)

# Feed pump and the permeate manifold with valves and gauges.
cyl("FeedPump", 0.16, 0.4, (-0.9, -0.35, 0.42), GREEN, axis="X", verts=16)
cyl("PumpMotor", 0.12, 0.3, (-1.25, -0.35, 0.42), CHARCOAL, axis="X",
    verts=14)
cyl("Manifold", 0.05, 2.2, (0, -0.42, 1.85), STEEL, axis="X", verts=12)
for n in range(4):
    mx = -0.85 + n * 0.55
    cyl("ManValve", 0.06, 0.04, (mx, -0.42, 1.97), YELLOW, verts=10)
    cyl("Gauge", 0.05, 0.03, (mx + 0.25, -0.47, 1.85), WARMWHITE, axis="Y",
        verts=12)
    cyl("DropPipe", 0.03, 0.55, (mx, -0.30, 1.55), STEEL, verts=8,
        axis="Z")
box("ControlBox", (0.4, 0.25, 0.55), (1.05, -0.35, 0.6), GREEN)
cyl("BoxEStop", 0.035, 0.04, (1.05, -0.49, 0.75), RED, axis="Y")
box("IDPlate", (0.02, 0.2, 0.11), (-1.21, 0, 0.22), WARMWHITE, chamfer=False)

export("SM_LB_Paint_UFMembraneSkid_v001", "PaintShop/UFMembraneSkid_v001")
preview("SM_LB_Paint_UFMembraneSkid_v001", "PaintShop/UFMembraneSkid_v001")
