"""Journey batch 3 - weld's untouched six, exported into DetailUplift.

Codex's uplifted weld machines passed the audit; these are the pieces he
never reached: index turntable, pedestal welder, metal finish bench, tip
dresser, stud feeder, clamp unit. Same filenames as the originals so
reimport_detail_uplift.py swaps every placed instance automatically.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- index turntable: drum base, round table, four fixture nests ----
NAME = "SM_LB_Weld_IndexTurntable_v001"
kit.reset()
kit.glass_material()
kit.cyl("Drum", 1.05, 0.55, (0.0, 0.0, 0.275), kit.CHARCOAL, verts=36)
kit.cyl("SlipRing", 1.12, 0.10, (0.0, 0.0, 0.60), kit.STEEL, verts=36)
kit.cyl("Table", 1.35, 0.10, (0.0, 0.0, 0.72), kit.GREEN, verts=40)
for quadrant in range(4):
    a = math.radians(45.0 + quadrant * 90.0)
    nx, ny = math.cos(a) * 0.78, math.sin(a) * 0.78
    kit.box("Nest", (0.55, 0.35, 0.14), (nx, ny, 0.84), kit.CHARCOAL,
            rot=(0.0, 0.0, a))
    for pin in (-0.18, 0.18):
        kit.cyl("NestPin", 0.03, 0.16,
                (nx + math.cos(a) * pin, ny + math.sin(a) * pin, 0.96),
                kit.STEEL, verts=10)
kit.box("DriveHouse", (0.65, 0.5, 0.45), (1.30, 0.0, 0.28), kit.GREEN)
kit.cyl("DriveShaft", 0.06, 0.35, (1.02, 0.0, 0.40), kit.STEEL, axis="X",
        verts=12)
kit.box("Cabinet", (0.35, 0.55, 0.85), (1.65, 0.0, 0.48), kit.CHARCOAL)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=4.6, height=1.9)

# ---- pedestal welder: transformer body on column, twin electrode arms ----
NAME = "SM_LB_Weld_PedestalWelder_v001"
kit.reset()
kit.glass_material()
kit.column("Col", (0.0, 0.0, 0.0), 1.15, kit.GREEN, width=0.26)
kit.box("Transformer", (0.62, 0.85, 0.72), (0.0, 0.0, 1.56), kit.GREEN)
kit.box("Fins", (0.66, 0.06, 0.6), (0.0, 0.30, 1.56), kit.CHARCOAL)
kit.box("Fins", (0.66, 0.06, 0.6), (0.0, -0.30, 1.56), kit.CHARCOAL)
for sz in (1.30, 1.78):
    kit.box("Arm", (0.85, 0.10, 0.10), (0.55, 0.0, sz), kit.STEEL)
    kit.cyl("Electrode", 0.035, 0.16, (0.96, 0.0, sz - 0.07 if sz > 1.5
            else sz + 0.07), kit.CHARCOAL, verts=10)
kit.cyl("CableLoop", 0.045, 0.9, (-0.42, 0.0, 1.15), kit.CHARCOAL,
        rot_hint=None, axis="Z", verts=12) if False else None
bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.035,
                                 location=(-0.45, 0.0, 1.30))
loop = bpy.context.active_object
loop.name = "CableLoop"
loop.rotation_euler = (math.radians(90.0), 0.0, 0.0)
loop.data.materials.append(kit.material(*kit.CHARCOAL))
kit.box("PedalBox", (0.35, 0.30, 0.14), (0.55, 0.0, 0.07), kit.YELLOW)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=3.6, height=1.8)

# ---- metal finish bench: bench, extraction hood, tool rail ----
NAME = "SM_LB_Weld_MetalFinishBench_v001"
kit.reset()
kit.glass_material()
kit.box("Top", (2.2, 1.0, 0.09), (0.0, 0.0, 0.90), kit.STEEL)
for sx in (-1.0, 1.0):
    for sy in (-1.0, 1.0):
        kit.box("Leg", (0.08, 0.08, 0.86), (sx * 1.0, sy * 0.42, 0.43),
                kit.GREEN)
kit.box("Shelf", (2.05, 0.85, 0.05), (0.0, 0.0, 0.32), kit.CHARCOAL)
kit.box("BackPanel", (2.2, 0.06, 0.75), (0.0, 0.48, 1.32), kit.GREEN)
kit.box("Hood", (1.9, 0.85, 0.35), (0.0, 0.05, 2.30), kit.CHARCOAL)
kit.cyl("HoodDuct", 0.14, 0.85, (0.0, 0.05, 2.85), kit.STEEL, verts=16)
kit.box("ToolRail", (1.9, 0.05, 0.06), (0.0, 0.44, 1.62), kit.STEEL)
for tx in (-0.6, 0.0, 0.6):
    kit.box("Tool", (0.10, 0.08, 0.30), (tx, 0.44, 1.42), kit.CHARCOAL)
    kit.cyl("ToolCord", 0.015, 0.5, (tx, 0.46, 1.75), kit.CHARCOAL,
            verts=8)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=4.4, height=2.2)

# ---- tip dresser: pedestal, cutter head, chip bin, lamp ----
NAME = "SM_LB_Weld_TipDresser_v001"
kit.reset()
kit.glass_material()
kit.column("Ped", (0.0, 0.0, 0.0), 0.85, kit.GREEN, width=0.18)
kit.box("Head", (0.45, 0.30, 0.28), (0.0, 0.0, 1.12), kit.CHARCOAL)
kit.cyl("Cutter", 0.09, 0.12, (0.28, 0.0, 1.12), kit.STEEL, axis="X",
        verts=20)
kit.cyl("CutterTeeth", 0.06, 0.14, (0.36, 0.0, 1.12), kit.CHARCOAL,
        axis="X", verts=12)
kit.box("ChipBin", (0.30, 0.26, 0.22), (0.28, 0.0, 0.55), kit.STEEL)
kit.cyl("Lamp", 0.03, 0.12, (-0.12, 0.0, 1.36), kit.GREEN, verts=10)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=2.6, height=1.4)

# ---- stud feeder: vibratory bowl, hopper, feed tubes, controls ----
NAME = "SM_LB_Weld_StudFeeder_v001"
kit.reset()
kit.glass_material()
kit.box("Base", (0.8, 0.65, 0.55), (0.0, 0.0, 0.275), kit.GREEN)
kit.cyl("Bowl", 0.42, 0.28, (0.0, 0.0, 0.72), kit.STEEL, verts=32)
kit.cyl("BowlSpiral", 0.36, 0.06, (0.0, 0.0, 0.88), kit.CHARCOAL,
        verts=28)
kit.cyl("Hopper", 0.26, 0.35, (0.0, 0.0, 1.12), kit.GREEN, verts=20)
kit.cyl("HopperCone", 0.32, 0.10, (0.0, 0.0, 0.94), kit.GREEN, verts=20)
for angle in (25.0, 55.0):
    a = math.radians(angle)
    kit.cyl("FeedTube", 0.025, 0.85,
            (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.55), kit.STEEL,
            rot_hint=None, verts=10) if False else None
    kit.box("FeedTube", (0.03, 0.03, 0.85),
            (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.50), kit.STEEL,
            rot=(math.radians(28.0), 0.0, a), chamfer=False)
kit.box("Controls", (0.22, 0.10, 0.30), (0.44, -0.25, 0.72),
        kit.CHARCOAL)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=2.8, height=1.5)

# ---- clamp unit: riser, toggle linkage, actuator ----
NAME = "SM_LB_Weld_ClampUnit_v001"
kit.reset()
kit.glass_material()
kit.box("Riser", (0.18, 0.16, 0.34), (0.0, 0.0, 0.17), kit.GREEN)
kit.box("Body", (0.30, 0.12, 0.14), (0.05, 0.0, 0.42), kit.CHARCOAL)
kit.box("ClampArm", (0.34, 0.05, 0.05), (0.18, 0.0, 0.54), kit.STEEL,
        rot=(0.0, math.radians(-18.0), 0.0))
kit.cyl("Pivot", 0.025, 0.16, (0.06, 0.0, 0.50), kit.STEEL, axis="Y",
        verts=10)
kit.box("Actuator", (0.22, 0.06, 0.06), (-0.14, 0.0, 0.34), kit.STEEL,
        rot=(0.0, math.radians(35.0), 0.0))
kit.cyl("Tip", 0.02, 0.06, (0.34, 0.0, 0.60), kit.CHARCOAL, verts=8)
kit.export(NAME, out(NAME))
kit.preview(NAME, out(NAME), distance=1.6, height=0.8)
print("BATCH03 COMPLETE")
