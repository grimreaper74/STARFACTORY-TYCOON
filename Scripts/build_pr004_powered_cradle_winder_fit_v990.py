import bpy
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
A = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/PoweredWrappedCoilCradle_v20260810/Cleaned/Cairnwell_PoweredWrappedCoilCradle_Controlled_v989.blend"
B = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/FilmWindingModule_v20260810/Cleaned/Cairnwell_FilmWindingModule_Controlled_v989.blend"
COIL = ROOT / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/WrappedCoil_v20260809_v003/Cairnwell_WrappedCoil_Repaired_v003.blend"
OUT = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CradleWinderFit_v990.blend"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/pr004_cradle_winder_fit_v990.json"

bpy.ops.wm.read_factory_settings(use_empty=True)

def append_meshes(path, prefix):
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        target.objects = list(source.objects)
    for obj in target.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
    # Freshly appended objects have not entered the evaluated dependency graph
    # yet. Updating here preserves every authored object transform when the
    # assembly transform is composed below.
    bpy.context.view_layer.update()
    added = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    for obj in added:
        obj.name = prefix + obj.name
    return added

cradle = append_meshes(A, "CRADLE_")
winder = append_meshes(B, "WINDER_")
coil = append_meshes(COIL, "FIT_COIL_")

# The cradle rollers run on X. Rotate the approved coil so its 1.50 m width/axis
# also runs on X. The winder is placed on the right with its spindle facing -X.
for obj in winder:
    obj.matrix_world = (
        Matrix.Translation((2.10, 0.0, 0.0))
        @ Matrix.Rotation(math.radians(-90.0), 4, "Z")
        @ obj.matrix_world
    )
for obj in coil:
    # The repaired coil is floor-seated (Z 0..1.789497 m). Lift its centre to
    # 1.275 m so its cylindrical surface rests on the two powered rollers.
    obj.matrix_world = (
        Matrix.Translation((0.0, 0.0, 0.3802515))
        @ Matrix.Rotation(math.radians(90.0), 4, "Z")
        @ obj.matrix_world
    )

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high

rows = {}
for name, objects in (("cradle", cradle), ("winder", winder), ("coil", coil)):
    low, high = bounds(objects)
    rows[name] = {
        "low_m": [round(value, 6) for value in low],
        "high_m": [round(value, 6) for value in high],
        "dimensions_m": [round(value, 6) for value in high - low],
    }

payload = {
    "status": "BLENDER_GEOMETRY_FIT_CANDIDATE__VISUAL_REVIEW_REQUIRED__NOT_UNREAL_PROMOTED",
    "output": str(OUT),
    "layout": "cradle centre; wrapped coil axis X; winder centre X=2.10m; winder spindle faces -X",
    "components": rows,
    "nominal_coil_width_m": 1.5,
    "cradle_roller_length_m": 1.598,
    "nominal_end_clearance_each_m": 0.049,
    "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_PR004_CRADLE_WINDER_FIT_V990", len(cradle), len(winder), len(coil))
