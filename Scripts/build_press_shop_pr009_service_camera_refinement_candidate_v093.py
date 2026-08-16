"""Refine only the retained v092 south service-camera sightline."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceFasciaIdentityCandidate_v092"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraRefinementCandidate_v093"
OUT = ROOT / "Saved/Audits/PR009_InMap_v093/service_camera_refinement_build.json"
LOCATION = (0.0, -2820.0, 300.0)
TARGET = (550.0, -2020.0, 145.0)
FOV = 48.0

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(PARENT_MAP)
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(TARGET_MAP)
    unreal.log("PR009_V093_MAP_DUPLICATED__RERUN_FOR_CAMERA_REFINEMENT")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

camera = None
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if "V092" in label:
        actor.set_actor_label(label.replace("V092", "V093"))
    actor.tags = [unreal.Name(str(tag).replace("v092", "v093")) for tag in actor.tags]
    if actor.get_actor_label() == "LB_PR009_V093_PRESENT_CAM_ServiceHero":
        camera = actor
if camera is None or not isinstance(camera, unreal.CameraActor):
    raise RuntimeError("Retained service camera not found")

camera.set_actor_location(unreal.Vector(*LOCATION), False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    unreal.Vector(*LOCATION), unreal.Vector(*TARGET)), False)
camera.camera_component.set_field_of_view(FOV)

flows = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPressShopMaterialFlowController)]
pr008 = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR008Station)]
pr009 = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR009Station)]
if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
flows[0].bind_blank_stations(pr008[0], pr009[0])
if not levels.save_current_level():
    raise RuntimeError(TARGET_MAP)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr009-service-camera-refinement-v093/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V093_LOWER_SERVICE_CAMERA_EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "camera_location_cm": LOCATION,
    "camera_target_cm": TARGET,
    "fov_degrees": FOV,
    "geometry_changed": False,
    "collision_changed": False,
    "navigation_changed": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"PR009_V093_SERVICE_CAMERA_REFINEMENT_BUILD_PASS output={OUT}")
