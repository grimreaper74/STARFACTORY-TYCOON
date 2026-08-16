"""Import modular v654 S03, bind native motion tags, and build isolated runtime map."""
from pathlib import Path
import hashlib,json
import unreal
PROJECT=Path(unreal.Paths.project_dir());STAGING=PROJECT/r"Saved\ImportStaging\CompleteS03Modular_v654"
RECEIPT=PROJECT/r"Saved\Audits\PressTrains\complete_s03_modular_staging_v654.json"
DEST="/Game/LineBoss/Developer/Validation/PressTrains/CompleteS03Modular_v655"
MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PTA_S03_ModularRuntime_v655"
AUDIT=PROJECT/r"Saved\Audits\PressTrains\complete_s03_modular_unreal_v655.json"
library=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_directory_exist(DEST) or library.does_asset_exist(MAP) or AUDIT.exists():raise RuntimeError("Refusing to overwrite v655")
receipt=json.loads(RECEIPT.read_text(encoding="utf-8"));rows=receipt["assets"]
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
assets={};records=[]
for row in rows:
 fbx=STAGING/row["fbx"];name=row["asset"]
 task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(fbx),"destination_path":DEST,
  "destination_name":name,"automated":True,"replace_existing":False,"save":True})
 ui=unreal.FbxImportUI();ui.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,
  "import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,
  "automated_import_should_detect_type":False})
 ui.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,
  "force_front_x_axis":False,"generate_lightmap_u_vs":False,"auto_generate_collision":False,"remove_degenerates":True,
  "transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False})
 task.options=ui;tools.import_asset_tasks([task]);mesh=library.load_asset(f"{DEST}/{name}")
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Import failed {name}: {task.imported_object_paths}")
 try:
  settings=mesh.get_editor_property("nanite_settings");settings.enabled=True;mesh.set_editor_property("nanite_settings",settings)
 except Exception:pass
 library.save_loaded_asset(mesh,only_if_is_dirty=False);assets[name]=mesh
 size=mesh.get_bounds().box_extent*2.0
 expected=[v*100 for v in row["bounds_m"]];actual=[size.x,size.y,size.z]
 if any(abs(a-e)>max(2.0,e*0.02) for a,e in zip(actual,expected)):
  raise RuntimeError(f"Bounds mismatch {name}: actual {actual}, expected {expected}")
 records.append({"asset":f"{DEST}/{name}","role":row["role"],"bounds_cm":[round(v,2) for v in actual],"pivot":row["pivot"]})
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.new_level(MAP):raise RuntimeError(f"Could not create {MAP}")
scope="LB.PressTrain.Installed.TRAIN_A";spawned=[]
for row in rows:
 loc=unreal.Vector(*row["actor_location_cm"]);a=actors.spawn_actor_from_class(unreal.StaticMeshActor,loc,unreal.Rotator())
 a.set_actor_label(row["source_object"].replace("_v649","_v655"));a.static_mesh_component.set_static_mesh(assets[row["asset"]])
 a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)
 tags=[scope,"LB.Asset.CandidateNotPromoted","LB.Engineering.Values.TBC"]
 if row["role"]!="static":tags.append("LB.PressTrain.Role."+row["role"])
 if row["role"] in ("moving_press_slide","moving_upper_die"):tags.append("LB.PressTrain.Stage.S03")
 a.tags=[unreal.Name(t) for t in tags];spawned.append(a)
cube=library.load_asset("/Engine/BasicShapes/Cube.Cube")
def proxy(label,loc,scale,role=None,component_offset=None):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label)
 a.static_mesh_component.set_static_mesh(cube);a.set_actor_scale3d(unreal.Vector(*scale))
 if component_offset:a.static_mesh_component.set_relative_location(unreal.Vector(*component_offset))
 a.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll"));a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
 a.static_mesh_component.set_editor_property("can_ever_affect_navigation",True);a.set_is_temporarily_hidden_in_editor(True)
 tags=[scope,"LB.Collision.Proxy","LB.Asset.CandidateNotPromoted"]
 if role:tags.append("LB.PressTrain.Role."+role)
 a.tags=[unreal.Name(t) for t in tags];return a
proxy("LB_S03_COLL_Base",(0,1500,110),(2.7,2.7,1.1));proxy("LB_S03_COLL_Upper",(0,1500,520),(2.8,2.8,3.0))
gate=next(r for r in rows if r["role"]=="access_gate")
proxy("LB_S03_COLL_AccessGate",gate["actor_location_cm"],(0.30,1.62,1.90),"access_gate",(0,50,0))
floor=proxy("LB_S03_REVIEW_Floor",(0,1500,-10),(10,10,0.1));floor.set_is_temporarily_hidden_in_editor(False)
station_class=unreal.load_class(None,"/Script/LineBossCarFactory.LBPressTrainAStation")
if not station_class:raise RuntimeError("Native press train authority class unavailable")
authority=actors.spawn_actor_from_class(station_class,unreal.Vector(),unreal.Rotator());authority.set_actor_label("LB_PressTrainA_Authority_v655")
authority.tags=[unreal.Name(scope),unreal.Name("LB.Authority.PressTrain.Native"),unreal.Name("LB.Asset.CandidateNotPromoted")]
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v655")
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({"revision":"v655",
 "status":"PASS__MODULAR_UNREAL_INTAKE_AND_NATIVE_TAG_BINDING__RUNTIME_TEST_PENDING","map":MAP,"assets":records,
 "visual_actor_count":len(spawned),"native_authority_class":"/Script/LineBossCarFactory.LBPressTrainAStation",
 "motion_roles":["moving_press_slide","moving_upper_die","access_gate","flywheel_rotor"],
 "collision":"visual NoCollision; shell and hinged gate BlockAll proxies","navigation":"proxy blockers enabled; path test pending",
 "save_authority":"native authority present; PIE restore test pending","protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_S03_MODULAR_V655_BUILD_PASS")
