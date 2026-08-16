"""Build isolated v006 by docking the actual retained CR01 v065 and MR01 v021 authorities.

The common contact frame is authoritative. Dock FBX is Blender CFR converted to
Unreal, so a -90 degree robot yaw maps robot -X rear contacts to dock +Y contacts.
No Press Shop placement or promotion is performed here.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v006"
MR_BP = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
CR_BP = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"
OUT = ROOT / "Saved/Audits/SupportRobots/service_dock_actual_robot_fit_build_v006.json"
V253 = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253.umap"

lib = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def vec(value):
    return [round(value.x, 4), round(value.y, 4), round(value.z, 4)]


def require_blueprint(path):
    bp = lib.load_asset(path)
    if not isinstance(bp, unreal.Blueprint):
        raise RuntimeError(f"Missing retained robot authority {path}")
    generated = blueprints.generated_class(bp)
    if generated is None:
        raise RuntimeError(f"Generated class unavailable {path}")
    return generated


def named_component(actor, name):
    for component in actor.get_components_by_class(unreal.SceneComponent):
        if component.get_name() == name:
            return component
    raise RuntimeError(f"{actor.get_actor_label()} missing component {name}")


def restore_cr01_visual(authority):
    count = 0
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    if len(mounts) != 1:
        raise RuntimeError(f"CR01 expected one presentation child, found {len(mounts)}")
    presentation = mounts[0].get_editor_property("child_actor")
    if presentation is None:
        raise RuntimeError("CR01 presentation child unavailable")
    for component in presentation.get_components_by_class(unreal.StaticMeshComponent):
        name = component.get_name().replace("_GEN_VARIABLE", "").replace("_0", "")
        if name.startswith("Condition_Mothballed"):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
            count += 1
        elif name.startswith("Condition_Restored"):
            component.set_visibility(True, True)
            component.set_hidden_in_game(False, True)
            count += 1
    return count


def add_camera(label, location, target, fov):
    position = unreal.Vector(*location)
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    if camera is None:
        raise RuntimeError(f"Could not spawn camera {label}")
    camera.set_actor_label(label)
    camera.tags = [unreal.Name("LB.Camera.Fixed.ServiceDockActualRobotFit.v006"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    component = camera.camera_component
    component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.35,
    })
    component.set_editor_property("post_process_settings", settings)
    return camera


if lib.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved fit candidate {MAP}")
v253_before = sha256(V253)
if not lib.duplicate_asset(SOURCE, MAP):
    raise RuntimeError(f"Could not duplicate {SOURCE} to {MAP}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

level_actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
mr_dock = level_actors.get("LB_DOCK_INTAKE_MR01_v005")
cr_dock = level_actors.get("LB_DOCK_INTAKE_CR01_v008")
if not isinstance(mr_dock, unreal.StaticMeshActor) or not isinstance(cr_dock, unreal.StaticMeshActor):
    raise RuntimeError("Required v005 dock actors unavailable")

mr = actors_api.spawn_actor_from_class(require_blueprint(MR_BP), unreal.Vector(0.0, -230.0, 62.5), unreal.Rotator(0.0, -90.0, 0.0))
cr = actors_api.spawn_actor_from_class(require_blueprint(CR_BP), unreal.Vector(0.0, 230.0, 56.0), unreal.Rotator(0.0, -90.0, 0.0))
if mr is None or cr is None:
    raise RuntimeError("Could not spawn actual retained dock-fit robots")
mr.set_actor_label("LB_DOCK_FIT_MR01_v021_ActualAuthority")
cr.set_actor_label("LB_DOCK_FIT_CR01_v065_ActualAuthority")
for actor, family, version in ((mr, "MR01", "v021"), (cr, "CR01", "v065")):
    actor.tags = [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Validation.ServiceDock.ActualRobotFit.v006"),
        unreal.Name(f"LB.DockFit.{family}.{version}"),
        unreal.Name("LB.Runtime.Authority.RetainedActualRobot"),
    ]

cr_condition_components = restore_cr01_visual(cr)

# Exact shared charging-contact frame. With yaw -90, robot local (-73.5,
# +/-12, z) maps to dock world (+/-12, +73.5, z).
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
        contact_rows.append({
            "family": family,
            "side": side,
            "component": component_name,
            "expected_world_cm": vec(expected[side]),
            "actual_world_cm": vec(actual),
            "error_cm": vec(delta),
            "error_magnitude_cm": round(delta.length(), 5),
        })

robot_rows = []
for family, actor, source_static_width_cm in (("MR01", mr, 93.0), ("CR01", cr, None)):
    origin, extent = actor.get_actor_bounds(False)
    robot_rows.append({
        "family": family,
        "actor": actor.get_actor_label(),
        "location_cm": vec(actor.get_actor_location()),
        "rotation_deg": [actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw],
        "bounds_origin_cm": vec(origin),
        "bounds_extent_cm": vec(extent),
        "bounds_size_cm": vec(extent * 2.0),
        "source_static_fit_width_cm": source_static_width_cm,
    })

camera_specs = (
    ("LB_DOCK_FIT_CAM_FamilyActual", (-560.0, 80.0, 285.0), (0.0, 0.0, 72.0), 49.0),
    ("LB_DOCK_FIT_CAM_MR01_Oblique", (-410.0, 130.0, 215.0), (0.0, -230.0, 70.0), 42.0),
    ("LB_DOCK_FIT_CAM_MR01_Portal", (0.0, 185.0, 145.0), (0.0, -230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Oblique", (-410.0, 590.0, 215.0), (0.0, 230.0, 65.0), 42.0),
    ("LB_DOCK_FIT_CAM_CR01_Portal", (0.0, 645.0, 145.0), (0.0, 230.0, 60.0), 42.0),
)
cameras = [add_camera(*spec) for spec in camera_specs]

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
map_file = ROOT / "Content/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v006.umap"
v253_after = sha256(V253)
if v253_after != v253_before:
    raise RuntimeError("Protected v253 changed")

max_contact_error = max(row["error_magnitude_cm"] for row in contact_rows)
mr_width = next(row["bounds_size_cm"][0] for row in robot_rows if row["family"] == "MR01")
mr_source_width = 93.0
mr_runtime_bounds_match_source = abs(mr_width - mr_source_width) <= 1.0
status = (
    "PASS__ACTUAL_RETAINED_ROBOTS_DOCKED_ON_EXACT_CONTACT_FRAME__STATIC_COLLISION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
    if max_contact_error <= 0.1 and mr_runtime_bounds_match_source else
    "HOLD__EXACT_CONTACT_FRAME_ALIGNED_BUT_ACTUAL_MR01_UNREAL_BOUNDS_DISAGREE_WITH_SOURCE_FIT_AUTHORITY__NOT_PROMOTED"
)
payload = {
    "$schema": "cairnwell/audit/service-dock-actual-robot-fit-build-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "source_map": SOURCE,
    "map": MAP,
    "map_sha256": sha256(map_file),
    "actual_robot_blueprints": {"MR01": MR_BP, "CR01": CR_BP},
    "contact_alignment": contact_rows,
    "maximum_contact_error_cm": max_contact_error,
    "robots": robot_rows,
    "mr01_source_v022_static_width_cm": mr_source_width,
    "mr01_actual_unreal_bounds_width_cm": mr_width,
    "mr01_runtime_bounds_match_source_fit": mr_runtime_bounds_match_source,
    "cr01_restored_condition_component_count": cr_condition_components,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "protected_v253_sha256_before": v253_before,
    "protected_v253_sha256_after": v253_after,
    "holds": [
        "Consolidated dock intake collision is not accepted as authored production collision.",
        "Actual mesh-pair collision, door/probe/drawer sweeps and approach navigation remain open.",
        "CR01 external envelope remains TBC.",
        "No Press Shop placement or runtime service behavior is authorised by this fit map."
    ],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SERVICE_DOCK_ACTUAL_ROBOT_FIT_V006_BUILD status={status} audit={OUT}")
