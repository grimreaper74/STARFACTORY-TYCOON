"""Bake Train A to Unreal axes while preserving readable station text on both faces."""
import bpy
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend"
SRC_SHA = "D4C7D36DB98CF728317FBBC05E8AE49EEA945ED9026F624739D95584D3DFCDF8"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/UnrealAxisReadableLabels_v040"
FBX_DIR = OUT / "FBX"
BLEND = OUT / "CA_MW_PressTrainA_UnrealAxisReadableLabels_v040.blend"
FBX = FBX_DIR / "SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040.fbx"
REPORT = OUT / "PRESS_TRAIN_A_UNREAL_AXIS_READABLE_LABELS_v040.json"

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

for directory in (OUT, FBX_DIR):
    directory.mkdir(parents=True, exist_ok=True)
if BLEND.exists() or FBX.exists() or REPORT.exists():
    raise RuntimeError("Refusing to overwrite v040")
if sha(SRC) != SRC_SHA:
    raise RuntimeError("v037 source hash drift")

bpy.ops.wm.open_mainfile(filepath=str(SRC))
for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(obj, do_unlink=True)

geo = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render and not o.name.startswith("SM_CA_MW_PressTrainA_ModularAssembly")]
label_names = []
for obj in geo:
    if obj.type == "FONT":
        # Text runs along local X, which maps to the train's longitudinal Y axis.
        # Pre-reflect local X so the later whole-train Y reflection does not mirror glyphs.
        obj.scale.x *= -1.0
        label_names.append(obj.name)

bpy.ops.object.select_all(action="DESELECT")
for obj in geo:
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(o for o in geo if o.type == "MESH")
bpy.ops.object.duplicate()
for obj in list(bpy.context.selected_objects):
    if obj.type in {"CURVE", "FONT"}:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
combined = bpy.context.object
combined.name = "SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040"
combined.scale.y = -1.0
combined.rotation_euler.x = -math.pi / 2
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
bpy.ops.object.select_all(action="DESELECT")
combined.select_set(True)
bpy.context.view_layer.objects.active = combined
bpy.ops.export_scene.fbx(
    filepath=str(FBX), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
    use_custom_props=True, object_types={"MESH"},
)
dims = combined.dimensions
payload = {
    "$schema": "cairnwell/source/press-train-a-unreal-axis-readable-labels-v040/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_AXIS_BAKED_LABEL_HANDEDNESS_CORRECTED__ISOLATED_REIMPORT_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_parent_sha256": SRC_SHA,
    "baked_transform": {"rotation_x_degrees": -90, "scale_y_reflection": -1},
    "label_pre_correction": {"local_x_reflection": -1, "count": len(label_names), "objects": label_names},
    "combined_dimensions_m": [dims.x, dims.y, dims.z],
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "promotion_authorized": False,
    "blend_sha256": sha(BLEND),
    "fbx_sha256": sha(FBX),
    "fbx_bytes": FBX.stat().st_size,
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
