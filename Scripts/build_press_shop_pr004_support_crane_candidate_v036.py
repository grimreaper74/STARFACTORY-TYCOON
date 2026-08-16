"""Bind v035's parked 30 t crane to a maintenance-only native authority."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_support_crane_candidate_v036.json"
PREFIX = "LB_PR004_V036_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)


def names(*values):
    return [unreal.Name(value) for value in values]


moving_tags = {
    "LB.Motion.CraneBridge", "LB.Motion.CraneTrolley",
    "LB.Motion.Hoist", "LB.Motion.CHook",
}
support_moving = []
master_coil_bindings = []
for actor in actors.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.Crane.30T" not in tags or not tags.intersection(moving_tags):
        continue
    support_moving.append({
        "actor": actor.get_actor_label(),
        "location_cm": list(actor.get_actor_location().to_tuple()),
        "motion_tags": sorted(tags.intersection(moving_tags)),
    })
    if tags.intersection({"LB.CoilSlot.CS-10", "LB.CoilSlot.CS-10.Attachment"}):
        master_coil_bindings.append(actor.get_actor_label())

if len(support_moving) != 52:
    raise RuntimeError(f"Expected 52 parked support-crane moving actors, found {len(support_moving)}")
if master_coil_bindings:
    raise RuntimeError(f"30 t crane incorrectly owns master-coil tags: {master_coil_bindings}")

# This target is an operational datum, not a visible prop. It keeps the 30 t
# bridge west of the 40 t master-coil system and moves only into an approved
# front-end maintenance support envelope.
service_point = actors.spawn_actor_from_class(
    unreal.TargetPoint, unreal.Vector(-7600.0, -3300.0, 760.0), unreal.Rotator())
service_point.set_actor_label(PREFIX + "FrontEndMaintenanceServicePoint")
service_point.tags = names(
    "LB.Crane.SupportPoint.FrontEndMaintenance",
    "LB.Operations.MaintenanceOnly",
    "LB.Asset.Candidate.v036",
    "LB.Asset.CandidateNotPromoted",
)

controller = actors.spawn_actor_from_class(
    unreal.LBSupportCraneController, unreal.Vector(-9100.0, -4700.0, 20.0), unreal.Rotator())
controller.set_actor_label(PREFIX + "SupportCraneController_CR-30-01")
controller.tags = names(
    "LB.Authority.SupportCrane.CR-30-01",
    "LB.Operations.MaintenanceOnly",
    "LB.Asset.Candidate.v036",
    "LB.Asset.CandidateNotPromoted",
)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names(
        "LB.Camera.Validation", "LB.Camera.Fixed.SupportCrane.v036",
        "LB.Asset.Candidate.v036", "LB.Asset.CandidateNotPromoted")
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
    camera(
        "SupportParkSouthInterior",
        (-6900.0, 260.0, 980.0), (-8750.0, -4050.0, 1220.0), 58.0, -0.06),
    camera(
        "SupportOnStationSouthInterior",
        (-6600.0, -920.0, 940.0), (-7600.0, -3300.0, 1120.0), 52.0, -0.04),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-support-crane-candidate-v036/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "30T_MAINTENANCE_AUTHORITY_AUTHORED__RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035",
    "map": MAP,
    "controller_class": "/Script/LineBossCarFactory.LBSupportCraneController",
    "crane_identity": "CR-30-01",
    "role": "front-end support and maintenance only",
    "master_coil_authority": False,
    "master_coil_tag_bindings": master_coil_bindings,
    "moving_actor_count": len(support_moving),
    "park_datums_cm": {"bridge_x": -9100.0, "trolley_y": -4700.0, "hook_z": 1010.0},
    "service_datums_cm": {"bridge_x": -7600.0, "trolley_y": -3300.0, "hook_z": 760.0},
    "required_interlocks": [
        "control power", "route clear", "personnel clear", "maintenance permit",
        "support zone reserved", "40 t swept zone clear",
    ],
    "moving_restore_policy": "fail-stopped pending named recovery evidence",
    "stable_restore_states": ["Parked", "OnStation"],
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "v035_package_identity_lighting_and_cameras_unchanged": True,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(
    f"LINE_BOSS_PR004_SUPPORT_CRANE_V036_BUILD_PASS moving={len(support_moving)} map={MAP}")
unreal.SystemLibrary.quit_editor()
