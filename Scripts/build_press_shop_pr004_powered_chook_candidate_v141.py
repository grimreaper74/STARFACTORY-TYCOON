"""Bind powered C-hook v035 into isolated v141 after the concurrent global-v140 collision."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

BASE="/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136"
MAP="/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141"
DEST="/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v035"
ASSET=DEST+"/SM_LB_Crane_PoweredCHook_Candidate_v035"
PROJECT=Path(unreal.Paths.project_dir())
FBX=PROJECT/"SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035/SM_LB_Crane_PoweredCHook_Candidate_v035.fbx"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr004_powered_chook_build_v141.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library=unreal.EditorAssetLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools()

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

protected={
    "v124":PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124.umap",
    "v135":PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135.umap",
    "v136":PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136.umap",
    "v138":PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004HallContextCandidate_v138.umap",
    "v139":PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v139.umap"}
hashes_before={key:sha256(path) for key,path in protected.items()}
if not FBX.is_file(): raise RuntimeError(f"Missing source {FBX}")
if library.does_asset_exist(MAP): raise RuntimeError(f"Refusing to overwrite existing successor {MAP}")
if not levels.load_level(BASE): raise RuntimeError(BASE)
unreal.SystemLibrary.collect_garbage()
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError(f"Could not create {MAP}")

unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
asset_reused=library.does_asset_exist(ASSET)
if not asset_reused:
    task=unreal.AssetImportTask()
    task.set_editor_properties({"filename":str(FBX),"destination_path":DEST,"destination_name":"SM_LB_Crane_PoweredCHook_Candidate_v035","automated":True,"replace_existing":False,"replace_existing_settings":False,"save":True})
    options=unreal.FbxImportUI()
    options.set_editor_properties({"import_mesh":True,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"automated_import_should_detect_type":False})
    options.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"import_uniform_scale":100.0})
    task.options=options
    tools.import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=library.load_asset(ASSET)
if mesh is None: raise RuntimeError(f"Import failed {ASSET}")
bounds=mesh.get_bounds().box_extent*2.0
if not (382.0<=bounds.x<=390.0 and 119.0<=bounds.y<=124.0 and 273.0<=bounds.z<=279.0):
    raise RuntimeError(f"Bounds fail {[bounds.x,bounds.y,bounds.z]}")

materials={
    "SafetyYellow":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031"),
    "YellowEdgeWear":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031"),
    "FabricatedDarkSteel":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031"),
    "WorkedSteel":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031"),
    "WeldMetal":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031"),
    "ReplaceableContactRed":library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_SafetyRed"),
    "LoadContactRubber":library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber"),
    "CairnwellPlate":library.load_asset("/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_LabelWhiteLayered_v025"),
    "SensorGreen":library.load_asset("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_StatusGreen_R_v002"),
    "StatusAmber":library.load_asset("/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_StateAmberRestrained_v025")}
if any(value is None for value in materials.values()): raise RuntimeError("Missing controlled material")
bindings=[]
for index,slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name=str(slot.get_editor_property("material_slot_name"))
    match=next((value for token,value in materials.items() if token in slot_name),None)
    if match is None: raise RuntimeError(f"Unmapped slot {slot_name}")
    mesh.set_material(index,match); bindings.append({"slot":slot_name,"material":match.get_path_name()})
library.save_loaded_asset(mesh,only_if_is_dirty=False)

old_hooks=[a for a in actors.get_all_level_actors() if "LB.Module.PoweredCHook" in {str(t) for t in a.tags} and "LB.Crane.40T" in {str(t) for t in a.tags}]
if len(old_hooks)!=1: raise RuntimeError(f"Expected one active inherited powered hook, found {len(old_hooks)}")
old=old_hooks[0]
transform=old.get_actor_transform()
old.set_is_temporarily_hidden_in_editor(True); old.set_actor_hidden_in_game(True)
old.tags=[t for t in old.tags if str(t) not in {"LB.Motion.CHook","LB.Animation.Pivot.CHook","LB.Crane.40T"}]

hook=actors.spawn_actor_from_class(unreal.StaticMeshActor,transform.translation,transform.rotation.rotator())
hook.set_actor_label("LB_PR004_V141_40T_PoweredCHook_ManufacturerNeutral")
hook.set_actor_scale3d(transform.scale3d)
hook.tags=[unreal.Name(v) for v in ("LB.Motion.CHook","LB.Animation.Pivot.CHook","LB.Crane.40T","LB.Safety.Padded","LB.Module.PoweredCHook","LB.Reference.OfficialManufacturerTypology","LB.Capacity.TBC","LB.Asset.Candidate.v141","LB.Asset.CandidateNotPromoted")]
hook.static_mesh_component.set_static_mesh(mesh)
hook.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
hook.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
hook.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
hook.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)

hoist=next((a for a in actors.get_all_level_actors() if a.get_actor_label()=="LB_INT_FRONT_40T_HoistBlock"),None)
if hoist is None: raise RuntimeError("Missing 40T hoist block")
hook_origin,hook_extent=hook.get_actor_bounds(False,False)
hoist_origin,hoist_extent=hoist.get_actor_bounds(False,False)
vertical_clearance=(hoist_origin.z-hoist_extent.z)-(hook_origin.z+hook_extent.z)
if vertical_clearance<35.0: raise RuntimeError(f"Hook-to-hoist visual clearance fail {vertical_clearance}")

def camera(label,location,target,fov):
    actor=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*location),unreal.Rotator())
    actor.set_actor_label("LB_PR004_V141_CAM_"+label)
    actor.tags=[unreal.Name(v) for v in ("LB.Camera.Validation","LB.Camera.Fixed.PoweredCHook.v141","LB.Asset.Candidate.v141","LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(),unreal.Vector(*target)),False)
    actor.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16.0/9.0,"constrain_aspect_ratio":True,"post_process_blend_weight":1.0})
    settings=actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":0.10})
    actor.camera_component.set_editor_property("post_process_settings",settings)
    return actor

cameras=[
    camera("PoweredCHookSide",(-5750,-1390,980),(-5050,-2030,775),38.0),
    camera("PoweredCHookBore",(-5410,-1510,785),(-5050,-2000,760),44.0),
    camera("PoweredCHookUnloaded",(-5650,-1510,1000),(-5050,-2150,805),40.0)]
if not levels.save_current_level(): raise RuntimeError(MAP)
hashes_after={key:sha256(path) for key,path in protected.items()}
if hashes_before!=hashes_after: raise RuntimeError(f"Protected lineage changed {hashes_before} {hashes_after}")
payload={"$schema":"cairnwell/audit/press-shop-pr004-powered-chook-build-v141/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__ISOLATED_MANUFACTURER_NEUTRAL_POWERED_CHOOK_BOUND__FULL_REGATES_REQUIRED__NOT_PROMOTED","source_map":BASE,"map":MAP,"source_fbx":str(FBX),"asset":ASSET,"asset_reused_after_owned_v140_collision":asset_reused,"mesh_bounds_cm":[bounds.x,bounds.y,bounds.z],"hook_actor":hook.get_actor_label(),"hook_transform":{"location_cm":[transform.translation.x,transform.translation.y,transform.translation.z],"yaw_deg":transform.rotation.rotator().yaw,"scale":[transform.scale3d.x,transform.scale3d.y,transform.scale3d.z]},"interfaces":{"bore_axis_world":"Y","body_to_load_centre_y_cm":150.0,"bore_load_datum_below_hook_cm":59.0,"nominal_coil_od_cm":190.0,"nominal_coil_width_cm":150.0,"coil_od_range_cm":[180.0,210.0],"coil_width_max_cm":155.0},"hook_to_hoist_vertical_clearance_cm":vertical_clearance,"engineering_values":"TBC_NOT_INVENTED","material_bindings":bindings,"old_v034_hook_hidden_and_unbound":True,"fixed_cameras":[a.get_actor_label() for a in cameras],"protected_hashes_before":hashes_before,"protected_hashes_after":hashes_after,"promotion_authorized":False}
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
