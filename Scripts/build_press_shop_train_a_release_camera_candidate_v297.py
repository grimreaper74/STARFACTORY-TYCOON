"""Build a camera-only direct-v295 child with restrained exposure calibration."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295"
MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseCameraCandidate_v297"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainAReleaseCameraCandidate_v297.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_train_a_release_camera_build_v297.json"
CAMERAS = [
    ("LB_V297_CAM_TrainAOperator", (5000, -5600, 650), (4000, -4742, 500), 48),
    ("LB_V297_CAM_TrainAFabrication", (3500, -5580, 580), (4100, -4742, 500), 46),
    ("LB_V297_CAM_TrainAOverview", (7000, -5700, 1200), (3850, -4742, 520), 50),
]
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite v297")
base_hash = sha(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh direct-v295 child failed")
removed = []
for actor in list(api.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_V295_CAM_TrainA"):
        removed.append(actor.get_actor_label())
        api.destroy_actor(actor)
cameras = []
for label, location, target, fov in CAMERAS:
    camera = api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    component = camera.camera_component
    component.set_editor_properties({"field_of_view": float(fov), "aspect_ratio": 16/9, "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.15,
    })
    component.set_editor_property("post_process_settings", settings)
    camera.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.TrainARelease.v297"), unreal.Name("LB.Asset.Candidate.v297"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    cameras.append(label)
shell = next((a for a in api.get_all_level_actors() if a.get_actor_label() == "LB_V295_PTA_FABRICATED_SHELL_V015"), None)
failures = []
if shell is None:
    failures.append("v295 shell missing")
elif str(shell.static_mesh_component.get_collision_profile_name()) != "NoCollision" or shell.static_mesh_component.get_editor_property("can_ever_affect_navigation"):
    failures.append("shell collision/navigation changed")
if len(cameras) != 3:
    failures.append(f"camera count {len(cameras)}")
if not levels.save_current_level():
    failures.append("save failed")
if sha(BASE_FILE) != base_hash:
    failures.append("protected v295 changed")
payload = {
    "$schema": "cairnwell/audit/press-shop-train-a-release-camera-build-v297/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__CAMERA_ONLY_DIRECT_V295_CHILD__VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V297_NOT_A_PARENT",
    "base": BASE, "map": MAP, "base_sha256": base_hash,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "removed_v295_cameras": removed, "added_cameras": cameras,
    "camera_exposure_bias": -0.15,
    "unchanged_contracts": ["lighting", "materials", "geometry", "transforms", "collision", "navigation", "runtime authority", "save authority"],
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
