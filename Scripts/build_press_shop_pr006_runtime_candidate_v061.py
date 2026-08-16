"""Bind native PR-006 cassette/roll-gap authority and live HMI on the current connected line."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061"
PREFIX = "LB_PR006_V061_"
AUDIT = ROOT / "Saved/Audits/press_shop_pr006_runtime_candidate_v061.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v060 to v061")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v061 map")
    unreal.log("LINE_BOSS_PR006_V061_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)
all_actors = list(actors_api.get_all_level_actors())
if any(isinstance(actor, unreal.LBPR006Station) for actor in all_actors):
    raise RuntimeError("Unexpected inherited PR-006 native authority")

station = actors_api.spawn_actor_from_class(unreal.LBPR006Station, unreal.Vector(), unreal.Rotator())
station.set_actor_label(PREFIX + "Station_PR-006")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR006", "LB.Authority.PR006.Native", "LB.Asset.Candidate.v061",
    "LB.Asset.CandidateNotPromoted", "LB.Process.PrecisionLevelling")]
components = {
    component.get_name(): component
    for component in station.get_components_by_class(unreal.SceneComponent)
}
by_label = {actor.get_actor_label(): actor for actor in all_actors}

bindings_spec = {}
for index in range(1, 10):
    bindings_spec[f"PR006_LowerRollMover_{index:02d}"] = [f"LB_PR006_V054_PR006_LowerRoll_{index:02d}"]
for index in range(1, 11):
    bindings_spec[f"PR006_UpperRollMover_{index:02d}"] = [f"LB_PR006_V054_PR006_UpperRoll_{index:02d}"]
bindings_spec["PR006_UpperCassetteMover"] = [
    "LB_PR006_V054_PR006_UpperCassette_Operator",
    "LB_PR006_V054_PR006_UpperCassette_Drive",
]
for index, suffix in enumerate(("-1_-1", "-1_+1", "+1_-1", "+1_+1"), 1):
    bindings_spec[f"PR006_GapCylinderMover_{index:02d}"] = [f"LB_PR006_V054_PR006_GapCylinder_{suffix}"]
for index in range(1, 4):
    bindings_spec[f"PR006_DriveMotorMover_{index:02d}"] = [f"LB_PR006_V054_PR006_DriveMotor_{index:02d}"]

bindings = []
for component_name, labels in bindings_spec.items():
    component = components.get(component_name)
    datum_actor = by_label.get(labels[0])
    if component is None or datum_actor is None:
        raise RuntimeError(f"Missing runtime mover datum {component_name} / {labels[0]}")
    component.set_world_location(datum_actor.get_actor_location(), False, False)
    component.set_world_rotation(datum_actor.get_actor_rotation(), False, False)
    for label in labels:
        actor = by_label.get(label)
        if actor is None:
            raise RuntimeError(f"Missing PR-006 runtime actor {label}")
        if isinstance(actor, unreal.StaticMeshActor):
            actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        attached = actor.attach_to_component(
            component, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
        if not attached:
            raise RuntimeError(f"Could not bind {label} to {component_name}")
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Authority.PR006.NativeBound"), unreal.Name("LB.Asset.Candidate.v061")]
        bindings.append({"actor": label, "mover": component_name})

dark = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_CharcoalFrame_v001"
)
steel = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR006/Candidate_v001/Materials/M_PR006_RollSteel_v001"
)
display_mesh = library.load_asset(
    "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling/SM_LB_HMI04_DisplaySurface"
)
cube_mesh = library.load_asset("/Engine/BasicShapes/Cube")
if not all((dark, steel, display_mesh, cube_mesh)):
    raise RuntimeError("Missing controlled PR-006 HMI assets")

hmi = []


def hmi_mesh(label, mesh, location, scale, material=None):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "HMI_" + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v061"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR006"), unreal.Name("LB.Module.CompactTouchHMI")]
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", True)
    hmi.append(actor)


hmi_mesh("TouchBase", cube_mesh, (-1750, -2600, 12), (0.62, 0.46, 0.24), dark)
hmi_mesh("TouchPost", cube_mesh, (-1750, -2600, 62), (0.12, 0.12, 0.76), steel)
hmi_mesh("TouchBezel", cube_mesh, (-1750, -2607, 119), (0.60, 0.12, 0.44), dark)
hmi_mesh("DisplaySurface", display_mesh, (-1750, -2614, 119), (0.80, 0.72, 0.78))


def text(label, value, z, size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(-1750, -2625, z), unreal.Rotator(yaw=-90)
    )
    actor.set_actor_label(PREFIX + "HMI_Text_" + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v061"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR006.HMI")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


hmi_text = [
    text("Brand", "CAIRNWELL / MOORCROSS", 130, 3.5, unreal.Color(45, 205, 155, 255)),
    text("Station", "PR-006  PRECISION LEVELLER", 120, 3.7, unreal.Color(225, 235, 232, 255)),
    text("State", "CALIBRATING | GAP 1.80 mm | LOAD 8%", 110, 2.65, unreal.Color(225, 166, 0, 255)),
]

station.set_control_power(True)
station.set_guards_closed(True)
station.set_strip_available(True)
station.set_cassette_locked(True)
station.set_drives_healthy(True)
station.set_leveller_recipe(unreal.Name("L-1500-A"), 1.20, 1.15, 16.0)
if not station.start_line():
    raise RuntimeError("Native PR-006 authority refused coherent validation start")


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR006.v061"),
        unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties(
        {"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True}
    )
    return actor


cameras = [
    camera("RuntimeHMI", (-1750, -2940, 145), (-1750, -2610, 120), 42),
    camera("RuntimeProcess", (-900, -3100, 410), (-1700, -2000, 130), 50),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr006-runtime-candidate-v061/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_PR006_RUNTIME_BINDING_AND_LIVE_HMI_ASSEMBLY_PASS__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "authority": station.get_actor_label(),
    "binding_count": len(bindings),
    "bindings": bindings,
    "initial_process_state": {
        "state": "Calibrating", "cassette_id": "L-1500-A",
        "strip_thickness_mm": 1.20, "target_roll_gap_mm": 1.15,
        "initial_roll_gap_mm": 1.80, "line_speed_metres_per_minute": 16.0,
        "guards_closed": True, "strip_available": True,
        "cassette_locked": True, "drives_healthy": True,
    },
    "save_format_version": 7,
    "automation_test": "LineBoss.PressShop.PR006.RuntimeAndSave",
    "hmi_module_count": len(hmi),
    "hmi_text_row_count": len(hmi_text),
    "fixed_runtime_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR006_V061_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
