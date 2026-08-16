"""Non-overwriting Train A visual refinement from the retained axis-corrected v032 source."""
import bpy, hashlib, json, math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v032/CA_MW_PressTrainA_ModularAssembly_v032.blend"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033"
FBX = OUT / "FBX"
BLEND = OUT / "CA_MW_PressTrainA_ModularAssembly_v033.blend"
REPORT = OUT / "PRESS_TRAIN_A_VISUAL_REFINEMENT_v033.json"
for directory in (OUT, FBX):
    directory.mkdir(parents=True, exist_ok=True)
if BLEND.exists() or REPORT.exists() or any(FBX.glob("*.fbx")):
    raise RuntimeError("refusing to overwrite v033")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

bpy.ops.wm.open_mainfile(filepath=str(SRC))
scene = bpy.context.scene
for obj in list(bpy.data.objects):
    if obj.name.startswith("SM_CA_MW_PressTrainA_ModularAssembly_v032") or "IdentityPlate_v032" in obj.name or "IdentityText_v032" in obj.name:
        bpy.data.objects.remove(obj, do_unlink=True)

def material(name, colour, metallic=0.0, roughness=0.4):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat

GREEN = material("CA_MW_v033_IdentityGreen", (0.018, 0.16, 0.09), 0.25, 0.34)
WHITE = material("CA_MW_v033_IdentityWhite", (0.9, 0.94, 0.9), 0.0, 0.3)
YELLOW = material("CA_MW_v033_ProcessYellow", (0.95, 0.58, 0.015), 0.15, 0.32)
DATUMS = {"S01": 0.0, "S02": 7.5, "S03": 15.0, "S04": 22.5, "S05": 30.0, "S06": 37.5, "S07": 45.0}
PROCESS = {
    "S01": "DESTACK / BLANK FEED", "S02": "DEEP DRAW", "S03": "FORM / RESTRIKE",
    "S04": "TRIM / SCRAP", "S05": "PIERCE / SLUG", "S06": "FLANGE / HEM",
    "S07": "INSPECT / UNLOAD",
}

def link_to_station(obj, station):
    target = bpy.data.collections.get(f"TrainA_{station}_v032")
    if target:
        for collection in list(obj.users_collection):
            collection.objects.unlink(obj)
        target.objects.link(obj)
    obj["train_id"] = "A"
    obj["station_id"] = station
    obj["engineering_status"] = "VISUAL_IDENTITY_ONLY_TBC"
    obj["runtime_authority"] = "NONE_SOURCE_ONLY"

def add_plate(station, side):
    y = DATUMS[station]
    x = side * 4.42
    bpy.ops.mesh.primitive_cube_add(location=(x, y, 4.7), scale=(0.055, 1.28, 0.48))
    plate = bpy.context.object
    plate.name = f"PTA_{station}_IdentityPlate_{'Operator' if side > 0 else 'Service'}_v033"
    plate.data.materials.append(GREEN)
    link_to_station(plate, station)
    face_x = x + side * 0.061
    rot_z = math.pi / 2 if side > 0 else -math.pi / 2
    for body, z, size, mat, suffix in ((station, 4.84, 0.42, WHITE, "Code"), (PROCESS[station], 4.54, 0.19, YELLOW, "Process")):
        bpy.ops.object.text_add(location=(face_x, y, z), rotation=(math.pi / 2, 0, rot_z))
        text = bpy.context.object
        text.name = f"PTA_{station}_Identity{suffix}_{'Operator' if side > 0 else 'Service'}_v033"
        text.data.body = body
        text.data.align_x = "CENTER"
        text.data.align_y = "CENTER"
        text.data.size = size
        text.data.extrude = 0.008
        text.data.materials.append(mat)
        link_to_station(text, station)

for station in DATUMS:
    add_plate(station, 1)
    add_plate(station, -1)

# Add a restrained yellow tooling datum strip so the five processes read as variants at train scale.
for station in ("S02", "S03", "S04", "S05", "S06"):
    y = DATUMS[station]
    bpy.ops.mesh.primitive_cube_add(location=(3.32, y, 1.42), scale=(0.045, 1.08, 0.055))
    strip = bpy.context.object
    strip.name = f"PTA_{station}_ToolingDatumCue_Operator_v033"
    strip.data.materials.append(YELLOW)
    link_to_station(strip, station)

# Remove review-only objects before saving the source asset.
for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"}:
        bpy.data.objects.remove(obj, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)

geo = [obj for obj in bpy.data.objects if obj.type in {"MESH", "CURVE", "FONT"} and not obj.hide_render]
bpy.ops.object.select_all(action="DESELECT")
for obj in geo:
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(obj for obj in geo if obj.type == "MESH")
bpy.ops.object.duplicate()
for obj in list(bpy.context.selected_objects):
    if obj.type in {"CURVE", "FONT"}:
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
bpy.ops.object.join()
combined = bpy.context.object
combined.name = "SM_CA_MW_PressTrainA_ModularAssembly_v033"
fbx = FBX / f"{combined.name}.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z",
    use_mesh_modifiers=True, mesh_smooth_type="FACE", add_leaf_bones=False,
    use_custom_props=True, object_types={"MESH"})
combined.hide_render = True

payload = {
    "$schema": "cairnwell/source/press-train-a-visual-refinement-v033/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_AXIS_CORRECTED_WITH_STATION_SPECIFIC_DUAL_SIDE_IDENTITY__FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_parent_sha256": sha(SRC),
    "station_identity": PROCESS,
    "identity_faces": ["operator", "service"],
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "promotion_authorized": False,
    "blend_sha256": sha(BLEND),
    "fbx_sha256": sha(fbx),
    "fbx_bytes": fbx.stat().st_size,
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
