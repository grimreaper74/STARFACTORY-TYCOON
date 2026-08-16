"""Import v014 fixed shell into a fresh collision-safe v034 Train A child."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v014/FBX/SM_CA_MW_PTA_PresentationShell_v014.fbx"
SOURCE_MANIFEST=ROOT/"SourceAssets/Candidate/PressTrains/TrainA/PresentationShell_v014/PRESS_TRAIN_A_PRESENTATION_SHELL_MANIFEST_v014.json"
BASE="/Game/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034"
MAP="/Game/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v035"
DEST="/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v035"
ASSET=DEST+"/SM_CA_MW_PTA_PresentationShell_v014"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAFabricationCollisionSafeCandidate_v034.umap"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainAPresentationShellCandidate_v035.umap"
OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_presentation_shell_build_v035.json"
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors_api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest().upper()
manifest=json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
if manifest.get("status")!="SOURCE_ONLY_HIGH_DETAIL_FIXED_SHELL__UNREAL_INTAKE_REQUIRED__NOT_PROMOTED": raise RuntimeError("unexpected v014 source status")
if lib.does_directory_exist(DEST) or lib.does_asset_exist(MAP) or OUT.exists(): raise RuntimeError("refusing to overwrite v035 candidate")
base_hash=sha(BASE_FILE)
task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE),"destination_path":DEST,"destination_name":"SM_CA_MW_PTA_PresentationShell_v014","automated":True,"replace_existing":False,"save":True})
ui=unreal.FbxImportUI(); ui.set_editor_properties({"import_mesh":True,"import_as_skeletal":False,"import_materials":True,"import_textures":False,"mesh_type_to_import":unreal.FBXImportType.FBXIT_STATIC_MESH})
data=ui.get_editor_property("static_mesh_import_data"); data.set_editor_properties({"combine_meshes":True,"convert_scene":True,"convert_scene_unit":True,"transform_vertex_to_absolute":False,"bake_pivot_in_vertex":False,"generate_lightmap_u_vs":True,"auto_generate_collision":False,"remove_degenerates":True})
task.set_editor_property("options",ui); unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError("v014 shell import missing")
if not levels.new_level_from_template(MAP,BASE): raise RuntimeError("could not create fresh v034 child")
actor=actors_api.spawn_actor_from_object(mesh,unreal.Vector(0,0,0),unreal.Rotator(0,0,0),False)
actor.set_actor_label("CA_MW_PTA_PresentationShell_v014_FIXED")
actor.tags=[unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.v014","LB.PressTrain.TrainA","LB.Asset.Candidate.v035","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision")]
comp=actor.static_mesh_component; comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); comp.set_editor_property("can_ever_affect_navigation",False); comp.set_editor_property("cast_shadow",True)
all_actors=actors_api.get_all_level_actors()
train=[a for a in all_actors if isinstance(a,unreal.StaticMeshActor) and "LB.PressTrain.ProcessDirection.PositiveY" in {str(t) for t in a.tags}]
stations=[a for a in all_actors if a.get_class().get_name()=="LBPressTrainAStation"]
bounds=mesh.get_bounds(); size=[float(bounds.box_extent.x*2),float(bounds.box_extent.y*2),float(bounds.box_extent.z*2)]
fail=[]
if len(train)!=336: fail.append(f"retained train actors {len(train)} != 336")
if len(stations)!=1: fail.append(f"native station count {len(stations)} != 1")
if str(comp.get_collision_enabled())!="CollisionEnabled.NO_COLLISION": fail.append("shell collision not disabled")
if comp.get_editor_property("can_ever_affect_navigation"): fail.append("shell affects navigation")
if not levels.save_current_level(): fail.append("map save failed")
if sha(BASE_FILE)!=base_hash: fail.append("protected v034 parent changed")
payload={"$schema":"cairnwell/audit/press-train-a-presentation-shell-build-v035/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__V014_FIXED_SHELL_IN_FRESH_COLLISION_SAFE_V034_CHILD__LIVE_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V035_NOT_A_PARENT","base":BASE,"map":MAP,"base_sha256":base_hash,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"source_fbx_sha256":sha(SOURCE),"shell_asset":ASSET,"shell_bounds_cm":size,"shell_material_slots":len(mesh.get_editor_property("static_materials")),"shell_collision":"NoCollision","shell_affects_navigation":False,"retained_train_actor_count":len(train),"native_station_count":len(stations),"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8"); print(json.dumps(payload,indent=2))
if fail: raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
