"""Non-overwriting dedicated S01/S07 presentation refinement from Train A v033."""
import bpy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v033/CA_MW_PressTrainA_ModularAssembly_v033.blend"
SRC_SHA = "8D7A9F589E8237D510F9A5B271A7108DCCCC775919B8E1969707B296C98B0CF6"
OUT = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v035"
FBX = OUT / "FBX"
BLEND = OUT / "CA_MW_PressTrainA_ModularAssembly_v035.blend"
REPORT = OUT / "PRESS_TRAIN_A_DEDICATED_END_REFINEMENT_v035.json"
for directory in (OUT, FBX):
    directory.mkdir(parents=True, exist_ok=True)
if BLEND.exists() or REPORT.exists() or any(FBX.glob("*.fbx")):
    raise RuntimeError("refusing to overwrite v035")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

if sha(SRC) != SRC_SHA:
    raise RuntimeError("v033 source hash drift")
bpy.ops.wm.open_mainfile(filepath=str(SRC))

def find_material(token):
    return next((mat for mat in bpy.data.materials if token.lower() in mat.name.lower()), bpy.data.materials[0])

GREEN = find_material("green")
YELLOW = find_material("yellow")
DARK = find_material("dark")
WHITE = find_material("white")

def station_collection(station):
    return bpy.data.collections.get(f"TrainA_{station}_v032")

def annotate(obj, station, role):
    target = station_collection(station)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    target.objects.link(obj)
    obj["train_id"] = "A"
    obj["station_id"] = station
    obj["assembly_role"] = role
    obj["engineering_status"] = "VISUAL_TBC"
    obj["runtime_authority"] = "NONE_SOURCE_ONLY"
    obj["collision_intent"] = "NoCollision_SOURCE_ONLY"

def box(name, location, dimensions, material, station, role):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    annotate(obj, station, role)
    return obj

def cylinder(name, location, radius, depth, material, station, role, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    annotate(obj, station, role)
    return obj

# Bring the dedicated-cell identity onto the equipment instead of leaving it at press-body height.
for station in ("S01", "S07"):
    for obj in bpy.data.objects:
        if obj.name.startswith(f"PTA_{station}_Identity") and obj.name.endswith("_v033"):
            obj.location.z -= 1.15
            obj.location.x = 3.05 if "Operator" in obj.name else -3.05

# S01: open destack lift tower, separator head and feed-centering cues.
for y in (-1.82, 1.82):
    box(f"PTA_S01_DestackTowerPost_{y:+.2f}_v035", (0.1, y, 2.25), (0.28, 0.28, 4.5), DARK, "S01", "DedicatedDestackLiftTower")
box("PTA_S01_DestackTowerHeader_v035", (0.1, 0, 4.45), (0.34, 3.92, 0.30), DARK, "S01", "DedicatedDestackLiftTower")
box("PTA_S01_SeparatorCarriage_v035", (0.35, 0, 3.62), (0.38, 2.65, 0.22), YELLOW, "S01", "DedicatedSeparatorCarriage")
for y in (-1.08, -0.36, 0.36, 1.08):
    cylinder(f"PTA_S01_VacuumDrop_{y:+.2f}_v035", (0.58, y, 3.10), 0.065, 0.92, DARK, "S01", "DedicatedVacuumHead")
    cylinder(f"PTA_S01_VacuumCup_{y:+.2f}_v035", (0.58, y, 2.62), 0.16, 0.09, DARK, "S01", "DedicatedVacuumHead")
box("PTA_S01_FeedCentres_v035", (1.05, 0, 1.24), (0.16, 2.8, 0.12), YELLOW, "S01", "DedicatedFeedCentering")

# S07: open inspection/light portal with visible sensor bar and classification interface.
for y in (43.15, 46.85):
    box(f"PTA_S07_InspectionPost_{y:.2f}_v035", (0.0, y, 2.20), (0.30, 0.30, 4.4), DARK, "S07", "DedicatedInspectionPortal")
box("PTA_S07_InspectionHeader_v035", (0.0, 45.0, 4.30), (0.34, 4.0, 0.30), DARK, "S07", "DedicatedInspectionPortal")
box("PTA_S07_LightBarOperator_v035", (0.22, 45.0, 3.65), (0.10, 3.25, 0.12), WHITE, "S07", "DedicatedInspectionLighting")
box("PTA_S07_CameraBeam_v035", (0.42, 45.0, 3.20), (0.12, 2.65, 0.14), YELLOW, "S07", "DedicatedInspectionSensors")
for y in (44.1, 45.0, 45.9):
    box(f"PTA_S07_InspectionCamera_{y:.2f}_v035", (0.58, y, 3.05), (0.22, 0.24, 0.18), DARK, "S07", "DedicatedInspectionSensors")
    cylinder(f"PTA_S07_InspectionLens_{y:.2f}_v035", (0.71, y, 3.05), 0.065, 0.08, WHITE, "S07", "DedicatedInspectionSensors", rotation=(0, 1.5707963268, 0))
box("PTA_S07_ClassificationHMI_v035", (2.2, 46.45, 1.58), (0.55, 0.42, 1.35), GREEN, "S07", "DedicatedClassificationHMI")
box("PTA_S07_ClassificationScreen_v035", (2.49, 46.45, 1.76), (0.035, 0.28, 0.40), WHITE, "S07", "DedicatedClassificationHMI")

for obj in list(bpy.data.objects):
    if obj.type in {"LIGHT", "CAMERA"} or obj.name.startswith("SM_CA_MW_PressTrainA_ModularAssembly_v033"):
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
combined.name = "SM_CA_MW_PressTrainA_ModularAssembly_v035"
fbx = FBX / f"{combined.name}.fbx"
bpy.ops.export_scene.fbx(filepath=str(fbx), use_selection=True, apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_ALL", axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
    mesh_smooth_type="FACE", add_leaf_bones=False, use_custom_props=True, object_types={"MESH"})
combined.hide_render = True

payload = {
    "$schema": "cairnwell/source/press-train-a-dedicated-end-refinement-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_ONLY_DEDICATED_S01_S07_PRESENTATION_REFINED__FRESH_VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
    "source_parent": str(SRC.relative_to(ROOT)).replace("\\", "/"),
    "source_parent_sha256": SRC_SHA,
    "refinements": {"S01": ["open lift tower", "separator carriage", "vacuum drops and cups", "feed-centering cue"], "S07": ["open inspection portal", "inspection lighting", "camera array", "classification HMI"]},
    "engineering_values": "TBC_NOT_INVENTED",
    "runtime_authority_added": False,
    "promotion_authorized": False,
    "blend_sha256": sha(BLEND),
    "fbx_sha256": sha(fbx),
    "fbx_bytes": fbx.stat().st_size
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
