"""Bind native PR-008 feed/punch/cut authority and a compact live HMI in isolated v060."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060"
PREFIX = "LB_PR008_V060_"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_runtime_candidate_v060.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v059 to v060")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v060 map")
    unreal.log("LINE_BOSS_PR008_V060_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)
all_actors = list(actors_api.get_all_level_actors())
if any(isinstance(actor, unreal.LBPR008Station) for actor in all_actors):
    raise RuntimeError("Unexpected inherited PR-008 native authority")

station = actors_api.spawn_actor_from_class(unreal.LBPR008Station, unreal.Vector(), unreal.Rotator())
station.set_actor_label(PREFIX + "Station_PR-008")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR008", "LB.Authority.PR008.Native", "LB.Asset.Candidate.v060",
    "LB.Asset.CandidateNotPromoted", "LB.Process.ServoBlanking")]
components = {
    component.get_name(): component
    for component in station.get_components_by_class(unreal.SceneComponent)
}

bindings_spec = {
    "PR008_FeedRollLowerMover": ["LB_PR008_V058_PR008_FeedRollLower_01"],
    "PR008_FeedRollUpperMover": ["LB_PR008_V058_PR008_FeedRollUpper_01"],
    "PR008_TelescopeMover": [
        "LB_PR008_V058_PR008_TelescopeBeam_01",
        "LB_PR008_V058_PR008_TelescopeBeam_01_Drive",
        "LB_PR008_V058_PR008_TelescopeBeam_02",
        "LB_PR008_V058_PR008_TelescopeBeam_02_Drive",
        "LB_PR008_V058_PR008_TelescopeBeam_03",
        "LB_PR008_V058_PR008_TelescopeBeam_03_Drive",
    ],
    "PR008_PressSlideMover": ["LB_PR008_V058_PR008_PressSlide"],
    "PR008_PrePunchMover": ["LB_PR008_V058_PR008_PrePunchDie"],
    "PR008_GuillotineMover": ["LB_PR008_V058_PR008_GuillotineBeam"],
    "PR008_OutfeedRollMover": ["LB_PR008_V058_PR008_OutfeedRoll_01"],
}
by_label = {actor.get_actor_label(): actor for actor in all_actors}
bindings = []
for component_name, actor_labels in bindings_spec.items():
    component = components.get(component_name)
    first_actor = by_label.get(actor_labels[0])
    if component is None or first_actor is None:
        raise RuntimeError(f"Missing runtime mover datum {component_name} / {actor_labels[0]}")
    component.set_world_location(first_actor.get_actor_location(), False, False)
    component.set_world_rotation(first_actor.get_actor_rotation(), False, False)
    for actor_label in actor_labels:
        actor = by_label.get(actor_label)
        if actor is None:
            raise RuntimeError(f"Missing PR-008 runtime actor {actor_label}")
        if isinstance(actor, unreal.StaticMeshActor):
            actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        attached = actor.attach_to_component(
            component,
            unreal.Name(),
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD,
            False,
        )
        if not attached:
            raise RuntimeError(f"Could not bind {actor_label} to {component_name}")
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Authority.PR008.NativeBound"),
            unreal.Name("LB.Asset.Candidate.v060"),
        ]
        bindings.append({"actor": actor_label, "mover": component_name})

dark = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_FoundryCharcoal_v001"
)
steel = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Candidate_v001/Materials/M_PR008_WorkedSteel_v001"
)
if not dark or not steel:
    raise RuntimeError("Missing controlled PR-008 HMI materials")
display_mesh = library.load_asset(
    "/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling/SM_LB_HMI04_DisplaySurface"
)
cube_mesh = library.load_asset("/Engine/BasicShapes/Cube")
if not display_mesh or not cube_mesh:
    raise RuntimeError("Missing compact shared HMI meshes")

hmi = []


def hmi_mesh(label, mesh, location, scale, material=None):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "HMI_" + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v060"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR008"), unreal.Name("LB.Module.CompactTouchHMI")]
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    component.set_collision_profile_name(unreal.Name("BlockAll"))
    component.set_editor_property("can_ever_affect_navigation", True)
    hmi.append(actor)
    return actor


hmi_mesh("TouchBase", cube_mesh, (-430, -2600, 12), (0.62, 0.46, 0.24), dark)
hmi_mesh("TouchPost", cube_mesh, (-430, -2600, 62), (0.12, 0.12, 0.76), steel)
hmi_mesh("TouchBezel", cube_mesh, (-430, -2607, 119), (0.58, 0.12, 0.44), dark)
hmi_mesh("DisplaySurface", display_mesh, (-430, -2614, 119), (0.78, 0.72, 0.78))


def text(label, value, z, size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(-430, -2625, z), unreal.Rotator(yaw=-90)
    )
    actor.set_actor_label(PREFIX + "HMI_Text_" + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v060"), unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Station.PR008.HMI")]
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
    text("Station", "PR-008  SERVO BLANKING", 120, 4.0, unreal.Color(225, 235, 232, 255)),
    text("State", "THREADING | BLANKS 0 | 1450 mm", 110, 2.8, unreal.Color(225, 166, 0, 255)),
]

station.set_control_power(True)
station.set_guards_closed(True)
station.set_strip_available(True)
station.set_feed_servo_healthy(True)
station.set_hydraulic_pressure(215.0)
station.set_scrap_bin_fill(18.0)
station.set_blank_outfeed_clear(True)
station.set_blank_recipe(1450.0, 18.0)
if not station.start_line():
    raise RuntimeError("Native PR-008 authority refused coherent validation start")


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR008.v060"),
        unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False
    )
    actor.camera_component.set_editor_properties(
        {"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True}
    )
    return actor


cameras = [
    camera("RuntimeHMI", (-430, -2940, 145), (-430, -2610, 120), 42),
    camera("RuntimeProcess", (-1420, -3380, 540), (-400, -2000, 165), 54),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-runtime-candidate-v060/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_PR008_RUNTIME_BINDING_AND_LIVE_HMI_ASSEMBLY_PASS__PIE_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "authority": station.get_actor_label(),
    "binding_count": len(bindings),
    "bindings": bindings,
    "initial_process_state": {
        "state": "Threading",
        "target_blank_length_mm": 1450.0,
        "line_speed_metres_per_minute": 18.0,
        "hydraulic_pressure_bar": 215.0,
        "scrap_bin_fill_percent": 18.0,
        "guards_closed": True,
        "strip_available": True,
        "feed_servo_healthy": True,
        "blank_outfeed_clear": True,
    },
    "save_format_version": 6,
    "automation_test": "LineBoss.PressShop.PR008.RuntimeAndSave",
    "hmi_module_count": len(hmi),
    "hmi_text_row_count": len(hmi_text),
    "fixed_runtime_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V060_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
