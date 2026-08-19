"""Assembly closure fit gauge: checks a door/closure against its aperture.

Recognised by the aperture-shaped gauge arch on a fixture table, the steel
gauge edges inside the arch, three dial indicator pods on flex arms, and
the granite-dark surface plate. Robots present closures to it in the
lights-out cell.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, cyl, export,
                          preview, reset)

reset()

# Fixture table with a dark surface plate.
for lx in (-0.7, 0.7):
    for ly in (-0.45, 0.45):
        box("Leg", (0.10, 0.10, 0.72), (lx, ly, 0.36), GREEN)
box("TableFrame", (1.7, 1.1, 0.10), (0, 0, 0.77), GREEN)
box("SurfacePlate", (1.6, 1.0, 0.10), (0, 0, 0.87), CHARCOAL)

# Aperture-shaped gauge arch: uprights, header, steel gauge edges inside.
for gx in (-0.62, 0.62):
    box("GaugeUpright", (0.12, 0.16, 1.10), (gx, 0, 1.47), CHARCOAL)
    box("GaugeEdgeV", (0.03, 0.10, 0.95), (gx - (0.075 if gx > 0 else -0.075),
        0, 1.42), STEEL, chamfer=False)
box("GaugeHeader", (1.36, 0.16, 0.14), (0, 0, 2.06), CHARCOAL)
box("GaugeEdgeH", (1.1, 0.10, 0.03), (0, 0, 1.975), STEEL, chamfer=False)
box("HeaderCrown", (0.5, 0.14, 0.08), (0, 0, 2.16), GREEN)

# Probe cross-rails span the aperture; the dial arms clamp to them.
for rz in (1.30, 1.75):
    box("ProbeRail", (1.24, 0.04, 0.05), (0, -0.18, rz), CHARCOAL,
        chamfer=False)
box("ProbeRailV", (0.05, 0.04, 0.80), (0, -0.18, 1.62), CHARCOAL,
    chamfer=False)

# Dial indicator pods on flex arms reaching into the aperture.
for n, (px, pz) in enumerate(((-0.45, 1.75), (0.45, 1.30), (0.0, 1.75))):
    cyl("FlexArm", 0.022, 0.30, (px, -0.18, pz), STEEL, axis="Y", verts=8)
    cyl("DialBody", 0.05, 0.04, (px, -0.35, pz), WARMWHITE, axis="Y",
        verts=14)
    cyl("DialTip", 0.008, 0.06, (px, -0.10, pz), STEEL, axis="Y", verts=6)

box("IDPlate", (0.02, 0.22, 0.12), (0.86, 0, 0.6), WARMWHITE, chamfer=False)
box("CalTag", (0.10, 0.01, 0.06), (0.5, -0.51, 0.92), WARMWHITE,
    chamfer=False)

export("SM_LB_Assembly_ClosureFitGauge_v001", "AssemblyShop/ClosureGauge_v001")
preview("SM_LB_Assembly_ClosureFitGauge_v001", "AssemblyShop/ClosureGauge_v001")
