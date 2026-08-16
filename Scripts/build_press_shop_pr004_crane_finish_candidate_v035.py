"""Consolidate package identity and correct management framing/ceiling balance."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_crane_finish_candidate_v035.json"
PREFIX = "LB_PR004_V035_"
PAPER = "/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v026/M_LB_CoilLabelPaper_v026"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lib = unreal.EditorAssetLibrary

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

paper = lib.load_asset(PAPER)
if paper is None:
    raise RuntimeError(f"Missing controlled package-label paper material {PAPER}")


def names(*values):
    return [unreal.Name(value) for value in values]


# The detailed package already owns two physical paper labels. Blank the fixed
# v003 ink and align Cairnwell's live identity with the existing main panel,
# eliminating the later floating third-label appearance.
packaged_components = []
station = None
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() == "LB_INT_PR004_V024_InteractiveUnpackageStation":
        station = actor
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v004" not in mesh.get_path_name():
            continue
        component.set_material(9, paper)
        packaged_components.append(f"{actor.get_actor_label()}:{component.get_name()}")
if len(packaged_components) != 15 or station is None:
    raise RuntimeError(f"Unexpected package inventory: coils={len(packaged_components)} station={station}")

label_shift = unreal.Vector(10.5, -21.0, -16.0)
backings = []
text_rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("LB_COIL_LABEL_V026_"):
        actor.set_actor_location(actor.get_actor_location() + label_shift, False, False)
        actor.set_actor_scale3d(unreal.Vector(0.42, 0.25, 1.0))
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        component.set_material(0, paper)
        backings.append(label)
    elif label.startswith("LB_COIL_TEXT_V026_"):
        actor.set_actor_location(actor.get_actor_location() + label_shift, False, False)
        component = actor.get_component_by_class(unreal.TextRenderComponent)
        component.set_world_size(3.6 if label.endswith("_Heading") else 2.6)
        text_rows.append(label)

static_components = {component.get_name(): component for component in station.get_components_by_class(unreal.StaticMeshComponent)}
text_components = {component.get_name(): component for component in station.get_components_by_class(unreal.TextRenderComponent)}
wrapped = static_components.get("PR004_WrappedCoilVisual")
native_backing = static_components.get("PR004_WrappedCoilLabelVisual")
native_heading = text_components.get("PR004_WrappedCoilLabelHeading")
native_detail = text_components.get("PR004_WrappedCoilLabelDetail")
if any(value is None for value in (wrapped, native_backing, native_heading, native_detail)):
    raise RuntimeError("Native PR-004 packaged identity is incomplete")
origin = wrapped.get_world_location()
native_backing.set_world_location(unreal.Vector(origin.x + 42.5, origin.y + 75.2, origin.z + 31.0), False, False)
native_backing.set_world_scale3d(unreal.Vector(0.42, 0.25, 1.0))
native_backing.set_material(0, paper)
native_heading.set_world_location(unreal.Vector(origin.x + 42.5, origin.y + 75.65, origin.z + 36.0), False, False)
native_detail.set_world_location(unreal.Vector(origin.x + 42.5, origin.y + 75.70, origin.z + 26.5), False, False)
native_heading.set_world_size(3.6)
native_detail.set_world_size(2.6)

# Reduce only the broad roof point sources. v034's floor-directed spots remain
# unchanged and continue to provide readable machinery/package values.
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    component = actor.get_component_by_class(unreal.LightComponent)
    if component is None or not label.startswith("LB_INT_FRONT_FactoryFill_"):
        continue
    old = float(component.get_editor_property("intensity"))
    number = int(label.rsplit("_", 1)[-1])
    new = 450.0 if number in (10, 11, 12) else 320.0
    component.set_editor_property("intensity", new)
    light_changes.append({"actor": label, "old": old, "new": new})


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names("LB.Camera.Validation", "LB.Camera.Fixed.PR004Crane.v035",
                       "LB.Asset.Candidate.v035", "LB.Asset.CandidateNotPromoted")
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    component = actor.camera_component
    component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
                                     "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0})
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
    camera("CraneManagementSouthInterior", (-3150.0, 480.0, 980.0), (-5350.0, -2500.0, 1220.0), 70.0, -0.08),
    camera("CraneManagementSouthInteriorAlt", (-3650.0, 430.0, 900.0), (-6000.0, -2650.0, 1180.0), 72.0, -0.08),
    camera("CHookPurposeBuilt", (-6000.0, -900.0, 980.0), (-5050.0, -1850.0, 780.0), 37.0, 0.08),
    camera("CHookSideProfile", (-3950.0, -1850.0, 1050.0), (-5050.0, -1850.0, 770.0), 40.0, 0.05),
    camera("PR004OperatorOblique", (-4050.0, -420.0, 660.0), (-5050.0, -1950.0, 190.0), 50.0, 0.12),
    camera("PR004HMIAndCradle", (-4790.0, -1160.0, 265.0), (-5230.0, -1580.0, 150.0), 45.0, 0.10),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-crane-finish-candidate-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PACKAGE_IDENTITY_CAMERA_AND_CEILING_REWORK_BUILT__REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034",
    "map": MAP,
    "package_ink_overrides": len(packaged_components),
    "aligned_external_backings": len(backings),
    "aligned_external_text_actors": len(text_rows),
    "main_label_panel_mm": [420, 250],
    "dynamic_label_world_shift_cm": [10.5, -21.0, -16.0],
    "roof_light_changes": light_changes,
    "v034_floor_spots_retained": True,
    "support_crane_park_state_retained": True,
    "primary_40t_hook_and_load_datums_unchanged": True,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_CRANE_V035_BUILD_PASS coils={len(packaged_components)} labels={len(backings)} map={MAP}")
unreal.SystemLibrary.quit_editor()
