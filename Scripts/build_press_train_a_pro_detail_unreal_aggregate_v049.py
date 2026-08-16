"""Bake retained modular v046 into one unambiguous visual-only Unreal aggregate."""
import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/CA_MW_PressTrainA_ProDetailModular_v046.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailUnrealAggregate_v049"
BLEND = OUT / "CA_MW_PressTrainA_ProDetailUnrealAggregate_v049.blend"
FBX = OUT / "FBX/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049.fbx"
REPORT = OUT / "PRESS_TRAIN_A_PRO_DETAIL_UNREAL_AGGREGATE_v049.json"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

for path in (BLEND, FBX, REPORT):
    if path.exists(): raise RuntimeError(f"Refusing to overwrite {path}")
OUT.mkdir(parents=True, exist_ok=True); FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
renderables = [o for o in bpy.context.scene.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render]
source_count = len(renderables)
if source_count != 474: raise RuntimeError(f"Unexpected v046 renderable count {source_count}")

# Convert each evaluated object to a mesh and bake its world transform. The modular
# master remains untouched on disk; this child exists only for inherited-hall review.
for obj in renderables:
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if obj.type != "MESH": bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    obj.select_set(False)
bpy.ops.object.select_all(action="DESELECT")
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.hide_render]
for obj in meshes: obj.select_set(True)
bpy.context.view_layer.objects.active = meshes[0]
bpy.ops.object.join()
aggregate = bpy.context.object
aggregate.name = "SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049"
aggregate["LB_VisualSource"] = "ProDetailModular_v046"
aggregate["LB_CollisionRole"] = "NO_COLLISION"
aggregate["LB_NavigationRole"] = "NONE"
aggregate["LB_RuntimeAuthority"] = "NONE"
aggregate["LB_EngineeringValues"] = "TBC_NOT_INVENTED"

minimum = Vector((float("inf"),) * 3); maximum = Vector((float("-inf"),) * 3)
for corner in aggregate.bound_box:
    p = aggregate.matrix_world @ Vector(corner)
    for axis in range(3):
        minimum[axis] = min(minimum[axis], p[axis]); maximum[axis] = max(maximum[axis], p[axis])
size = maximum - minimum
if not (57.5 <= size.y <= 57.8 and size.x <= 15.0):
    raise RuntimeError(f"Aggregate source bounds invalid: {list(size)}")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
bpy.ops.object.select_all(action="DESELECT"); aggregate.select_set(True); bpy.context.view_layer.objects.active = aggregate
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True,
    object_types={"MESH", "OTHER"})
payload = {"$schema": "cairnwell/source/press-train-a-pro-detail-unreal-aggregate-v049/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "VISUAL_ONLY_SINGLE_MESH_UNREAL_AGGREGATE__ISOLATED_REVIEW_ONLY__NOT_PROMOTED",
    "modular_source": str(SRC.relative_to(ROOT)).replace("\\", "/"), "modular_source_sha256": sha(SRC),
    "source_renderable_count": source_count, "aggregate_object_count": 1,
    "bounds_min_m": list(minimum), "bounds_max_m": list(maximum), "bounds_size_m": list(size),
    "protected_width_limit_m": 15.0, "protected_width_pass": bool(size.x <= 15.0),
    "collision": "NoCollision", "navigation": "None", "runtime_authority": "None",
    "engineering_values": "TBC_NOT_INVENTED", "replacement_authorized": False,
    "promotion_authorized": False, "blend_sha256": sha(BLEND), "fbx_sha256": sha(FBX),
    "fbx_bytes": FBX.stat().st_size}
REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
