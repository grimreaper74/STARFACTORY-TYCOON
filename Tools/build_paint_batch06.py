"""Journey batch 6 - paint's seven tunnel and booth shells.

Footprint-true rebuilds of the pieces the paint journey runs through:
spray booth (glazed sides, plenum roof), flash-off, quality light
tunnel (vision arches - lights-out plant, no walkways), pretreatment
wash, ED dip hood, curing oven and tack-off. Original names into
DetailUplift for the standard swap.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402


def out(name):
    return "DetailUplift_v001/" + name


def end_aperture(width, height, x, depth=0.12):
    """Recessed dark end panel reading as the tunnel opening."""
    kit.box("Aperture", (depth, width, height), (x, 0.0, height / 2.0),
            kit.CHARCOAL, chamfer=False)


# ---- spray booth shell: glazed hero booth ----
NAME = "SM_LB_Paint_SprayBoothShell_v001"
kit.reset(); kit.glass_material()
kit.box("FloorBand", (13.7, 7.4, 0.25), (0.0, 0.0, 0.125), kit.CHARCOAL)
kit.box("GratingLane", (13.7, 3.0, 0.06), (0.0, 0.0, 0.28), kit.STEEL)
for sy in (-3.62, 3.62):
    kit.box("SillBeam", (13.7, 0.16, 0.9), (0.0, sy, 0.7), kit.GREEN)
    kit.box("HeadBeam", (13.7, 0.16, 0.5), (0.0, sy, 4.2), kit.GREEN)
    for i in range(8):
        mx = -6.0 + i * 1.71
        kit.box("Mullion", (0.14, 0.14, 3.1), (mx, sy, 2.6), kit.GREEN)
    for i in range(7):
        gx = -5.14 + i * 1.71
        kit.box("Glazing", (1.5, 0.04, 2.9), (gx, sy, 2.6), kit.GLASS,
                chamfer=False)
    kit.box("LightRail", (13.4, 0.10, 0.16), (0.0, sy * 0.96, 4.0),
            kit.WARMWHITE)
kit.box("PlenumRoof", (13.75, 7.46, 1.1), (0.0, 0.0, 5.0), kit.GREEN)
for i in range(6):
    kit.box("FilterSeam", (0.06, 7.2, 0.9), (-5.6 + i * 2.26, 0.0, 5.0),
            kit.CHARCOAL, chamfer=False)
for dx in (-4.5, -1.5, 1.5, 4.5):
    kit.cyl("SupplyCollar", 0.5, 0.5, (dx, 0.0, 5.75), kit.STEEL,
            verts=16)
for ex in (-6.82, 6.82):
    kit.box("EndFrame", (0.18, 7.46, 5.4), (ex, 0.0, 2.7), kit.GREEN)
end_aperture(3.4, 4.4, -6.86); end_aperture(3.4, 4.4, 6.86)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=20.0,
                                         height=6.5)

# ---- flash-off tunnel: sealed panel tunnel, roof extract fans ----
NAME = "SM_LB_Paint_FlashOffTunnel_v001"
kit.reset(); kit.glass_material()
kit.box("Shell", (7.0, 5.8, 4.7), (0.0, 0.0, 2.35), kit.GREEN)
for i in range(4):
    kit.box("PanelSeam", (0.08, 5.9, 4.4), (-2.6 + i * 1.75, 0.0, 2.3),
            kit.CHARCOAL, chamfer=False)
kit.box("SkirtBand", (7.05, 5.85, 0.4), (0.0, 0.0, 0.2), kit.CHARCOAL)
for fx in (-1.8, 1.8):
    kit.cyl("ExtractFan", 0.55, 0.5, (fx, 0.0, 4.90), kit.STEEL,
            verts=16)
    kit.cyl("FanCowl", 0.65, 0.15, (fx, 0.0, 5.05), kit.CHARCOAL,
            verts=16)
kit.box("AccessHatch", (0.9, 0.06, 1.6), (2.4, -2.94, 1.3),
        kit.CHARCOAL)
end_aperture(3.2, 4.2, -3.52); end_aperture(3.2, 4.2, 3.52)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=12.0,
                                         height=5.0)

# ---- quality light tunnel: vision arches, no human decks ----
NAME = "SM_LB_Paint_QualityLightTunnel_v001"
kit.reset(); kit.glass_material()
for ax in (-2.7, -0.9, 0.9, 2.7):
    for sy in (-2.85, 2.85):
        kit.column("Post", (ax, sy, 0.0), 3.9, kit.GREEN, width=0.16)
    kit.box("ArchBeam", (0.18, 5.9, 0.22), (ax, 0.0, 4.05), kit.GREEN)
    kit.box("LightArch", (0.12, 4.6, 0.14), (ax, 0.0, 3.82),
            kit.WARMWHITE, chamfer=False)
    for sy in (-2.35, 2.35):
        kit.box("LightColumn", (0.12, 0.14, 2.6), (ax, sy, 2.35),
                kit.WARMWHITE, chamfer=False)
kit.box("RoofSpine", (5.9, 0.3, 0.18), (0.0, 0.0, 4.22), kit.GREEN)
for cx in (-1.8, 0.0, 1.8):
    kit.box("CameraPod", (0.28, 0.22, 0.20), (cx, 0.0, 3.95),
            kit.CHARCOAL)
    kit.cyl("Lens", 0.05, 0.12, (cx, 0.0, 3.80), kit.STEEL, verts=10)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=10.5,
                                         height=4.5)

# ---- pretreatment wash tunnel: stainless shell, spray plumbing ----
NAME = "SM_LB_Paint_PretreatmentWashTunnel_v001"
kit.reset(); kit.glass_material()
kit.box("Shell", (8.5, 6.0, 5.0), (0.0, 0.0, 2.5), kit.STEEL)
for i in range(5):
    kit.box("PanelRib", (0.10, 6.1, 4.7), (-3.4 + i * 1.7, 0.0, 2.45),
            kit.CHARCOAL, chamfer=False)
kit.box("DrainChannel", (8.55, 1.2, 0.3), (0.0, 0.0, 0.15),
        kit.CHARCOAL)
kit.box("RoofManifold", (8.2, 0.5, 0.4), (0.0, 1.9, 5.2), kit.STEEL)
kit.box("RoofManifold", (8.2, 0.5, 0.4), (0.0, -1.9, 5.2), kit.STEEL)
for px in (-3.0, -1.0, 1.0, 3.0):
    kit.cyl("RiserPipe", 0.09, 0.7, (px, 1.9, 4.85), kit.STEEL,
            verts=10)
    kit.cyl("RiserPipe", 0.09, 0.7, (px, -1.9, 4.85), kit.STEEL,
            verts=10)
    kit.cyl("ValveWheel", 0.12, 0.08, (px, 2.42, 5.2), kit.RED,
            verts=12, axis="Y")
end_aperture(3.3, 4.3, -4.27); end_aperture(3.3, 4.3, 4.27)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=13.0,
                                         height=5.5)

# ---- ED dip hood: raked entry shell over the tank ----
NAME = "SM_LB_Paint_EDDipTunnel_v001"
kit.reset(); kit.glass_material()
kit.box("Shell", (8.1, 6.1, 5.4), (0.0, 0.0, 2.95), kit.GREEN)
kit.box("RakePanel", (2.6, 6.15, 0.18), (-3.2, 0.0, 4.6), kit.GREEN,
        rot=(0.0, math.radians(-28.0), 0.0))
kit.box("RakePanel", (2.6, 6.15, 0.18), (3.2, 0.0, 4.6), kit.GREEN,
        rot=(0.0, math.radians(28.0), 0.0))
for i in range(4):
    kit.box("PanelSeam", (0.08, 6.2, 5.1), (-2.4 + i * 1.6, 0.0, 2.9),
            kit.CHARCOAL, chamfer=False)
kit.box("BusbarDuct", (7.9, 0.6, 0.35), (0.0, 0.0, 5.85), kit.CHARCOAL)
for ty in (-3.12, 3.12):
    kit.box("CableTray", (7.8, 0.12, 0.30), (0.0, ty, 4.6), kit.STEEL)
end_aperture(3.2, 4.6, -4.07); end_aperture(3.2, 4.6, 4.07)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=13.0,
                                         height=5.8)

# ---- curing oven tunnel: insulated shell, twin burner houses ----
NAME = "SM_LB_Paint_CuringOvenTunnel_v001"
kit.reset(); kit.glass_material()
kit.box("Shell", (9.0, 6.0, 5.0), (0.0, 0.0, 2.5), kit.GREEN)
for i in range(6):
    kit.box("PanelSeam", (0.08, 6.1, 4.7), (-3.75 + i * 1.5, 0.0, 2.45),
            kit.CHARCOAL, chamfer=False)
for ex in (-4.42, 4.42):
    kit.box("SealVestibule", (0.35, 6.05, 5.2), (ex, 0.0, 2.6),
            kit.CHARCOAL)
for bx in (-2.2, 2.2):
    kit.box("BurnerHouse", (1.6, 1.2, 0.9), (bx, 1.6, 5.45), kit.STEEL)
    kit.cyl("BurnerStack", 0.18, 0.7, (bx, 1.6, 6.1), kit.STEEL,
            verts=14)
kit.box("RecircDuct", (5.5, 0.5, 0.4), (0.0, -1.7, 5.2), kit.STEEL)
end_aperture(3.1, 4.1, -4.62); end_aperture(3.1, 4.1, 4.62)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=14.0,
                                         height=5.8)

# ---- tack-off tunnel: ionised-air frame with curtain strips ----
NAME = "SM_LB_Paint_TackOffTunnel_v001"
kit.reset(); kit.glass_material()
for ax in (-2.8, 0.0, 2.8):
    for sy in (-1.17, 1.17):
        kit.column("Post", (ax, sy, 0.0), 3.2, kit.GREEN, width=0.14)
    kit.box("ArchBeam", (0.16, 2.5, 0.18), (ax, 0.0, 3.32), kit.GREEN)
kit.box("Plenum", (6.1, 2.2, 0.35), (0.0, 0.0, 3.30), kit.STEEL)
for nx in (-2.0, -0.7, 0.7, 2.0):
    kit.box("IonBar", (0.10, 2.0, 0.10), (nx, 0.0, 3.06),
            kit.WARMWHITE, chamfer=False)
for ex in (-3.0, 3.0):
    for i in range(6):
        kit.box("Curtain", (0.03, 0.34, 2.6), (ex, -0.95 + i * 0.38,
                1.55), kit.CHARCOAL, chamfer=False)
kit.export(NAME, out(NAME)); kit.preview(NAME, out(NAME), distance=8.5,
                                         height=3.5)
print("BATCH06 COMPLETE")
