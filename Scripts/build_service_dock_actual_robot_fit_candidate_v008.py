"""Build a correct-yaw actual-robot/dock comparison in an already-open v008 map."""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
MR_BP = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actual_robot_fit_build_v008.json"
MAP_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008.umap"
SOURCE_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005.umap"
V253_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"
LIB = unreal.EditorAssetLibrary
BLUEPRINTS = unreal.BlueprintEditorLibrary
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def xyz(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def length(value):
    return math.sqrt(value.x ** 2 + value.y ** 2 + value.z ** 2)


def generated_class(path):
    blueprint = LIB.load_asset(path)
    if not isinstance(blueprint, unreal.Blueprint):
        raise RuntimeError("Missing Blueprint authority {}".format(path))
    result = BLUEPRINTS.generated_class(blueprint)
    if result is None:
        raise RuntimeError("Blueprint generated class unavailable {}".format(path))
    return result


def component(actor, name):
    for item in actor.get_components_by_class(unreal.SceneComponent):
        if item.get_name() == name:
            return item
    raise RuntimeError("{} missing {}".format(actor.get_actor_label(), name))


def restore_cr01(authority):
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    if len(mounts) != 1:
        raise RuntimeError("CR01 presentation mount count is {}".format(len(mounts)))
    child = mounts[0].get_editor_property("child_actor")
    if child is None:
        raise RuntimeError("CR01 presentation child unavailable")
    changed = 0
    for mesh in child.get_components_by_class(unreal.StaticMeshComponent):
        name = mesh.get_name()
        for suffix in ("_GEN_VARIABLE", "_0"):
            if name.endswith(suffix):
                name = name[: -len(suffix)]
        if name.startswith("Condition_Mothballed"):
            mesh.set_visibility(False, True)
            mesh.set_hidden_in_game(True, True)
            changed += 1
        elif name.startswith("Condition_Restored"):
            mesh.set_visibility(True, True)
            mesh.set_hidden_in_game(False, True)
            changed += 1
    return changed


def camera(label, location, target, fov):
    position = unreal.Vector(*location)
    actor = ACTORS.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    if actor is None:
        raise RuntimeError("Could not spawn camera {}".format(label))
    actor.set_actor_label(label)
    actor.tags = [
        unreal.Name("LB.Camera.Fixed.ServiceDockActualRobotFit.v008"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False
    )
    actor.camera_component.set_editor_properties(
        {"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True}
    )
    settings = actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties(
        {
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": -0.35,
        }
    )
    actor.camera_component.set_editor_property("post_process_settings", settings)
    return actor


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))

source_before = sha256(SOURCE_FILE)
v253_before = sha256(V253_FILE)
by_label = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
mr_dock = by_label.get("LB_DOCK_INTAKE_MR01_v005")
cr_dock = by_label.get("LB_DOCK_INTAKE_CR01_v008")
if not isinstance(mr_dock, unreal.StaticMeshActor) or not isinstance(cr_dock, unreal.StaticMeshActor):
    raise RuntimeError("Required retained dock actors unavailable")
if "LB_DOCK_FIT_MR01_v021_ActualAuthority" in by_label:
    raise RuntimeError("Refusing to rebuild populated v008")

# Unreal Python Rotator positional order is roll, pitch, yaw. The third value is intentional.
docking_rotation = unreal.Rotator(0.0, 0.0, -90.0)
mr = ACTORS.spawn_actor_from_class(
    generated_class(MR_BP), unreal.Vector(0.0, -230.0, 62.5), docking_rotation
)
cr = ACTORS.spawn_actor_from_class(
    generated_class(CR_BP), unreal.Vector(0.0, 230.0, 56.0), docking_rotation
)
if mr is None or cr is None:
    raise RuntimeError("Could not spawn retained robot authorities")
mr.set_actor_label("LB_DOCK_FIT_MR01_v021_ActualAuthority")
cr.set_actor_label("LB_DOCK_FIT_CR01_v065_ActualAuthority")
for actor, family, version in ((mr, "MR01", "v021"), (cr, "CR01", "v065")):
    actor.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Validation.ServiceDock.ActualRobotFit.v008"),
        unreal.Name("LB.DockFit.{}.{}".format(family, version)),
        unreal.Name("LB.Runtime.Authority.RetainedActualRobot"),
    ]
cr_restored_count = restore_cr01(cr)

contacts = []
for family, actor, dock, left, right in (
    ("MR01", mr, mr_dock, "PVT_DockCharge_L", "PVT_DockCharge_R"),
    ("CR01", cr, cr_dock, "PVT_DockChargeContact_L", "PVT_DockChargeContact_R"),
):
    dock_location = dock.get_actor_location()
    expected = {
        "left": unreal.Vector(dock_location.x - 12.0, dock_location.y + 73.5, 34.0),
        "right": unreal.Vector(dock_location.x + 12.0, dock_location.y + 73.5, 34.0),
    }
    for side, name in (("left", left), ("right", right)):
        actual = component(actor, name).get_world_location()
        error = actual - expected[side]
        contacts.append(
            {
                "family": family,
                "side": side,
                "component": name,
                "expected_world_cm": xyz(expected[side]),
                "actual_world_cm": xyz(actual),
                "error_cm": xyz(error),
                "error_magnitude_cm": round(length(error), 5),
            }
        )

robots = []
for family, actor in (("MR01", mr), ("CR01", cr)):
    origin, extent = actor.get_actor_bounds(False)
    size = extent * 2.0
    robots.append(
        {
            "family": family,
            "actor": actor.get_actor_label(),
            "location_cm": xyz(actor.get_actor_location()),
            "rotation_roll_pitch_yaw_deg": [
                round(actor.get_actor_rotation().roll, 4),
                round(actor.get_actor_rotation().pitch, 4),
                round(actor.get_actor_rotation().yaw, 4),
            ],
            "bounds_origin_cm": xyz(origin),
            "bounds_size_cm": xyz(size),
            "dock_portal_width_cm": 126.0,
            "lateral_clearance_cm_using_world_x_bounds": round(126.0 - size.x, 4),
        }
    )

camera_specs = (
    ("LB_DOCK_FIT_CAM_FamilyActual", (-560.0, 80.0, 285.0), (0.0, 0.0, 72.0), 49.0),
    ("LB_DOCK_FIT_CAM_MR01_Oblique", (-410.0, 130.0, 215.0), (0.0, -230.0, 70.0), 42.0),
    ("LB_DOCK_FIT_CAM_MR01_Portal", (0.0, 185.0, 145.0), (0.0, -230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Oblique", (-410.0, 590.0, 215.0), (0.0, 230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Portal", (0.0, 645.0, 145.0), (0.0, 230.0, 60.0), 42.0),
)
cameras = [camera(*spec) for spec in camera_specs]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not LEVELS.save_current_level():
    raise RuntimeError("Could not save v008")
source_after = sha256(SOURCE_FILE)
v253_after = sha256(V253_FILE)
if source_after != source_before or v253_after != v253_before:
    raise RuntimeError("Protected retained package changed")

max_contact_error = max(row["error_magnitude_cm"] for row in contacts)
minimum_clearance = min(row["lateral_clearance_cm_using_world_x_bounds"] for row in robots)
contact_pass = max_contact_error <= 0.1
portal_pass = minimum_clearance >= 0.0
if contact_pass and portal_pass:
    status = "PASS__CONTACT_FRAME_AND_AGGREGATE_PORTAL_BOUNDS__FURTHER_GATES_OPEN__NOT_PROMOTED"
elif contact_pass:
    status = "HOLD__CONTACT_FRAME_ALIGNED__MR01_AGGREGATE_BOUNDS_EXCEED_PORTAL__NOT_PROMOTED"
else:
    status = "HOLD__CONTACT_FRAME_MISALIGNED__NOT_PROMOTED"

payload = {
    "$schema": "cairnwell/audit/service-dock-actual-robot-fit-build-v008/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "map": MAP,
    "map_sha256": sha256(MAP_FILE),
    "actual_robot_blueprints": {"MR01": MR_BP, "CR01": CR_BP},
    "docking_rotation_roll_pitch_yaw_deg": [0.0, 0.0, -90.0],
    "contact_alignment": contacts,
    "maximum_contact_error_cm": max_contact_error,
    "contact_frame_pass": contact_pass,
    "robots": robots,
    "minimum_lateral_clearance_cm": minimum_clearance,
    "portal_bounds_pass": portal_pass,
    "cr01_restored_condition_component_count": cr_restored_count,
    "fixed_cameras": [item.get_actor_label() for item in cameras],
    "source_v005_sha256_before": source_before,
    "source_v005_sha256_after": source_after,
    "protected_v253_sha256_before": v253_before,
    "protected_v253_sha256_after": v253_after,
    "holds": [
        "Consolidated dock collision is not accepted as production collision.",
        "Aggregate bounds require component-level portal-interference inspection.",
        "Door, probe, drawer and approach-navigation sweeps remain open.",
        "No Press Shop placement or runtime service behavior is authorised."
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_ACTUAL_ROBOT_FIT_V008_BUILD status={}".format(status))
