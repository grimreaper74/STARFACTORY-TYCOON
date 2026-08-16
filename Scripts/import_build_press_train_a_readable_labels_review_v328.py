"""Import v040 into a fresh isolated Unreal map with matched broadside cameras."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/UnrealAxisReadableLabels_v040/FBX/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040.fbx"
SOURCE_SHA = "9E2E5F205567F3083F1BDAB9ACF779957CE02A63CFB383F55F88F9B510D1FF4F"
DEST = "/Game/LineBoss/Candidates/PressTrains/TrainA/ReadableLabels_v328"
ASSET = DEST + "/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040"
MAP = "/Game/LineBoss/Maps/LB_PressTrainA_ReadableLabelsReviewCandidate_v328"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_ReadableLabelsReviewCandidate_v328.umap"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_readable_labels_unreal_intake_v328.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

if sha(SOURCE) != SOURCE_SHA:
    raise RuntimeError("v040 FBX hash drift")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v328")

task = unreal.AssetImportTask()
task.set_editor_properties({"filename": str(SOURCE), "destination_path": DEST, "destination_name": "SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040", "automated": True, "replace_existing": False, "save": True})
opts = unreal.FbxImportUI()
opts.set_editor_properties({"import_mesh": True, "import_as_skeletal": False, "import_materials": True, "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH})
data = opts.get_editor_property("static_mesh_import_data")
data.set_editor_properties({"combine_meshes": True, "convert_scene": True, "convert_scene_unit": True, "transform_vertex_to_absolute": False, "bake_pivot_in_vertex": False, "generate_lightmap_u_vs": True, "auto_generate_collision": False, "remove_degenerates": True})
task.set_editor_property("options", opts)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh = lib.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("v328 mesh import missing")
if not levels.new_level(MAP):
    raise RuntimeError("Could not create v328 review map")

candidate = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
candidate.static_mesh_component.set_static_mesh(mesh)
candidate.set_actor_label("CA_MW_PTA_ReadableLabels_v040_STUDIO_VISUAL_ONLY_v328")
candidate.set_actor_scale3d(unreal.Vector(100, 100, 100))
candidate.tags = [unreal.Name(x) for x in ("LB.PressTrain.TrainA.ReadableLabelsSource.v040", "LB.Review.IsolatedStudio.v328", "LB.Collision.NoCollision", "LB.Asset.CandidateNotPromoted")]
candidate.static_mesh_component.set_collision_profile_name("NoCollision")
candidate.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
origin, extent = candidate.get_actor_bounds(False)
candidate.add_actor_world_offset(unreal.Vector(0, 0, -(origin.z - extent.z)), False, False)
origin, extent = candidate.get_actor_bounds(False)

cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(origin.x, origin.y, -12.5), unreal.Rotator())
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_label("LB_V328_STUDIO_FLOOR")
floor.set_actor_scale3d(unreal.Vector(max(18, extent.x / 50 + 4), max(62, extent.y / 50 + 8), 0.25))

for index, y in enumerate((origin.y - 2300, origin.y - 1500, origin.y - 750, origin.y, origin.y + 750, origin.y + 1500, origin.y + 2300), 1):
    for face, x in (("A", origin.x - 900), ("B", origin.x + 900)):
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, origin.z + 500), unreal.Rotator())
        light.set_actor_label(f"LB_V328_LIGHT_{face}_{index:02d}")
        light.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.point_light_component.set_editor_properties({"intensity": 70000.0, "attenuation_radius": 2200.0, "cast_shadows": False})

def camera(label, x):
    cam = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(x, origin.y, origin.z), unreal.Rotator())
    cam.set_actor_label(label)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(), unreal.Vector(origin.x, origin.y, origin.z)), False)
    cam.camera_component.set_editor_properties({"projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC, "ortho_width": extent.y * 2.15, "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True})
    pp = cam.camera_component.get_editor_property("post_process_settings")
    pp.set_editor_properties({"override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC, "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True, "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0, "override_auto_exposure_bias": True, "auto_exposure_bias": 3.5})
    cam.camera_component.set_editor_property("post_process_settings", pp)
    cam.camera_component.set_editor_property("post_process_blend_weight", 1.0)

camera("LB_V328_CAM_BROADSIDE_A", origin.x - 2200)
camera("LB_V328_CAM_BROADSIDE_B", origin.x + 2200)

failures = []
size = [extent.x * 2, extent.y * 2, extent.z * 2]
if abs(origin.z - extent.z) > 1:
    failures.append("floor placement")
if min(size) <= 0:
    failures.append("invalid bounds")
if not levels.save_current_level():
    failures.append("save failed")
payload = {
    "$schema": "cairnwell/audit/press-train-a-readable-labels-unreal-intake-v328/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MECHANICALLY_UPRIGHT_READABLE_LABELS_VISUAL_GATE_READY__NOT_PROMOTED" if not failures else "FAIL__V328_NOT_EVIDENCE",
    "source_fbx_sha256": SOURCE_SHA,
    "asset": ASSET,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "candidate_scale": [100, 100, 100],
    "candidate_rotation": [0, 0, 0],
    "candidate_origin": [origin.x, origin.y, origin.z],
    "candidate_size_cm": size,
    "candidate_floor_z": origin.z - extent.z,
    "collision": "NoCollision",
    "runtime_authority": None,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
