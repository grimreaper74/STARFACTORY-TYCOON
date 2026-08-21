"""Dev car v004: parametric family fitted from the owner's concept.

Samples the concept GLB's real cross-sections (40 stations x 7 height
bands of measured half-widths) into a dense loft table, so the script
car carries his design's silhouette - then breeds the Estate (held
roof) and Cross (lifted, clad) from the same fit. The exact mesh
(v003) stays the hero; this family shares its DNA and stays editable.
"""
import math
import sys

sys.path.append(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Tools")
import bmesh  # noqa: E402
import bpy  # noqa: E402
import lb_model_kit as kit  # noqa: E402

SRC = ("C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/"
       "SourceAssets/Candidate/DevCar_v003/cairnwell_concept_base.glb")
OUT_DIR = "DevCar_v004/"
TARGET_LEN = 4.36
N_STATIONS = 40
N_BANDS = 7

COLOURS = {
    "EmeraldGreen": kit.GREEN,
    "AlpineWhite": ("MAT_AlpineWhite", (0.85, 0.86, 0.84, 1.0)),
    "GraphiteGrey": ("MAT_GraphiteGrey", (0.16, 0.17, 0.18, 1.0)),
}


def load_concept_verts():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    verts = []
    for ob in meshes:
        mat = ob.matrix_world
        for v in ob.data.vertices:
            verts.append(mat @ v.co)
    xs = [v.x for v in verts]
    ys = [v.y for v in verts]
    if (max(ys) - min(ys)) > (max(xs) - min(xs)):
        for v in verts:
            v.x, v.y = v.y, v.x
        xs = [v.x for v in verts]
    x0, x1 = min(xs), max(xs)
    scale = TARGET_LEN / (x1 - x0)
    zs = [v.z for v in verts]
    z0 = min(zs)
    ymid = (max(v.y for v in verts) + min(v.y for v in verts)) / 2.0
    out = [((v.x - x0) * scale, (v.y - ymid) * scale, (v.z - z0) * scale)
           for v in verts]
    return out


def fit_table(verts):
    """Per station: top z and half-width at each of N_BANDS z levels."""
    table = []
    for i in range(N_STATIONS):
        xa = TARGET_LEN * i / N_STATIONS
        xb = TARGET_LEN * (i + 1) / N_STATIONS
        slab = [v for v in verts if xa <= v[0] <= xb]
        if len(slab) < 8:
            table.append(None)
            continue
        top = max(v[2] for v in slab)
        sill = max(0.14, min(v[2] for v in slab) + 0.02)
        # Exclude wheel/mirror geometry: wheels live near the axles
        # below ~0.55 m; mirrors are tiny outliers - use the 92nd
        # percentile of band widths instead of the maximum.
        ax_f = TARGET_LEN * 0.20
        ax_r = TARGET_LEN * 0.82
        def is_wheel(v):
            return (v[2] < 0.55 and (abs(v[0] - ax_f) < 0.55
                                     or abs(v[0] - ax_r) < 0.55)
                    and abs(v[1]) > 0.62)
        body = [v for v in slab if not is_wheel(v)]
        if len(body) < 8:
            body = slab
        bands = []
        for b in range(N_BANDS):
            z_lo = sill + (top - sill) * b / N_BANDS
            z_hi = sill + (top - sill) * (b + 1) / N_BANDS
            in_band = sorted(abs(v[1]) for v in body
                             if z_lo <= v[2] <= z_hi)
            if in_band:
                width = in_band[min(len(in_band) - 1,
                                    int(len(in_band) * 0.92))]
            else:
                width = bands[-1] if bands else 0.5
            bands.append(width)
        table.append(((xa + xb) / 2.0, sill, top, bands))
    return [row for row in table if row]


def style_rows(rows, style):
    out = []
    hold_top = None
    for x, sill, top, bands in rows:
        s, t = sill, top
        bb = list(bands)
        if style == "Estate" and x > TARGET_LEN * 0.70:
            if hold_top is None:
                hold_top = top
            blend = (x - TARGET_LEN * 0.70) / (TARGET_LEN * 0.30)
            t = max(top, hold_top - 0.30 * blend ** 2.0)
        elif style == "Cross":
            s += 0.055
            t += 0.055
        out.append((x, s, t, bb))
    return out


def build_fitted(rows, style, colour_name):
    body_mat = COLOURS[colour_name]
    mesh = bpy.data.meshes.new("FitLoft")
    obj = bpy.data.objects.new("FitLoft", mesh)
    bpy.context.collection.objects.link(obj)
    body = kit.material(*body_mat)
    glass = kit.material(*kit.GLASS)
    obj.data.materials.append(body)
    obj.data.materials.append(glass)

    bm = bmesh.new()
    rings = []
    for x, sill, top, bands in rows:
        x0 = x - TARGET_LEN / 2.0
        ring = []
        for b in range(N_BANDS):
            z = sill + (top - sill) * (b + 0.5) / N_BANDS
            ring.append(bm.verts.new((x0, -bands[b], z)))
        ring.append(bm.verts.new((x0, 0.0, top)))
        for b in reversed(range(N_BANDS)):
            z = sill + (top - sill) * (b + 0.5) / N_BANDS
            ring.append(bm.verts.new((x0, bands[b], z)))
        rings.append((x, top, ring))

    n = len(rings[0][2])
    max_top = max(r[1] for r in rings)
    for (xa, ta, ra), (xb, tb, rb) in zip(rings, rings[1:]):
        x_mid = (xa + xb) / 2.0
        t_mid = (ta + tb) / 2.0
        for k in range(n - 1):
            try:
                face = bm.faces.new((ra[k], ra[k + 1], rb[k + 1], rb[k]))
            except ValueError:
                continue
            hi_band = k >= N_BANDS - 2 and k <= n - N_BANDS + 1
            cabin = 0.28 * TARGET_LEN < x_mid < 0.95 * TARGET_LEN
            face.material_index = 1 if (hi_band and cabin
                                        and t_mid > max_top * 0.82) else 0
    for ring, flip in ((rings[0][2], True), (rings[-1][2], False)):
        try:
            face = bm.faces.new(tuple(reversed(ring)) if flip else
                                tuple(ring))
            face.material_index = 0
        except ValueError:
            pass
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    if hasattr(mesh, "set_sharp_from_angle"):
        mesh.set_sharp_from_angle(angle=math.radians(48.0))
    return obj


def dress(style, colour_name):
    body = COLOURS[colour_name]
    lift = 0.055 if style == "Cross" else 0.0

    def cx(x):
        return x - TARGET_LEN / 2.0

    kit.box("FrontLightBar", (0.05, 1.30, 0.05),
            (cx(0.03), 0.0, 0.55 + lift), kit.WARMWHITE, chamfer=False)
    kit.box("RearLightBar", (0.05, 1.10, 0.05),
            (cx(TARGET_LEN - 0.10), 0.0, 0.98 + lift), kit.RED,
            chamfer=False)
    kit.box("FrontApron", (0.10, 1.05, 0.14),
            (cx(0.07), 0.0, 0.24 + lift), kit.CHARCOAL)
    kit.box("RearApron", (0.10, 1.05, 0.13),
            (cx(TARGET_LEN - 0.07), 0.0, 0.23 + lift), kit.CHARCOAL)
    for x_axle in (0.20 * TARGET_LEN, 0.82 * TARGET_LEN):
        for side in (-1.0, 1.0):
            wx = cx(x_axle)
            wy = side * 0.78
            r = 0.36
            kit.cyl("Tire", r, 0.24, (wx, wy, r + lift), kit.TIRE,
                    axis="Y", verts=28)
            kit.cyl("Alloy", 0.24, 0.25, (wx, wy, r + lift),
                    kit.STEEL, axis="Y", verts=22)
            kit.cyl("Hub", 0.06, 0.255, (wx, wy, r + lift),
                    kit.CHARCOAL, axis="Y", verts=10)


CONCEPT = load_concept_verts()
ROWS = fit_table(CONCEPT)
print("FIT rows:", len(ROWS))

for style in ("Hatch", "Estate", "Cross"):
    rows = style_rows(ROWS, style)
    for colour in COLOURS:
        name = "SM_LB_DevCar_{}_{}_v004".format(style, colour)
        kit.reset(); kit.glass_material()
        build_fitted(rows, style, colour)
        dress(style, colour)
        kit.export(name, OUT_DIR + name)
        kit.preview(name, OUT_DIR + name, distance=6.6, height=1.6)

print("V004 COMPLETE")
