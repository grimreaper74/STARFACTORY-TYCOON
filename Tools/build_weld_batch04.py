"""Journey batch 4 - weld's final nine, exported into DetailUplift.

Marshalling rack, overhead drop lift, BIW buffer rack, CMM bed, rework
booth frame, roof magazine, water chiller skid, skid lift transfer and
closure door fixture. Original filenames so the standard pipeline swaps
every placed instance.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- marshalling rack: three bays, three shelves, braced ----
NAME = "SM_LB_Weld_MarshallingRack_v001"
kit.reset(); kit.glass_material()
for bx in (-1.4, -0.45, 0.45, 1.4):
    kit.column("Post", (bx, -1.0, 0.0), 2.7, kit.GREEN, width=0.10)
    kit.column("Post", (bx, 1.0, 0.0), 2.7, kit.GREEN, width=0.10)
for z in (0.45, 1.35, 2.25):
    kit.box("Shelf", (2.9, 2.1, 0.06), (0.0, 0.0, z), kit.STEEL)
    for bx in (-0.925, 0.0, 0.925):
        kit.box("Panel", (0.75, 1.8, 0.05), (bx, 0.0, z + 0.30),
                kit.CHARCOAL, rot=(math.radians(8.0), 0.0, 0.0))
kit.box("Brace", (0.05, 0.05, 3.2), (-1.4, -1.0, 1.35), kit.STEEL,
        rot=(math.radians(38.0), 0.0, 0.0))
kit.box("Brace", (0.05, 0.05, 3.2), (1.4, 1.0, 1.35), kit.STEEL,
        rot=(math.radians(-38.0), 0.0, 0.0))
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=5.2,
                                         height=2.6)

# ---- overhead drop lift: portal, carriage, scissor drop, hook frame ----
NAME = "SM_LB_Weld_OverheadDropLift_v001"
kit.reset(); kit.glass_material()
for sy in (-1.0, 1.0):
    kit.column("Leg", (0.0, sy * 1.75, 0.0), 5.3, kit.GREEN, width=0.30)
kit.box("HeadBeam", (0.9, 3.9, 0.45), (0.0, 0.0, 5.5), kit.GREEN)
kit.box("Carriage", (0.7, 1.3, 0.35), (0.0, 0.0, 5.1), kit.CHARCOAL)
kit.scissor("Drop", (0.0, 0.0, 4.2), 0.5, 1.3, kit.STEEL)
kit.box("HookFrame", (0.6, 1.6, 0.12), (0.0, 0.0, 3.35), kit.GREEN)
for hy in (-0.6, 0.6):
    kit.box("Hook", (0.08, 0.06, 0.35), (0.0, hy, 3.15), kit.STEEL)
kit.box("EPanel", (0.35, 0.5, 0.7), (0.0, 1.72, 4.6), kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=4.0)

# ---- BIW buffer rack: two tiers, three cradle slots ----
NAME = "SM_LB_Weld_BIWBufferRack_v001"
kit.reset(); kit.glass_material()
for bx in (-2.2, 0.0, 2.2):
    kit.column("Post", (bx, -0.9, 0.0), 2.05, kit.GREEN, width=0.14)
    kit.column("Post", (bx, 0.9, 0.0), 2.05, kit.GREEN, width=0.14)
for z in (0.55, 1.55):
    for sy in (-0.75, 0.75):
        kit.box("Runner", (4.7, 0.12, 0.10), (0.0, sy, z), kit.STEEL)
    for bx in (-1.5, 0.0, 1.5):
        for sy in (-0.75, 0.75):
            kit.box("Saddle", (0.5, 0.3, 0.09), (bx, sy, z + 0.09),
                    kit.CHARCOAL, rot=(0.0, 0.0, 0.0))
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.2,
                                         height=2.4)

# ---- CMM bed: granite bed, twin gantry, probe, control desk ----
NAME = "SM_LB_Weld_CMMBed_v001"
kit.reset(); kit.glass_material()
kit.box("Bed", (4.4, 2.3, 0.55), (0.0, 0.0, 0.45), kit.CHARCOAL)
kit.box("BedTop", (4.2, 2.1, 0.10), (0.0, 0.0, 0.78), kit.STEEL)
for gx in (-1.1, 1.1):
    for sy in (-1.0, 1.0):
        kit.box("GantryLeg", (0.14, 0.14, 1.5), (gx, sy * 1.0, 1.55),
                kit.GREEN)
    kit.box("GantryBeam", (0.16, 2.25, 0.18), (gx, 0.0, 2.35), kit.GREEN)
kit.box("XRail", (2.4, 0.12, 0.10), (0.0, 0.0, 2.45), kit.STEEL)
kit.box("ZColumn", (0.10, 0.10, 0.85), (0.35, 0.0, 2.02), kit.STEEL)
kit.cyl("Probe", 0.025, 0.30, (0.35, 0.0, 1.52), kit.CHARCOAL, verts=10)
kit.box("Desk", (0.7, 0.5, 0.75), (2.65, 0.9, 0.38), kit.CHARCOAL)
kit.box("Screen", (0.04, 0.4, 0.28), (2.45, 0.9, 0.95), kit.GLASS,
        chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=6.4,
                                         height=2.6)

# ---- rework booth frame: posts, header, screens, light bar ----
NAME = "SM_LB_Weld_ReworkBoothFrame_v001"
kit.reset(); kit.glass_material()
for sx in (-1.0, 1.0):
    for sy in (-1.0, 1.0):
        kit.column("Post", (sx * 1.95, sy * 1.5, 0.0), 4.1, kit.GREEN,
                   width=0.14)
for sy in (-1.5, 1.5):
    kit.box("Header", (4.2, 0.14, 0.30), (0.0, sy, 4.25), kit.GREEN)
for sx in (-1.95, 1.95):
    kit.box("SideScreen", (0.05, 2.9, 2.4), (sx, 0.0, 1.75), kit.STEEL)
kit.box("LightBar", (3.6, 0.35, 0.12), (0.0, 0.0, 4.05), kit.WARMWHITE)
kit.box("Sill", (4.2, 3.2, 0.06), (0.0, 0.0, 0.03), kit.YELLOW,
        chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.0,
                                         height=3.4)

# ---- roof magazine: angled roof-panel slots on casters ----
NAME = "SM_LB_Weld_RoofMagazine_v001"
kit.reset(); kit.glass_material()
kit.box("Base", (2.4, 1.25, 0.12), (0.0, 0.0, 0.18), kit.GREEN)
for cx in (-1.0, 1.0):
    for cy in (-0.5, 0.5):
        kit.cyl("Caster", 0.07, 0.05, (cx, cy, 0.07), kit.CHARCOAL,
                axis="Y", verts=12)
for slot in range(6):
    kit.box("RoofPanel", (0.03, 1.15, 1.35),
            (-0.85 + slot * 0.34, 0.0, 0.95), kit.STEEL,
            rot=(0.0, math.radians(-12.0), 0.0), chamfer=False)
    kit.box("SlotRail", (0.05, 1.2, 0.06), (-0.85 + slot * 0.34, 0.0,
            0.28), kit.CHARCOAL)
kit.box("EndFrame", (2.45, 0.08, 1.5), (0.0, 0.60, 0.95), kit.GREEN)
kit.box("EndFrame", (2.45, 0.08, 1.5), (0.0, -0.60, 0.95), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.0,
                                         height=1.9)

# ---- water chiller skid: compressors, condenser fins, manifold ----
NAME = "SM_LB_Weld_WaterChillerSkid_v001"
kit.reset(); kit.glass_material()
kit.box("Skid", (2.9, 1.35, 0.12), (0.0, 0.0, 0.06), kit.CHARCOAL)
for cx in (-0.85, -0.15):
    kit.cyl("Compressor", 0.26, 0.75, (cx, -0.25, 0.55), kit.GREEN,
            axis="X", verts=24)
    kit.cyl("CompDome", 0.26, 0.10, (cx + 0.42, -0.25, 0.55), kit.GREEN,
            axis="X", verts=24)
for fin in range(14):
    kit.box("CondFin", (0.02, 1.15, 0.85),
            (0.55 + fin * 0.055, 0.0, 0.75), kit.STEEL, chamfer=False)
kit.box("CondFrame", (0.9, 1.25, 1.0), (0.9, 0.0, 0.72), kit.GREEN)
for py in (-0.35, 0.0, 0.35):
    kit.cyl("Pipe", 0.05, 1.6, (-0.6, py, 1.18), kit.STEEL, axis="X",
            verts=12)
    kit.cyl("Valve", 0.08, 0.10, (-1.1, py, 1.18), kit.RED, verts=10)
kit.box("Cabinet", (0.4, 0.3, 0.9), (-1.28, 0.45, 0.57), kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=4.4,
                                         height=2.0)

# ---- skid lift transfer: scissor lift with skid rails ----
NAME = "SM_LB_Weld_SkidLiftTransfer_v001"
kit.reset(); kit.glass_material()
kit.box("Base", (2.4, 1.3, 0.14), (0.0, 0.0, 0.07), kit.CHARCOAL)
kit.scissor("Lift", (0.0, 0.0, 0.62), 1.5, 0.75, kit.STEEL)
kit.box("Deck", (2.45, 1.3, 0.10), (0.0, 0.0, 1.08), kit.GREEN)
for sy in (-0.45, 0.45):
    kit.box("SkidRail", (2.5, 0.10, 0.09), (0.0, sy, 1.20), kit.STEEL)
for rx in (-1.0, 0.0, 1.0):
    kit.cyl("Roller", 0.05, 1.0, (rx, 0.0, 1.16), kit.CHARCOAL,
            axis="Y", verts=14)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.8,
                                         height=1.8)

# ---- closure door fixture: frame with door plate and clamps ----
NAME = "SM_LB_Weld_ClosureDoorFixture_v001"
kit.reset(); kit.glass_material()
kit.box("Base", (1.4, 0.95, 0.10), (0.0, 0.0, 0.05), kit.GREEN)
kit.column("Mast", (-0.45, 0.0, 0.0), 1.85, kit.GREEN, width=0.14)
kit.box("DoorPlate", (0.05, 1.15, 1.35), (0.15, 0.0, 1.15), kit.STEEL,
        rot=(0.0, math.radians(-6.0), 0.0))
for cz in (0.65, 1.15, 1.62):
    kit.box("ClampArm", (0.30, 0.06, 0.06), (-0.18, 0.45, cz),
            kit.CHARCOAL)
    kit.cyl("ClampTip", 0.03, 0.07, (0.02, 0.45, cz), kit.RED, verts=8)
kit.box("ToolShelf", (0.5, 0.4, 0.05), (-0.55, -0.55, 0.85),
        kit.STEEL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.2,
                                         height=1.8)
print("BATCH04 COMPLETE")
