"""Journey batch 1 - coil intake: coil AGV, blank-stack AGV, coil scale.

The catalogue rebuild follows the car from coils to finished vehicle
(owner). These are the first machines a player sees. Real proportions:
heavy AGVs are low flat carriers (~0.45 m deck height) with corner
wheel pods, lidar pucks and light strips; the coil scale is a shallow
platform with ramp edges and a readout pillar. Bevel everything,
mechanisms modelled, no bare faces.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

FOLDER = "PressShop/IntakeRework_v001"


def agv_base(length, width):
    """Shared AGV platform: hull, skirt, wheel pods, sensors, lights."""
    deck_z = 0.42
    kit.box("Hull", (length, width, 0.30), (0.0, 0.0, deck_z - 0.15),
            kit.GREEN)
    kit.box("Skirt", (length * 0.96, width * 0.96, 0.09),
            (0.0, 0.0, 0.10), kit.CHARCOAL)
    # Corner wheel pods with visible drive wheels.
    for sx in (-1.0, 1.0):
        for sy in (-1.0, 1.0):
            px = sx * (length / 2 - 0.30)
            py = sy * (width / 2 - 0.22)
            kit.box("Pod", (0.44, 0.30, 0.16), (px, py, 0.14),
                    kit.CHARCOAL)
            kit.cyl("Wheel", 0.11, 0.09, (px, py + sy * 0.06, 0.11),
                    kit.TIRE, axis="Y", verts=20)
    # Lidar pucks on two corners, e-stops mid-side, light strip all round.
    for sx, sy in ((-1.0, -1.0), (1.0, 1.0)):
        kit.cyl("Lidar", 0.055, 0.07,
                (sx * (length / 2 - 0.12), sy * (width / 2 - 0.12),
                 deck_z + 0.055), kit.CHARCOAL, verts=16)
    for sy in (-1.0, 1.0):
        kit.box("EStop", (0.06, 0.05, 0.09),
                (0.0, sy * (width / 2 + 0.005), deck_z - 0.06), kit.RED,
                chamfer=False)
    for sx in (-1.0, 1.0):
        kit.box("LightStrip", (0.02, width * 0.9, 0.03),
                (sx * (length / 2 + 0.005), 0.0, deck_z - 0.02),
                kit.GREEN, chamfer=False)
    kit.box("Antenna", (0.02, 0.02, 0.28),
            (-length / 2 + 0.15, width / 2 - 0.15, deck_z + 0.14),
            kit.STEEL, chamfer=False)
    return deck_z


# ---- coil AGV: saddle cradle for a 1.4 m coil ----
kit.reset()
kit.glass_material()
deck = agv_base(2.7, 1.7)
# V-saddle: two plates meeting at the valley, ribs beneath, end stops.
for sx in (-1.0, 1.0):
    kit.box("CradleFace", (0.72, 1.5, 0.07),
            (sx * 0.315, 0.0, deck + 0.26), kit.STEEL,
            rot=(0.0, sx * math.radians(-33.0), 0.0))
    for ry in (-0.55, 0.0, 0.55):
        kit.box("CradleRib", (0.30, 0.07, 0.16),
                (sx * 0.38, ry, deck + 0.10), kit.CHARCOAL)
for sy in (-0.80, 0.80):
    kit.box("CradleEnd", (1.35, 0.07, 0.42), (0.0, sy, deck + 0.21),
            kit.GREEN)
kit.box("ValleyPad", (0.28, 1.44, 0.04), (0.0, 0.0, deck + 0.07),
        kit.CHARCOAL, chamfer=False)
kit.cyl("Beacon", 0.05, 0.10, (-1.15, 0.7, deck + 0.35), kit.YELLOW,
        verts=12)
kit.export("SM_LB_Press_CoilAGV_v002", FOLDER)
kit.preview("SM_LB_Press_CoilAGV_v002", FOLDER, distance=5.5, height=1.8)

# ---- blank-stack AGV: flat deck with corner stack guides ----
kit.reset()
kit.glass_material()
deck = agv_base(2.4, 1.6)
kit.box("DeckPlate", (2.0, 1.35, 0.05), (0.0, 0.0, deck + 0.025),
        kit.STEEL)
for sx in (-1.0, 1.0):
    for sy in (-1.0, 1.0):
        kit.box("StackGuide", (0.07, 0.07, 0.55),
                (sx * 0.92, sy * 0.60, deck + 0.30), kit.GREEN)
        kit.box("GuideFoot", (0.13, 0.13, 0.04),
                (sx * 0.92, sy * 0.60, deck + 0.05), kit.CHARCOAL)
kit.cyl("Beacon", 0.05, 0.10, (-1.0, 0.65, deck + 0.35), kit.YELLOW,
        verts=12)
kit.export("SM_LB_Press_BlankStackAGV_v002", FOLDER)
kit.preview("SM_LB_Press_BlankStackAGV_v002", FOLDER, distance=5.2,
            height=1.8)

# ---- coil scale: platform, ramps, readout pillar ----
kit.reset()
kit.glass_material()
kit.box("Platform", (2.3, 2.3, 0.22), (0.0, 0.0, 0.11), kit.CHARCOAL)
kit.box("Tread", (2.1, 2.1, 0.03), (0.0, 0.0, 0.235), kit.STEEL)
for sx in (-1.0, 1.0):
    kit.box("Ramp", (0.5, 2.3, 0.05), (sx * 1.42, 0.0, 0.07),
            kit.CHARCOAL, rot=(0.0, sx * math.radians(-12.0), 0.0))
for sx in (-1.0, 1.0):
    for sy in (-1.0, 1.0):
        kit.cyl("LoadCell", 0.09, 0.10,
                (sx * 0.95, sy * 0.95, 0.05), kit.STEEL, verts=14)
kit.box("SaddleChock", (0.5, 1.7, 0.16), (-0.45, 0.0, 0.32), kit.GREEN,
        rot=(0.0, math.radians(24.0), 0.0))
kit.box("SaddleChock", (0.5, 1.7, 0.16), (0.45, 0.0, 0.32), kit.GREEN,
        rot=(0.0, math.radians(-24.0), 0.0))
kit.column("Pillar", (1.45, 1.35, 0.0), 1.5, kit.GREEN, width=0.16)
kit.box("Readout", (0.10, 0.55, 0.35), (1.45, 1.35, 1.70), kit.CHARCOAL)
kit.box("ReadoutGlass", (0.02, 0.45, 0.25), (1.39, 1.35, 1.70),
        kit.GLASS, chamfer=False)
kit.export("SM_LB_Press_CoilScale_v002", FOLDER)
kit.preview("SM_LB_Press_CoilScale_v002", FOLDER, distance=5.0,
            height=2.0)
print("BATCH01 COMPLETE")
