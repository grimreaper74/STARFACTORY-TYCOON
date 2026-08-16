"""Prove the new D saddle orientation against the approved bare-coil authority."""
import bpy
import json
import math
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SADDLE = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/BareCoilOutputSaddle_v20260810/Cleaned/Cairnwell_BareCoilOutputSaddle_Controlled_v994.blend"
RIG = ROOT / "SourceAssets/PR004/PackagingRig_v004/LB_PR004_PackagingRig_Candidate_v004.blend"
OUT = ROOT / "SourceAssets/Candidate/PressShop/PR004_FilmDepack/BareCoilOutputSaddle_v20260810/Fit/Cairnwell_BareCoilSaddleFit_v995.blend"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/BareCoilOutputSaddle_v993/bare_coil_fit_v995.json"

bpy.ops.wm.read_factory_settings(use_empty=True)


def append_objects(path, names=None, prefix=""):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        target.objects = [name for name in source.objects if names is None or name in names]
    result = []
    for obj in target.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            obj.name = prefix + obj.name
            result.append(obj)
    return result


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


saddle = append_objects(SADDLE, prefix="SADDLE_")
coil = append_objects(RIG, {"SM_LB_PR004_BareCoilCore_v004"}, "FIT_")
if len(coil) != 1:
    raise RuntimeError(f"expected one approved bare coil, got {len(coil)}")

# Saddle V is visible in its X/Z front profile, therefore its supported coil
# axis is Y. The approved bare coil is authored with axis X; rotate it +90 Z.
for obj in coil:
    obj.matrix_world = Matrix.Translation((0.0, 0.0, 1.35)) @ Matrix.Rotation(math.radians(90.0), 4, "Z") @ obj.matrix_world

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))

rows = {}
for name, objects in (("saddle", saddle), ("bare_coil", coil)):
    low, high = bounds(objects)
    rows[name] = {
        "low_m": [round(value, 6) for value in low],
        "high_m": [round(value, 6) for value in high],
        "dimensions_m": [round(value, 6) for value in high - low],
    }

payload = {
    "status": "PASS__BLENDER_AXIS_AND_ENVELOPE_FIT__CONTACT_VISUAL_REVIEW_REQUIRED",
    "output": str(OUT),
    "coil_authority": str(RIG),
    "coil_axis_before": "X",
    "coil_axis_after": "Y",
    "coil_rotation_z_deg": 90.0,
    "coil_centre_z_m": 1.35,
    "components": rows,
    "reuse": ["PR004 bare-coil output", "player-placeable bare-coil storage"],
    "meshy_credits_used": 0,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_BARE_COIL_SADDLE_FIT_V995", rows)
