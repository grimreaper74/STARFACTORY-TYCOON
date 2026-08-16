"""Set deterministic fixed-camera exposure for the v030 visual gate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_camera_exposure_v030.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

targets = {
    "LB_PR004_V030_CAM_CraneFullSpanWest": -1.25,
    "LB_PR004_V028_CAM_CHookEngagement": -0.20,
    "LB_PR004_V028_CAM_PR004Deposit": -0.45,
}
configured = []
by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
for label, bias in targets.items():
    actor = by_label.get(label)
    if actor is None or not isinstance(actor, unreal.CameraActor):
        raise RuntimeError(f"Missing fixed camera {label}")
    component = actor.camera_component
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": bias,
    })
    component.set_editor_property("post_process_settings", settings)
    component.set_editor_property("post_process_blend_weight", 1.0)
    configured.append({"camera": label, "auto_exposure_bias": bias})

service_fill = by_label.get("LB_PR004_V028_CraneServiceFill")
if service_fill is None:
    raise RuntimeError("Missing inherited crane service fill")
service_fill.point_light_component.set_editor_property("intensity", 40.0)

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "line-boss/audit/press-shop-pr004-crane-camera-exposure-v030/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DETERMINISTIC_FIXED_CAMERA_EXPOSURE_CONFIGURED__FRESH_CAPTURE_REQUIRED",
    "map": MAP,
    "cameras": configured,
    "candidate_service_fill_intensity": 40.0,
    "capture_harness_copies_authored_post_process": True,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_CAMERA_EXPOSURE_V030_PASS cameras={len(configured)}")
unreal.SystemLibrary.quit_editor()
