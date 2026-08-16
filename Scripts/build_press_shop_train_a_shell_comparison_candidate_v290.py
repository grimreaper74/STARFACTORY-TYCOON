"""Install one fixed Train A shell in a fresh direct-v288 inherited-hall child."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()); BASE="/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288"; MAP="/Game/LineBoss/Maps/LB_PressShop_TrainAShellComparisonCandidate_v290"; BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288.umap"; MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAShellComparisonCandidate_v290.umap"; OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_train_a_shell_comparison_build_v290.json"
ASSET="/Game/LineBoss/Candidates/PressTrains/TrainA/PresentationShell_v035/SM_CA_MW_PTA_PresentationShell_v014"
MATS={"charcoal":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_Charcoal_Integration_v004","green":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_Green_Integration_v004","steel":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_WorkedSteel_Integration_v004","yellow":"/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v004/Materials/M_CA_MW_PTA_SafetyYellow_Integration_v004"}
CAMERAS=[("LB_V290_CAM_TrainAOperatorShell",(7200,-5450,620),(3900,-4500,430),50),("LB_V290_CAM_TrainAShellClose",(6350,-5600,520),(3850,-4700,470),46),("LB_V290_CAM_TrainAShellManagement",(8650,-6100,1180),(4200,-4450,480),56)]
lib=unreal.EditorAssetLibrary; levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest().upper()
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v290")
base_hash=sha(BASE_FILE); mesh=lib.load_asset(ASSET); mats={k:lib.load_asset(v) for k,v in MATS.items()}
if not isinstance(mesh,unreal.StaticMesh) or not all(isinstance(v,unreal.MaterialInterface) for v in mats.values()):raise RuntimeError("shell or material source missing")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh direct-v288 child failed")
before=api.get_all_level_actors(); train_a_before=[a for a in before if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in a.tags}]
a=api.spawn_actor_from_object(mesh,unreal.Vector(1600,-4300,0),unreal.Rotator(0,-90,0),False); a.set_actor_label("LB_V290_PTA_PRESENTATION_SHELL_V014")
a.set_actor_scale3d(unreal.Vector(100,-100,100)); a.tags=[unreal.Name(x) for x in ("LB.PressTrain.PresentationShell.TrainA.v014","LB.PressTrain.TrainA","LB.Asset.Candidate.v290","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision","LB.Integration.InheritedHallComparisonOnly")]
c=a.static_mesh_component; slots=mesh.get_editor_property("static_materials"); bindings=[];fail=[]
for i,s in enumerate(slots):
 n=str(s.material_slot_name).lower(); key="green" if "green" in n else "yellow" if "yellow" in n else "steel" if "workedsteel" in n or ("steel" in n and "dark" not in n) else "charcoal" if "dark" in n or "charcoal" in n else None
 if key is None:fail.append(f"unmapped shell slot {i}:{n}");continue
 c.set_material(i,mats[key]);bindings.append({"index":i,"slot":str(s.material_slot_name),"material":mats[key].get_path_name()})
c.set_collision_profile_name(unreal.Name("NoCollision"),True);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property("generate_overlap_events",False);c.set_editor_property("can_ever_affect_navigation",False);c.set_editor_property("cast_shadow",True)
camera_labels=[]
for label,loc,target,fov in CAMERAS:
 cam=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());cam.set_actor_label(label);cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(*target)),False);cam.camera_component.set_editor_properties({"field_of_view":float(fov),"aspect_ratio":16/9,"constrain_aspect_ratio":True});cam.tags=[unreal.Name("LB.Camera.Validation"),unreal.Name("LB.Camera.Fixed.TrainAShell.v290"),unreal.Name("LB.Asset.Candidate.v290"),unreal.Name("LB.Asset.CandidateNotPromoted")];camera_labels.append(label)
after=api.get_all_level_actors();train_a_after=[x for x in after if "LB.PressTrain.Installed.TRAIN_A" in {str(t) for t in x.tags}]
if len(train_a_before)!=338 or len(train_a_after)!=338:fail.append(f"installed Train A contract changed {len(train_a_before)}->{len(train_a_after)}")
if len(bindings)!=len(slots):fail.append(f"material bindings {len(bindings)}/{len(slots)}")
if str(c.get_collision_profile_name())!="NoCollision" or c.get_editor_property("can_ever_affect_navigation"):fail.append("shell collision/navigation contract invalid")
# Exact known installed transform from v223-v288 retained Train A: source local (x,y)->world (y+1600,-x-4300).
expected={"S02":[2350,-4742],"S03":[3100,-4742],"S04":[3850,-4742],"S05":[4600,-4742],"S06":[5350,-4742]}
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=base_hash:fail.append("protected v288 changed")
p={"status":"PASS__ONE_TRAIN_A_DETAIL_SHELL_IN_FRESH_DIRECT_V288_INHERITED_HALL_CHILD__VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V290_NOT_A_PARENT","base":BASE,"map":MAP,"base_sha256":base_hash,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"shell_asset":ASSET,"shell_transform":{"location_cm":[1600,-4300,0],"rotation_pyr":[0,-90,0],"scale":[100,-100,100],"mapping":"source local (x,y)->installed world (y+1600,-x-4300)"},"expected_operator_shell_stage_centres_cm":expected,"shell_material_bindings":bindings,"shell_collision_profile":str(c.get_collision_profile_name()),"shell_affects_navigation":False,"installed_train_a_actor_count_before":len(train_a_before),"installed_train_a_actor_count_after":len(train_a_after),"added_cameras":camera_labels,"added_lights":[],"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(p,indent=2),encoding="utf-8");print(json.dumps(p,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
