"""Build isolated fixed-camera visual gate map for reusable MR01 v021."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_MR01_Candidate_v021_FunctionalAuthority"
BP_PATH = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v021_functional_validation_map.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


def component_with_tag(actor, cls, tag):
    for component in actor.get_components_by_class(cls):
        if unreal.Name(tag) in component.get_editor_property("component_tags"):
            return component
    return None


if assets.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved validation map {MAP}")
bp = require(BP_PATH, unreal.Blueprint)
generated_class = blueprints.generated_class(bp)
if generated_class is None or not levels.new_level(MAP):
    raise RuntimeError("Could not create MR01 v021 validation map")

stowed = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, -270.0, 62.5), unreal.Rotator())
reach = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 270.0, 62.5), unreal.Rotator())
if stowed is None or reach is None:
    raise RuntimeError("Could not spawn stowed and machine-reach MR01 instances")
stowed.set_actor_label("LB_MR01_v021_Stowed_Authority")
reach.set_actor_label("LB_MR01_v021_T6_MachineReach_Authority")
for actor in (stowed, reach):
    actor.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Validation.MR01.v021"),
        unreal.Name("LB.Brand.CairnwellAutomotive"), unreal.Name("LB.Site.MoorcrossWorks"),
        unreal.Name("LB.MR01.NativeAuthority"), unreal.Name("LB.Safety.NonNavigableValidation"),
    ])

# Fixed visual proof of the same 400 mm state exercised by the passing runtime
# test. The arm's horizontal reach comes from its articulated six-axis rest/reach
# geometry; only the vertical lift telescopes.
arm = component_with_tag(reach, unreal.PoseableMeshComponent, "LB.MR01.ArmPoseable")
sleeve = component_with_tag(reach, unreal.StaticMeshComponent, "LB.MR01.ArmLiftSleeve")
carriage = component_with_tag(reach, unreal.StaticMeshComponent, "LB.MR01.ArmLiftCarriage")
stored_t6 = component_with_tag(reach, unreal.StaticMeshComponent, "LB.MR01.Tool.T6.Stored")
equipped_t6 = component_with_tag(reach, unreal.StaticMeshComponent, "LB.MR01.Tool.T6.Equipped")
if None in (arm, sleeve, carriage, stored_t6, equipped_t6):
    raise RuntimeError("MR01 v021 reach presentation components are incomplete")
lift_transform = arm.get_bone_transform_by_name(unreal.Name("lift"), unreal.BoneSpaces.COMPONENT_SPACE)
lift_transform.translation = lift_transform.translation + unreal.Vector(0.0, 0.0, 40.0)
arm.set_bone_transform_by_name(unreal.Name("lift"), lift_transform, unreal.BoneSpaces.COMPONENT_SPACE)
sleeve.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 20.0))
carriage.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, 40.0))
stored_t6.set_visibility(False, True)
stored_t6.set_hidden_in_game(True, True)
equipped_t6.attach_to_component(
    arm, unreal.Name("tool_coupler"), unreal.AttachmentRule.SNAP_TO_TARGET,
    unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.KEEP_RELATIVE, False)
equipped_t6.set_visibility(True, True)
equipped_t6.set_hidden_in_game(False, True)

cube = require("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh)
floor_material = require("/Game/LineBoss/Materials/M_LB_FactoryConcrete", unreal.MaterialInterface)
wall_material = require("/Game/LineBoss/Materials/M_LB_ShellCharcoal", unreal.MaterialInterface)


def spawn_mesh(label, location, scale, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(cube)
    component.set_material(0, material)
    return actor


spawn_mesh("LB_MR01_v021_ValidationFloor", (0.0, 0.0, -7.0), (9.0, 11.0, 0.10), floor_material)
spawn_mesh("LB_MR01_v021_ValidationBackdrop", (-310.0, 0.0, 230.0), (0.10, 11.0, 3.4), wall_material)

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 650.0), unreal.Rotator(-42.0, -32.0, 0.0))
sun.set_actor_label("LB_MR01_v021_KeySun")
sun.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 1.25, "light_color": unreal.Color(255, 248, 236, 255)})
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 420.0), unreal.Rotator())
sky.set_actor_label("LB_MR01_v021_Sky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.5)
for label, location, intensity in (
    ("StowedFill", (330.0, -520.0, 260.0), 310.0),
    ("ReachFill", (330.0, 520.0, 300.0), 340.0),
    ("LiftRim", (-100.0, 270.0, 390.0), 300.0),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_MR01_v021_{label}")
    light.get_editor_property("point_light_component").set_editor_properties({
        "intensity": intensity, "attenuation_radius": 1050.0})

camera_specs = [
    ("Stowed_Oblique", (390.0, -650.0, 225.0), (0.0, -270.0, 72.0), 47.0),
    ("Stowed_Side", (10.0, -760.0, 135.0), (0.0, -270.0, 72.0), 44.0),
    ("Reach_Oblique", (410.0, -80.0, 265.0), (25.0, 270.0, 115.0), 48.0),
    ("Reach_Profile", (20.0, 790.0, 175.0), (30.0, 270.0, 112.0), 43.0),
    ("Reach_LiftTool", (300.0, 520.0, 255.0), (55.0, 270.0, 140.0), 39.0),
]
camera_labels = []
for suffix, location, target, fov in camera_specs:
    position = unreal.Vector(*location)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    camera.set_actor_label(f"LB_MR01_v021_CAM_{suffix}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    component = camera.get_editor_property("camera_component")
    component.set_editor_property("field_of_view", fov)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": -0.65,
    })
    camera_labels.append(camera.get_actor_label())

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-mr01-candidate-v021-functional-validation-map",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FIXED_CAMERA_MAP_BUILT__FRESH_SCREENSHOTS_AND_PRO_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "blueprint": BP_PATH,
    "instances": [stowed.get_actor_label(), reach.get_actor_label()],
    "reach_state": {"lift_mm": 400.0, "sleeve_mm": 200.0, "tool": "T6_TorqueTool"},
    "arm_reach_type": "SIX_AXIS_ARTICULATED__VERTICAL_LIFT_TELESCOPIC__NO_HORIZONTAL_TELESCOPE",
    "fixed_cameras": camera_labels,
    "runtime_automation": "PASS__LineBoss.SupportRobots.MR01.FunctionalRuntime",
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_MR01_V021_VALIDATION_MAP_PASS cameras={len(camera_labels)} audit={AUDIT}")
