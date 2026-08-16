"""Non-overwriting identity correction from dedicated-end refined Train A v035."""
import bpy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v035/CA_MW_PressTrainA_ModularAssembly_v035.blend"
SRC_SHA = "75D189D76BD34C891288FB93CC5A2BC800E393FA8DE3C8C4FB3E53E1F21C378A"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037"
FBX = OUT / "FBX"
BLEND = OUT / "CA_MW_PressTrainA_ModularAssembly_v037.blend"
REPORT = OUT / "PRESS_TRAIN_A_IDENTITY_CORRECTION_v037.json"
for directory in (OUT, FBX): directory.mkdir(parents=True, exist_ok=True)
if BLEND.exists() or REPORT.exists() or any(FBX.glob("*.fbx")): raise RuntimeError("refusing to overwrite v037")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""): h.update(chunk)
    return h.hexdigest().upper()

if sha(SRC) != SRC_SHA: raise RuntimeError("v035 source hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
GREEN = next((m for m in bpy.data.materials if "identitygreen" in m.name.lower()), bpy.data.materials[0])

# Place the S01/S07 text just proud of its plate after the v035 integration move.
for station in ("S01", "S07"):
    for obj in bpy.data.objects:
        if obj.name.startswith(f"PTA_{station}_Identity") and obj.type == "FONT":
            obj.location.x = 3.118 if "Operator" in obj.name else -3.118

def station_collection(station): return bpy.data.collections.get(f"TrainA_{station}_v032")
def cover(station, y):
    bpy.ops.mesh.primitive_cube_add(location=(2.31, y, 5.86))
    obj = bpy.context.object
    obj.name = f"PTA_{station}_InheritedS03BadgeCover_Operator_v037"
    obj.dimensions = (0.055, 0.82, 0.27)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(GREEN)
    for collection in list(obj.users_collection): collection.objects.unlink(obj)
    station_collection(station).objects.link(obj)
    obj["station_id"] = station
    obj["engineering_status"] = "VISUAL_IDENTITY_CORRECTION_ONLY"
    obj["runtime_authority"] = "NONE_SOURCE_ONLY"
    obj["collision_intent"] = "NoCollision_SOURCE_ONLY"

for station, y in {"S02": 7.5, "S03": 15.0, "S04": 22.5, "S05": 30.0, "S06": 37.5}.items(): cover(station, y)

for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"} or obj.name.startswith("SM_CA_MW_PressTrainA_ModularAssembly_v035"):
        bpy.data.objects.remove(obj, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
geo = [obj for obj in bpy.data.objects if obj.type in {"MESH", "CURVE", "FONT"} and not obj.hide_render]
bpy.ops.object.select_all(action="DESELECT")
for obj in geo: obj.select_set(True)
bpy.context.view_layer.objects.active = next(obj for obj in geo if obj.type == "MESH")
bpy.ops.object.duplicate()
for obj in list(bpy.context.selected_objects):
    if obj.type in {"CURVE", "FONT"}:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
combined = bpy.context.object
combined.name = "SM_CA_MW_PressTrainA_ModularAssembly_v037"
fbx = FBX / f"{combined.name}.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH"})
combined.hide_render = True
payload = {"$schema":"cairnwell/source/press-train-a-identity-correction-v037/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"SOURCE_ONLY_IDENTITY_CORRECTED__FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED","source_parent":str(SRC.relative_to(ROOT)).replace("\\","/"),"source_parent_sha256":SRC_SHA,"corrections":["S01/S07 text offset from integrated plates","operator-side inherited repeated S03 badge covered on S02-S06"],"engineering_values":"TBC_NOT_INVENTED","runtime_authority_added":False,"promotion_authorized":False,"blend_sha256":sha(BLEND),"fbx_sha256":sha(fbx),"fbx_bytes":fbx.stat().st_size}
REPORT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
