"""Build an isolated mothballed/restored CR01 v042 material-review map."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v042_SurfacePaintTechnical"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Blueprints/BP_LB_CR01_CleaningAMR_v042"
SHARED_PAINT_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002"
AUDIT = ROOT / "Saved/Audits/lb_cr01_v042_surfacepaint_validation_map.json"

asset_library = unreal.EditorAssetLibrary
bp_library = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def normalize(name):
    value = str(name)
    for suffix in ("_GEN_VARIABLE", "_0"):
        if value.endswith(suffix):
            value = value[:-len(suffix)]
    return value


def require(path, cls=None):
    asset = asset_library.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


if asset_library.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved validation map {MAP}")
blueprint = require(BP_PATH, unreal.Blueprint)
generated_class = bp_library.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v042 generated class is missing")
if not levels.new_level(MAP):
    raise RuntimeError(f"Could not create {MAP}")

paint = {}
for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey"):
    for condition in ("Restored", "Mothballed"):
        paint[f"{semantic}_{condition}"] = require(
            f"{SHARED_PAINT_ROOT}/MI_LB_Robot_{semantic}_{condition}_v002",
            unreal.MaterialInstanceConstant,
        )


def restored_material_for_slot(slot_name):
    if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:
        return paint["BodyCharcoal_Restored"]
    if "SafetyYellow" in slot_name:
        return paint["SafetyYellow_Restored"]
    if "CairnwellGreen" in slot_name:
        return paint["CairnwellGreen_Restored"]
    if "CairnwellWarmWhite" in slot_name:
        return paint["ServiceGrey_Restored"]
    return None


def set_restored_visual_state(robot):
    changed = 0
    for component in robot.get_components_by_class(unreal.StaticMeshComponent):
        name = normalize(component.get_name())
        if name.startswith("Condition_Mothballed"):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
        elif name.startswith("Condition_Restored"):
            component.set_visibility(True, True)
            component.set_hidden_in_game(False, True)
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or not mesh.get_path_name().startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v042/Meshes/"):
            continue
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            material = restored_material_for_slot(str(slot.get_editor_property("material_slot_name")))
            if material is not None:
                component.set_material(index, material)
                changed += 1
    return changed


moth_location = unreal.Vector(0.0, -300.0, 0.0)
restored_location = unreal.Vector(0.0, 300.0, 0.0)
moth = actors.spawn_actor_from_class(generated_class, moth_location, unreal.Rotator())
restored = actors.spawn_actor_from_class(generated_class, restored_location, unreal.Rotator())
if moth is None or restored is None:
    raise RuntimeError("Could not spawn both CR01 v042 validation instances")
moth.set_actor_label("LB_CR01_v042_Mothballed_SurfacePaint")
restored.set_actor_label("LB_CR01_v042_Restored_SurfacePaint")
for actor in (moth, restored):
    actor.set_editor_property("FaultLatched", True)
    actor.set_editor_property("FaultCode", "VISUAL_VALIDATION_ONLY")
    actor.set_editor_property("BatteryChargePercent", 0.0)
    actor.set_editor_property("BatteryHealthPercent", 0.0)
    actor.set_editor_property("IsEnabled", False)
    actor.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Validation.CR01.v042"),
        unreal.Name("LB.Safety.NonNavigable"),
        unreal.Name("LB.CR01.StowConflictOpen"),
    ])
moth.set_editor_property("ConditionState", "MOTHBALLED")
restored.set_editor_property("ConditionState", "RESTORED")
restored_binding_count = set_restored_visual_state(restored)

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
    actor.set_editor_property("tags", [unreal.Name("LB.Validation.CR01.v042"), unreal.Name("LB.Asset.CandidateNotPromoted")])
    return actor


spawn_mesh("LB_CR01_v042_ValidationFloor", (0.0, 0.0, -7.0), (8.0, 10.0, 0.10), floor_material)
spawn_mesh("LB_CR01_v042_ValidationBackdrop", (-260.0, 0.0, 210.0), (0.10, 10.0, 3.0), wall_material)

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 600.0), unreal.Rotator(-42.0, -32.0, 0.0))
sun.set_actor_label("LB_CR01_v042_KeySun")
sun.get_editor_property("directional_light_component").set_editor_properties({
    "intensity": 2.2, "light_color": unreal.Color(255, 250, 240, 255)
})
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 400.0), unreal.Rotator())
sky.set_actor_label("LB_CR01_v042_Sky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.8)
for label, location, intensity in (
    ("MothFill", (300.0, -430.0, 250.0), 650.0),
    ("RestoredFill", (300.0, 430.0, 250.0), 650.0),
    ("Rim", (-100.0, 0.0, 320.0), 480.0),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_CR01_v042_{label}")
    light.get_editor_property("point_light_component").set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 950.0,
        "light_color": unreal.Color(255, 255, 255, 255),
    })

camera_specs = [
    ("Mothballed_Oblique", (340.0, -690.0, 220.0), (0.0, -300.0, 52.0), 46.0),
    ("Mothballed_Left", (0.0, -790.0, 118.0), (0.0, -300.0, 52.0), 43.0),
    ("Restored_Oblique", (340.0, -90.0, 220.0), (0.0, 300.0, 52.0), 46.0),
    ("Restored_Right", (0.0, 790.0, 118.0), (0.0, 300.0, 52.0), 43.0),
    ("Restored_Front", (490.0, 300.0, 118.0), (0.0, 300.0, 52.0), 43.0),
    ("Restored_Top", (0.0, 300.0, 620.0), (0.0, 300.0, 35.0), 46.0),
]
cameras = []
for suffix, location, target, fov in camera_specs:
    camera_location = unreal.Vector(*location)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
    camera.set_actor_label(f"LB_CR01_v042_CAM_{suffix}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, unreal.Vector(*target)), False)
    camera_component = camera.get_editor_property("camera_component")
    camera_component.set_editor_property("field_of_view", fov)
    settings = camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": -0.3,
    })
    cameras.append(camera.get_actor_label())

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
result = {
    "$schema": "line-boss/audit/lb-cr01-v042-surfacepaint-validation-map",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_FIXED_CAMERA_MAP_BUILT__FRESH_RENDER_AND_PRO_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "blueprint": BP_PATH,
    "instances": [moth.get_actor_label(), restored.get_actor_label()],
    "instance_separation_cm": 600.0,
    "restored_shared_paint_override_count": restored_binding_count,
    "fixed_cameras": cameras,
    "exposure_bias": -0.3,
    "safety_state": "BOTH_DISABLED_ZERO_BATTERY_FAULT_LATCHED_NON_NAVIGABLE",
    "stow_conflict": "OPEN__DEFAULT_POSE_IS_NOT_TRAVEL_AUTHORITY",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V042_SURFACEPAINT_MAP_PASS cameras={len(cameras)} audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
