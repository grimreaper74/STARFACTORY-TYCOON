"""Journey batch 2: destack magazine, cleaning dock + robot, trailer.

Intake's remaining rebuilds plus the transporter trailer that pairs with
the approved tractor. Proportion-first per the standing rules.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

FOLDER = "PressShop/IntakeRework_v001"

# ---- destack magazine: fanned blank slots in a framed rack ----
kit.reset()
kit.glass_material()
for sx in (-1.0, 1.0):
    for sy in (-1.0, 1.0):
        kit.column("Leg", (sx * 1.05, sy * 0.80, 0.0), 2.15, kit.GREEN,
                   width=0.12)
for z in (0.35, 2.10):
    kit.box("Rail", (2.3, 0.08, 0.10), (0.0, -0.80, z), kit.GREEN)
    kit.box("Rail", (2.3, 0.08, 0.10), (0.0, 0.80, z), kit.GREEN)
for slot in range(9):
    angle = math.radians(-16.0 + slot * 4.0)
    kit.box("Blank", (0.02, 1.45, 1.35),
            (-0.85 + slot * 0.21, 0.0, 1.15), kit.STEEL,
            rot=(0.0, angle, 0.0), chamfer=False)
for x in (-0.9, -0.3, 0.3, 0.9):
    kit.cyl("BaseRoller", 0.055, 1.5, (x, 0.0, 0.16), kit.CHARCOAL,
            axis="Y", verts=16)
kit.box("RollerBed", (2.25, 1.6, 0.08), (0.0, 0.0, 0.06), kit.CHARCOAL)
kit.box("HMI", (0.10, 0.42, 0.30), (1.18, 0.55, 1.45), kit.CHARCOAL)
kit.box("HMIGlass", (0.02, 0.34, 0.22), (1.12, 0.55, 1.45), kit.GLASS,
        chamfer=False)
kit.export("SM_LB_Press_DestackMagazine_v002", FOLDER)
kit.preview("SM_LB_Press_DestackMagazine_v002", FOLDER, distance=5.4,
            height=2.4)

# ---- cleaning dock: portal with brush drums and drip tray ----
kit.reset()
kit.glass_material()
for sx in (-1.0, 1.0):
    kit.column("Post", (sx * 1.35, 0.0, 0.0), 2.35, kit.GREEN, width=0.16)
kit.box("Header", (3.0, 0.5, 0.35), (0.0, 0.0, 2.45), kit.GREEN)
for z, r in ((0.85, 0.28), (1.55, 0.28)):
    kit.cyl("BrushDrum", r, 2.4, (0.0, 0.0, z), kit.CHARCOAL, axis="X",
            verts=24)
    for cap_x in (-1.22, 1.22):
        kit.cyl("DrumCap", r * 0.7, 0.10, (cap_x, 0.0, z), kit.STEEL,
                axis="X", verts=18)
kit.box("DripTray", (2.9, 1.3, 0.10), (0.0, 0.0, 0.06), kit.STEEL)
kit.box("TrayLip", (2.9, 0.06, 0.16), (0.0, 0.62, 0.12), kit.STEEL)
kit.box("TrayLip", (2.9, 0.06, 0.16), (0.0, -0.62, 0.12), kit.STEEL)
kit.cyl("Duct", 0.16, 1.1, (1.35, 0.0, 2.95), kit.STEEL, verts=16)
kit.box("Cabinet", (0.45, 0.30, 0.9), (-1.62, 0.55, 0.50), kit.CHARCOAL)
kit.export("SM_LB_Press_CleaningDock_v002", FOLDER)
kit.preview("SM_LB_Press_CleaningDock_v002", FOLDER, distance=6.0,
            height=2.6)

# ---- cleaning robot: tracked unit with brush arm ----
kit.reset()
kit.glass_material()
kit.box("Body", (1.15, 0.75, 0.34), (0.0, 0.0, 0.42), kit.GREEN)
for sy in (-1.0, 1.0):
    kit.box("Track", (1.25, 0.16, 0.30), (0.0, sy * 0.47, 0.20),
            kit.CHARCOAL)
    for tx in (-0.45, 0.0, 0.45):
        kit.cyl("Roller", 0.10, 0.14, (tx, sy * 0.47, 0.14), kit.TIRE,
                axis="Y", verts=16)
kit.cyl("Turret", 0.16, 0.16, (0.25, 0.0, 0.66), kit.CHARCOAL, verts=18)
kit.box("Arm", (0.68, 0.10, 0.09), (0.62, 0.0, 0.76), kit.STEEL,
        rot=(0.0, math.radians(-18.0), 0.0))
kit.cyl("BrushHead", 0.16, 0.30, (0.98, 0.0, 0.62), kit.CHARCOAL,
        axis="X", verts=20)
kit.cyl("Lidar", 0.05, 0.06, (-0.42, 0.28, 0.63), kit.CHARCOAL, verts=14)
kit.box("LightStrip", (0.02, 0.6, 0.03), (0.58, 0.0, 0.50), kit.GREEN,
        chamfer=False)
kit.export("SM_LB_Press_CleaningRobot_v002", FOLDER)
kit.preview("SM_LB_Press_CleaningRobot_v002", FOLDER, distance=3.2,
            height=1.3)

# ---- transporter trailer: full-length twin decks ----
kit.reset()
kit.glass_material()
L, W = 10.4, 2.5
# Chassis spine and lower deck.
for sy in (-0.5, 0.5):
    kit.box("Spine", (L * 0.96, 0.10, 0.24), (0.0, sy, 0.62),
            kit.CHARCOAL)
kit.box("LowerDeck", (L, W, 0.08), (0.0, 0.0, 0.80), kit.STEEL)
for strip in range(12):
    kit.box("DeckPerf", (L * 0.94, 0.06, 0.012),
            (0.0, -W / 2 + 0.18 + strip * 0.195, 0.85), kit.CHARCOAL,
            chamfer=False)
# Upper deck on posts, full length, with rear tilt rams.
kit.box("UpperDeck", (L * 0.97, W * 0.94, 0.07), (0.0, 0.0, 2.05),
        kit.STEEL)
for px in (-4.6, -2.3, 0.0, 2.3, 4.6):
    for sy in (-1.0, 1.0):
        kit.box("Post", (0.09, 0.09, 1.22), (px, sy * (W / 2 - 0.07),
                1.44), kit.GREEN)
for sy in (-0.9, 0.9):
    kit.cyl("TiltRam", 0.045, 1.9, (-4.55, sy, 1.35), kit.STEEL,
            axis="Z", verts=12)
    kit.box("RampPlate", (1.15, 0.5, 0.05), (-5.35, sy, 1.05),
            kit.CHARCOAL, rot=(0.0, math.radians(24.0), 0.0))
# Side guide rails along both decks.
for z in (1.02, 2.27):
    for sy in (-1.0, 1.0):
        kit.box("GuideRail", (L * 0.95, 0.05, 0.09),
                (0.0, sy * (W / 2 + 0.01), z), kit.GREEN)
# Landing legs at the kingpin end; kingpin plate.
for sy in (-0.55, 0.55):
    kit.box("LandingLeg", (0.10, 0.10, 0.62), (3.9, sy, 0.31),
            kit.STEEL)
    kit.box("LegFoot", (0.22, 0.18, 0.05), (3.9, sy, 0.03), kit.CHARCOAL)
kit.box("KingpinPlate", (0.9, 0.9, 0.06), (4.55, 0.0, 0.72),
        kit.CHARCOAL)
kit.cyl("Kingpin", 0.05, 0.16, (4.55, 0.0, 0.60), kit.STEEL, verts=12)
# Tandem bogie with mudguards, lamp bar, chock rack.
for bx in (-2.9, -4.1):
    kit.cyl("BogieAxle", 0.07, 2.1, (bx, 0.0, 0.525), kit.CHARCOAL,
            axis="Y", verts=14)
    kit.wheel(bx, -0.98, twin=True)
    kit.wheel(bx, 0.98, twin=True)
    for sy in (-0.98, 0.98):
        kit.arc_shell("Guard", (bx, sy, 0.525), 0.66, 0.58,
                      kit.CHARCOAL)
kit.box("LampBar", (0.08, W * 0.9, 0.14), (-5.15, 0.0, 0.66),
        kit.CHARCOAL)
for ly in (-0.9, -0.55, 0.55, 0.9):
    kit.box("Lamp", (0.03, 0.12, 0.08), (-5.20, ly, 0.66), kit.RED,
            chamfer=False)
kit.box("ChockRack", (0.5, 0.3, 0.22), (3.2, -1.05, 0.92), kit.STEEL)
for cx in (3.08, 3.32):
    kit.box("Chock", (0.10, 0.16, 0.12), (cx, -1.05, 0.98), kit.YELLOW)
kit.export("SM_LB_Site_Transporter_v001_Trailer", "Site/TransporterRework_v001")
kit.preview("SM_LB_Site_Transporter_v001_Trailer",
            "Site/TransporterRework_v001", distance=13.5, height=3.2)
print("BATCH02 COMPLETE")
