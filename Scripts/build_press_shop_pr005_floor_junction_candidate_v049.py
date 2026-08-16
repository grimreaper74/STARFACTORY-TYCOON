"""Import and bind the dimensioned PR-005 cross-aisle junction module v049."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049"
DEST = "/Game/LineBoss/Stations/Press/PR005/Candidate_v049/FloorRoutes"
ASSET = DEST + "/SM_PR005_CAD_FloorRoutes_Junction_Candidate_v049"
FBX = Path(unreal.Paths.project_dir()) / (
    "SourceAssets/PR005/FloorRoutes/Candidate_v049/"
    "SM_PR005_CAD_FloorRoutes_Junction_Candidate_v049.fbx")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_floor_junction_candidate_v049.json"
PREFIX = "LB_PR005_V049_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

if "ONEDRIVE" in str(FBX).upper() or not FBX.is_file():
    raise RuntimeError(f"Invalid canonical FBX source: {FBX}")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

old_route = next((actor for actor in actors.get_all_level_actors()
                  if actor.get_actor_label() == "LB_PR005_V048_CADFloorRoutes_StationLocal"), None)
if old_route is None:
    raise RuntimeError("Missing inherited v048 CAD floor module")
old_route.set_is_temporarily_hidden_in_editor(True)
old_route.set_actor_hidden_in_game(True)
old_route.tags = list(old_route.tags) + [unreal.Name("LB.Asset.ReplacedBy.Candidate.v049")]

materials = {
    "PR005_Route_ProtectedGreen": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_ProtectedGreen_v048"),
    "PR005_Route_SafetyYellow": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_SafetyYellow_v048"),
    "PR005_Route_MaintenanceRed": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_MaintenanceRed_v048"),
    "PR005_Route_FlowCyan": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_FlowCyan_v048"),
    "PR005_Route_LabelWhite": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_LabelWhite_v048"),
}
if any(value is None for value in materials.values()):
    raise RuntimeError("Missing retained v048 controlled floor-route materials")

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET):
    library.delete_asset(ASSET)
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX), "destination_path": DEST,
    "destination_name": "SM_PR005_CAD_FloorRoutes_Junction_Candidate_v049",
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
if not (245.0 <= bounds.x <= 260.0 and 1148.0 <= bounds.y <= 1152.0 and 4.0 <= bounds.z <= 5.2):
    raise RuntimeError(f"PR-005 v049 junction bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

bindings = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    selected = next((mat for token, mat in materials.items() if token in slot_name), None)
    if selected is None:
        continue
    mesh.set_material(index, selected)
    bindings.append({"index": index, "slot": slot_name, "material": selected.get_path_name()})
if len(bindings) != 5:
    raise RuntimeError(f"Expected five semantic v049 bindings, found {len(bindings)}: {bindings}")
library.save_loaded_asset(mesh, only_if_is_dirty=False)

rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": -90.0, "roll": 0.0})
route = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-4000.0, -2000.0, 2.5), rotation)
route.set_actor_label(PREFIX + "CADFloorRoutes_CrossAisleJunction")
route.tags = [
    unreal.Name("LB.Asset.Candidate.v049"), unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Floor.PR005.CADRouteModule"), unreal.Name("LB.Floor.CrossAisleJunction"),
    unreal.Name("LB.Module.StationLocal")]
route.static_mesh_component.set_static_mesh(mesh)
route.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
route.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
route.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
route.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v049"),
        unreal.Name("LB.Asset.Candidate.v049"), unreal.Name("LB.Asset.CandidateNotPromoted")]
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
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    component.set_editor_property("post_process_settings", settings)
    return actor


cameras = [
    camera("JunctionPlayer", (-5050.0, -650.0, 330.0), (-4410.0, -1370.0, 15.0), 46.0, 0.05),
    camera("JunctionElevated", (-5100.0, -730.0, 650.0), (-4400.0, -1400.0, 0.0), 48.0, 0.04),
    camera("JunctionWholeLine", (-5200.0, -720.0, 700.0), (-3920.0, -1900.0, 110.0), 54.0, 0.06),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "line-boss/audit/press-shop-pr005-floor-junction-candidate-v049/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DIMENSIONED_CROSS_AISLE_JUNCTION_BUILT__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048",
    "source_fbx": str(FBX), "asset": ASSET,
    "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "walkway_dimensions_mm": [11500, 1500], "crossing_dimensions_mm": [1800, 1260],
    "crossing_bar_count": 8, "threshold_count": 2,
    "material_bindings": bindings, "v048_actor_hidden": old_route.get_actor_label(),
    "collision_profile": "NoCollision", "can_ever_affect_navigation": False,
    "equipment_coordinates_modified": False,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_FLOOR_JUNCTION_V049_BUILD_PASS bounds={payload['mesh_bounds_cm']} bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
