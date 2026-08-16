"""Add fixed HMI validation cameras and audit the native v043 components."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_live_hmi_candidate_v043.json"
PREFIX = "LB_PR005_V043_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)


def names(*values):
    return [unreal.Name(value) for value in values]


def camera(label, location, target, fov, bias):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names(
        "LB.Camera.Validation", "LB.Camera.Fixed.PR005.v043",
        "LB.Asset.Candidate.v043", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
    })
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
    return actor


cameras = [
    camera("LiveHMI", (-3695.0, -1586.0, 152.0), (-3720.0, -1703.3, 110.5), 30.0, 0.12),
    camera("LoadedCell", (-5050.0, -980.0, 430.0), (-4050.0, -1980.0, 150.0), 42.0, 0.10),
    camera("LoadingMotion", (-4850.0, -1150.0, 330.0), (-4100.0, -1980.0, 105.0), 36.0, 0.10),
]

pr005_rows = [actor for actor in actors_api.get_all_level_actors()
              if isinstance(actor, unreal.LBPR005Station)]
if len(pr005_rows) != 1:
    raise RuntimeError(f"Expected one native PR-005 station, found {len(pr005_rows)}")
component_names = sorted(component.get_name() for component in
                         pr005_rows[0].get_components_by_class(unreal.ActorComponent))
required = {
    "PR005_OperatorHMI", "PR005_HMITextRoot", "PR005_HMI_BrandText",
    "PR005_HMI_StateText", "PR005_HMI_CoilText", "PR005_HMI_ActionText",
}
missing = sorted(required.difference(component_names))
if missing:
    raise RuntimeError(f"Native PR-005 HMI components missing: {missing}")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-live-hmi-candidate-v043/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_LIVE_HMI_MOUNTED__PIE_VISUAL_AND_FULL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": BASE,
    "map": MAP,
    "pr005": pr005_rows[0].get_actor_label(),
    "required_hmi_components": sorted(required),
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_LIVE_HMI_V043_BUILD_PASS map={MAP}")
unreal.SystemLibrary.quit_editor()
