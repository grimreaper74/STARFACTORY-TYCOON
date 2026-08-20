"""Cab-over tractor unit for the car transporter - proportion-first.

Both rejected attempts failed on proportions (narrow tall cab, oversized
wheels). This build starts from real haulage dimensions: 6.1 m long,
2.45 m cab width, 3.3 m cab height, 1.05 m wheels, visible chassis
rails, 6x4 axle layout with twin drive tyres. Then the day's geometry
rules: bevel everything, mechanisms modelled (fifth wheel, suzies,
steps, wipers), glass as glass, no bare faces.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

NAME = "SM_LB_Site_Transporter_v001_Tractor"
FOLDER = "Site/TransporterRework_v001"

TIRE = ("MAT_TireBlack", (0.015, 0.016, 0.018, 1.0))
GLASS = ("MAT_CabGlass", (0.04, 0.10, 0.10, 1.0))

kit.reset()

# Custom glass finish.
glass_mat = kit.material(*GLASS)
glass_mat.node_tree.nodes["Principled BSDF"].inputs[
    "Roughness"].default_value = 0.08
glass_mat.node_tree.nodes["Principled BSDF"].inputs[
    "Metallic"].default_value = 0.4


def wheel(x, y, twin=False):
    """Tyre + dished hub + bolt circle; twins for the drive axles."""
    offsets = (-0.17, 0.17) if twin else (0.0,)
    for off in offsets:
        kit.cyl("Tire", 0.525, 0.30, (x, y + off, 0.525), TIRE,
                axis="Y", verts=36)
        side = 1.0 if y > 0 else -1.0
        face_y = y + off + side * 0.16
        kit.cyl("Hub", 0.30, 0.05, (x, face_y, 0.525), kit.STEEL,
                axis="Y", verts=28)
        kit.cyl("HubCap", 0.09, 0.08, (x, face_y + side * 0.02, 0.525),
                kit.CHARCOAL, axis="Y", verts=16)
        for bolt in range(8):
            angle = bolt * math.tau / 8.0
            kit.cyl("Bolt", 0.024, 0.04,
                    (x + math.cos(angle) * 0.19, face_y + side * 0.015,
                     0.525 + math.sin(angle) * 0.19),
                    kit.CHARCOAL, axis="Y", verts=8)


# ---- chassis ----
for y in (-0.44, 0.44):
    kit.box("Rail", (5.9, 0.09, 0.26), (0.0, y, 0.82), kit.CHARCOAL)
for x in (-2.6, -1.2, 0.2, 1.6):
    kit.box("CrossMember", (0.08, 0.98, 0.18), (x, 0.0, 0.82),
            kit.CHARCOAL)
kit.box("Bumper", (0.16, 2.42, 0.34), (3.02, 0.0, 0.62), kit.CHARCOAL)
kit.box("BumperStep", (0.10, 1.10, 0.06), (3.06, 0.0, 0.82), kit.STEEL)
kit.box("Plate", (0.02, 0.52, 0.13), (3.11, 0.0, 0.60), kit.WARMWHITE,
        chamfer=False)

# ---- axles and wheels ----
wheel(2.05, -0.95)
wheel(2.05, 0.95)
for x in (-1.05, -2.35):
    kit.cyl("Axle", 0.075, 1.9, (x, 0.0, 0.525), kit.CHARCOAL, axis="Y",
            verts=14)
    wheel(x, -0.86, twin=True)
    wheel(x, 0.86, twin=True)
kit.cyl("SteerAxle", 0.07, 1.9, (2.05, 0.0, 0.525), kit.CHARCOAL,
        axis="Y", verts=14)

# Drive mudguards: segmented arcs over the tandem, one shell each side.
for y in (-0.9, 0.9):
    for x_c in (-1.05, -2.35):
        for seg in range(5):
            a = math.radians(30 + seg * 26)
            kit.box("Guard", (0.34, 0.62, 0.045),
                    (x_c - math.cos(a) * 0.66, y,
                     0.525 + math.sin(a) * 0.66),
                    kit.CHARCOAL, rot=(0.0, a - math.pi / 2, 0.0))

# ---- cab (wide and low; x +0.75 .. +3.0) ----
kit.box("CabLower", (2.2, 2.42, 0.72), (1.88, 0.0, 1.32), kit.CHARCOAL)
kit.box("CabUpper", (2.05, 2.42, 1.28), (1.80, 0.0, 2.32), kit.CHARCOAL)
kit.box("CabRoof", (2.0, 2.30, 0.10), (1.78, 0.0, 3.01), kit.CHARCOAL)
kit.box("RoofDeflector", (0.85, 2.24, 0.05), (1.58, 0.0, 3.16),
        kit.CHARCOAL, rot=(0.0, math.radians(-16.0), 0.0))
# Windscreen: full-width raked glass with pillars and a visor.
kit.box("Screen", (0.04, 2.05, 1.00), (2.86, 0.0, 2.42), GLASS,
        rot=(0.0, math.radians(8.0), 0.0), chamfer=False)
for y in (-1.12, 1.12):
    kit.box("APillar", (0.10, 0.09, 1.05), (2.85, y, 2.42), kit.CHARCOAL,
            rot=(0.0, math.radians(8.0), 0.0))
kit.box("Visor", (0.34, 2.30, 0.05), (2.88, 0.0, 3.02), kit.CHARCOAL,
        rot=(0.0, math.radians(12.0), 0.0))
for wiper_y in (-0.55, 0.25):
    kit.box("Wiper", (0.02, 0.50, 0.02), (2.90, wiper_y, 2.12), kit.STEEL,
            rot=(0.0, math.radians(8.0), math.radians(18.0)), chamfer=False)
# Grille slats, lights, livery.
for slat in range(4):
    kit.box("Grille", (0.05, 1.85, 0.09),
            (2.97, 0.0, 1.30 + slat * 0.155), kit.STEEL)
for y in (-0.95, 0.95):
    kit.box("Lamp", (0.08, 0.42, 0.16), (3.00, y, 1.02), kit.WARMWHITE)
    kit.box("LampBezel", (0.05, 0.48, 0.20), (2.98, y, 1.02),
            kit.CHARCOAL)
kit.box("LiveryBand", (2.06, 2.46, 0.16), (1.80, 0.0, 1.62), kit.GREEN,
        chamfer=False)
kit.box("DecalPanel", (0.02, 1.30, 0.34), (2.99, 0.0, 2.94),
        kit.WARMWHITE, chamfer=False)
# Side glass, door lines, handles, steps, mirrors.
for y in (-1.22, 1.22):
    kit.box("SideGlass", (1.15, 0.03, 0.62), (2.05, y, 2.42), GLASS,
            chamfer=False)
    kit.box("DoorLine", (0.02, 0.05, 1.55), (1.45, y, 2.02),
            kit.CHARCOAL, chamfer=False)
    kit.box("Handle", (0.18, 0.04, 0.05), (1.62, y + (0.02 if y > 0
            else -0.02), 1.80), kit.STEEL)
    for step in range(2):
        kit.box("Step", (0.42, 0.30, 0.05),
                (2.35, y * 1.02, 0.62 + step * 0.34), kit.STEEL)
    arm_dir = 1.0 if y > 0 else -1.0
    kit.cyl("MirrorArm", 0.02, 0.42, (2.72, y + arm_dir * 0.18, 2.95),
            kit.STEEL, axis="Y", verts=10)
    kit.box("Mirror", (0.06, 0.05, 0.42), (2.72, y + arm_dir * 0.40, 2.72),
            kit.CHARCOAL)

# ---- behind-cab deck ----
kit.box("Catwalk", (1.05, 2.0, 0.05), (0.10, 0.0, 1.00), kit.STEEL)
for y in (-0.9, 0.0, 0.9):
    kit.cyl("RailPost", 0.022, 0.55, (-0.28, y, 1.30), kit.STEEL,
            verts=10)
kit.box("RailBar", (0.03, 1.86, 0.04), (-0.28, 0.0, 1.56), kit.STEEL)
kit.cyl("Exhaust", 0.085, 1.65, (0.42, -1.05, 1.95), kit.STEEL, verts=16)
kit.box("HeatShield", (0.24, 0.14, 1.35), (0.42, -0.92, 1.95),
        kit.CHARCOAL)
for idx, y in enumerate((-0.35, 0.0, 0.35)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.16, minor_radius=0.025,
        location=(-0.05, y, 1.42 + (idx % 2) * 0.05))
    coil = bpy.context.active_object
    coil.name = "Suzie"
    coil.rotation_euler = (0.0, math.radians(90.0), 0.0)
    coil.data.materials.append(kit.material(*kit.YELLOW if idx == 1
                                            else kit.CHARCOAL))
# Fifth wheel: plate, disc with entry ramps.
kit.box("FWPlate", (1.0, 1.1, 0.08), (-1.55, 0.0, 1.00), kit.CHARCOAL)
kit.cyl("FifthWheel", 0.48, 0.09, (-1.55, 0.0, 1.09), kit.STEEL,
        verts=32)
for y in (-0.22, 0.22):
    kit.box("FWRamp", (0.5, 0.16, 0.06), (-2.05, y, 1.05), kit.STEEL,
            rot=(0.0, math.radians(14.0), 0.0))

# ---- tanks and skirts ----
for y in (-0.86, 0.86):
    kit.cyl("FuelTank", 0.31, 1.25, (0.85, y, 0.66), kit.STEEL, axis="X",
            verts=24)
    for strap_x in (0.45, 1.25):
        kit.box("TankStrap", (0.05, 0.05, 0.68), (strap_x, y, 0.66),
                kit.CHARCOAL)
kit.box("BatteryBox", (0.8, 0.28, 0.4), (-0.55, -0.92, 0.62),
        kit.CHARCOAL)
kit.box("SideSkirt", (1.15, 0.04, 0.35), (-0.45, 0.92, 0.60),
        kit.CHARCOAL)

# Roof furniture: marker lamps and twin air horns.
for y in (-0.75, -0.25, 0.25, 0.75):
    kit.box("MarkerLamp", (0.07, 0.12, 0.05), (2.72, y, 3.09),
            kit.YELLOW, chamfer=False)
for y in (-0.35, 0.35):
    kit.cyl("Horn", 0.045, 0.5, (1.35, y, 3.14), kit.STEEL, axis="X",
            verts=12)

kit.export(NAME, FOLDER)
kit.preview(NAME, FOLDER, distance=11.5, height=2.3)
