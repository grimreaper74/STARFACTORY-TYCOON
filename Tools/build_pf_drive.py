"""Paint PF conveyor drive: the caterpillar drive station on the track run.

Matches the goalpost track segment (track box at 5.33, chain cover 5.50,
posts at y +-1.7): the drive frame hangs its caterpillar chain housing
alongside the track box, with the motor and gearbox stack rising above
the bridge and a service ladder up one post.
"""
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, STEEL, WARMWHITE, box, column, cyl,
                          export, preview, reset)

reset()

# Same goalpost as the track segment so the drive drops into the run.
for sy in (-1.7, 1.7):
    column("Post", (0, sy, 0), 5.35, GREEN, width=0.30)
box("Bridge", (0.55, 3.8, 0.34), (0, 0, 5.70), GREEN)
box("TrackStub", (1.6, 0.32, 0.26), (0, 0, 5.33), CHARCOAL)
for sy in (-0.12, 0.12):
    box("SlotFlange", (1.6, 0.08, 0.05), (0, sy, 5.17), STEEL, chamfer=False)

# Caterpillar chain housing riding beside the track box.
box("CatHousing", (1.5, 0.24, 0.3), (0, -0.34, 5.42), GREEN)
for n in range(6):
    box("CatTooth", (0.12, 0.06, 0.1), (-0.6 + n * 0.24, -0.22, 5.33), STEEL,
        chamfer=False)
box("TensionerArm", (0.4, 0.1, 0.1), (0.9, -0.34, 5.42), CHARCOAL)
cyl("TensionerWheel", 0.1, 0.08, (1.14, -0.34, 5.42), STEEL, axis="Y",
    verts=14)

# Motor and gearbox stack on the bridge, shaft dropping to the housing.
box("GearBox", (0.5, 0.45, 0.4), (0, -0.3, 6.05), CHARCOAL)
cyl("DriveShaft", 0.06, 0.55, (0, -0.34, 5.7), STEEL, verts=10)
cyl("DriveMotor", 0.17, 0.55, (0, 0.25, 6.1), STEEL, axis="Y", verts=16)
box("MotorFoot", (0.4, 0.3, 0.08), (0, 0.3, 5.91), CHARCOAL)
box("DrivePanel", (0.36, 0.06, 0.5), (0, 1.55, 6.12), GREEN)
box("PanelFace", (0.28, 0.02, 0.34), (0, 1.51, 6.12), WARMWHITE,
    chamfer=False)

# Service ladder up the south post to the drive level.
for rz in range(10):
    box("Rung", (0.26, 0.02, 0.02), (0.28, -1.7, 0.7 + rz * 0.5), STEEL,
        chamfer=False)
for rx in (0.16, 0.4):
    box("LadderRail", (0.03, 0.03, 5.0), (rx, -1.7, 3.1), STEEL,
        chamfer=False)
box("IDPlate", (0.02, 0.20, 0.12), (0.16, -1.86, 2.4), WARMWHITE,
    chamfer=False)

export("SM_LB_Paint_PFDrive_v001", "PaintShop/PFDrive_v001")
preview("SM_LB_Paint_PFDrive_v001", "PaintShop/PFDrive_v001")
