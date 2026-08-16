"""Build isolated CR01 v065 proof map from accepted PR-004 v006 lighting baseline."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v065_PR004Lighting"
BP_PATH = "/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"
PAINT_ROOT = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v004"
AUDIT = ROOT / "Saved/Audits/lb_cr01_v065_pr004_lighting_validation_map.json"

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
if not assets.duplicate_asset(BASE_MAP, MAP):
    raise RuntimeError(f"Could not duplicate {BASE_MAP} -> {MAP}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load isolated validation map {MAP}")

blueprint = require(BP_PATH, unreal.Blueprint)
generated_class = blueprints.generated_class(blueprint)
if generated_class is None:
    raise RuntimeError("CR01 v065 generated class unavailable")

paint = {}
for semantic in ("BodyCharcoal", "SafetyYellow", "CairnwellGreen", "ServiceGrey", "MarkingWarmWhite"):
    paint[semantic] = require(f"{PAINT_ROOT}/MI_LB_Robot_{semantic}_Restored_v004", unreal.MaterialInstanceConstant)


def restored_material(slot_name):
    if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat")):
        return paint["BodyCharcoal"]
    if any(token in slot_name for token in ("SafetyYellow", "FunctionSafetyYellow", "CairnwellSafetyYellow")):
        return paint["SafetyYellow"]
    if "CairnwellGreen" in slot_name or "RuggedGreen" in slot_name:
        return paint["CairnwellGreen"]
    if "CairnwellWarmWhite" in slot_name:
        return paint["MarkingWarmWhite"]
    if any(token in slot_name for token in ("BrushedSteel", "CarrierSteel", "WearSteel", "HopperPolymer", "DarkServiceMetal")):
        return paint["ServiceGrey"]
    return None


def presentation_actor(authority):
    mounts = authority.get_components_by_class(unreal.ChildActorComponent)
    child = mounts[0].get_editor_property("child_actor") if len(mounts) == 1 else None
    if child is None:
        raise RuntimeError(f"Authority {authority.get_actor_label()} has no presentation child")
    return child


def restore_and_deploy(presentation):
    bindings = 0
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
        path = mesh.get_path_name()
        if not (path.startswith("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v059/Meshes/")
                or path.startswith("/Game/LineBoss/Robots/Shared/RP01/")):
            continue
        for index, slot in enumerate(mesh.get_editor_property("static_materials")):
            slot_name = str(slot.get_editor_property("material_slot_name"))
            material = paint["BodyCharcoal"] if name == "PVT_FrontBrushLift" and index == 0 else restored_material(slot_name)
            if material is not None:
                component.set_material(index, material)
                bindings += 1
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
            raise RuntimeError(f"Missing deployed pivot {name}")
        if location is not None:
            component.set_editor_property("relative_location", location)
        if rotation is not None:
            component.set_editor_property("relative_rotation", rotation)
    return bindings


moth = actors.spawn_actor_from_class(generated_class, unreal.Vector(-6100.0, -3300.0, 56.0), unreal.Rotator(0.0, 0.0, 0.0))
restored = actors.spawn_actor_from_class(generated_class, unreal.Vector(-6100.0, -2850.0, 56.0), unreal.Rotator(0.0, 0.0, 0.0))
if moth is None or restored is None:
    raise RuntimeError("Could not spawn CR01 v065 proof actors")
moth.set_actor_label("LB_CR01_v065_PR004_Mothballed")
restored.set_actor_label("LB_CR01_v065_PR004_RestoredDeployed")
for actor in (moth, restored):
    actor.set_editor_property("tags", [
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Validation.CR01.v065.PR004Lighting"),
        unreal.Name("LB.CR01.Authority.ProjectModule"),
    ])
restored_bindings = restore_and_deploy(presentation_actor(restored))

camera_specs = [
    ("Mothballed_Oblique", (-5550.0, -3650.0, 245.0), (-6100.0, -3300.0, 62.0), 48.0),
    ("Mothballed_Left", (-6100.0, -3900.0, 145.0), (-6100.0, -3300.0, 58.0), 44.0),
    ("Restored_Oblique", (-5550.0, -2500.0, 245.0), (-6100.0, -2850.0, 62.0), 48.0),
    ("Restored_Front", (-5500.0, -2850.0, 145.0), (-6100.0, -2850.0, 58.0), 44.0),
]
camera_labels = []
for suffix, location, target, fov in camera_specs:
    position = unreal.Vector(*location)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, position, unreal.Rotator())
    camera.set_actor_label(f"LB_CR01_v065_PR004_CAM_{suffix}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    component = camera.get_editor_property("camera_component")
    component.set_editor_property("field_of_view", fov)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.25,
    })
    camera_labels.append(camera.get_actor_label())

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({
    "$schema": "line-boss/audit/lb-cr01-v065-pr004-lighting-validation-map",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "ISOLATED_ACCEPTED_LIGHTING_PROOF_MAP_BUILT__FRESH_RENDER_AND_PRO_REVIEW_REQUIRED__NOT_PROMOTED",
    "accepted_base_map_preserved": BASE_MAP,
    "validation_map": MAP,
    "blueprint": BP_PATH,
    "actors": [moth.get_actor_label(), restored.get_actor_label()],
    "restored_material_override_count": restored_bindings,
    "fixed_cameras": camera_labels,
    "line_boss_in_world_branding_added": False,
    "promotion_authorized": False,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V065_PR004_MAP_PASS cameras={len(camera_labels)} audit={AUDIT}")
