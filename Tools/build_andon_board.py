"""Assembly andon board over the line entry.

Recognised by its two slim posts carrying a wide display board: warmwhite
main panel, green header band, a row of station cells and one alarm cell,
with the catwalk-style service rail behind and conduit down one post.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, box, cyl,
                          export, preview, reset)

reset()

for sx in (-1.9, 1.9):
    box("PostPlate", (0.30, 0.30, 0.04), (sx, 0, 0.02), CHARCOAL,
        chamfer=False)
    box("Post", (0.16, 0.16, 4.4), (sx, 0, 2.24), GREEN)
box("Board", (4.4, 0.18, 1.30), (0, 0, 4.0), CHARCOAL)
box("Header", (4.4, 0.02, 0.28), (0, -0.10, 4.48), GREEN, chamfer=False)
box("MainPanel", (3.9, 0.02, 0.62), (0, -0.10, 3.98), WARMWHITE,
    chamfer=False)
for n in range(6):
    box("StationCell", (0.48, 0.02, 0.22), (-1.55 + n * 0.62, -0.105, 3.52),
        CHARCOAL, chamfer=False)
box("AlarmCell", (0.48, 0.02, 0.22), (1.55, -0.105, 3.52), RED,
    chamfer=False)
box("ServiceRail", (4.2, 0.08, 0.08), (0, 0.16, 4.55), STEEL, chamfer=False)
cyl("Conduit", 0.025, 3.2, (1.82, 0.12, 1.9), STEEL, verts=10)
box("JBox", (0.14, 0.12, 0.18), (1.82, 0.14, 3.55), GREEN)

export("SM_LB_Assembly_AndonBoard_v001", "AssemblyShop/AndonBoard_v001")
preview("SM_LB_Assembly_AndonBoard_v001", "AssemblyShop/AndonBoard_v001")
