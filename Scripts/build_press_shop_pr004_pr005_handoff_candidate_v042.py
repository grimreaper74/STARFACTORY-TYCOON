"""Bind native PR-005 and transactional material flow to existing full-map modules."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_pr005_handoff_candidate_v042.json"
PREFIX = "LB_PR004_PR005_V042_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)


def names(*values):
    return [unreal.Name(value) for value in values]


all_actors = list(actors_api.get_all_level_actors())
pr004 = next((actor for actor in all_actors if isinstance(actor, unreal.LBPR004Station)), None)
if pr004 is None:
    raise RuntimeError("Existing native PR-004 station was not found")
if any(isinstance(actor, unreal.LBPR005Station) for actor in all_actors):
    raise RuntimeError("Unexpected inherited native PR-005 authority")

pr005 = actors_api.spawn_actor_from_class(
    unreal.LBPR005Station, unreal.Vector(-4000.0, -2000.0, 0.0), unreal.Rotator())
pr005.set_actor_label(PREFIX + "Station_PR-005")
pr005.tags = names(
    "LB.Station.PR005", "LB.Authority.PR005.Native", "LB.Production.Traceability",
    "LB.Asset.Candidate.v042", "LB.Asset.CandidateNotPromoted")

components = {component.get_name(): component for component in pr005.get_components_by_class(unreal.SceneComponent)}
required_components = {
    "coil_car": "PR005_CoilCarMover",
    "mandrel": "PR005_MandrelMover",
    "payoff": "PR005_PayoffCoilMover",
    "strip": "PR005_StripMover",
    "crop_clamp": "PR005_CropClampMover",
    "crop_shear": "PR005_CropShearMover",
    "crop_piece": "PR005_CropPieceMover",
}
if any(name not in components for name in required_components.values()):
    raise RuntimeError(f"Missing native PR-005 mover components: {sorted(components)}")

payoff_actor = next((actor for actor in all_actors
                     if actor.get_actor_label() == "LB_INT_PR005_PayoffCoil_PR-005_PayoffCoilTransferMover"), None)
if payoff_actor is None:
    raise RuntimeError("Existing PR-005 payoff-coil presentation actor was not found")


def mover_key(label):
    if "CoilCar_" in label and "Mover" in label:
        return "coil_car"
    if "Mandrel_" in label and "Mover" in label:
        return "mandrel"
    if "PayoffCoil_PR-005_PayoffCoilTransferMover" in label:
        return "payoff"
    if "ContinuousStrip_PR-005_StripTravelWitnessMover" in label:
        return "strip"
    if "CropShear_PR-005_CropClampMover" in label:
        return "crop_clamp"
    if "CropShear_PR-005_CropShearMover" in label:
        return "crop_shear"
    if "CropShear_PR-005_CropPieceMover" in label:
        return "crop_piece"
    return None


bindings = []
for actor in all_actors:
    label = actor.get_actor_label()
    key = mover_key(label)
    if key is None:
        continue
    if isinstance(actor, unreal.StaticMeshActor):
        actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    attached = actor.attach_to_component(
        components[required_components[key]], unreal.Name(),
        unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD, False)
    if not attached:
        raise RuntimeError(f"Could not bind {label} to {required_components[key]}")
    actor.tags = list(actor.tags) + names("LB.Authority.PR005.NativeBound", "LB.Asset.Candidate.v042")
    bindings.append({"actor": label, "mover": required_components[key]})

pr005.set_editor_property("payoff_coil_presentation_actors", [payoff_actor])

flow = actors_api.spawn_actor_from_class(
    unreal.LBPressShopMaterialFlowController, unreal.Vector(-4525.0, -2000.0, 20.0), unreal.Rotator())
flow.set_actor_label(PREFIX + "MaterialFlowController_PR004_PR005")
flow.tags = names(
    "LB.Authority.MaterialFlow.PR004.PR005", "LB.Production.Traceability",
    "LB.Asset.Candidate.v042", "LB.Asset.CandidateNotPromoted")
flow.set_editor_property("pr004_station", pr004)
flow.set_editor_property("pr005_station", pr005)


def camera(label, location, target, fov, bias):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = names(
        "LB.Camera.Validation", "LB.Camera.Fixed.PR004PR005.v042",
        "LB.Asset.Candidate.v042", "LB.Asset.CandidateNotPromoted")
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
    camera("HandoffWide", (-5550.0, -650.0, 880.0), (-4550.0, -2000.0, 210.0), 50.0, 0.08),
    camera("PR005PayoffLoaded", (-5000.0, -900.0, 480.0), (-4010.0, -2000.0, 165.0), 40.0, 0.10),
]

if len(bindings) != 15:
    raise RuntimeError(f"Expected 15 native mover bindings, found {len(bindings)}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-pr005-handoff-candidate-v042/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_PR005_AND_TRACEABLE_HANDOFF_BOUND__PIE_VISUAL_AND_FULL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041",
    "map": MAP,
    "pr004": pr004.get_actor_label(),
    "pr005": pr005.get_actor_label(),
    "flow_controller": flow.get_actor_label(),
    "payoff_presentation": payoff_actor.get_actor_label(),
    "native_mover_binding_count": len(bindings),
    "native_mover_bindings": bindings,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_PR005_HANDOFF_V042_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
