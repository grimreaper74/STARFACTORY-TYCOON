"""Bind the detailed PR-008 Modules 01-10 to one native authority in isolated v074."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008Module10Candidate_v073"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"
PREFIX = "LB_PR008_V074_"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_native_runtime_candidate_v074.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate protected v073 direction checkpoint to isolated v074")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v074 map")
    unreal.log("LINE_BOSS_PR008_V074_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

all_actors = list(actors_api.get_all_level_actors())
obsolete_v060 = [actor for actor in all_actors if actor.get_actor_label().startswith("LB_PR008_V060_")]
for actor in obsolete_v060:
    actors_api.destroy_actor(actor)
all_actors = list(actors_api.get_all_level_actors())
inherited_authorities = [
    actor for actor in all_actors if isinstance(actor, unreal.LBPR008Station)]
if inherited_authorities:
    raise RuntimeError("Unexpected inherited PR-008 native authority in v074 base: "
                       + ", ".join(actor.get_actor_label() for actor in inherited_authorities))

by_label = {actor.get_actor_label(): actor for actor in all_actors}


def require_actor(label):
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing detailed PR-008 presentation actor {label}")
    return actor


station = actors_api.spawn_actor_from_class(unreal.LBPR008Station, unreal.Vector(), unreal.Rotator())
station.set_actor_label(PREFIX + "Station_PR-008_NativeAuthority")
station.tags = [unreal.Name(value) for value in (
    "LB.Station.PR008", "LB.Authority.PR008.Native", "LB.Authority.RemoteHMI.SharedGateway",
    "LB.Asset.Candidate.v074", "LB.Asset.CandidateNotPromoted", "LB.Process.ServoBlanking")]
components = {
    component.get_name(): component
    for component in station.get_components_by_class(unreal.SceneComponent)
}

bindings_spec = {
    "PR008_FeedRollLowerMover": [
        "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Lower_01",
        "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Lower_01",
    ],
    "PR008_FeedRollUpperMover": [
        "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedRoll_Upper_01",
        "LB_PR008_V066_SM_CA_MW_PR008_ServoFeedSleeve_Upper_01",
    ],
    "PR008_EdgeGuideOperatorMover": ["LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Operator"],
    "PR008_EdgeGuideDriveMover": ["LB_PR008_V065_SM_CA_MW_PR008_EdgeGuide_Drive"],
    "PR008_TelescopeStage1Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage1_01"],
    "PR008_TelescopeStage2Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage2_01"],
    "PR008_TelescopeStage3Mover": ["LB_PR008_V067_SM_CA_MW_PR008_TelescopeStage3_01"],
    "PR008_PrePunchMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchSlide_01"],
    "PR008_ScrapFlapMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchScrapFlap_01"],
    "PR008_ServiceDoorOperatorMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Operator"],
    "PR008_ServiceDoorDriveMover": ["LB_PR008_V068_SM_CA_MW_PR008_PrePunchServiceDoor_Drive"],
    "PR008_GuillotineMover": ["LB_PR008_V069_SM_CA_MW_PR008_ShearBladeBeam_01"],
}

bindings = []
for component_name, actor_labels in bindings_spec.items():
    component = components.get(component_name)
    if component is None:
        raise RuntimeError(f"Missing native PR-008 motion contract {component_name}")
    datum_actor = require_actor(actor_labels[0])
    component.set_world_location(datum_actor.get_actor_location(), False, False)
    component.set_world_rotation(datum_actor.get_actor_rotation(), False, False)
    for actor_label in actor_labels:
        actor = require_actor(actor_label)
        if isinstance(actor, unreal.StaticMeshActor):
            actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        if not actor.attach_to_component(
            component, unreal.Name(), unreal.AttachmentRule.KEEP_WORLD,
            unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False):
            raise RuntimeError(f"Could not attach {actor_label} to {component_name}")
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Authority.PR008.NativeBound"),
            unreal.Name(f"LB.PresentationContract.{component_name}"),
            unreal.Name("LB.Asset.Candidate.v074"),
        ]
        bindings.append({"actor": actor_label, "contract": component_name, "mode": "attached"})

direct_groups = {
    "LB.Presentation.PR008.LoopRoll": [
        f"LB_PR008_V064_SM_CA_MW_PR008_LoopRoll_{index:02d}" for index in range(1, 4)
    ] + [
        f"LB_PR008_V064_SM_CA_MW_PR008_LoopRollSleeve_{index:02d}" for index in range(1, 4)
    ],
    "LB.Presentation.PR008.DischargeRoll": [
        f"LB_PR008_V070_SM_CA_MW_PR008_DischargeRoll_{index:02d}" for index in range(1, 8)
    ],
}
for presentation_tag, actor_labels in direct_groups.items():
    for actor_label in actor_labels:
        actor = require_actor(actor_label)
        if isinstance(actor, unreal.StaticMeshActor):
            actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        actor.tags = list(actor.tags) + [
            unreal.Name("LB.Authority.PR008.NativeBound"), unreal.Name(presentation_tag),
            unreal.Name("LB.Asset.Candidate.v074")]
        bindings.append({"actor": actor_label, "contract": presentation_tag, "mode": "tag_bound_own_pivot"})

interaction_contracts = {
    "LB_PR008_V073_SM_CA_MW_PR008_HMITouchDisplay_01": "LB.HMI.PR008.TouchSurface",
    "LB_PR008_V073_SM_CA_MW_PR008_HMIControls_01": "LB.HMI.PR008.LocalControls",
    "LB_PR008_V073_SM_CA_MW_PR008_HMIEStop_01": "LB.HMI.PR008.EStop",
}
for actor_label, contract_tag in interaction_contracts.items():
    actor = require_actor(actor_label)
    actor.tags = list(actor.tags) + [
        unreal.Name(contract_tag), unreal.Name("LB.Authority.PR008.NativeCommandGateway"),
        unreal.Name("LB.Asset.Candidate.v074")]
    if isinstance(actor, unreal.StaticMeshActor):
        component = actor.static_mesh_component
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_editor_property("can_ever_affect_navigation", False)


def hmi_text(label, value, location, size, colour, live=False):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90))
    actor.set_actor_label(PREFIX + "HMI_Text_" + label)
    tags = ["LB.Asset.Candidate.v074", "LB.Asset.CandidateNotPromoted", "LB.Station.PR008.HMI"]
    if live:
        tags.append("LB.HMI.PR008.LiveState")
    actor.tags = [unreal.Name(value) for value in tags]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


hmi_rows = [
    hmi_text("Brand", "CAIRNWELL / MOORCROSS", (-185.0, -2281.5, 159.5), 1.9,
             unreal.Color(50, 205, 155, 255)),
    hmi_text("Station", "PR-008  SERVO BLANKING", (-185.0, -2281.5, 154.2), 2.1,
             unreal.Color(225, 235, 232, 255)),
    hmi_text("State", "THREADING / LOOP CONTROL | BLANKS 0 | 1450 mm",
             (-185.0, -2281.5, 148.5), 1.65, unreal.Color(225, 166, 0, 255), live=True),
]

station.set_control_power(True)
station.set_guards_closed(True)
station.set_strip_available(True)
station.set_strip_loop_percent(50.0)
station.set_edge_tracking_deviation(0.0)
station.set_feed_position_error(0.0)
station.set_feed_servo_healthy(True)
station.set_pre_punch_tool_healthy(True)
station.set_press_shear_load(45.0)
station.set_hydraulic_pressure(215.0)
station.set_slug_chute_fill(12.0)
station.set_scrap_bin_fill(18.0)
station.set_blank_outfeed_clear(True)
station.set_safety_circuit_healthy(True)
station.set_blank_recipe(1450.0, 18.0)
station.set_measured_cut_length(1450.0)
if not station.execute_remote_command(
        unreal.LBPR008Command.START, unreal.Name("MW.MCR.PR008.CONSOLE"),
        unreal.Name("CW.MW.CONTROL_ROOM")):
    raise RuntimeError("Native PR-008 authority refused coherent control-room start command")


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PR008.v074", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties(
        {"field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("NativeProcess", (-1650, -3300, 830), (-520, -2000, 125), 57),
    camera("NativeMotion", (-980, -1480, 440), (-500, -2000, 115), 51),
    camera("NativeHMI", (-185, -2635, 205), (-185, -2250, 132), 40),
    camera("PR008ToPR009Interface", (420, -2850, 480), (-70, -2000, 100), 48),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-native-runtime-candidate-v074/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DETAILED_PR008_NATIVE_AUTHORITY_BINDINGS_REMOTE_COMMAND_GATEWAY_AND_LIVE_HMI_ASSEMBLED__RUNTIME_SAVE_COLLISION_NAVIGATION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "removed_obsolete_v060_actor_count": len(obsolete_v060),
    "authority": station.get_actor_label(),
    "authority_id": "CW.MW.CONTROL_ROOM",
    "binding_count": len(bindings),
    "bindings": bindings,
    "interaction_contracts": interaction_contracts,
    "hmi_rows": [actor.get_actor_label() for actor in hmi_rows],
    "fixed_runtime_cameras": [actor.get_actor_label() for actor in cameras],
    "save_root_format": 7,
    "station_save_version": 2,
    "automation_test": "LineBoss.PressShop.PR008.RuntimeAndSave",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V074_BUILD_PASS bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
