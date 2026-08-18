"""Weld shop skid conveyor module, 3 m: the roller bed the body skids ride on.

A skid conveyor is recognised by its twin frame rails full of closely pitched
rollers, the chain guard and drive motor hanging off one side, and the stop pin
unit at the downstream end. Legs with adjuster feet, sensors and a pull-wire
e-stop line say it is a working line section rather than a table.
"""
import math
import sys

sys.path.insert(0, r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
from lb_model_kit import (CHARCOAL, GREEN, RED, STEEL, WARMWHITE, YELLOW, box,
                          cyl, export, preview, reset)

reset()

# ---- frame rails and legs ---------------------------------------------------
for sy in (-0.55, 0.55):
    box("FrameRail", (3.0, 0.16, 0.26), (0, sy, 0.56), GREEN)
    box("RailCap", (3.0, 0.20, 0.03), (0, sy, 0.705), CHARCOAL, chamfer=False)
for lx in (-1.32, -0.44, 0.44, 1.32):
    for sy in (-0.55, 0.55):
        box("LegPlate", (0.20, 0.20, 0.025), (lx, sy, 0.012), CHARCOAL,
            chamfer=False)
        cyl("LegFoot", 0.035, 0.06, (lx, sy, 0.05), STEEL, verts=10)
        box("Leg", (0.11, 0.11, 0.36), (lx, sy, 0.26), GREEN)
    # Cross brace between each leg pair keeps the frame from reading as stilts.
    box("LegBrace", (0.09, 1.02, 0.08), (lx, 0, 0.20), CHARCOAL)

# ---- roller bed -------------------------------------------------------------
for n in range(9):
    rx = -1.32 + n * 0.33
    cyl("Roller", 0.055, 1.14, (rx, 0, 0.72), STEEL, axis="Y")
    # Stub axles through the rail faces.
    for sy in (-0.63, 0.63):
        cyl("RollerAxle", 0.022, 0.06, (rx, sy, 0.72), CHARCOAL, axis="Y",
            verts=10)

# ---- guides, chain guard and drive ------------------------------------------
for sy in (-0.52, 0.52):
    box("SkidGuide", (3.0, 0.035, 0.07), (0, sy, 0.80), CHARCOAL)
box("ChainGuard", (2.86, 0.06, 0.17), (0, 0.685, 0.66), CHARCOAL)
box("GuardRib", (2.86, 0.02, 0.03), (0, 0.72, 0.66), GREEN, chamfer=False)
box("Gearbox", (0.26, 0.22, 0.26), (1.28, 0.80, 0.56), CHARCOAL)
cyl("DriveMotor", 0.10, 0.34, (1.28, 1.06, 0.56), GREEN, axis="Y")
for n in range(4):
    cyl("MotorFin", 0.105, 0.02, (1.28, 0.95 + n * 0.07, 0.56), CHARCOAL,
        axis="Y", verts=16)
cyl("DriveShaft", 0.03, 0.12, (1.28, 0.66, 0.56), STEEL, axis="Y", verts=10)

# ---- stop pin unit at the downstream end -------------------------------------
box("StopBody", (0.20, 0.30, 0.20), (1.42, 0, 0.52), CHARCOAL)
cyl("StopPin", 0.045, 0.22, (1.42, 0, 0.72), STEEL)
cyl("StopCyl", 0.055, 0.20, (1.42, 0, 0.36), CHARCOAL)
cyl("StopAirline", 0.014, 0.5, (1.42, 0.25, 0.40), STEEL, axis="Y", verts=10)

# ---- sensors along the inner face ---------------------------------------------
for nx in (-1.0, 0.0, 1.0):
    box("SensorBracket", (0.03, 0.05, 0.12), (nx, -0.60, 0.62), STEEL,
        chamfer=False)
    box("Sensor", (0.05, 0.04, 0.05), (nx, -0.615, 0.70), YELLOW,
        chamfer=False)

# ---- pull-wire e-stop line down one side ---------------------------------------
for px in (-1.35, 1.35):
    cyl("PullPost", 0.015, 0.30, (px, -0.72, 0.60), STEEL, verts=10)
box("PullSwitch", (0.10, 0.06, 0.14), (-1.35, -0.72, 0.80), RED)
cyl("PullWire", 0.006, 2.7, (0, -0.72, 0.76), STEEL, axis="X", verts=8)

# ---- junction box and conduit on a leg -----------------------------------------
box("JBox", (0.14, 0.10, 0.18), (0.44, 0.68, 0.30), GREEN)
cyl("Conduit", 0.018, 0.30, (0.44, 0.68, 0.50), STEEL, verts=10)
box("IDPlate", (0.14, 0.015, 0.08), (0, -0.635, 0.52), WARMWHITE,
    chamfer=False)

export("SM_LB_Weld_SkidConveyorModule_3000_v001", "WeldShop/SkidConveyor_v001")
preview("SM_LB_Weld_SkidConveyorModule_3000_v001", "WeldShop/SkidConveyor_v001")
