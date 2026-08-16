"""Create isolated v090 with one Pro-guided south-west service hero camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090"
OUT = ROOT / "Saved/Audits/PR009_InMap_v090/service_camera_build.json"
CAMERA_LABEL = "LB_PR009_V090_PRESENT_CAM_ServiceHero"
LOCATION = (0.0, -2820.0, 400.0)
TARGET = (550.0, -2020.0, 130.0)
FOV = 50.0

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(f"Could not duplicate {PARENT_MAP}")
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save {TARGET_MAP}")
    unreal.log("PR009_V090_MAP_DUPLICATED__RERUN_FOR_SERVICE_CAMERA")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(TARGET_MAP):
    raise RuntimeError(f"Could not load {TARGET_MAP}")
for actor in actors_api.get_all_level_actors():
    if "V089" in actor.get_actor_label():
        actor.set_actor_label(actor.get_actor_label().replace("V089", "V090"))
    actor.tags = [unreal.Name(str(tag).replace("v089", "v090")) for tag in actor.tags]

old = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL]
for actor in old:
    actors_api.destroy_actor(actor)
camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*LOCATION), unreal.Rotator())
camera.set_actor_label(CAMERA_LABEL)
camera.tags = [
    unreal.Name("LB.Camera.Validation"),
    unreal.Name("LB.Camera.Fixed.PR009.v090"),
    unreal.Name("LB.Camera.ServiceSideHero"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(*TARGET)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": FOV,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})

flows = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
pr008 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
flows[0].bind_blank_stations(pr008[0], pr009[0])
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {TARGET_MAP}")

payload = {
    "$schema": "cairnwell/audit/pr009-service-camera-build-v090/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V090_SOUTH_WEST_SERVICE_HERO_CAMERA_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "camera": {"label": CAMERA_LABEL, "location_cm": LOCATION, "target_cm": TARGET, "fov_degrees": FOV},
    "must_show": ["authored HMI", "electrical cabinet", "trace portal", "gantry", "blank stack", "open-mesh guarding"],
    "geometry_changed": False,
    "materials_changed": False,
    "lighting_changed": False,
    "collision_changed": False,
    "parent_v089_modified": False,
    "pr010_started": False,
    "robots_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"PR009_V090_SERVICE_CAMERA_BUILD_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
