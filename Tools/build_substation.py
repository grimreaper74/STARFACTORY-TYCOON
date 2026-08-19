"""Site substation and battery farm: the EV plant's own energy compound.

Recognised by the two finned transformers with bushings on plinths, the
HV portal frame with insulator strings, the row of battery containers
with vent bands and status stripes, and the LV cabinet row.
"""
import sys

import bpy

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import lb_model_kit as kit
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("Pad", (26.0, 32.0, 0.2), (0, 0, 0.1), CHARCOAL)

# Two transformers: finned tank, plinth, conservator drum, HV bushings.
for tx in (-6.0, 6.0):
    box("TxPlinth", (4.6, 3.6, 0.4), (tx, -10.0, 0.4), CHARCOAL)
    box("TxTank", (4.0, 3.0, 3.2), (tx, -10.0, 2.2), GREEN)
    for n in range(6):
        box("TxFin", (0.08, 2.6, 2.6), (tx - 2.06 + n * 0.82, -11.56, 2.1),
            STEEL, chamfer=False)
    cyl("Conservator", 0.5, 2.4, (tx, -8.3, 4.1), STEEL, axis="Y", verts=16)
    for bx in (-1.2, 0.0, 1.2):
        cyl("Bushing", 0.14, 1.2, (tx + bx, -10.0, 4.4), WARMWHITE, verts=10)
        cyl("BushingCap", 0.2, 0.1, (tx + bx, -10.0, 5.05), STEEL, verts=10)

# HV portal with insulator strings feeding the transformers.
for px in (-10.0, 10.0):
    box("PortalPost", (0.3, 0.3, 7.0), (px, -14.5, 3.5), STEEL)
box("PortalBeam", (20.6, 0.3, 0.35), (0, -14.5, 7.0), STEEL)
for ix in (-6.0, 0.0, 6.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.04,
                                     location=(ix, -14.5, 6.86),
                                     major_segments=12, minor_segments=6)
    ring = bpy.context.active_object
    ring.name = "InsulatorRing"
    ring.data.materials.append(kit.material(*CHARCOAL))
    cyl("InsulatorString", 0.09, 1.4, (ix, -14.5, 6.1), WARMWHITE, verts=10)

# Battery farm: two rows of three containers with vent bands and stripes.
for row, ry in enumerate((4.0, 10.0)):
    for n in range(3):
        cx = -8.0 + n * 8.0
        box("BatteryContainer", (6.5, 2.6, 2.9), (cx, ry, 1.45), GREEN)
        box("ContainerRoof", (6.6, 2.7, 0.08), (cx, ry, 2.94), CHARCOAL)
        box("VentBand", (6.0, 0.06, 0.8), (cx, ry - 1.31, 1.9), STEEL,
            chamfer=False)
        box("StatusStripe", (6.0, 0.05, 0.18), (cx, ry - 1.32, 0.9),
            ("MAT_StatusGreen", (0.05, 0.5, 0.15, 1.0)), chamfer=False)

# LV cabinet row along the east edge.
for n in range(5):
    box("LVCabinet", (1.2, 0.8, 2.0), (11.6, -6.0 + n * 3.0, 1.1), GREEN)
    box("LVCap", (1.3, 0.9, 0.07), (11.6, -6.0 + n * 3.0, 2.16), CHARCOAL)
box("IDPlate", (0.02, 0.6, 0.3), (12.22, -6.0, 1.3), WARMWHITE, chamfer=False)

export("SM_LB_Site_Substation_v001", "Site/Substation_v001")
preview("SM_LB_Site_Substation_v001", "Site/Substation_v001", distance=60.0)
