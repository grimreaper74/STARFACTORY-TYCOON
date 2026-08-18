"""Assembly fluid fill machine: evacuate-and-fill unit for the final line.

The Cairnwell 2040 is electric, so the farm is coolant, brake fluid,
refrigerant and screenwash - no fuel. One machine is recognised by its tall
cabinet with a reel boom, the coiled fill hose with a heavy coupler head, the
vacuum gauge cluster, and the bunded drip tray it stands in.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# Bunded tray and the cabinet standing in it.
box("Bund", (1.30, 1.00, 0.10), (0, 0, 0.05), CHARCOAL)
for ly in (-0.48, 0.48):
    box("BundLipY", (1.30, 0.04, 0.14), (0, ly, 0.11), YELLOW, chamfer=False)
for lx in (-0.63, 0.63):
    box("BundLipX", (0.04, 1.00, 0.14), (lx, 0, 0.11), YELLOW, chamfer=False)
box("Cabinet", (0.85, 0.65, 1.75), (0, 0.05, 0.98), GREEN)
box("CabDoor", (0.60, 0.02, 1.30), (-0.05, -0.28, 0.85), CHARCOAL,
    chamfer=False)
cyl("DoorHandle", 0.012, 0.14, (0.20, -0.30, 0.95), STEEL, verts=8)
for v in range(4):
    box("Louvre", (0.42, 0.02, 0.02), (-0.05, -0.29, 0.35 + v * 0.07),
        CHARCOAL, chamfer=False)

# Gauge cluster and controls on the face.
for n, gx in enumerate((-0.25, -0.05, 0.15)):
    cyl("Gauge", 0.055, 0.03, (gx, -0.29, 1.55), WARMWHITE, axis="Y",
        verts=14)
box("Panel", (0.42, 0.02, 0.20), (-0.05, -0.29, 1.28), CHARCOAL,
    chamfer=False)
cyl("EStop", 0.045, 0.05, (0.26, -0.30, 1.28), RED, axis="Y")
cyl("Isolator", 0.03, 0.05, (0.26, -0.30, 1.48), YELLOW, axis="Y")

# Reel boom with the coiled hose and coupler head.
box("Boom", (0.90, 0.12, 0.12), (0.30, 0.05, 1.95), GREEN)
cyl("Reel", 0.26, 0.14, (0.68, 0.05, 1.72), CHARCOAL, axis="Y", verts=20)
cyl("ReelHub", 0.08, 0.18, (0.68, 0.05, 1.72), STEEL, axis="Y", verts=12)
# Hose drop with a catenary segment and the coupler head at working height.
cyl("HoseDrop", 0.03, 0.85, (0.68, 0.05, 1.22), CHARCOAL, verts=12)
box("Coupler", (0.10, 0.10, 0.22), (0.68, 0.05, 0.72), STEEL)
cyl("CouplerTip", 0.035, 0.10, (0.68, 0.05, 0.58), YELLOW, verts=10)

# Vacuum pump pod and supply pipes up the back.
cyl("VacPump", 0.14, 0.36, (-0.30, -0.42, 0.28), CHARCOAL, axis="X",
    verts=16)
cyl("PumpPipe", 0.03, 0.35, (-0.30, -0.30, 0.50), STEEL, verts=10)
for n, px in enumerate((-0.15, 0.0, 0.15)):
    cyl("SupplyPipe", 0.025, 1.9, (px, 0.36, 1.05), STEEL, verts=10)
box("PipeClamp", (0.44, 0.06, 0.06), (0, 0.36, 1.60), CHARCOAL)
box("IDPlate", (0.20, 0.02, 0.10), (-0.05, -0.29, 1.80), WARMWHITE,
    chamfer=False)
# Vent grid high on the reel side so no face reads blank.
for v in range(3):
    box("SideVent", (0.02, 0.30, 0.02), (0.44, 0.05, 1.30 + v * 0.06),
        CHARCOAL, chamfer=False)
box("HosePark", (0.06, 0.12, 0.10), (0.44, -0.10, 0.90), CHARCOAL)

export("SM_LB_Assembly_FluidFillMachine_v001", "AssemblyShop/FluidFill_v001")
preview("SM_LB_Assembly_FluidFillMachine_v001", "AssemblyShop/FluidFill_v001")
