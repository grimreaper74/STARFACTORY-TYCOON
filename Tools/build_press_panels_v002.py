"""Stamped press panels for the dev car v002, with thumbnails.

The panels the press lines and stillages carry, derived from the same
car: bodyside outers (L/R) with window cutline form, roof outer with
crown, door outers, bonnet with power dome, tailgate outer, floor pan
with seat cross-ribs. Bare machined-steel stampings with flanges and
slight crown so they read as drawn sheet metal, not tiles. Each panel
lies flat as pressed (largest face up), floor pivot.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

OUT_DIR = "PressPanels_v002/"
STEEL = kit.STEEL


def crowned_sheet(name, length, width, crown, thick=0.012, seg=6):
    """A gently crowned sheet lying in XY, apex up."""
    for i in range(seg):
        a0 = (i / seg - 0.5) * math.pi
        a1 = ((i + 1) / seg - 0.5) * math.pi
        y0 = math.sin(a0) * width / 2.0
        y1 = math.sin(a1) * width / 2.0
        z_mid = crown * (math.cos((a0 + a1) / 2.0))
        seg_w = y1 - y0
        ang = math.atan2(crown * (math.cos(a1) - math.cos(a0)), seg_w)
        kit.box(name + "Seg", (length, seg_w * 1.02, thick),
                ((0.0), (y0 + y1) / 2.0, 0.05 + z_mid), STEEL,
                rot=(ang, 0.0, 0.0), chamfer=False)


def flange(name, length, width, drop=0.05):
    """Perimeter flanges turned down around a sheet."""
    for sy in (-width / 2.0, width / 2.0):
        kit.box(name + "FlangeY", (length, 0.012, drop),
                (0.0, sy, 0.03), STEEL, chamfer=False)
    for sx in (-length / 2.0, length / 2.0):
        kit.box(name + "FlangeX", (0.012, width, drop),
                (sx, 0.0, 0.03), STEEL, chamfer=False)


def export_panel(name, distance=3.2, height=1.4):
    full = "SM_LB_PressPanel_{}_v002".format(name)
    kit.export(full, OUT_DIR + full)
    kit.preview(full, OUT_DIR + full, distance=distance, height=height)


# ---- bodyside outer (one per side; R mirrored) ----
for tag, mirror in (("BodysideOuter_L", 1.0), ("BodysideOuter_R", -1.0)):
    kit.reset(); kit.glass_material()
    crowned_sheet("Side", 3.6, 1.15, 0.05)
    # Window aperture read: a raised cutline frame where glass would be.
    kit.box("WindowLine", (1.9, 0.012, 0.05),
            (0.15 * mirror, 0.18, 0.075), STEEL, chamfer=False)
    kit.box("ArchCut", (0.012, 0.5, 0.05), (-1.35 * mirror, -0.30,
            0.075), STEEL, chamfer=False)
    kit.box("ArchCut", (0.012, 0.5, 0.05), (1.30 * mirror, -0.30,
            0.075), STEEL, chamfer=False)
    flange("Side", 3.6, 1.15)
    export_panel(tag, distance=4.4)

# ---- roof outer ----
kit.reset(); kit.glass_material()
crowned_sheet("Roof", 1.75, 1.45, 0.06)
flange("Roof", 1.75, 1.45)
export_panel("RoofOuter", distance=3.4)

# ---- door outers ----
for tag, dlen in (("DoorOuter_F", 1.02), ("DoorOuter_R", 0.90)):
    kit.reset(); kit.glass_material()
    crowned_sheet("Door", dlen, 0.78, 0.035)
    kit.box("HandleRecess", (0.16, 0.05, 0.02),
            (dlen * 0.28, 0.22, 0.075), STEEL, chamfer=False)
    flange("Door", dlen, 0.78, drop=0.04)
    export_panel(tag, distance=2.4, height=1.0)

# ---- bonnet outer with power dome ----
kit.reset(); kit.glass_material()
crowned_sheet("Bonnet", 1.30, 1.55, 0.05)
kit.box("Dome", (0.85, 0.48, 0.028), (0.05, 0.0, 0.105), STEEL)
flange("Bonnet", 1.30, 1.55)
export_panel("BonnetOuter", distance=3.2)

# ---- tailgate outer ----
kit.reset(); kit.glass_material()
crowned_sheet("Tailgate", 1.15, 1.42, 0.04)
kit.box("PlatePocket", (0.50, 0.14, 0.015), (0.12, -0.28, 0.08),
        STEEL, chamfer=False)
flange("Tailgate", 1.15, 1.42, drop=0.045)
export_panel("TailgateOuter", distance=3.0)

# ---- floor pan with cross ribs and tunnel ----
kit.reset(); kit.glass_material()
kit.box("Pan", (2.9, 1.6, 0.014), (0.0, 0.0, 0.05), STEEL,
        chamfer=False)
for rx in (-1.0, -0.35, 0.35, 1.0):
    kit.box("CrossRib", (0.10, 1.55, 0.045), (rx, 0.0, 0.085), STEEL)
kit.box("Tunnel", (2.85, 0.28, 0.09), (0.0, 0.0, 0.10), STEEL)
for side in (-0.72, 0.72):
    kit.box("SillBox", (2.85, 0.10, 0.07), (0.0, side, 0.085), STEEL)
export_panel("FloorPan", distance=4.0)

print("PANELS COMPLETE")
