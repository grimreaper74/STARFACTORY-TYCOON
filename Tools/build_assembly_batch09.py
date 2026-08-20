"""Journey batch 9 - assembly trim line: lowerator, doors, cockpit.

Body arrives from paint on the lowerator, doors come off onto the
climb section and carriers, cockpit installs by gantry assist, the
nutrunner rail runs the fastening, the andon board reports the line.
Original names into DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


# ---- body lowerator: twin-mast lift with fork carriage ----
NAME = "SM_LB_Assembly_BodyLowerator_v001"
kit.reset(); kit.glass_material()
for sx in (-2.95, 2.95):
    kit.box("MastBase", (0.9, 1.5, 0.5), (sx, 0.0, 0.25), kit.GREEN)
    kit.box("Mast", (0.45, 0.6, 6.9), (sx, 0.0, 3.7), kit.GREEN)
    kit.box("MastRail", (0.08, 0.14, 6.5), (sx - 0.28 if sx > 0
            else sx + 0.28, 0.0, 3.6), kit.CHARCOAL)
kit.box("TopBeam", (6.6, 0.7, 0.45), (0.0, 0.0, 7.18), kit.GREEN)
kit.cyl("DriveDrum", 0.28, 0.9, (0.0, 0.0, 6.9), kit.CHARCOAL,
        axis="X", verts=16)
kit.box("Carriage", (4.6, 0.5, 0.6), (0.0, 0.0, 3.1), kit.STEEL)
for fx in (-1.7, 1.7):
    kit.box("ForkArm", (0.35, 1.6, 0.18), (fx, 0.55, 2.95), kit.STEEL)
    kit.box("ForkPad", (0.4, 0.3, 0.08), (fx, 1.25, 3.05),
            kit.CHARCOAL)
kit.box("CounterWeight", (0.7, 0.5, 1.6), (-2.95, 0.0, 5.6),
        kit.CHARCOAL)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=12.0,
                                         height=6.0)

# ---- door climb section: inclined door conveyor ----
NAME = "SM_LB_Assembly_DoorClimbSection_v001"
kit.reset(); kit.glass_material()
kit.box("LowPost", (0.2, 0.5, 1.4), (-2.1, 0.0, 0.7), kit.GREEN)
kit.box("HighPost", (0.2, 0.5, 4.3), (2.1, 0.0, 2.15), kit.GREEN)
kit.box("ClimbRail", (5.1, 0.16, 0.3), (0.0, 0.0, 2.85), kit.STEEL,
        rot=(0.0, math.radians(-33.0), 0.0))
kit.box("ReturnRail", (5.1, 0.10, 0.14), (0.0, 0.0, 2.45), kit.CHARCOAL,
        rot=(0.0, math.radians(-33.0), 0.0))
kit.box("DriveBox", (0.8, 0.55, 0.6), (2.1, 0.0, 4.45), kit.GREEN)
for i, hx in enumerate((-1.5, 0.0, 1.5)):
    hz = 2.85 + math.tan(math.radians(33.0)) * hx - 0.55
    kit.box("HangerBar", (0.08, 0.08, 0.9), (hx, 0.0, hz), kit.STEEL)
    kit.box("DoorBlank", (1.05, 0.06, 1.1), (hx, 0.0, hz - 0.9),
            kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=8.5,
                                         height=3.6)

# ---- door carrier: trolley with padded hooks ----
NAME = "SM_LB_Assembly_DoorCarrier_v001"
kit.reset(); kit.glass_material()
kit.box("Trolley", (0.5, 0.2, 0.18), (0.0, 0.0, 2.5), kit.CHARCOAL)
for wx in (-0.16, 0.16):
    kit.cyl("TrolleyWheel", 0.07, 0.06, (wx, 0.0, 2.62), kit.STEEL,
            axis="Y", verts=12)
kit.box("DropBar", (0.1, 0.1, 1.9), (0.0, 0.0, 1.5), kit.GREEN)
kit.box("SpreadBar", (0.85, 0.1, 0.1), (0.0, 0.0, 0.6), kit.GREEN)
for hx in (-0.35, 0.35):
    kit.box("HookArm", (0.08, 0.3, 0.08), (hx, 0.12, 0.42), kit.STEEL)
    kit.box("HookPad", (0.14, 0.1, 0.3), (hx, 0.3, 0.3), kit.CHARCOAL)
kit.box("ClampHead", (0.2, 0.12, 0.2), (0.0, 0.0, 0.14), kit.RED)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=3.4,
                                         height=1.5)

# ---- cockpit install assist: portal manipulator ----
NAME = "SM_LB_Assembly_CockpitInstallAssist_v001"
kit.reset(); kit.glass_material()
for sx in (-2.05, 2.05):
    for sy in (-1.0, 1.0):
        kit.column("Post", (sx, sy, 0.0), 3.1, kit.GREEN, width=0.16)
    kit.box("SideBeam", (4.3, 0.16, 0.2), (0.0, sy if sy else 0, 3.2),
            kit.GREEN) if False else None
for sy in (-1.0, 1.0):
    kit.box("SideBeam", (4.3, 0.16, 0.2), (0.0, sy, 3.2), kit.GREEN)
kit.box("XRail", (0.2, 2.1, 0.24), (0.6, 0.0, 3.18), kit.STEEL)
kit.cyl("TelescopeOuter", 0.16, 1.1, (0.6, 0.0, 2.55), kit.STEEL,
        verts=14)
kit.cyl("TelescopeInner", 0.10, 1.1, (0.6, 0.0, 1.7), kit.CHARCOAL,
        verts=12)
kit.box("GripperPaddle", (1.3, 0.55, 0.12), (0.6, 0.0, 1.1), kit.GREEN)
for gx in (0.15, 1.05):
    kit.box("GripperFinger", (0.1, 0.5, 0.35), (gx, 0.0, 0.95),
            kit.CHARCOAL)
kit.box("ServoCab", (0.6, 0.4, 1.1), (-1.85, -0.85, 0.57), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=3.2)

# ---- cockpit module: the dash part itself ----
NAME = "SM_LB_Assembly_CockpitModule_v001"
kit.reset(); kit.glass_material()
kit.box("DashBeam", (1.55, 0.12, 0.12), (0.0, -0.1, 0.72),
        kit.STEEL)
kit.box("IPBody", (1.5, 0.55, 0.4), (0.0, 0.0, 0.85), kit.CHARCOAL)
kit.box("IPTopPad", (1.5, 0.45, 0.1), (0.0, -0.05, 1.1), kit.GREEN)
kit.box("ClusterHump", (0.45, 0.3, 0.14), (-0.45, -0.15, 1.16),
        kit.CHARCOAL)
kit.box("ColumnStub", (0.09, 0.09, 0.5), (-0.45, 0.1, 0.5), kit.STEEL,
        rot=(math.radians(35.0), 0.0, 0.0))
kit.box("HVACBlock", (0.7, 0.5, 0.35), (0.15, 0.05, 0.4),
        kit.STEEL)
kit.box("CenterStack", (0.3, 0.25, 0.35), (0.15, -0.18, 0.9),
        kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=2.6,
                                         height=1.1)

# ---- nutrunner reaction rail: overhead tools on trolleys ----
NAME = "SM_LB_Assembly_NutrunnerReactionRail_v001"
kit.reset(); kit.glass_material()
for px in (-3.95, 0.0, 3.95):
    kit.box("Post", (0.16, 0.16, 3.1), (px, 0.45, 1.55), kit.GREEN)
kit.box("Rail", (8.4, 0.14, 0.26), (0.0, 0.45, 3.1), kit.STEEL)
kit.box("KickBrace", (0.1, 0.4, 0.1), (0.0, 0.25, 2.95), kit.GREEN)
for i, tx in enumerate((-2.6, -0.3, 2.2)):
    kit.box("Trolley", (0.3, 0.16, 0.16), (tx, 0.45, 2.95),
            kit.CHARCOAL)
    kit.cyl("Balancer", 0.12, 0.35, (tx, 0.45, 2.7), kit.GREEN,
            verts=12)
    kit.cyl("ToolCable", 0.03, 1.5, (tx, 0.45, 1.85), kit.CHARCOAL,
            verts=8)
    kit.cyl("NutrunnerBody", 0.07, 0.45, (tx, 0.45, 1.0), kit.STEEL,
            verts=10)
    kit.cyl("SocketHead", 0.05, 0.15, (tx, 0.45, 0.72), kit.CHARCOAL,
            verts=8)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=11.0,
                                         height=3.2)

# ---- andon board: line status display ----
NAME = "SM_LB_Assembly_AndonBoard_v001"
kit.reset(); kit.glass_material()
for px in (-1.9, 1.9):
    kit.box("Post", (0.14, 0.14, 3.1), (px, 0.0, 1.55), kit.GREEN)
kit.box("BoardShell", (4.35, 0.3, 1.5), (0.0, 0.0, 3.85), kit.CHARCOAL)
kit.box("ScreenFace", (4.1, 0.05, 1.25), (0.0, -0.17, 3.85),
        kit.GLASS, chamfer=False)
for i in range(4):
    kit.box("SegBlock", (0.85, 0.04, 0.5), (-1.55 + i * 1.05, -0.2,
            4.1), kit.WARMWHITE, chamfer=False)
kit.box("StatusStrip", (4.1, 0.04, 0.18), (0.0, -0.2, 3.4), kit.GREEN,
        chamfer=False)
kit.box("RoofStrip", (4.45, 0.36, 0.08), (0.0, 0.0, 4.66), kit.GREEN)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=7.5,
                                         height=3.8)
print("BATCH09 COMPLETE")
