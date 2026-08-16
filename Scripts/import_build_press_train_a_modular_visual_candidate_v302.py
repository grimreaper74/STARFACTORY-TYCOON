"""Isolated no-physics Unreal visual intake of retained Train A v037 under v301 lighting."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/FBX/SM_CA_MW_PressTrainA_ModularAssembly_v037.fbx"
SOURCE_SHA="25162CC50513E15B44008E188AF460E3956C2FE8F31CBD3BC5E055D12357FB7E"
DECISION=ROOT/"Saved/Audits/PressTrains/press_train_a_modular_source_decision_v037.json"
BASE="/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301.umap"
BASE_SHA="8ECBEF72EE262899A15E70B2924EF8F2F1EB8A8480E49525DDFA4FF9245D8BF6"
MAP="/Game/LineBoss/Maps/LB_PressShop_TrainAModularVisualIntakeCandidate_v302"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAModularVisualIntakeCandidate_v302.umap"
DEST="/Game/LineBoss/Candidates/PressTrains/TrainA/ModularVisual_v302"
ASSET=DEST+"/SM_CA_MW_PressTrainA_ModularAssembly_v037"
OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_modular_visual_intake_build_v302.json"
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as handle:
  for chunk in iter(lambda:handle.read(1048576),b""):h.update(chunk)
 return h.hexdigest().upper()
decision=json.loads(DECISION.read_text(encoding="utf-8"))
if decision.get("isolated_unreal_visual_intake_authorized") is not True or any(decision.get(k) is not False for k in ("replacement_authorized","runtime_authority_authorized","collision_authorized","navigation_authorized","promotion_authorized")):raise RuntimeError("v037 decision contract invalid")
if sha(SOURCE)!=SOURCE_SHA:raise RuntimeError("v037 FBX hash drift")
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("v301 hash drift")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v302")
task=unreal.AssetImportTask();task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"destination_name":"SM_CA_MW_PressTrainA_ModularAssembly_v037","automated":True,"replace_existing":False,"save":True})
options=unreal.FbxImportUI();options.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
data=options.get_editor_property("static_mesh_import_data");data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",options);unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("v037 mesh import missing")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v301 child failed")
base_hash=sha(BASE_FILE)
actors=api.get_all_level_actors();native=[a for a in actors if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
for actor in native:
 actor.set_is_temporarily_hidden_in_editor(True);actor.set_actor_hidden_in_game(True)
candidate=api.spawn_actor_from_object(mesh,unreal.Vector(1600,-4300,0),unreal.Rotator(),False)
candidate.set_actor_label("CA_MW_PTA_ModularTrain_v037_VISUAL_ONLY")
candidate.set_actor_scale3d(unreal.Vector(100,-100,100))
candidate.tags=[unreal.Name(x) for x in ("LB.PressTrain.TrainA.ModularSource.v037","LB.Asset.Candidate.v302","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision","LB.Navigation.None","LB.RuntimeAuthority.None","LB.EngineeringValues.TBC")]
comp=candidate.static_mesh_component;comp.set_collision_profile_name(unreal.Name("NoCollision"),True);comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property("generate_overlap_events",False);comp.set_editor_property("can_ever_affect_navigation",False);comp.set_editor_property("cast_shadow",True)
origin,extent=candidate.get_actor_bounds(False,False);size=[extent.x*2,extent.y*2,extent.z*2];location=[candidate.get_actor_location().x,candidate.get_actor_location().y,candidate.get_actor_location().z]
fail=[]
if len(native)!=338:fail.append(f"native Train A count {len(native)} != 338")
if not (4500<=size[0]<=6000 and 700<=size[1]<=1800 and 800<=size[2]<=1100):fail.append(f"unexpected candidate size {size}")
if str(comp.get_collision_profile_name())!="NoCollision" or comp.get_editor_property("can_ever_affect_navigation"):fail.append("candidate physical policy invalid")
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=base_hash:fail.append("protected v301 changed")
payload={"$schema":"cairnwell/audit/press-train-a-modular-visual-intake-v302/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__ISOLATED_COMPLETE_TRAIN_A_VISUAL_INTAKE__FRESH_UNREAL_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V302_NOT_A_PARENT","base":BASE,"base_sha256":base_hash,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"source_fbx_sha256":SOURCE_SHA,"asset":ASSET,"candidate_location_cm":location,"candidate_scale":[100,-100,100],"candidate_world_size_cm":size,"hidden_native_train_a_actor_count":len(native),"native_actors_deleted":False,"collision":"NoCollision","affects_navigation":False,"runtime_authority":"None","replacement_authorized":False,"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
