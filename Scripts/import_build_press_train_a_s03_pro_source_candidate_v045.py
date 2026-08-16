"""Import retained-direction S03 v022 beside the protected isolated Train A map."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PressModulePrototype_v022/FBX/SM_CA_MW_PressModulePrototype_v022.fbx"
SOURCE_SHA="4A9E47D3374AFC868987D50B77346B6EF49EC09AD8CB6B1DE75832781722952B"
DECISION=ROOT/"Saved/Audits/PressTrains/press_train_a_s03_compact_service_source_decision_v022.json"
BASE="/Game/LineBoss/Maps/LB_PressTrainAFabricatedShellCandidate_v041"
MAP="/Game/LineBoss/Maps/LB_PressTrainAS03ProSourceIntakeCandidate_v045"
DEST="/Game/LineBoss/Candidates/PressTrains/TrainA/S03ProSource_v045"
ASSET=DEST+"/SM_CA_MW_PressModulePrototype_v022"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAFabricatedShellCandidate_v041.umap"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAS03ProSourceIntakeCandidate_v045.umap"
OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_s03_pro_source_intake_build_v045.json"
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1048576),b""): h.update(c)
    return h.hexdigest().upper()
decision=json.loads(DECISION.read_text(encoding="utf-8"))
if decision.get("isolated_unreal_intake_authorized") is not True or decision.get("promotion_authorized") is not False: raise RuntimeError("v022 visual decision does not authorize isolated intake")
if sha(SOURCE)!=SOURCE_SHA: raise RuntimeError("v022 FBX hash drift")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v045")
base_hash=sha(BASE_FILE)
task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"destination_name":"SM_CA_MW_PressModulePrototype_v022","automated":True,"replace_existing":False,"save":True})
options=unreal.FbxImportUI(); options.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
data=options.get_editor_property("static_mesh_import_data"); data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",options); unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError("v022 mesh import missing")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("fresh v041 child failed")
actor=api.spawn_actor_from_object(mesh,unreal.Vector(-1300,0,0),unreal.Rotator(),False)
actor.set_actor_label("CA_MW_PTA_S03_ProSource_v022_COMPARISON_ONLY")
actor.set_actor_scale3d(unreal.Vector(100,-100,100))
actor.tags=[unreal.Name(x) for x in ("LB.PressTrain.S03.ProSource.v022","LB.PressTrain.TrainA","LB.Asset.Candidate.v045","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision","LB.RuntimeAuthority.None")]
comp=actor.static_mesh_component; comp.set_collision_profile_name(unreal.Name("NoCollision"),True); comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); comp.set_editor_property("generate_overlap_events",False); comp.set_editor_property("can_ever_affect_navigation",False); comp.set_editor_property("cast_shadow",True)
origin,extent=actor.get_actor_bounds(False,False); size=[extent.x*2,extent.y*2,extent.z*2]
all_actors=api.get_all_level_actors(); stations=[a for a in all_actors if a.get_class().get_name()=="LBPressTrainAStation"]
fail=[]
if len(stations)!=1: fail.append(f"native station count {len(stations)} != 1")
if not (680<=size[0]<=720 and 430<=size[1]<=470 and 920<=size[2]<=960): fail.append(f"unexpected world size {size}")
if str(comp.get_collision_profile_name())!="NoCollision" or comp.get_editor_property("can_ever_affect_navigation"): fail.append("comparison mesh collision/navigation contract invalid")
if len(mesh.get_editor_property("static_materials"))<5: fail.append("insufficient material slots")
if not levels.save_current_level(): fail.append("save failed")
if sha(BASE_FILE)!=base_hash: fail.append("protected v041 changed")
payload={"$schema":"cairnwell/audit/press-train-a-s03-pro-source-intake-v045/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__V022_ISOLATED_UNREAL_COMPARISON_INTAKE__FRESH_VISUAL_AND_TECHNICAL_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V045_NOT_A_PARENT","base":BASE,"map":MAP,"base_sha256":base_hash,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"source_fbx_sha256":sha(SOURCE),"asset":ASSET,"actor_location_cm":[-1300,0,0],"actor_scale":[100,-100,100],"world_size_cm":size,"material_slots":[str(x.material_slot_name) for x in mesh.get_editor_property("static_materials")],"collision":"NoCollision","affects_navigation":False,"native_station_count":len(stations),"replacement_authorized":False,"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2))
if fail: raise RuntimeError('; '.join(fail))
unreal.SystemLibrary.quit_editor()
