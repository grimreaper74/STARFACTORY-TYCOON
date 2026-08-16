"""Bind the native PR-007 controller to the accepted v056 visual direction."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057"
PREFIX = "LB_PR007_V057_"
AUDIT = ROOT / "Saved/Audits/press_shop_pr007_runtime_candidate_v057.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057.umap"
if not map_file.exists():
    if not lib.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v056")
    if not lib.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v057 map")
    unreal.log("LINE_BOSS_PR007_V057_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

all_actors = list(actors_api.get_all_level_actors())
for actor in all_actors:
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)
all_actors = list(actors_api.get_all_level_actors())
if any(isinstance(actor, unreal.LBPR007Station) for actor in all_actors):
    raise RuntimeError("Unexpected inherited native PR-007 authority")

station = actors_api.spawn_actor_from_class(unreal.LBPR007Station, unreal.Vector(), unreal.Rotator())
station.set_actor_label(PREFIX + "Station_PR-007")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR007", "LB.Authority.PR007.Native", "LB.Asset.Candidate.v057",
    "LB.Asset.CandidateNotPromoted", "LB.Process.WashLube")]
components = {component.get_name(): component for component in station.get_components_by_class(unreal.SceneComponent)}

bindings_spec = {
    "LB_PR007_V055_PR007_HoodWash": "PR007_WashHoodMover",
    "LB_PR007_V055_PR007_WashPumpMotor": "PR007_WashPumpMover",
    "LB_PR007_V055_PR007_LubePumpMotor": "PR007_LubePumpMover",
    "LB_PR007_V055_PR007_InfeedRollLower": "PR007_FeedRollerMover",
    "LB_PR007_V055_PR007_WashRollLower": "PR007_WashRollerMover",
    "LB_PR007_V055_PR007_LubeRollLower": "PR007_LubeRollerMover",
    "LB_PR007_V055_PR007_OutfeedRollLower": "PR007_OutfeedRollerMover",
}
by_label = {actor.get_actor_label(): actor for actor in all_actors}
bindings = []
for label, component_name in bindings_spec.items():
    actor = by_label.get(label)
    component = components.get(component_name)
    if actor is None or component is None:
        raise RuntimeError(f"Missing runtime binding {label} -> {component_name}")
    component.set_world_location(actor.get_actor_location(), False, False)
    component.set_world_rotation(actor.get_actor_rotation(), False, False)
    if isinstance(actor, unreal.StaticMeshActor):
        actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    attached = actor.attach_to_component(
        component, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    if not attached:
        raise RuntimeError(f"Could not bind {label} to {component_name}")
    actor.tags = list(actor.tags) + [unreal.Name("LB.Authority.PR007.NativeBound"), unreal.Name("LB.Asset.Candidate.v057")]
    bindings.append({"actor": label, "mover": component_name})

# Persist a healthy priming state so PIE proves the actual state transition and HMI binding.
station.set_control_power(True)
station.set_guards_closed(True)
station.set_strip_threaded(True)
station.set_mist_extraction_healthy(True)
station.set_fluid_levels(82.0, 76.0)
station.set_filter_differential(0.34)
if not station.start_line():
    raise RuntimeError("Native PR-007 authority refused coherent validation start")

# Keep the selected compact pedestal, but make its information genuinely legible at PC distance.
for label, scale in {
    "LB_PR007_V056_HMI_TouchBase": unreal.Vector(0.70, 0.52, 0.24),
    "LB_PR007_V056_HMI_TouchBezel": unreal.Vector(0.65, 0.12, 0.48),
}.items():
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing compact HMI presentation actor {label}")
    actor.set_actor_scale3d(scale)
for label, world_size in {
    "LB_PR007_V056_HMI_Text_Brand": 3.8,
    "LB_PR007_V056_HMI_Text_Station": 4.4,
    "LB_PR007_V056_HMI_Text_State": 3.25,
}.items():
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing compact HMI text actor {label}")
    actor.text_render.set_world_size(world_size)

def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR007.v057"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({"field_of_view": fov, "aspect_ratio": 16 / 9, "constrain_aspect_ratio": True})
    return actor

cameras = [
    camera("RuntimeHMI", (-2475, -2825, 145), (-2475, -2520, 122), 42),
    camera("RuntimeServiceMotion", (-3400, -1200, 330), (-2750, -1780, 145), 50),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
payload = {
    "$schema": "line-boss/audit/press-shop-pr007-runtime-candidate-v057/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_PR007_RUNTIME_BINDING_ASSEMBLY_PASS__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "authority": station.get_actor_label(),
    "binding_count": len(bindings),
    "bindings": bindings,
    "initial_process_state": {
        "state": "Priming", "wash_level_percent": 82.0, "lube_level_percent": 76.0,
        "filter_differential_bar": 0.34, "guards_closed": True,
        "strip_threaded": True, "mist_extraction_healthy": True,
    },
    "automation_test": "LineBoss.PressShop.PR007.RuntimeAndSave",
    "fixed_runtime_cameras": [camera_actor.get_actor_label() for camera_actor in cameras],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR007_V057_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
