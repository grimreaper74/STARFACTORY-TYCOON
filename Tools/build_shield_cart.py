"""Assembly underbody battery-shield cart (EV - no exhaust systems exist).

Recognised by its castored cart frame with two rails of leaning composite
shield panels, the end retainers, and the kanban pocket. Stages the
underbody aero and battery shield panels at the underbody stations.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

box("Deck", (1.8, 1.0, 0.08), (0, 0, 0.24), GREEN)
for cx in (-0.75, 0.75):
    for cy in (-0.38, 0.38):
        cyl("Castor", 0.07, 0.05, (cx, cy, 0.07), CHARCOAL, axis="Y",
            verts=12)
        box("CastorFork", (0.05, 0.09, 0.10), (cx, cy, 0.15), STEEL,
            chamfer=False)
cyl("Handle", 0.02, 0.9, (-0.95, 0, 0.95), STEEL, axis="Y", verts=10)
for hy in (-0.4, 0.4):
    cyl("HandlePost", 0.02, 0.6, (-0.95, hy, 0.62), STEEL, verts=10)

# Two rails of leaning shield panels with end retainers.
for ry in (-0.3, 0.3):
    box("Rail", (1.7, 0.08, 0.08), (0, ry, 0.32), CHARCOAL)
    for n in range(5):
        box("Shield", (0.03, 0.52, 0.75), (-0.6 + n * 0.3, ry, 0.72),
            CHARCOAL, rot=(0.0, -0.18, 0.0), chamfer=False)
        box("ShieldRib", (0.032, 0.40, 0.06), (-0.6 + n * 0.3, ry, 0.72),
            STEEL, rot=(0.0, -0.18, 0.0), chamfer=False)
for ex in (-0.85, 0.85):
    box("Retainer", (0.06, 0.9, 0.5), (ex, 0, 0.55), GREEN)
box("Kanban", (0.02, 0.24, 0.16), (0.92, 0, 0.62), WARMWHITE, chamfer=False)

export("SM_LB_Assembly_ShieldCart_v001", "AssemblyShop/ShieldCart_v001")
preview("SM_LB_Assembly_ShieldCart_v001", "AssemblyShop/ShieldCart_v001")
