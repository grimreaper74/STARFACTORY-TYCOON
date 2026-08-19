"""Site solar canopy module: the PV roof over the dispatch lanes.

2040 EV plant flavour: recognised by the four raking columns, the tilted
panel deck with its grid of PV cells (charcoal panels with steel frame
lines), and the cable drop to a combiner box. 20 x 18 m module that
chains along the dispatch compound.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

TILT = math.radians(8.0)
# Four raking columns, taller pair at the north edge for the tilt.
for sx in (-8.0, 8.0):
    column("PostS", (sx, -7.0, 0), 4.6, GREEN, width=0.34)
    column("PostN", (sx, 7.0, 0), 6.6, GREEN, width=0.34)
# Rafters follow the tilt from south (low) to north (high).
for sx in (-8.0, 0.0, 8.0):
    box("Rafter", (0.24, 15.4, 0.3), (sx, 0, 5.75), STEEL,
        rot=(TILT, 0.0, 0.0))
box("EdgeBeamS", (17.0, 0.25, 0.3), (0, -7.0, 4.72), GREEN)
box("EdgeBeamN", (17.0, 0.25, 0.3), (0, 7.0, 6.68), GREEN)

# Tilted PV deck: panel field with frame lines reading as cell rows.
box("PVDeck", (16.6, 14.6, 0.12), (0, 0, 5.85), CHARCOAL,
    rot=(TILT, 0.0, 0.0))
for n in range(7):
    sy = -6.0 + n * 2.0
    box("PVFrameRow", (16.6, 0.08, 0.05),
        (0, sy, 5.92 + math.tan(TILT) * sy), STEEL, rot=(TILT, 0.0, 0.0),
        chamfer=False)
for n in range(5):
    sx = -6.64 + n * 3.32
    box("PVFrameCol", (0.08, 14.6, 0.05),
        (sx, 0, 5.92), STEEL, rot=(TILT, 0.0, 0.0), chamfer=False)

# Cable drop to the combiner box on the north-west post.
box("Combiner", (0.5, 0.3, 0.7), (-8.0, 6.68, 2.4), GREEN)
cyl("CableDrop", 0.035, 3.4, (-8.0, 6.85, 4.6), CHARCOAL, verts=8)
box("IDPlate", (0.02, 0.3, 0.16), (-8.24, 6.68, 1.6), WARMWHITE,
    chamfer=False)

export("SM_LB_Site_SolarCanopy_v001", "Site/SolarCanopy_v001")
preview("SM_LB_Site_SolarCanopy_v001", "Site/SolarCanopy_v001",
        distance=45.0)
