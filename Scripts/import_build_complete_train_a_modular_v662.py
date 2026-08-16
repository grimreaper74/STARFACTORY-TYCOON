"""Build complete modular Train A in a fresh isolated Unreal map."""
from pathlib import Path
import json,hashlib
import unreal
PROJECT=Path(unreal.Paths.project_dir())
SUPPORT_STAGE=PROJECT/r"Saved\ImportStaging\CompleteTrainASupports_v661"
SUPPORT_RECEIPT=PROJECT/r"Saved\Audits\PressTrains\complete_train_a_support_staging_v661.json"
MODULE_RECEIPT=PROJECT/r"Saved\Audits\PressTrains\complete_s03_modular_staging_v656.json"
MODULE_ROOT="/Game/LineBoss/Developer/Validation/PressTrains/CompleteS03Modular_v658"
DEST="/Game/LineBoss/Developer/Validation/PressTrains/CompleteTrainA_v662/Supports"
MAP="/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_CompleteModular_v662"
AUDIT=PROJECT/r"Saved\Audits\PressTrains\complete_train_a_unreal_v662.json"
library=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_directory_exist(DEST) or library.does_asset_exist(MAP) or AUDIT.exists():raise RuntimeError("Refusing to overwrite v662")
supports=json.loads(SUPPORT_RECEIPT.read_text(encoding="utf-8"));modules=json.loads(MODULE_RECEIPT.read_text(encoding="utf-8"))
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
support_assets={};support_records=[]
for row in supports["assets"]:
 fbx=SUPPORT_STAGE/row["fbx"];name=row["asset"];task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(fbx),"destination_path":DEST,"destination_name":name,"automated":True,"replace_existing":False,"save":True})
 ui=unreal.FbxImportUI();ui.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH,"automated_import_should_detect_type":False})
 ui.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"force_front_x_axis":False,"generate_lightmap_u_vs":False,"auto_generate_collision":False,"remove_degenerates":True,"transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False})
 task.options=ui;tools.import_asset_tasks([task]);mesh=library.load_asset(f"{DEST}/{name}")
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Support import failed {name}")
 try:
  ns=mesh.nanite_settings;ns.enabled=True;mesh.nanite_settings=ns
 except Exception:pass
 library.save_loaded_asset(mesh,only_if_is_dirty=False);support_assets[name]=mesh;size=mesh.get_bounds().box_extent*2;actual=[size.x,size.y,size.z];expected=[v*100 for v in row["bounds_m"]]
 if any(abs(a-e)>max(2,e*.02) for a,e in zip(actual,expected)):raise RuntimeError(f"Support bounds mismatch {name}: {actual} vs {expected}")
 support_records.append({"asset":f"{DEST}/{name}","bounds_cm":[round(v,2) for v in actual],"instances":len(row["source_examples"])})
module_assets={}
for row in modules["assets"]:
 path=f"{MODULE_ROOT}/{row['asset']}";mesh=library.load_asset(path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"Missing validated module {path}")
 module_assets[row["asset"]]=mesh
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.new_level(MAP):raise RuntimeError(f"Could not create {MAP}")
scope="LB.PressTrain.Installed.TRAIN_A";visuals=[];motion_counts={}
station_y={"S02":750.0,"S03":1500.0,"S04":2250.0,"S05":3000.0,"S06":3750.0}
for station,y in station_y.items():
 delta=y-1500.0
 for row in modules["assets"]:
  loc=list(row["actor_location_cm"]);loc[1]+=delta
  a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());role=row["role"]
  base=row["source_object"].replace("S03",station).replace("_v649","");a.set_actor_label(base+"_v662");a.static_mesh_component.set_static_mesh(module_assets[row["asset"]])
  a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)
  tags=[scope,"LB.Asset.CandidateNotPromoted","LB.Engineering.Values.TBC",f"LB.PressTrain.Stage.{station}"]
  if role!="static":tags.append("LB.PressTrain.Role."+role);motion_counts[role]=motion_counts.get(role,0)+1
  a.tags=[unreal.Name(t) for t in tags];visuals.append(a)
for row in supports["instances"]:
 # v661 baked source rotation into each unique local mesh; actor rotation stays zero.
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*row["location_cm"]),unreal.Rotator())
 a.set_actor_label(row["object"].replace("_v640","_v662").replace("_v660","_v662"));a.static_mesh_component.set_static_mesh(support_assets[row["asset"]])
 a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_editor_property("can_ever_affect_navigation",False)
 a.tags=[unreal.Name(scope),unreal.Name("LB.Asset.CandidateNotPromoted"),unreal.Name("LB.PressTrain.SourceRole."+row["role"]),unreal.Name("LB.RuntimeMovingPartSeparation.Pending")];visuals.append(a)
cube=library.load_asset("/Engine/BasicShapes/Cube.Cube");collision=[]
def cube_actor(label,loc,scale,visible,collide=True,role=None,offset=None):
 a=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label);a.static_mesh_component.set_static_mesh(cube);a.set_actor_scale3d(unreal.Vector(*scale))
 if offset:a.static_mesh_component.set_relative_location(unreal.Vector(*offset),False,False)
 a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collide else unreal.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_collision_profile_name(unreal.Name("BlockAll" if collide else "NoCollision"));a.static_mesh_component.set_editor_property("can_ever_affect_navigation",collide)
 a.set_is_temporarily_hidden_in_editor(not visible);tags=[scope,"LB.Asset.CandidateNotPromoted"]
 if collide:tags.append("LB.Collision.Proxy")
 if role:tags.append("LB.PressTrain.Role."+role)
 a.tags=[unreal.Name(t) for t in tags]
 if collide:collision.append(a)
 return a
# Press blockers and hinge-following gate blockers.
gate_row=next(r for r in modules["assets"] if r["role"]=="access_gate")
for station,y in station_y.items():
 cube_actor(f"LB_{station}_COLL_Base",(0,y,110),(2.7,2.7,1.1),False);cube_actor(f"LB_{station}_COLL_Upper",(0,y,520),(2.8,2.8,3.0),False)
 gl=list(gate_row["actor_location_cm"]);gl[1]+=y-1500;cube_actor(f"LB_{station}_COLL_AccessGate",gl,(.30,1.62,1.90),False,True,"access_gate",(0,50,0))
# Zero-credit visible service decks/rails and collidable ladders.
for station,y in station_y.items():
 cube_actor(f"LB_{station}_ServiceDeck",(535,y,305),(.75,2.45,.09),True)
 cube_actor(f"LB_{station}_RailTop",(602,y,427),(.035,2.4,.035),True)
 for yy in (y-235,y+235):cube_actor(f"LB_{station}_RailPost",(602,yy,365),(.035,.035,.65),True)
 for xx in (575,615):cube_actor(f"LB_{station}_LadderStile",(xx,y-255,152),(.025,.025,1.52),True)
 for z in (25,62,99,136,173,210,247,284):cube_actor(f"LB_{station}_LadderRung",(595,y-255,z),(.22,.025,.025),True)
floor=cube_actor("LB_TrainA_ReviewFloor",(0,2250,-10),(11,31,.1),True)
station_class=unreal.load_class(None,"/Script/LineBossCarFactory.LBPressTrainAStation");authority=actors.spawn_actor_from_class(station_class,unreal.Vector(),unreal.Rotator());authority.set_actor_label("LB_PressTrainA_Authority_v662");authority.tags=[unreal.Name(scope),unreal.Name("LB.Authority.PressTrain.Native"),unreal.Name("LB.Asset.CandidateNotPromoted")]
nav=actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume,unreal.Vector(0,2250,250),unreal.Rotator());nav.set_actor_label("LB_TrainA_NavBounds_v662");nav.set_actor_scale3d(unreal.Vector(14,34,5));nav.tags=[unreal.Name("LB.Navigation.ValidationBounds"),unreal.Name("LB.Asset.CandidateNotPromoted")]
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():raise RuntimeError("Failed saving v662")
AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({"revision":"v662","status":"PASS__COMPLETE_TRAIN_A_MODULAR_UNREAL_BUILD__RUNTIME_NAV_VISUAL_PENDING","map":MAP,
 "presses":5,"station_y_cm":station_y,"validated_module_asset_count":len(module_assets),"module_visual_instances":60,"support_assets":support_records,"support_instances":len(supports["instances"]),
 "motion_role_instances":motion_counts,"native_authority":"/Script/LineBossCarFactory.LBPressTrainAStation","visual_collision":"NoCollision","collision_proxy_count":len(collision),
 "navigation_bounds":True,"navigation_path_test":"pending","runtime_test":"pending in-map PIE","whole_train_visual_test":"pending","protected_map_modified":False,"promotion_authorized":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_V662_BUILD_PASS")
