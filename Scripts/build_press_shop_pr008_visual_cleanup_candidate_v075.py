"""Build isolated PR-008 v075 visual cleanup without altering v074 or hall structure."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075"
PREFIX = "LB_PR008_V075_"
DEST = "/Game/LineBoss/Stations/Press/PR008/VisualCleanup_v075"
MAT = DEST + "/Materials"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_cleanup_candidate_v075.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075.umap"
if not map_file.exists():
    if not library.duplicate_asset(BASE, MAP):
        raise RuntimeError("Could not duplicate v074 to isolated v075")
    if not library.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v075 map")
    unreal.log("LINE_BOSS_PR008_V075_PREPARE_PASS__RERUN_FOR_POPULATION")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}


def require_actor(label):
    actor = actors.get(label)
    if actor is None:
        raise RuntimeError(f"Missing inherited actor {label}")
    return actor


def suppress_actor(actor):
    actor.set_actor_hidden_in_game(True)
    for component in actor.get_components_by_class(unreal.SceneComponent):
        component.set_visibility(False, True)


# These are explicit engineering artefacts, not production geometry.
engineering_placeholders = [
    "LB_PR008_V062_00_FIXED_PLANNING_ENVELOPE",
    "LB_PR008_V062_11_StripCentreDatum",
    "LB_PR008_V062_TEXT_Brand",
    "LB_PR008_V062_TEXT_Station",
    "LB_PR008_V062_TEXT_Status",
]
for label in engineering_placeholders:
    suppress_actor(require_actor(label))

# v074 now owns the live screen; retain physical v073 HMI but suppress its old
# duplicate pedestal captions so there is one readable information hierarchy.
obsolete_hmi_text = ["LB_PR008_V073_TEXT_Brand", "LB_PR008_V073_TEXT_Station"]
for label in obsolete_hmi_text:
    suppress_actor(require_actor(label))


def make_material(name, colour, metallic, roughness):
    path = f"{MAT}/{name}"
    asset = library.load_asset(path) if library.does_asset_exist(path) else asset_tools.create_asset(
        name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    material_editing.delete_all_material_expressions(asset)
    base = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -340, -70)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 45)
    metal.set_editor_property("r", metallic)
    rough = material_editing.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 150)
    rough.set_editor_property("r", roughness)
    material_editing.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_editing.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_editing.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "epoxy": make_material("M_CA_MW_PR008_EpoxyMachinePad_v075", (0.105, 0.118, 0.116), 0.04, 0.82),
    "aisle": make_material("M_CA_MW_PR008_ServiceAisle_v075", (0.235, 0.245, 0.238), 0.03, 0.88),
    "yellow": make_material("M_CA_MW_PR008_SafetyLine_v075", (0.86, 0.49, 0.008), 0.10, 0.62),
}
strip_material = library.load_asset(
    "/Game/LineBoss/Stations/Press/PR008/Detailed_v001/Materials/M_CA_MW_PR008_GroundSteel_v001")
if not strip_material:
    raise RuntimeError("Missing detailed PR-008 ground-steel material")


def cube_actor(label, centre, dimensions, material, tags):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*centre), unreal.Rotator())
    actor.set_actor_label(PREFIX + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Asset.Candidate.v075", "LB.Asset.CandidateNotPromoted", *tags)]
    component = actor.static_mesh_component
    component.set_static_mesh(library.load_asset("/Engine/BasicShapes/Cube.Cube"))
    component.set_world_scale3d(unreal.Vector(dimensions[0] / 100.0, dimensions[1] / 100.0, dimensions[2] / 100.0))
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


floor_actors = [
    cube_actor("Floor_MachinePad", (-500.0, -1995.0, 5.25), (1120.0, 610.0, 0.5), materials["epoxy"],
               ("LB.Floor.PR008.MachinePad", "LB.Navigation.Neutral")),
    cube_actor("Floor_RemoteServiceAisle", (-500.0, -2420.0, 5.30), (1120.0, 220.0, 0.6), materials["aisle"],
               ("LB.Floor.PR008.RemoteServiceAisle", "LB.Navigation.Neutral")),
    cube_actor("Floor_Line_Operator", (-500.0, -2307.0, 5.65), (1120.0, 8.0, 0.7), materials["yellow"],
               ("LB.Floor.PR008.SafetyBoundary", "LB.Navigation.Neutral")),
    cube_actor("Floor_Line_Drive", (-500.0, -1683.0, 5.65), (1120.0, 8.0, 0.7), materials["yellow"],
               ("LB.Floor.PR008.SafetyBoundary", "LB.Navigation.Neutral")),
    cube_actor("Floor_Line_Infeed", (-1056.0, -1995.0, 5.65), (8.0, 632.0, 0.7), materials["yellow"],
               ("LB.Floor.PR008.SafetyBoundary", "LB.Navigation.Neutral")),
    cube_actor("Floor_Line_Discharge", (56.0, -1995.0, 5.65), (8.0, 632.0, 0.7), materials["yellow"],
               ("LB.Floor.PR008.SafetyBoundary", "LB.Navigation.Neutral")),
]

# Replace the hidden engineering datum with a production-presentation strip,
# retaining the exact Pro transform while giving it the detailed steel finish.
datum = require_actor("LB_PR008_V062_11_StripCentreDatum")
strip = actors_api.spawn_actor_from_class(
    unreal.StaticMeshActor, datum.get_actor_location(), datum.get_actor_rotation())
strip.set_actor_label(PREFIX + "Live_ProcessStrip")
strip.set_actor_scale3d(datum.get_actor_scale3d())
strip.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v075", "LB.Asset.CandidateNotPromoted", "LB.Station.PR008",
    "LB.Presentation.PR008.LiveStrip", "LB.Process.MaterialFlow", "LB.Navigation.Neutral")]
strip_component = strip.static_mesh_component
strip_component.set_static_mesh(datum.static_mesh_component.static_mesh)
strip_component.set_material(0, strip_material)
strip_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
strip_component.set_collision_profile_name(unreal.Name("NoCollision"))
strip_component.set_editor_property("can_ever_affect_navigation", False)


def camera(label, location, target, fov):
    actor = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name(value) for value in (
        "LB.Camera.Validation", "LB.Camera.Fixed.PR008.v075", "LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), unreal.Vector(*target)), False)
    actor.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
    return actor


cameras = [
    camera("CleanProcess", (-1510.0, -3040.0, 690.0), (-520.0, -1995.0, 130.0), 56.0),
    camera("CleanMotion", (-930.0, -1450.0, 410.0), (-500.0, -1995.0, 115.0), 50.0),
    camera("CleanHMI", (-405.0, -2600.0, 185.0), (-185.0, -2255.0, 132.0), 34.0),
    camera("ClearPR009Interface", (360.0, -1450.0, 360.0), (-70.0, -1995.0, 105.0), 45.0),
]

column = require_actor("LB_PRESS_Column_0_-2250")
if column.get_editor_property("hidden"):
    raise RuntimeError("The fixed hall column must remain present in v075")

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-cleanup-candidate-v075/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PR008_CONFIRMED_ENGINEERING_PLACEHOLDERS_SUPPRESSED__FLOOR_AND_CAMERA_DIRECTION_ASSEMBLED__RUNTIME_COLLISION_NAVIGATION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": BASE,
    "suppressed_engineering_placeholders": engineering_placeholders,
    "suppressed_obsolete_hmi_text": obsolete_hmi_text,
    "replacement_process_strip": strip.get_actor_label(),
    "floor_actor_count": len(floor_actors),
    "floor_dimensions_cm": {
        "machine_pad": [1120.0, 610.0],
        "remote_service_aisle": [1120.0, 220.0],
        "safety_line_width": 8.0,
    },
    "floor_collision": "NoCollision",
    "floor_navigation": "neutral",
    "fixed_hall_column_preserved": column.get_actor_label(),
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR008_V075_VISUAL_CLEANUP_BUILD_PASS floor={len(floor_actors)} cameras={len(cameras)}")
unreal.SystemLibrary.quit_editor()
