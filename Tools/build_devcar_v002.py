"""Clean-room development car v002 - the Cairnwell product family.

The body is one lofted surface: cross-section rings (belt width, top
width for tumblehome, top height from the side profile) connected
nose to tail, with glass assigned by face slope and station - so the
silhouette is a real car, not stacked boxes. Kit boxes add the
jewellery: light bars, aprons, mirrors, handles, shut lines, wheels.
Three body styles (hatch / estate / crossover) x three colourways.
Zero real-car references; the full-width light bars are the Cairnwell
signature.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bmesh  # noqa: E402
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

OUT_DIR = "DevCar_v002/"

LEN = 4.36
FRONT_AXLE = 0.88
WHEELBASE = 2.72
WHEEL_R = 0.345
SILL_Z = 0.16

BODY_COLOURS = {
    "EmeraldGreen": kit.GREEN,
    "AlpineWhite": ("MAT_AlpineWhite", (0.85, 0.86, 0.84, 1.0)),
    "GraphiteGrey": ("MAT_GraphiteGrey", (0.16, 0.17, 0.18, 1.0)),
}

# Hatch profile: (x, top_z, belt_z, half_w_belt, half_w_top)
HATCH = [
    (0.00, 0.62, 0.62, 0.64, 0.60),
    (0.08, 0.76, 0.72, 0.76, 0.72),
    (0.35, 0.85, 0.80, 0.86, 0.82),
    (0.90, 0.905, 0.86, 0.905, 0.87),
    (1.48, 0.925, 0.88, 0.92, 0.885),
    (1.80, 1.16, 0.90, 0.92, 0.80),
    (2.35, 1.44, 0.915, 0.92, 0.75),
    (3.30, 1.455, 0.925, 0.91, 0.745),
    (3.85, 1.30, 0.935, 0.885, 0.73),
    (4.20, 1.08, 0.945, 0.835, 0.71),
    (4.36, 0.98, 0.95, 0.78, 0.69),
]


def style_profile(style):
    """Transform the hatch table into the requested body style."""
    rows = []
    for x, top, belt, wb, wt in HATCH:
        if style == "Estate":
            # Long roof: hold the crown further back, gentler rake.
            if x >= 3.30:
                blend = (x - 3.30) / (4.36 - 3.30)
                top = max(top, 1.455 - 0.28 * blend ** 1.6)
        elif style == "Cross":
            top += 0.055
            belt += 0.05
        rows.append((x, top, belt, wb, wt))
    return rows


GLASS_SIDE_X = (1.56, 3.98)      # side glass runs between these stations
SCREEN_X = (1.48, 2.40)          # sloped top faces here are windscreen
REAR_GLASS_X = (3.45, 4.32)      # sloped top faces here are rear glass


def loft_body(style, body_mat):
    profile = style_profile(style)
    lift = 0.06 if style == "Cross" else 0.0
    mesh = bpy.data.meshes.new("BodyLoft")
    obj = bpy.data.objects.new("BodyLoft", mesh)
    bpy.context.collection.objects.link(obj)
    body = kit.material(*body_mat)
    glass = kit.material(*kit.GLASS)
    obj.data.materials.append(body)
    obj.data.materials.append(glass)

    bm = bmesh.new()
    rings = []
    for x, top, belt, wb, wt in profile:
        x0 = x - LEN / 2.0
        sill = SILL_Z + lift
        top += lift
        belt += lift
        ring = [
            bm.verts.new((x0, -wb, sill)),
            bm.verts.new((x0, -wb, belt)),
            bm.verts.new((x0, -wt, top)),
            bm.verts.new((x0, wt, top)),
            bm.verts.new((x0, wb, belt)),
            bm.verts.new((x0, wb, sill)),
        ]
        rings.append((x, ring))

    def face_mat(kind, x_mid, slope_deg):
        if kind == "side":
            lo, hi = GLASS_SIDE_X
            return 1 if lo < x_mid < hi else 0
        if kind == "top" and slope_deg > 20.0:
            if SCREEN_X[0] < x_mid < SCREEN_X[1]:
                return 1
            if REAR_GLASS_X[0] < x_mid < REAR_GLASS_X[1]:
                return 1
        return 0

    for (xa, ra), (xb, rb) in zip(rings, rings[1:]):
        x_mid = (xa + xb) / 2.0
        quads = (
            (ra[0], ra[1], rb[1], rb[0], "lower"),
            (ra[1], ra[2], rb[2], rb[1], "side"),
            (ra[2], ra[3], rb[3], rb[2], "top"),
            (ra[3], ra[4], rb[4], rb[3], "side"),
            (ra[4], ra[5], rb[5], rb[4], "lower"),
        )
        for va, vb, vc, vd, kind in quads:
            face = bm.faces.new((va, vb, vc, vd))
            rise = abs((vc.co.z + vd.co.z) - (va.co.z + vb.co.z)) / 2.0
            run = max(abs(xb - xa), 1e-4)
            slope = math.degrees(math.atan2(rise, run))
            face.material_index = face_mat(kind, x_mid, slope)

    # Close the nose and tail faces (body colour).
    for ring, flip in ((rings[0][1], True), (rings[-1][1], False)):
        verts = list(reversed(ring)) if flip else ring
        face = bm.faces.new(verts)
        face.material_index = 0

    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()

    bevel = obj.modifiers.new("Bevel", "BEVEL")
    bevel.width = 0.025
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bevel.angle_limit = math.radians(38.0)
    return obj


def dress_car(style, body_mat):
    p = dict((row[0], row) for row in style_profile(style))
    lift = 0.06 if style == "Cross" else 0.0
    sill = SILL_Z + lift
    belt_f = 0.88 + lift
    nose_top = 0.62 + lift
    tail_belt = 0.95 + lift
    body = body_mat

    def cx(x):
        return x - LEN / 2.0

    # Signature light bars set into the nose and tail faces.
    kit.box("FrontLightBar", (0.05, 1.34, 0.055),
            (cx(0.015), 0.0, nose_top - 0.10), kit.WARMWHITE,
            chamfer=False)
    kit.box("RearLightBar", (0.05, 1.30, 0.055),
            (cx(LEN - 0.015), 0.0, tail_belt - 0.12), kit.RED,
            chamfer=False)
    kit.box("FrontApron", (0.10, 1.10, 0.15),
            (cx(0.06), 0.0, sill + 0.10), kit.CHARCOAL)
    kit.box("RearApron", (0.10, 1.10, 0.14),
            (cx(LEN - 0.06), 0.0, sill + 0.09), kit.CHARCOAL)
    kit.box("NumberBlank", (0.02, 0.46, 0.11),
            (cx(LEN - 0.005), 0.0, tail_belt - 0.30), kit.STEEL,
            chamfer=False)

    # Belt trim, shut lines and handles along each side.
    for side in (-1.0, 1.0):
        sy = side * 0.925
        kit.box("BeltTrim", (2.55, 0.018, 0.03),
                (cx(2.80), sy - side * 0.0, belt_f + 0.045 + lift * 0.0),
                kit.CHARCOAL, chamfer=False)
        for shut_x in (1.52, 2.56, 3.48):
            kit.box("ShutLine", (0.014, 0.02, 0.62),
                    (cx(shut_x), side * 0.915, sill + 0.42),
                    kit.CHARCOAL, chamfer=False)
        for handle_x in (2.30, 3.28):
            kit.box("DoorHandle", (0.15, 0.02, 0.03),
                    (cx(handle_x), side * 0.93, belt_f - 0.055),
                    kit.CHARCOAL, chamfer=False)
        kit.box("MirrorArm", (0.05, 0.07, 0.026),
                (cx(1.58), side * 0.955, belt_f + 0.075),
                kit.CHARCOAL, chamfer=False)
        kit.box("MirrorHead", (0.10, 0.08, 0.07),
                (cx(1.56), side * 1.01, belt_f + 0.095), body)
        kit.box("SillTrim", (2.5, 0.035,
                0.11 if style == "Cross" else 0.05),
                (cx(2.24), side * 0.905, sill + 0.03), kit.CHARCOAL)
    kit.box("ChargeDoor", (0.15, 0.015, 0.125),
            (cx(0.72), 0.90, belt_f - 0.10), kit.CHARCOAL,
            chamfer=False)
    kit.box("CowlVent", (0.07, 1.20, 0.02),
            (cx(1.50), 0.0, 0.93 + lift), kit.CHARCOAL, chamfer=False)
    kit.box("BonnetShut", (1.05, 0.012, 0.012),
            (cx(0.88), -0.70, 0.90 + lift), kit.CHARCOAL, chamfer=False)
    kit.box("BonnetShut", (1.05, 0.012, 0.012),
            (cx(0.88), 0.70, 0.90 + lift), kit.CHARCOAL, chamfer=False)

    # Roof furniture.
    roof_z = (1.455 if style != "Cross" else 1.51) + (0.0 if style
              != "Cross" else 0.0)
    roof_z = 1.455 + (0.055 if style == "Cross" else 0.0)
    for side in (-1.0, 1.0):
        kit.box("RoofRail", (0.85, 0.05, 0.04),
                (cx(2.80), side * 0.56, roof_z + 0.012), kit.CHARCOAL)
    kit.cyl("SharkFin", 0.03, 0.075, (cx(3.85), 0.0,
            (1.30 if style == "Hatch" else 1.40) + lift),
            kit.CHARCOAL, verts=8)

    # Wheels with alloy faces, tucked, under tight arch lips.
    for x_axle in (FRONT_AXLE, FRONT_AXLE + WHEELBASE):
        for side in (-1.0, 1.0):
            wx = cx(x_axle)
            wy = side * 0.775
            kit.cyl("Tire", WHEEL_R, 0.235, (wx, wy, WHEEL_R),
                    kit.TIRE, axis="Y", verts=28)
            kit.cyl("HubFace", 0.15, 0.245, (wx, wy, WHEEL_R),
                    kit.STEEL, axis="Y", verts=18)
            for spoke in range(5):
                ang = spoke * math.tau / 5.0
                kit.box("Spoke", (0.045, 0.25, 0.16),
                        (wx + 0.10 * math.cos(ang), wy,
                         WHEEL_R + 0.10 * math.sin(ang)),
                        kit.CHARCOAL, rot=(0.0, ang, 0.0),
                        chamfer=False)
            kit.arc_shell("ArchLip", (wx, side * 0.885, WHEEL_R),
                          WHEEL_R + 0.10, 0.06, kit.CHARCOAL,
                          start_deg=20.0, end_deg=160.0, segments=8,
                          thickness=0.045)


def export_car(style, colour):
    name = "SM_LB_DevCar_{}_{}_v002".format(style, colour)
    kit.reset(); kit.glass_material()
    loft_body(style, BODY_COLOURS[colour])
    dress_car(style, BODY_COLOURS[colour])
    kit.export(name, OUT_DIR + name)
    kit.preview(name, OUT_DIR + name, distance=6.6, height=1.55)


for style in ("Hatch", "Estate", "Cross"):
    for colour in BODY_COLOURS:
        export_car(style, colour)

print("DEVCAR COMPLETE")
