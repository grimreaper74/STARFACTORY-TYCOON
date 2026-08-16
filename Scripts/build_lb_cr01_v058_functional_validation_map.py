"""Build fixed-camera validation map for functional CR01 v058 authority/presentation integration."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v058_FunctionalAuthority"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v058/Blueprints/BP_LB_CR01_CleaningAMR_v058"
PAINT_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v003"
AUDIT = ROOT / "Saved/Audits/lb_cr01_v058_functional_validation_map.json"

assets = unreal.EditorAssetLibrary
blueprints = unreal.BlueprintEditorLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def require(path, cls=None):
    asset = assets.load_asset(path)
    if asset is None or (cls is not None and not isinstance(asset, cls)):
        raise RuntimeError(f"Missing required asset {path}")
    return asset


def normalize(value):
    name = str(value)
    for suffix in ("_0", "_GEN_VARIABLE"):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return name


if assets.does_asset_exist(MAP):
    raise RuntimeError(f"Refusing to overwrite preserved validation map {MAP}")
blueprint = require(BP_PATH, unreal.Blueprint)
generated_class = blueprints.generated_class(blueprint)
if generated_class is None or not levels.new_level(MAP):
    raise RuntimeError("Could not create v058 functional validation map")

paint = {}
for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey", "MarkingWarmWhite"):
    for condition in ("Restored", "Mothballed"):
        paint[f"{semantic}_{condition}"] = require(
            f"{PAINT_ROOT}/MI_LB_Robot_{semantic}_{condition}_v003", unreal.MaterialInstanceConstant)


def restored_material(slot_name):
    if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):
        return paint["BodyCharcoal_Restored"]
    if any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):
        return paint["SafetyYellow_Restored"]
    if "CairnwellGreen" in slot_name or "RuggedGreen" in slot_name:
        return paint["CairnwellGreen_Restored"]
    if any(token in slot_name for token in ("CairnwellWarmWhite", "BrushedSteel", "CarrierSteel", "WearSteel")):
        return paint["ServiceGrey_Restored"]
    return None


def presentation_actor(authority):
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    child = mounts[0].get_editor_property("child_actor") if len(mounts) == 1 else None
    if child is None:
        raise RuntimeError(f"Authority {authority.get_actor_label()} has no v056 presentation")
    return child


def set_restored_deployed(presentation):
    restored_bindings = 0
    components = {normalize(c.get_name()): c for c in presentation.get_components_by_class(unreal.SceneComponent)}
    for component in presentation.get_components_by_class(unreal.StaticMeshComponent):
        name = normalize(component.get_name())
        if name.startswith("Condition_Mothballed"):
            component.set_visibility(False, True)
            component.set_hidden_in_game(True, True)
        elif name.startswith("Condition_Restored"):
            component.set_visibility(True, True)
            component.set_hidden_in_game(False, True)
        mesh = component.get_editor_property("static_mesh")
        if mesh is None:
            continue
        mesh_path = mesh.get_path_name()
        if not (mesh_path.startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v052/Meshes/")
                or mesh_path.startswith("/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Meshes/")):
            continue
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            material = restored_material(str(slot.get_editor_property("material_slot_name")))
            if material is not None:
                component.set_material(index, material)
                restored_bindings += 1
    pose = {
        "PVT_FrontBrushLift": (unreal.Vector(63.5, 0.0, 16.5), None),
        "PVT_SideBrushArm_L": (None, unreal.Rotator(0.0, -65.0, 0.0)),
        "PVT_SideBrushArm_R": (None, unreal.Rotator(0.0, 65.0, 0.0)),
        "PVT_SideBrushLift_L": (unreal.Vector(7.0, -17.0, -5.0), None),
        "PVT_SideBrushLift_R": (unreal.Vector(7.0, 17.0, -5.0), None),
        "PVT_ScrubDeckLift": (unreal.Vector(4.0, 0.0, 18.5), None),
        "PVT_SqueegeeLift": (unreal.Vector(-69.0, 0.0, 16.5), None),
    }
    for name, (location, rotation) in pose.items():
        component = components.get(name)
        if component is None:
            raise RuntimeError(f"Missing deployed presentation pivot {name}")
        if location is not None:
            component.set_editor_property("relative_location", location)
        if rotation is not None:
            component.set_editor_property("relative_rotation", rotation)
    return restored_bindings


moth = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, -300.0, 56.0), unreal.Rotator())
restored = actors.spawn_actor_from_class(generated_class, unreal.Vector(0.0, 300.0, 56.0), unreal.Rotator())
if moth is None or restored is None:
    raise RuntimeError("Could not spawn both v058 authority instances")
moth.set_actor_label("LB_CR01_v058_Mothballed_Authority")
restored.set_actor_label("LB_CR01_v058_RestoredDeployed_Authority")
for actor in (moth, restored):
    actor.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Validation.CR01.v058"),
        unreal.Name("LB.CR01.Authority.ProjectModule"), unreal.Name("LB.Safety.NonNavigableValidation"),
    ])
restored_bindings = set_restored_deployed(presentation_actor(restored))

cube = require("/Engine/BasicShapes/Cube.Cube", unreal.StaticMesh)
floor_material = require("/Game/LineBoss/Materials/M_LB_FactoryConcrete", unreal.MaterialInterface)
wall_material = require("/Game/LineBoss/Materials/M_LB_ShellCharcoal", unreal.MaterialInterface)


def spawn_mesh(label, location, scale, material):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    mesh_component = actor.get_editor_property("static_mesh_component")
    mesh_component.set_static_mesh(cube)
    mesh_component.set_material(0, material)
    return actor


spawn_mesh("LB_CR01_v058_ValidationFloor", (0.0, 0.0, -7.0), (8.0, 10.0, 0.10), floor_material)
spawn_mesh("LB_CR01_v058_ValidationBackdrop", (-260.0, 0.0, 210.0), (0.10, 10.0, 3.0), wall_material)

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 600.0), unreal.Rotator(-42.0, -32.0, 0.0))
sun.set_actor_label("LB_CR01_v058_KeySun")
sun.get_editor_property("directional_light_component").set_editor_properties({"intensity": 1.15, "light_color": unreal.Color(255, 250, 240, 255)})
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 400.0), unreal.Rotator())
sky.set_actor_label("LB_CR01_v058_Sky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.42)
for label, location, intensity in (
    ("MothFill", (300.0, -430.0, 250.0), 260.0),
    ("RestoredFill", (300.0, 430.0, 250.0), 260.0),
    ("Rim", (-100.0, 0.0, 320.0), 220.0),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    light.set_actor_label(f"LB_CR01_v058_{label}")
    light.get_editor_property("point_light_component").set_editor_properties({"intensity": intensity, "attenuation_radius": 950.0})

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
    position = unreal.Vector(*location)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    camera.set_actor_label(f"LB_CR01_v058_CAM_{suffix}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    camera_component = camera.get_editor_property("camera_component")
    camera_component.set_editor_property("field_of_view", fov)
    settings = camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True, "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True, "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": -0.75,
    })
    cameras.append(camera.get_actor_label())

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-cr01-v058-functional-validation-map",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FUNCTIONAL_AUTHORITY_FIXED_CAMERA_MAP_BUILT__FRESH_RENDER_AND_PRO_REVIEW_REQUIRED__NOT_PROMOTED",
    "map": MAP, "blueprint": BP_PATH,
    "instances": [moth.get_actor_label(), restored.get_actor_label()],
    "authority_actor_z_cm": 56.0,
    "presentation_visual_ground_z_cm": 0.0,
    "restored_material_override_count": restored_bindings,
    "restored_instance_pose": "DEPLOYED_VISUAL_VALIDATION_POSE",
    "fixed_cameras": cameras,
    "runtime_functional_automation": "PASS__LineBoss.SupportRobots.CR01.FunctionalRuntime",
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V058_FUNCTIONAL_MAP_PASS cameras={len(cameras)} audit={AUDIT}")
