"""Create v307 clean Unreal studio successor to prove v037 import orientation and materials.

The v305/v306 maps are retained as failed empty-map API attempts.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressTrainA_IsolatedStudioCandidate_v307.umap"
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/ModularVisual_v302/SM_CA_MW_PressTrainA_ModularAssembly_v037"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_isolated_studio_build_v307.json"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v307")
if not levels.new_level(MAP):
    raise RuntimeError("new studio level failed")
mesh = lib.load_asset(ASSET)
if mesh is None:
    raise RuntimeError(ASSET)

candidate = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 809.05), unreal.Rotator())
candidate.static_mesh_component.set_static_mesh(mesh)
candidate.set_actor_label("CA_MW_PTA_ModularTrain_v037_STUDIO_VISUAL_ONLY_v307")
candidate.set_actor_scale3d(unreal.Vector(100.0, -100.0, 100.0))
candidate.tags = [
    unreal.Name("LB.PressTrain.TrainA.ModularSource.v037"),
    unreal.Name("LB.Review.IsolatedStudio.v307"),
    unreal.Name("LB.Collision.NoCollision"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]
component = candidate.static_mesh_component
component.set_collision_profile_name("NoCollision")
component.set_editor_property("can_ever_affect_navigation", False)

# Neutral floor for an unambiguous upright/fallen-over judgment.
cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
floor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(2788.0, 100.0, -12.5), unreal.Rotator())
floor.static_mesh_component.set_static_mesh(cube)
floor.set_actor_label("LB_V307_STUDIO_FLOOR")
floor.set_actor_scale3d(unreal.Vector(60.0, 22.0, 0.25))

sky = actors_api.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1500), unreal.Rotator())
sky.set_actor_label("LB_V307_STUDIO_SKYLIGHT")
sky.light_component.set_editor_property("intensity", 2.0)
sun = actors_api.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1500), unreal.Rotator(-45, -35, 0))
sun.set_actor_label("LB_V307_STUDIO_KEY")
sun.light_component.set_editor_property("intensity", 6.0)

def add_ortho(label, location, target, width):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "projection_mode": unreal.CameraProjectionMode.ORTHOGRAPHIC,
        "ortho_width": width,
        "aspect_ratio": 16/9,
        "constrain_aspect_ratio": True,
    })
    return camera

def add_perspective(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16/9, "constrain_aspect_ratio": True})
    return camera

centre = (2788.0, 100.0, 520.0)
add_ortho("LB_V307_CAM_Operator", (2788.0, -1800.0, 520.0), centre, 6200.0)
add_ortho("LB_V307_CAM_Rear", (2788.0, 2000.0, 520.0), centre, 6200.0)
add_perspective("LB_V307_CAM_Elevated", (6200.0, -2800.0, 1900.0), centre, 68.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
origin, extent = candidate.get_actor_bounds(False)
floor_z = origin.z - extent.z
failures = []
if abs(floor_z) > 1.0:
    failures.append(f"candidate floor z {floor_z}")
if not levels.save_current_level():
    failures.append("save failed")
payload = {
    "$schema": "cairnwell/audit/press-train-a-isolated-studio-v307/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_UE_IMPORT_ORIENTATION_GATE_READY__NOT_PROMOTED" if not failures else "FAIL__V305_NOT_EVIDENCE",
    "map": MAP,
    "map_sha256": hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper() if MAP_FILE.exists() else None,
    "asset": ASSET,
    "candidate_origin": [origin.x, origin.y, origin.z],
    "candidate_extent": [extent.x, extent.y, extent.z],
    "candidate_floor_z": floor_z,
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
