"""Weld respot gun stand: parks the spare C-guns beside the respot cells.

Recognised by the A-stand with three cradles, each holding a C-gun
silhouette (body, crossed arms, electrode caps), the coiled cable hooks
above each cradle, and the tip-dressing pocket on the end.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, box, cyl,
                          export, preview, reset)

reset()

# Stand frame.
box("Base", (1.8, 0.7, 0.08), (0, 0, 0.04), CHARCOAL)
for sx in (-0.8, 0.8):
    box("Upright", (0.10, 0.10, 1.5), (sx, 0, 0.83), GREEN)
box("TopRail", (1.8, 0.10, 0.10), (0, 0, 1.60), GREEN)
box("MidRail", (1.7, 0.08, 0.08), (0, 0, 0.95), CHARCOAL)

# Three parked C-guns in cradles.
for n, gx in enumerate((-0.55, 0.0, 0.55)):
    box("Cradle", (0.28, 0.30, 0.06), (gx, -0.05, 0.99), STEEL)
    box("GunBody", (0.16, 0.22, 0.30), (gx, 0.0, 1.20), GREEN)
    box("GunArmU", (0.05, 0.30, 0.05), (gx, -0.22, 1.33), STEEL)
    box("GunArmL", (0.05, 0.30, 0.05), (gx, -0.22, 1.10), STEEL)
    cyl("CapU", 0.02, 0.05, (gx, -0.36, 1.30), RED, verts=8)
    cyl("CapL", 0.02, 0.05, (gx, -0.36, 1.13), STEEL, verts=8)
    cyl("CableHook", 0.06, 0.04, (gx, 0.05, 1.62), STEEL, axis="Y", verts=10)
    cyl("CableLoop", 0.09, 0.02, (gx, 0.05, 1.52), CHARCOAL, axis="Y",
        verts=14)

# Tip-dressing pocket on the end upright.
box("TipPocket", (0.14, 0.20, 0.18), (0.88, 0, 1.15), CHARCOAL)
box("IDPlate", (0.02, 0.18, 0.10), (-0.91, 0, 1.2), WARMWHITE, chamfer=False)

export("SM_LB_Weld_RespotGunStand_v001", "WeldShop/RespotGunStand_v001")
preview("SM_LB_Weld_RespotGunStand_v001", "WeldShop/RespotGunStand_v001")
