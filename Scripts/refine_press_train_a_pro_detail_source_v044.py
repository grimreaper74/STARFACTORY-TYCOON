"""Correct v042 end-cell orientation and service-side presentation without overwrite."""
import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v042/CA_MW_PressTrainA_ProDetailModular_v042.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v044"
BLEND = OUT / "CA_MW_PressTrainA_ProDetailModular_v044.blend"
FBX = OUT / "FBX/SM_CA_MW_PressTrainA_ProDetailModular_v044.fbx"
REPORT = OUT / "PRESS_TRAIN_A_PRO_DETAIL_MODULAR_REFINEMENT_v044.json"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

for p in (BLEND, FBX, REPORT):
    if p.exists():
        raise RuntimeError(f"Refusing to overwrite {p}")
OUT.mkdir(parents=True, exist_ok=True)
FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SRC))
collection = bpy.data.collections.get("PTA_ProDetail_v042") or bpy.context.scene.collection
GREEN = bpy.data.materials["CAI_MainStructureGreen_v042"]
DARK = bpy.data.materials["CAI_ServiceCharcoal_v042"]

removed = []
for name in (
    "SM_CA_MW_PTA_S01_FramePost_L_v042", "SM_CA_MW_PTA_S01_FramePost_R_v042",
    "SM_CA_MW_PTA_S01_FrameCrosshead_v042",
    "SM_CA_MW_PTA_S07_InspectGantryPost_L_v042", "SM_CA_MW_PTA_S07_InspectGantryPost_R_v042",
    "SM_CA_MW_PTA_S07_InspectGantryTop_v042",
):
    obj = bpy.data.objects.get(name)
    if obj:
        removed.append(name)
        bpy.data.objects.remove(obj, do_unlink=True)

def box(name, loc, dims, mat, bevel=0.04):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj["LB_MobilityRole"] = "STATIC"
    obj["LB_CollisionRole"] = "SIMPLE"
    obj["LB_PivotAuthority"] = "OBJECT_ORIGIN_TBC"
    obj["LB_EngineeringValues"] = "TBC_NOT_INVENTED"
    if bevel:
        mod = obj.modifiers.new("FabricatedEdge", "BEVEL")
        mod.width, mod.segments = bevel, 2
    return obj

added = []
# End-cell frames now express the longitudinal station width in full-line elevation.
for stage, centre_y, span, z_top in (("S01", 0.0, 5.4, 5.0), ("S07", 45.0, 6.2, 5.25)):
    for side, y in (("IN", centre_y-span/2), ("OUT", centre_y+span/2)):
        for depth, x in (("OP", 2.8), ("SV", -2.8)):
            added.append(box(f"SM_CA_MW_PTA_{stage}_FramePost_{side}_{depth}_v044", (x, y, z_top/2),
                             (0.34, 0.34, z_top), GREEN if stage == "S01" else DARK))
    added.append(box(f"SM_CA_MW_PTA_{stage}_FrameCrosshead_OP_v044", (2.8, centre_y, z_top),
                     (0.38, span+0.34, 0.48), GREEN if stage == "S01" else DARK))
    added.append(box(f"SM_CA_MW_PTA_{stage}_FrameCrosshead_SV_v044", (-2.8, centre_y, z_top),
                     (0.38, span+0.34, 0.48), GREEN if stage == "S01" else DARK))
    added.append(box(f"SM_CA_MW_PTA_{stage}_FrameTopTie_v044", (0, centre_y, z_top),
                     (5.9, 0.30, 0.30), DARK))

# Put scrap/slug collection on the service side (-X), behind the press in operator views.
moved = []
service_tokens = (
    "S04_ScrapChute_", "S04_TransitionHopper", "S04_ScrapConveyorHousing",
    "S04_ConveyorDrive", "S04_RemovableScrapBin", "S04_BinDockPost_",
    "S05_SlugChute_", "S05_SlugHopper", "S05_RemovableSlugBin", "S05_LevelSensor",
)
for obj in bpy.data.objects:
    if any(token in obj.name for token in service_tokens) and obj.location.x > 0:
        obj.location.x *= -1
        obj.rotation_euler.y *= -1
        moved.append(obj.name)

renderables = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render]
minimum = Vector((float("inf"),) * 3); maximum = Vector((float("-inf"),) * 3)
for obj in renderables:
    for corner in obj.bound_box:
        p = obj.matrix_world @ Vector(corner)
        for i in range(3): minimum[i], maximum[i] = min(minimum[i], p[i]), max(maximum[i], p[i])
size = maximum - minimum
if size.x > 15.0:
    raise RuntimeError(f"Protected width exceeded: {size.x:.3f} m")
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
bpy.ops.object.select_all(action="DESELECT")
for obj in renderables: obj.select_set(True)
bpy.context.view_layer.objects.active = next(o for o in renderables if o.type == "MESH")
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH", "OTHER"})
payload = {"$schema": "cairnwell/source/press-train-a-pro-detail-modular-refinement-v044/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_END_CELL_AND_SERVICE_SIDE_REFINEMENT__FRESH_REVIEW_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"), "source_parent_sha256": sha(SRC),
    "removed_superseded_parts": removed, "added_part_count": len(added), "service_parts_moved": moved,
    "bounds_size_m": list(size), "protected_width_limit_m": 15.0,
    "engineering_values": "TBC_NOT_INVENTED", "runtime_authority_added": False,
    "promotion_authorized": False, "blend_sha256": sha(BLEND), "fbx_sha256": sha(FBX),
    "fbx_bytes": FBX.stat().st_size}
REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
