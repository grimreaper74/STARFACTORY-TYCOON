"""Fresh direct-v386 physical signboards with builder-ready dynamic identity text."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386";BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386.umap";BASE_SHA="057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038"
MAP="/Game/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v418";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v418.umap";DEST="/Game/LineBoss/Candidates/PressShop/TrainIdentity/PhysicalSigns_v411";MATROOT="/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_dynamic_train_identity_build_v418.json";ROWS={"A":-4300.0,"B":-2100.0,"C":100.0,"D":2300.0}
def sha(p):
 d=hashlib.sha256()
 with p.open("rb") as s:
  for c in iter(lambda:s.read(1048576),b""):d.update(c)
 return d.hexdigest().upper()
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("protected v386 drift")
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing overwrite v418")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("child failed")
green=lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredCairnwellGreen_v086");charcoal=lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredFoundryCharcoal_v086");yellow=lib.load_asset(MATROOT+"/M_CA_MW_PR009_LayeredSafetyYellow_v086")
if not all(isinstance(m,unreal.MaterialInterface) for m in (green,charcoal,yellow)):raise RuntimeError("materials missing")
added=[]
for train,y in ROWS.items():
 mesh=lib.load_asset(f"{DEST}/SM_CA_MW_PressTrainIdentity_{train}_v410")
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(f"mesh {train}")
 board=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(1115,y,850),unreal.Rotator())
 board.set_actor_label(f"LB_V418_TRAIN_{train}_PHYSICAL_IDENTITY_BOARD");board.static_mesh_component.set_static_mesh(mesh);board.set_actor_scale3d(unreal.Vector(100,100,100))
 for i,m in enumerate((green,charcoal,yellow,charcoal)):board.static_mesh_component.set_material(i,m)
 board.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);board.static_mesh_component.set_editor_property("can_ever_affect_navigation",False);board.static_mesh_component.set_editor_property("generate_overlap_events",False)
 board.tags=[unreal.Name(v) for v in (f"LB.PressTrain.Identity.Train{train}","LB.FactoryBuilder.ReusablePhysicalSign","LB.Identity.VisualOnly.NoRuntimeAuthority","LB.Collision.NoCollision.VisualOnly","LB.Navigation.None","LB.Asset.Candidate.v418","LB.Asset.CandidateNotPromoted")]
 text=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(1106,y,850),unreal.Rotator())
 text.set_actor_label(f"LB_V418_TRAIN_{train}_DYNAMIC_ALLOCATED_LABEL");c=text.text_render;c.set_text(f"PRESS TRAIN {train}\nS01 - S07");c.set_world_size(27);c.set_text_render_color(unreal.Color(224,236,228,255));c.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER);c.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER);c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);c.set_editor_property("can_ever_affect_navigation",False);c.set_editor_property("generate_overlap_events",False)
 text.tags=[unreal.Name(v) for v in (f"LB.PressTrain.DisplayDesignation.{train}","LB.PressTrain.Identity.AllocatedAutomatically","LB.PressTrain.Stations.S01-S07","LB.FactoryBuilder.DynamicIdentityLabel","LB.Identity.VisualOnly.NoRuntimeAuthority","LB.Collision.NoCollision.VisualOnly","LB.Navigation.None","LB.Asset.Candidate.v418","LB.Asset.CandidateNotPromoted")]
 added.append({"train":train,"board":board.get_actor_label(),"dynamic_label":text.get_actor_label(),"display":f"PRESS TRAIN {train} / S01-S07","persistent_guid":"RUNTIME_REQUIRED_NOT_INVENTED"})
counts={k:sum(1 for a in actors.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{k}" in {str(t) for t in a.tags}) for k in "ABCD"};fail=[]
if len(added)!=4:fail.append("identity count")
if counts!={"A":338,"B":338,"C":338,"D":338}:fail.append(f"train counts {counts}")
if not levels.save_current_level():fail.append("save")
if sha(BASE_FILE)!=BASE_SHA:fail.append("base changed")
payload={"$schema":"cairnwell/audit/press-shop-dynamic-train-identity-build-v418/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__PHYSICAL_BOARDS_WITH_DYNAMIC_ALLOCATED_LABELS__FRESH_VISUAL_RUNTIME_SAVE_GATES_REQUIRED__NOT_PROMOTED" if not fail else "FAIL__V418_NOT_A_PARENT","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"rejected_predecessors":["v398","v400","v404","v408","v412","v416"],"identities":added,"train_actor_counts":counts,"builder_contract":{"next_available_designation":"A..Z","survivors_never_renumbered":True,"station_ids":"<designation>-S01..S07","immutable_save_guid":"required","custom_display_name":"future supported","runtime_allocator":"OPEN_NOT_CLAIMED"},"promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError(";".join(fail))
unreal.SystemLibrary.quit_editor()
