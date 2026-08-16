"""Import and bind the PR-005 service-cover identity/wear candidate v052."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052"
DEST = "/Game/LineBoss/Stations/Press/PR005/Candidate_v052/HydraulicRouting"
ASSET = DEST + "/SM_PR005_HydraulicServiceIdentity_Candidate_v052"
FBX = Path(unreal.Paths.project_dir()) / (
    "SourceAssets/PR005/HydraulicRouting/Candidate_v052/"
    "SM_PR005_HydraulicServiceIdentity_Candidate_v052.fbx")
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr005_service_identity_candidate_v052.json"
PREFIX = "LB_PR005_V052_"
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

old_cover = next((actor for actor in actors.get_all_level_actors()
                  if actor.get_actor_label() == "LB_PR005_V051_HydraulicServiceCovers_Removable"), None)
if old_cover is None:
    raise RuntimeError("Missing inherited v051 cover actor")
old_cover.set_is_temporarily_hidden_in_editor(True)
old_cover.set_actor_hidden_in_game(True)
old_cover.tags = list(old_cover.tags) + [unreal.Name("LB.Asset.ReplacedBy.Candidate.v052")]

materials = {
    "PR005_ServiceCover_Galvanised": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v050/Materials/M_PR005_Service_GalvanisedCarrier_v050"),
    "PR005_ServiceCover_AntiSlip": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v050/Materials/M_PR005_Service_CrossingGrip_v050"),
    "PR005_ServiceCover_SafetyYellow": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_SafetyYellow_v048"),
    "PR005_ServiceCover_IdentityWhite": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v048/Materials/M_PR005_CADRoute_LabelWhite_v048"),
    "PR005_ServiceCover_WearDark": library.load_asset(
        "/Game/LineBoss/Stations/Press/PR005/Candidate_v050/Materials/M_PR005_Service_CrossingTread_v050"),
}
if any(value is None for value in materials.values()):
    raise RuntimeError("Missing retained service identity/wear materials")

unreal.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET):
    library.delete_asset(ASSET)
task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": str(FBX), "destination_path": DEST,
    "destination_name": "SM_PR005_HydraulicServiceIdentity_Candidate_v052",
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
    "auto_generate_collision": True, "import_uniform_scale": 100.0,
})
task.options = options
asset_tools.import_asset_tasks([task])
mesh = library.load_asset(ASSET)
if mesh is None:
    raise RuntimeError(f"Failed to import {ASSET}")
bounds = mesh.get_bounds().box_extent * 2.0
if not (79.0 <= bounds.x <= 81.0 and 353.0 <= bounds.y <= 357.0 and 25.0 <= bounds.z <= 28.0):
    raise RuntimeError(f"PR-005 service identity bounds out of gate: {[bounds.x, bounds.y, bounds.z]}")

bindings = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name = str(slot.get_editor_property("imported_material_slot_name"))
    selected = next((mat for token, mat in materials.items() if token in slot_name), None)
    if selected is None:
        continue
    mesh.set_material(index, selected)
    bindings.append({"index": index, "slot": slot_name, "material": selected.get_path_name()})
if len(bindings) != 5:
    raise RuntimeError(f"Expected five semantic identity bindings, found {len(bindings)}: {bindings}")
library.save_loaded_asset(mesh, only_if_is_dirty=False)

rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": -90.0, "roll": 0.0})
cover = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, unreal.Vector(-4000.0, -2000.0, 2.5), rotation)
cover.set_actor_label(PREFIX + "HydraulicServiceCovers_IdentityWear")
cover.tags = [
    unreal.Name("LB.Asset.Candidate.v052"), unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Service.HydraulicRouting.RemovableCovers"),
    unreal.Name("LB.Service.Identity.HYD_NO_STEP"), unreal.Name("LB.Module.StationLocal")]
component = cover.static_mesh_component
component.set_static_mesh(mesh)
component.set_mobility(unreal.ComponentMobility.STATIC)
component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
component.set_collision_profile_name(unreal.Name("BlockAll"))
component.set_editor_property("can_ever_affect_navigation", True)


def camera(label, location, target, fov, bias):
    actor = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(PREFIX + "CAM_" + label)
    actor.tags = [unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.PR005.v052"),
                  unreal.Name("LB.Asset.Candidate.v052"), unreal.Name("LB.Asset.CandidateNotPromoted")]
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
    camera("ServiceIdentityPlayer", (-4560.0, -720.0, 230.0), (-3820.0, -1510.0, 42.0), 39.0, 0.06),
    camera("ServiceIdentityElevated", (-4550.0, -850.0, 480.0), (-3820.0, -1510.0, 45.0), 43.0, 0.05),
    camera("ServiceIdentityWholeLine", (-5200.0, -720.0, 700.0), (-3920.0, -1900.0, 110.0), 54.0, 0.06),
]

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)
payload = {
    "$schema": "line-boss/audit/press-shop-pr005-service-identity-candidate-v052/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FUNCTIONAL_HYD_NO_STEP_IDENTITY_AND_RESTRAINED_WEAR_BUILT__FULL_RUNTIME_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "map": MAP, "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051",
    "source_fbx": str(FBX), "asset": ASSET, "mesh_bounds_cm": [bounds.x, bounds.y, bounds.z],
    "functional_identity": ["HYD", "NO STEP"], "wear_mark_count": 8,
    "line_boss_in_world_branding": False, "material_bindings": bindings,
    "collision_profile": "BlockAll", "can_ever_affect_navigation": True,
    "equipment_coordinates_modified": False,
    "fixed_cameras": [actor.get_actor_label() for actor in cameras],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR005_SERVICE_IDENTITY_V052_BUILD_PASS bounds={payload['mesh_bounds_cm']} bindings={len(bindings)}")
unreal.SystemLibrary.quit_editor()
