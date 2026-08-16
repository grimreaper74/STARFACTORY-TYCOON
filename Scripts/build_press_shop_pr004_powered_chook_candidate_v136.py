"""Import and bind real-reference-led powered C-hook v034 in isolated map v136."""

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import unreal

BASE="/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135"
MAP="/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136"
DEST="/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/PoweredCHook/Candidate_v034"
ASSET=DEST+"/SM_LB_Crane_PoweredCHook_Candidate_v034"
PROJECT=Path(unreal.Paths.project_dir())
FBX=PROJECT/"SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v034/SM_LB_Crane_PoweredCHook_Candidate_v034.fbx"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/press_shop_pr004_powered_chook_build_v136.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library=unreal.EditorAssetLibrary
tools=unreal.AssetToolsHelpers.get_asset_tools()

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

v135_package=PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135.umap"
v124_package=PROJECT/"Content/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124.umap"
hashes_before={"v135":sha256(v135_package),"v124":sha256(v124_package)}
if not FBX.is_file(): raise RuntimeError(f"Missing powered C-hook source {FBX}")
if not levels.load_level(BASE): raise RuntimeError(BASE)
unreal.SystemLibrary.collect_garbage()
if library.does_asset_exist(MAP) and not library.delete_asset(MAP): raise RuntimeError(f"Could not delete owned {MAP}")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError(f"Could not create {MAP}")

unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
if library.does_asset_exist(ASSET): library.delete_asset(ASSET)
task=unreal.AssetImportTask()
task.set_editor_properties({"filename":str(FBX),"destination_path":DEST,"destination_name":"SM_LB_Crane_PoweredCHook_Candidate_v034","automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
options=unreal.FbxImportUI()
options.set_editor_properties({"import_mesh":True,"import_materials":False,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"automated_import_should_detect_type":False})
options.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"import_uniform_scale":100.0})
task.options=options
tools.import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=library.load_asset(ASSET)
if mesh is None: raise RuntimeError(f"Import failed {ASSET}")
bounds=mesh.get_bounds().box_extent*2.0
if not (270.0<=bounds.x<=276.0 and 103.0<=bounds.y<=110.0 and 278.0<=bounds.z<=287.0):
    raise RuntimeError(f"Powered C-hook bounds fail {[bounds.x,bounds.y,bounds.z]}")

materials={
    "SafetyYellow":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_RAL1023_Aged_v031"),
    "MachinedSteel":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_ExposedSteel_v031"),
    "ReplaceableContactRed":library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_SafetyRed"),
    "LoadContactElastomer":library.load_asset("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Materials/M_PR005_Rubber"),
    "FabricatedDarkSteel":library.load_asset("/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/Candidate_v031/MI_LB_Crane_DarkSteel_v031"),
    "IdentityPlate":library.load_asset("/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_LabelWhiteLayered_v025"),
    "SensorGreen":library.load_asset("/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_StatusGreen_R_v002")}
if any(value is None for value in materials.values()): raise RuntimeError("Missing controlled C-hook material")
bindings=[]
for index,slot in enumerate(mesh.get_editor_property("static_materials")):
    slot_name=str(slot.get_editor_property("material_slot_name"))
    match=next((value for token,value in materials.items() if token in slot_name),None)
    if match is None: raise RuntimeError(f"Unmapped powered C-hook slot {slot_name}")
    mesh.set_material(index,match); bindings.append({"slot":slot_name,"material":match.get_path_name()})
library.save_loaded_asset(mesh,only_if_is_dirty=False)

old_hooks=[a for a in actors.get_all_level_actors() if "LB.Module.CHookPurposeBuilt" in {str(t) for t in a.tags} and "LB.Crane.40T" in {str(t) for t in a.tags}]
if len(old_hooks)!=1: raise RuntimeError(f"Expected one inherited purpose-built 40T hook, found {len(old_hooks)}")
old=old_hooks[0]
transform=old.get_actor_transform()
old.set_is_temporarily_hidden_in_editor(True); old.set_actor_hidden_in_game(True)
old.tags=[t for t in old.tags if str(t) not in {"LB.Motion.CHook","LB.Animation.Pivot.CHook","LB.Crane.40T"}]

hook=actors.spawn_actor_from_class(unreal.StaticMeshActor,transform.translation,transform.rotation.rotator())
hook.set_actor_label("LB_PR004_V136_40T_PoweredCHook_RealReference")
hook.set_actor_scale3d(transform.scale3d)
hook.tags=[unreal.Name(v) for v in ("LB.Motion.CHook","LB.Animation.Pivot.CHook","LB.Crane.40T","LB.Safety.Padded","LB.Module.PoweredCHook","LB.Reference.OwnerSupplied.RealPoweredCHook","LB.Capacity.TBC","LB.Asset.Candidate.v136","LB.Asset.CandidateNotPromoted")]
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
if vertical_clearance<35.0: raise RuntimeError(f"Powered hook to hoist clearance below candidate gate: {vertical_clearance}")

def camera(label,location,target,fov):
    actor=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*location),unreal.Rotator())
    actor.set_actor_label("LB_PR004_V136_CAM_"+label)
    actor.tags=[unreal.Name(v) for v in ("LB.Camera.Validation","LB.Camera.Fixed.PoweredCHook.v136","LB.Asset.Candidate.v136","LB.Asset.CandidateNotPromoted")]
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(),unreal.Vector(*target)),False)
    actor.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16.0/9.0,"constrain_aspect_ratio":True,"post_process_blend_weight":1.0})
    settings=actor.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":0.05})
    actor.camera_component.set_editor_property("post_process_settings",settings)
    return actor

cameras=[camera("PoweredCHookSide",(-5950,-1130,1000),(-5050,-2030,790),42.0),camera("PoweredCHookBore",(-5480,-1290,800),(-5050,-1990,760),48.0)]
if not levels.save_current_level(): raise RuntimeError(MAP)
hashes_after={"v135":sha256(v135_package),"v124":sha256(v124_package)}
if hashes_before!=hashes_after: raise RuntimeError(f"Protected parent hash changed {hashes_before} {hashes_after}")
payload={"$schema":"cairnwell/audit/press-shop-pr004-powered-chook-build-v136/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__ISOLATED_REAL_REFERENCE_POWERED_CHOOK_BOUND__REGATES_REQUIRED__NOT_PROMOTED","source_map":BASE,"map":MAP,"source_fbx":str(FBX),"asset":ASSET,"mesh_bounds_cm":[bounds.x,bounds.y,bounds.z],"hook_actor":hook.get_actor_label(),"hook_transform":{"location_cm":[transform.translation.x,transform.translation.y,transform.translation.z],"yaw_deg":transform.rotation.rotator().yaw},"interface":{"bore_axis_world":"Y","body_to_load_centre_y_cm":150.0,"bore_centre_below_datum_cm":59.0,"verified_coil_od_cm":190.0,"verified_coil_width_cm":150.0},"hook_to_hoist_vertical_clearance_cm":vertical_clearance,"capacity":"TBC__NO_16T_REFERENCE_MARKING_COPIED","material_bindings":bindings,"old_v033_hook_hidden_and_unbound":True,"fixed_cameras":[a.get_actor_label() for a in cameras],"protected_hashes_before":hashes_before,"protected_hashes_after":hashes_after,"promotion_authorized":False}
OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
print(json.dumps(payload,indent=2))
