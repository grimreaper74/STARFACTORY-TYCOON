"""Build matched whole-shop old/new Train A visual review children without promoting either."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
OLD_MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAOldInGameReview_v329"
NEW_MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainANewInGameReview_v330"
MESH_PATH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ReadableLabels_v328/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_old_new_ingame_review_build_v330.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

if any(lib.does_asset_exist(p) for p in (OLD_MAP, NEW_MAP)) or OUT.exists():
    raise RuntimeError("Refusing to overwrite v329/v330")
if not lib.duplicate_asset(SOURCE_MAP, OLD_MAP):
    raise RuntimeError("Could not duplicate v301 as v329")
if not levels.load_level(OLD_MAP):
    raise RuntimeError("Could not load v329")

def add_camera(label):
    # Same fixed elevated operator-side camera in both review children.
    location = unreal.Vector(3850.0, -9850.0, 1850.0)
    target = unreal.Vector(3850.0, -4300.0, 430.0)
    cam = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
    cam.set_actor_label(label)
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    cam.camera_component.set_editor_properties({"field_of_view": 61.0, "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True})
    pp = cam.camera_component.get_editor_property("post_process_settings")
    pp.set_editor_properties({"override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC, "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True, "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0, "override_auto_exposure_bias": True, "auto_exposure_bias": 2.5})
    cam.camera_component.set_editor_property("post_process_settings", pp)
    cam.camera_component.set_editor_property("post_process_blend_weight", 1.0)
    return cam

add_camera("LB_V329_CAM_TRAIN_A_MATCHED_INGAME")
if not levels.save_current_level():
    raise RuntimeError("Could not save v329")
if not lib.duplicate_asset(OLD_MAP, NEW_MAP):
    raise RuntimeError("Could not duplicate v329 as v330")
if not levels.load_level(NEW_MAP):
    raise RuntimeError("Could not load v330")

all_actors = actors.get_all_level_actors()
native_train = [a for a in all_actors if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
for actor in native_train:
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)

mesh = lib.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("v328 mesh missing")
replacement = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator(0, -90, 0))
replacement.static_mesh_component.set_static_mesh(mesh)
replacement.set_actor_label("CA_MW_PTA_ReadableLabels_v040_WHOLE_SHOP_VISUAL_ONLY_v330")
replacement.set_actor_scale3d(unreal.Vector(100, 100, 100))
replacement.static_mesh_component.set_collision_profile_name("NoCollision")
replacement.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
replacement.tags = [unreal.Name(x) for x in ("LB.PressTrain.TrainA.ReadableLabelsSource.v040", "LB.Review.WholeShopVisualOnly.v330", "LB.NativeAuthorityPreservedHidden", "LB.Collision.NoCollision", "LB.Asset.CandidateNotPromoted")]
origin, extent = replacement.get_actor_bounds(False)
replacement.add_actor_world_offset(unreal.Vector(3850.0 - origin.x, -4300.0 - origin.y, -(origin.z - extent.z)), False, False)
origin, extent = replacement.get_actor_bounds(False)

old_cam = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_V329_CAM_TRAIN_A_MATCHED_INGAME")
old_cam.set_actor_label("LB_V330_CAM_TRAIN_A_MATCHED_INGAME")
if not levels.save_current_level():
    raise RuntimeError("Could not save v330")

old_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAOldInGameReview_v329.umap"
new_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainANewInGameReview_v330.umap"
payload = {
    "$schema": "cairnwell/audit/press-train-a-old-new-ingame-review-build-v330/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__MATCHED_INGAME_VISUAL_REVIEW_READY__NOT_PROMOTED",
    "source_map": SOURCE_MAP,
    "old_review_map": OLD_MAP,
    "new_review_map": NEW_MAP,
    "old_map_sha256": sha(old_file),
    "new_map_sha256": sha(new_file),
    "native_train_actor_count_hidden_in_new_child": len(native_train),
    "native_runtime_authority_deleted": False,
    "replacement_mesh": MESH_PATH,
    "replacement_rotation": [0, -90, 0],
    "replacement_scale": [100, 100, 100],
    "replacement_bounds_origin_cm": [origin.x, origin.y, origin.z],
    "replacement_bounds_size_cm": [extent.x * 2, extent.y * 2, extent.z * 2],
    "replacement_floor_z": origin.z - extent.z,
    "collision": "NoCollision_visual_review_only",
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
