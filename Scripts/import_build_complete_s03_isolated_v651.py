"""Fresh isolated Unreal intake for the complete v649 S03 visual assembly."""
from pathlib import Path
import hashlib, json
import unreal

PROJECT=Path(unreal.Paths.project_dir())
FBX=PROJECT/r"Saved\ImportStaging\CompleteS03_v650\SM_CA_MW_PTA_S03_CompleteVisual_v650.fbx"
DEST="/Game/LineBoss/Developer/Validation/PressTrains/CompleteS03_v651"
ASSET=DEST+"/SM_CA_MW_PTA_S03_CompleteVisual_v650"
MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PTA_S03_CompleteVisual_v651"
AUDIT=Path(unreal.Paths.project_saved_dir())/"Audits/PressTrains/complete_s03_unreal_intake_v651.json"
library=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not FBX.is_file():raise RuntimeError(f"Missing staging FBX {FBX}")
if library.does_asset_exist(ASSET) or library.does_asset_exist(MAP):raise RuntimeError("Refusing to overwrite v651")
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(FBX),"destination_path":DEST,
 "destination_name":"SM_CA_MW_PTA_S03_CompleteVisual_v650","automated":True,"replace_existing":False,"save":True})
ui=unreal.FbxImportUI();ui.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,
 "import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,
 "automated_import_should_detect_type":False})
ui.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"convert_scene":True,
 "convert_scene_unit":True,"force_front_x_axis":False,"generate_lightmap_u_vs":False,
 "auto_generate_collision":False,"remove_degenerates":True})
task.options=ui;tools.import_asset_tasks([task]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=library.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Import failed {task.imported_object_paths}")
nanite={"requested":True,"enabled":False,"error":None}
try:
 settings=mesh.get_editor_property("nanite_settings");settings.set_editor_property("enabled",True)
 mesh.set_editor_property("nanite_settings",settings);nanite["enabled"]=bool(mesh.get_editor_property("nanite_settings").enabled)
except Exception as exc:nanite["error"]=str(exc)
library.save_loaded_asset(mesh,only_if_is_dirty=False)
size=mesh.get_bounds().box_extent*2.0
bounds=[round(size.x,2),round(size.y,2),round(size.z,2)]
if not (700.0<=max(bounds)<=6500.0 and 700.0<=bounds[2]<=900.0):
 raise RuntimeError(f"S03 scale gate failed: {bounds}")
if not levels.new_level(MAP):raise RuntimeError(f"Could not create {MAP}")
visual=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(),unreal.Rotator())
visual.set_actor_label("CA_MW_PTA_S03_CompleteVisual_v651")
visual.static_mesh_component.set_static_mesh(mesh);visual.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
visual.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)
visual.tags=[unreal.Name(x) for x in ("LB.Asset.CandidateNotPromoted","LB.PressTrain.TrainA.S03",
 "LB.Visual.Aggregate.NoCollision","LB.Engineering.Values.TBC","LB.Runtime.ModularImport.Pending")]
cube=library.load_asset("/Engine/BasicShapes/Cube.Cube")
def proxy(label,loc,scale,nav=True):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label)
 a.static_mesh_component.set_static_mesh(cube);a.set_actor_scale3d(unreal.Vector(*scale))
 a.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"));a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
 a.static_mesh_component.set_editor_property("can_ever_affect_navigation",nav)
 a.set_is_temporarily_hidden_in_editor(True);a.tags=[unreal.Name("LB.Collision.Proxy"),unreal.Name("LB.Asset.CandidateNotPromoted")]
 return a
# Hidden coarse shell/base blockers prove the aggregate does not use render-mesh collision.
proxy("LB_S03_COLL_Base",(0,1500,110),(2.7,2.7,1.1))
proxy("LB_S03_COLL_Upper",(0,1500,520),(2.8,2.8,3.0))
floor=proxy("LB_S03_REVIEW_Floor",(0,1500,-10),(10,10,0.1))
floor.set_is_temporarily_hidden_in_editor(False)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v651")
AUDIT.parent.mkdir(parents=True,exist_ok=True)
AUDIT.write_text(json.dumps({"revision":"v651","status":"PASS__ISOLATED_UNREAL_SCALE_AND_INTAKE__NOT_PROMOTED",
 "map":MAP,"asset":ASSET,"fbx":str(FBX),"fbx_sha256":hashlib.sha256(FBX.read_bytes()).hexdigest().upper(),
 "bounds_cm":bounds,"nanite":nanite,"visual_collision":"NoCollision","proxy_collision":"BlockAll",
 "navigation":"proxy blockers enabled; navmesh path test pending","runtime_modular_binding":"pending",
 "protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_S03_V651_BUILD_PASS")
