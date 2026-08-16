"""Build the isolated v007 actual-robot dock comparison in an already-open v007 map.

The process must be launched with v007 as its positional map. It deliberately
does not duplicate or load a world, preserving the one-map-per-process rule.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v007"
MR_BP = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actual_robot_fit_build_v007.json"
MAP_FILE = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v007.umap"
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


def vec(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def magnitude(value):
    return math.sqrt(value.x * value.x + value.y * value.y + value.z * value.z)


def require_blueprint(path):
    blueprint = LIB.load_asset(path)
    if not isinstance(blueprint, unreal.Blueprint):
        raise RuntimeError("Missing retained robot authority {}".format(path))
    generated = BLUEPRINTS.generated_class(blueprint)
    if generated is None:
        raise RuntimeError("Generated class unavailable {}".format(path))
    return generated


def named_component(actor, name):
    for component in actor.get_components_by_class(unreal.SceneComponent):
        if component.get_name() == name:
            return component
    raise RuntimeError("{} missing component {}".format(actor.get_actor_label(), name))


def normalized_component_name(name):
    value = name
    if value.endswith("_GEN_VARIABLE"):
        value = value[: -len("_GEN_VARIABLE")]
    if value.endswith("_0"):
        value = value[:-2]
    return value


def restore_cr01_visual(authority):
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    if len(mounts) != 1:
        raise RuntimeError("CR01 expected one presentation child, found {}".format(len(mounts)))
    presentation = mounts[0].get_editor_property("child_actor")
    if presentation is None:
        raise RuntimeError("CR01 presentation child unavailable")
    changed = 0
    for component in presentation.get_components_by_class(unreal.StaticMeshComponent):
        name = normalized_component_name(component.get_name())
        if name.startswith("Condition_Mothballed"):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
            changed += 1
        elif name.startswith("Condition_Restored"):
            component.set_visibility(True, True)
            component.set_hidden_in_game(False, True)
            changed += 1
    return changed


def add_camera(label, location, target, fov):
    position = unreal.Vector(*location)
    camera = ACTORS.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    if camera is None:
        raise RuntimeError("Could not spawn camera {}".format(label))
    camera.set_actor_label(label)
    camera.tags = [
        unreal.Name("LB.Camera.Fixed.ServiceDockActualRobotFit.v007"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False
    )
    component = camera.camera_component
    component.set_editor_properties(
        {
            "field_of_view": fov,
            "aspect_ratio": 16.0 / 9.0,
            "constrain_aspect_ratio": True,
        }
    )
    settings = component.get_editor_property("post_process_settings")
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
    component.set_editor_property("post_process_settings", settings)
    return camera


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))

source_before = sha256(SOURCE_FILE)
v253_before = sha256(V253_FILE)
existing_labels = {actor.get_actor_label() for actor in ACTORS.get_all_level_actors()}
for forbidden in (
    "LB_DOCK_FIT_MR01_v021_ActualAuthority",
    "LB_DOCK_FIT_CR01_v065_ActualAuthority",
):
    if forbidden in existing_labels:
        raise RuntimeError("Refusing to rebuild already-authored v007 actor {}".format(forbidden))

level_actors = {actor.get_actor_label(): actor for actor in ACTORS.get_all_level_actors()}
mr_dock = level_actors.get("LB_DOCK_INTAKE_MR01_v005")
cr_dock = level_actors.get("LB_DOCK_INTAKE_CR01_v008")
if not isinstance(mr_dock, unreal.StaticMeshActor) or not isinstance(cr_dock, unreal.StaticMeshActor):
    raise RuntimeError("Required retained v005 dock actors unavailable")

mr = ACTORS.spawn_actor_from_class(
    require_blueprint(MR_BP), unreal.Vector(0.0, -230.0, 62.5), unreal.Rotator(0.0, -90.0, 0.0)
)
cr = ACTORS.spawn_actor_from_class(
    require_blueprint(CR_BP), unreal.Vector(0.0, 230.0, 56.0), unreal.Rotator(0.0, -90.0, 0.0)
)
if mr is None or cr is None:
    raise RuntimeError("Could not spawn actual retained dock-fit robots")
mr.set_actor_label("LB_DOCK_FIT_MR01_v021_ActualAuthority")
cr.set_actor_label("LB_DOCK_FIT_CR01_v065_ActualAuthority")
for actor, family, version in ((mr, "MR01", "v021"), (cr, "CR01", "v065")):
    actor.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Validation.ServiceDock.ActualRobotFit.v007"),
        unreal.Name("LB.DockFit.{}.{}".format(family, version)),
        unreal.Name("LB.Runtime.Authority.RetainedActualRobot"),
    ]

cr_condition_components = restore_cr01_visual(cr)

# Common contact frame: robot local rear contacts map to dock FBX +Y at yaw -90.
contact_rows = []
for family, actor, dock, left_name, right_name in (
    ("MR01", mr, mr_dock, "PVT_DockCharge_L", "PVT_DockCharge_R"),
    ("CR01", cr, cr_dock, "PVT_DockChargeContact_L", "PVT_DockChargeContact_R"),
):
    dock_location = dock.get_actor_location()
    expected = {
        "left": unreal.Vector(dock_location.x - 12.0, dock_location.y + 73.5, 34.0),
        "right": unreal.Vector(dock_location.x + 12.0, dock_location.y + 73.5, 34.0),
    }
    for side, component_name in (("left", left_name), ("right", right_name)):
        actual = named_component(actor, component_name).get_world_location()
        delta = actual - expected[side]
        contact_rows.append(
            {
                "family": family,
                "side": side,
                "component": component_name,
                "expected_world_cm": vec(expected[side]),
                "actual_world_cm": vec(actual),
                "error_cm": vec(delta),
                "error_magnitude_cm": round(magnitude(delta), 5),
            }
        )

robot_rows = []
for family, actor, portal_width_cm in (("MR01", mr, 126.0), ("CR01", cr, 126.0)):
    origin, extent = actor.get_actor_bounds(False)
    size = extent * 2.0
    robot_rows.append(
        {
            "family": family,
            "actor": actor.get_actor_label(),
            "location_cm": vec(actor.get_actor_location()),
            "rotation_deg": [
                round(actor.get_actor_rotation().roll, 4),
                round(actor.get_actor_rotation().pitch, 4),
                round(actor.get_actor_rotation().yaw, 4),
            ],
            "bounds_origin_cm": vec(origin),
            "bounds_extent_cm": vec(extent),
            "bounds_size_cm": vec(size),
            "dock_portal_width_cm": portal_width_cm,
            "lateral_clearance_cm_using_actor_x_bounds": round(portal_width_cm - size.x, 4),
        }
    )

camera_specs = (
    ("LB_DOCK_FIT_CAM_FamilyActual", (-560.0, 80.0, 285.0), (0.0, 0.0, 72.0), 49.0),
    ("LB_DOCK_FIT_CAM_MR01_Oblique", (-410.0, 130.0, 215.0), (0.0, -230.0, 70.0), 42.0),
    ("LB_DOCK_FIT_CAM_MR01_Portal", (0.0, 185.0, 145.0), (0.0, -230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Oblique", (-410.0, 590.0, 215.0), (0.0, 230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Portal", (0.0, 645.0, 145.0), (0.0, 230.0, 60.0), 42.0),
)
cameras = [add_camera(*spec) for spec in camera_specs]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not LEVELS.save_current_level():
    raise RuntimeError("Could not save {}".format(MAP))

source_after = sha256(SOURCE_FILE)
v253_after = sha256(V253_FILE)
if source_after != source_before or v253_after != v253_before:
    raise RuntimeError("A protected retained package changed during the isolated build")

max_contact_error = max(row["error_magnitude_cm"] for row in contact_rows)
minimum_lateral_clearance = min(row["lateral_clearance_cm_using_actor_x_bounds"] for row in robot_rows)
contact_frame_pass = max_contact_error <= 0.1
portal_bounds_pass = minimum_lateral_clearance >= 0.0
status = (
    "PASS__ACTUAL_ROBOTS_ALIGN_AND_FIT_PORTAL_BOUNDS__COLLISION_VISUAL_AND_RUNTIME_GATES_OPEN__NOT_PROMOTED"
    if contact_frame_pass and portal_bounds_pass
    else "HOLD__ACTUAL_ROBOT_CONTACTS_ALIGN_BUT_ONE_OR_MORE_ACTOR_BOUNDS_EXCEED_THE_126CM_PORTAL__NOT_PROMOTED"
)

payload = {
    "$schema": "cairnwell/audit/service-dock-actual-robot-fit-build-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "map": MAP,
    "map_sha256": sha256(MAP_FILE),
    "actual_robot_blueprints": {"MR01": MR_BP, "CR01": CR_BP},
    "contact_alignment": contact_rows,
    "maximum_contact_error_cm": max_contact_error,
    "contact_frame_pass": contact_frame_pass,
    "robots": robot_rows,
    "minimum_lateral_clearance_cm_using_actor_x_bounds": minimum_lateral_clearance,
    "portal_bounds_pass": portal_bounds_pass,
    "cr01_restored_condition_component_count": cr_condition_components,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "source_v005_sha256_before": source_before,
    "source_v005_sha256_after": source_after,
    "protected_v253_sha256_before": v253_before,
    "protected_v253_sha256_after": v253_after,
    "holds": [
        "Consolidated dock intake collision is not accepted as authored production collision.",
        "Actor aggregate bounds are conservative; component-level portal interference still requires inspection.",
        "Door, probe, drawer and approach-navigation sweeps remain open.",
        "No Press Shop placement or runtime service behavior is authorised by this fit map."
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_SERVICE_DOCK_ACTUAL_ROBOT_FIT_V007_BUILD status={} audit={}".format(status, OUT))
