"""Import and bind the station-local PR-005 CAD floor-route module."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048"
DEST = "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/FloorRoutes"
MAT_ROOT = "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials"
ASSET = DEST + "/SM_PR005_CAD_FloorRoutes_Candidate_v048"
FBX = Path(unreal.Paths.project_dir()) / (
    "SourceAssets/PR005/FloorRoutes/Candidate_v048/"
    "SM_PR005_CAD_FloorRoutes_Candidate_v048.fbx")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_cad_floor_candidate_v048.json"
PREFIX = "LB_PR005_V048_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

if "ONEDRIVE" in str(FBX).upper() or not FBX.is_file():
    raise RuntimeError(f"Invalid canonical FBX source: {FBX}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

# The inherited authored zoning mesh was useful as a layout study, but its
# pale cross-route conflicts with this exact station-local replacement.
inherited_floor = next((actor for actor in actors.get_all_level_actors()
                        if actor.get_actor_label() == "LB_INT_PR005_FloorZoning_Static"), None)
if inherited_floor is None:
    raise RuntimeError("Missing inherited PR-005 floor-zoning study")
inherited_floor.set_is_temporarily_hidden_in_editor(True)
inherited_floor.set_actor_hidden_in_game(True)
inherited_floor.tags = list(inherited_floor.tags) + [
    unreal.Name("LB.Asset.ReplacedBy.Candidate.v048"),
    unreal.Name("LB.Asset.CandidateNotPromoted")]


def matte_material(name, colour, roughness):
    path = MAT_ROOT + "/" + name
    asset = library.load_asset(path)
    if asset is None:
        asset = asset_tools.create_asset(name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    if asset is None:
        raise RuntimeError(f"Could not create {path}")
    mel.delete_all_material_expressions(asset)
    base = mel.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -300, -60)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 70)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 170)
    metal.set_editor_property("r", 0.0)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(asset)
    library.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


materials = {
    "PR005_Route_ProtectedGreen": matte_material(
        "M_PR005_CADRoute_ProtectedGreen_v048", (0.035, 0.18, 0.085), 0.82),
    "PR005_Route_SafetyYellow": matte_material(
        "M_PR005_CADRoute_SafetyYellow_v048", (0.70, 0.35, 0.008), 0.70),
    "PR005_Route_MaintenanceRed": matte_material(
        "M_PR005_CADRoute_MaintenanceRed_v048", (0.38, 0.012, 0.008), 0.74),
    "PR005_Route_FlowCyan": matte_material(
        "M_PR005_CADRoute_FlowCyan_v048", (0.006, 0.25, 0.34), 0.68),
    "PR005_Route_LabelWhite": matte_material(
        "M_PR005_CADRoute_LabelWhite_v048", (0.66, 0.70, 0.68), 0.80),
}

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET):
    library.delete_asset(ASSET)
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX), "destination_path": DEST,
    "destination_name": "SM_PR005_CAD_FloorRoutes_Candidate_v048",
    "automated": True, "replace_existing": True, "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True, "import_materials": False, "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    "automated_import_should_detect_type": False,
})
options.static_mesh_import_data.set_editor_properties({
    "combine_meshes": True, "generate_lightmap_u_vs": True,
    "auto_generate_collision": False, "import_uniform_scale": 100.0,
})
task.options = options
asset_tools.import_asset_tasks([task])
mesh = library.load_asset(ASSET)
if mesh is None:
    raise RuntimeError(f"Failed to import {ASSET}")

bounds = mesh.get_bounds().box_extent * 2.0
if not (245.0 <= bounds.x <= 260.0 and 1148.0 <= bounds.y <= 1152.0 and 3.0 <= bounds.z <= 4.5):
    raise RuntimeError(f"PR-005 CAD floor bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

bindings = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    selected = next((mat for token, mat in materials.items() if token in slot_name), None)
    if selected is None:
        continue
    mesh.set_material(index, selected)
    bindings.append({"index": index, "slot": slot_name, "material": selected.get_path_name()})
if len(bindings) != 5:
    raise RuntimeError(f"Expected five semantic CAD route bindings, found {len(bindings)}: {bindings}")
library.save_loaded_asset(mesh, only_if_is_dirty=False)

rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": -90.0, "roll": 0.0})
route = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-4000.0, -2000.0, 2.5), rotation)
if route is None:
    raise RuntimeError("Could not spawn PR-005 CAD route module")
route.set_actor_label(PREFIX + "CADFloorRoutes_StationLocal")
route.tags = [
    unreal.Name("LB.Asset.Candidate.v048"), unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Floor.PR005.CADRouteModule"), unreal.Name("LB.Module.StationLocal"),
    unreal.Name("LB.Floor.PR005.ProtectedWalkway"), unreal.Name("LB.Floor.PR005.MaterialFlow")]
component = route.static_mesh_component
component.set_static_mesh(mesh)
component.set_mobility(unreal.ComponentMobility.STATIC)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
component.set_collision_profile_name(unreal.Name("NoCollision"))
component.set_editor_property("can_ever_affect_navigation", False)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v048"),
        unreal.Name("LB.Asset.Candidate.v048"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        actor.get_actor_location(), unreal.Vector(*target)), False)
    camera_component = actor.camera_component
    camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True, "post_process_blend_weight": 1.0,
    })
    settings = camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    camera_component.set_editor_property("post_process_settings", settings)
    return actor


cameras = [
    camera("CADRoutesPlayer", (-4800.0, -760.0, 360.0), (-4000.0, -1450.0, 25.0), 48.0, 0.06),
    camera("CADRoutesPlan", (-4850.0, -720.0, 690.0), (-4000.0, -1420.0, 0.0), 49.0, 0.04),
    camera("CADRoutesWholeLine", (-5200.0, -720.0, 700.0), (-3920.0, -1900.0, 110.0), 54.0, 0.06),
]

if route.static_mesh_component.get_collision_profile_name() != unreal.Name("NoCollision"):
    raise RuntimeError("CAD route module collision profile changed")
if route.static_mesh_component.get_editor_property("can_ever_affect_navigation"):
    raise RuntimeError("CAD route module can affect navigation")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
library.save_directory(MAT_ROOT, only_if_is_dirty=False, recursive=True)

payload = {
    "$schema": "line-boss/audit/press-shop-pr005-cad-floor-candidate-v048/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "STATION_LOCAL_DIMENSIONED_CAD_FLOOR_MODULE_BUILT__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP,
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045",
    "source_fbx": str(FBX), "asset": ASSET,
    "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "station_datum_cm": [-4000.0, -2000.0, 2.5], "station_yaw_degrees": -90.0,
    "walkway_dimensions_mm": [11500, 1500],
    "material_bindings": bindings,
    "inherited_floor_zoning_hidden": inherited_floor.get_actor_label(),
    "collision_profile": "NoCollision", "can_ever_affect_navigation": False,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "equipment_coordinates_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_CAD_FLOOR_V048_BUILD_PASS bounds={payload['mesh_bounds_cm']} bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
