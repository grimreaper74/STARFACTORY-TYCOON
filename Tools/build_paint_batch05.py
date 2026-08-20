"""Journey batch 5 - paint's six most-placed, footprint-true rebuilds.

The ED line's shapes are owner-approved; these lift fidelity while
keeping each mesh's measured footprint so the approved read survives:
PF track portal (4.0 x 4.0 x 5.9 m), PF carrier, ED dip tank
(19 x 6.3 x 4.6 m), oven segment, rectifier cabinet, pipe bridge.
Original names into DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- PF track portal: legs, head rail, hanger trolleys ----
NAME = "SM_LB_Paint_PFTrackSegment_v001"
kit.reset(); kit.glass_material()
for sy in (-1.85, 1.85):
    kit.column("Leg", (0.0, sy, 0.0), 5.45, kit.GREEN, width=0.22)
kit.box("HeadRail", (4.0, 0.16, 0.30), (0.0, 0.0, 5.70), kit.STEEL)
kit.box("CrossBeam", (0.20, 3.9, 0.26), (0.0, 0.0, 5.45), kit.GREEN)
for sy in (-1.72, 1.72):
    kit.box("Gusset", (0.10, 0.35, 0.35), (0.0, sy, 5.28), kit.GREEN,
            rot=(math.radians(45.0), 0.0, 0.0))
kit.cyl("PowerRail", 0.05, 3.9, (0.35, 0.0, 5.52), kit.CHARCOAL,
        axis="X", verts=10)
for tx in (-1.2, 1.2):
    kit.box("Trolley", (0.4, 0.18, 0.22), (tx, 0.0, 5.52), kit.CHARCOAL)
    kit.cyl("TrolleyWheel", 0.07, 0.06, (tx - 0.12, 0.0, 5.66),
            kit.STEEL, axis="Y", verts=12)
    kit.cyl("TrolleyWheel", 0.07, 0.06, (tx + 0.12, 0.0, 5.66),
            kit.STEEL, axis="Y", verts=12)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=11.0,
                                         height=5.0)

# ---- PF carrier: sling frame with body cradle arms ----
NAME = "SM_LB_Paint_PFCarrier_v001"
kit.reset(); kit.glass_material()
kit.box("TopBar", (3.9, 0.14, 0.14), (0.0, 0.0, 2.22), kit.GREEN)
for sx in (-1.75, 1.75):
    kit.box("DropArm", (0.12, 0.12, 1.6), (sx, 0.0, 1.42), kit.GREEN)
    kit.box("Yoke", (0.14, 1.76, 0.12), (sx, 0.0, 0.62), kit.GREEN)
    for sy in (-0.80, 0.80):
        kit.box("SillArm", (0.5, 0.12, 0.10), (sx * 0.86, sy, 0.56),
                kit.STEEL)
        kit.box("SillPad", (0.24, 0.18, 0.06), (sx * 0.72, sy, 0.62),
                kit.CHARCOAL)
kit.box("SpreaderBar", (3.4, 0.10, 0.10), (0.0, 0.0, 0.58), kit.GREEN)
for hx in (-1.2, 1.2):
    kit.cyl("Hook", 0.05, 0.16, (hx, 0.0, 2.24), kit.STEEL, verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.0,
                                         height=2.2)

# ---- ED dip tank: open bath with stiffened walls and service walk ----
NAME = "SM_LB_Paint_EDDipTank_v001"
kit.reset(); kit.glass_material()
kit.box("Shell", (19.0, 6.3, 3.9), (0.0, 0.0, 1.95), kit.GREEN)
kit.box("Bath", (18.4, 5.7, 0.25), (0.0, 0.0, 3.95), kit.CHARCOAL,
        chamfer=False)
for rib in range(11):
    rx = -8.6 + rib * 1.72
    kit.box("WallRib", (0.16, 6.5, 3.6), (rx, 0.0, 1.9), kit.GREEN)
kit.box("RimRail", (19.1, 0.12, 0.16), (0.0, 3.2, 4.15), kit.STEEL)
kit.box("RimRail", (19.1, 0.12, 0.16), (0.0, -3.2, 4.15), kit.STEEL)
kit.box("Walkway", (19.0, 0.6, 0.06), (0.0, 2.95, 4.0), kit.STEEL)
for px in range(10):
    kit.cyl("RailPost", 0.03, 1.0, (-8.5 + px * 1.9, 2.95, 4.5),
            kit.STEEL, verts=8)
kit.box("HandRail", (19.0, 0.05, 0.05), (0.0, 2.95, 5.0), kit.STEEL)
for vx in (-6.0, 0.0, 6.0):
    kit.cyl("CircPipe", 0.12, 3.6, (vx, -3.05, 2.0), kit.STEEL, verts=12)
    kit.cyl("Valve", 0.14, 0.14, (vx, -3.05, 0.6), kit.RED, verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=16.0,
                                         height=5.0)

# ---- oven segment: insulated tunnel ring with burner spine ----
NAME = "SM_LB_Paint_OvenSegment_v003"
kit.reset(); kit.glass_material()
kit.box("Ring", (5.9, 4.9, 5.2), (0.0, 0.0, 2.75), kit.GREEN)
kit.box("Tunnel", (6.0, 3.4, 3.6), (0.0, 0.0, 2.0), kit.CHARCOAL,
        chamfer=False)
for seam_x in (-1.9, 0.0, 1.9):
    kit.box("PanelSeam", (0.10, 5.0, 5.3), (seam_x, 0.0, 2.72),
            kit.CHARCOAL, chamfer=False)
kit.box("BurnerSpine", (5.7, 0.5, 0.3), (0.0, 1.6, 5.45), kit.STEEL)
for bx in (-1.8, 0.0, 1.8):
    kit.cyl("BurnerStub", 0.10, 0.5, (bx, 1.6, 5.30), kit.STEEL,
            verts=12)
kit.box("RoofDuct", (0.35, 1.5, 0.28), (0.0, 0.75, 5.45), kit.STEEL)
kit.cyl("StackStub", 0.22, 0.5, (0.0, 0.0, 5.50), kit.STEEL, verts=16)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=12.0,
                                         height=5.5)

# ---- rectifier cabinet: finned twin-bay cabinet with busbars ----
NAME = "SM_LB_Paint_RectifierCabinet_v001"
kit.reset(); kit.glass_material()
kit.box("Body", (1.85, 1.28, 2.30), (0.0, 0.0, 1.18), kit.GREEN)
for door_x in (-0.46, 0.46):
    kit.box("Door", (0.86, 0.05, 2.0), (door_x, -0.66, 1.18),
            kit.CHARCOAL)
    kit.box("Handle", (0.05, 0.04, 0.20), (door_x + 0.32, -0.70, 1.18),
            kit.STEEL)
for fin in range(8):
    kit.box("Fin", (1.7, 0.03, 0.5), (0.0, 0.55 + fin * 0.008,
            2.2 - fin * 0.02), kit.STEEL, chamfer=False)
kit.box("Vent", (1.5, 0.04, 0.3), (0.0, -0.68, 2.25), kit.CHARCOAL)
for bx in (-0.5, 0.0, 0.5):
    kit.cyl("Busbar", 0.04, 0.5, (bx, 0.3, 2.55), kit.CHARCOAL, verts=8)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.4,
                                         height=1.9)

# ---- pipe bridge: braced frame carrying a pipe rack ----
NAME = "SM_LB_Paint_PipeBridge_Module_v001"
kit.reset(); kit.glass_material()
for sx in (-2.9, 2.9):
    kit.column("Leg", (sx, 0.0, 0.0), 4.0, kit.GREEN, width=0.14)
kit.box("Deck", (6.1, 1.3, 0.12), (0.0, 0.0, 4.10), kit.GREEN)
for py, r in ((-0.42, 0.10), (-0.14, 0.08), (0.14, 0.08), (0.42, 0.06)):
    kit.cyl("Pipe", r, 6.0, (0.0, py, 4.16 + r), kit.STEEL, axis="X",
            verts=12)
for cx in (-2.0, 0.0, 2.0):
    kit.box("PipeClamp", (0.10, 1.25, 0.14), (cx, 0.0, 4.30),
            kit.CHARCOAL)
for sx in (-1.0, 1.0):
    kit.box("KneeBrace", (0.08, 0.08, 1.5), (sx * 2.37, 0.0, 3.55),
            kit.STEEL, rot=(0.0, math.radians(sx * 45.0), 0.0))
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=3.4)
print("BATCH05 COMPLETE")
