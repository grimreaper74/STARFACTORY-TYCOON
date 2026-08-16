"""Fresh v354 child: expand A-D train centres to 22 m and preview v049 on all lines."""
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
BASE="/Game/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v354"
BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_TrainAProDetailVisualCandidate_v354.umap"
BASE_SHA="1EC3804CE40FE4F5312FBE658E436CC7AC7D05B09562D7ABBE28429333E9AD82"
MAP="/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356"
MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356.umap"
ASSET="/Game/LineBoss/Candidates/PressTrains/TrainA/ProDetailVisual_v354/SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_expanded_train_pitch_build_v356.json"

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as stream:
  for chunk in iter(lambda:stream.read(1048576),b""):h.update(chunk)
 return h.hexdigest().upper()

lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("protected v354 hash drift")
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v356")
mesh=lib.load_asset(ASSET)
if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError("v049 visual aggregate missing")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v354 child failed")

targets={"A":-4300.0,"B":-2100.0,"C":100.0,"D":2300.0}
old={"A":-4300.0,"B":-2600.0,"C":-900.0,"D":800.0}
inventory={};native_collision=0
for train in "ABCD":
 tag=f"LB.PressTrain.Installed.TRAIN_{train}"
 members=[];authorities=[]
 for actor in api.get_all_level_actors():
  tags={str(t) for t in actor.tags}
  label=actor.get_actor_label().upper()
  if tag not in tags and not label.startswith(f"LB_INST_PT{train}_"):continue
  members.append(actor)
  if actor.get_class().get_name()=="LBPressTrainAStation":authorities.append(actor)
 if len(members)!=338 or len(authorities)!=1:raise RuntimeError(f"Train {train} inventory invalid {len(members)}/{len(authorities)}")
 delta=targets[train]-old[train]
 if train!="A":
  for actor in members:
   actor.add_actor_world_offset(unreal.Vector(0,delta,0),False,False)
 # Hide native presentation only; keep every collision component and authority.
 hidden=0;collision_count=0
 for actor in members:
  if actor in authorities:continue
  actor.set_actor_hidden_in_game(True)
  for comp in actor.get_components_by_class(unreal.PrimitiveComponent):
   if comp.get_collision_enabled()!=unreal.CollisionEnabled.NO_COLLISION:
    collision_count+=1;native_collision+=1
   comp.set_visibility(False,True);comp.set_hidden_in_game(True,True)
  hidden+=1
 inventory[train]={"member_count":len(members),"authority_count":len(authorities),"hidden_native_presentation_count":hidden,"collision_component_count":collision_count,"old_centre_y_cm":old[train],"target_centre_y_cm":targets[train],"delta_y_cm":delta}

# Keep v354 A visual; add identical source-family previews for B-D. Identity signs remain separate/TBC.
visuals=[]
for actor in api.get_all_level_actors():
 if "LB.PressTrain.TrainA.ProDetailSource.v046" in {str(t) for t in actor.tags}:
  visuals.append(actor)
if len(visuals)!=1:raise RuntimeError(f"A visual count {len(visuals)}")
for train in "BCD":
 actor=api.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(),unreal.Rotator(0,0,90))
 actor.static_mesh_component.set_static_mesh(mesh);actor.set_actor_scale3d(unreal.Vector(100,100,100))
 actor.set_actor_label(f"CA_MW_PT{train}_v049_PRO_DETAIL_LAYOUT_PREVIEW_v356")
 comp=actor.static_mesh_component;comp.set_collision_profile_name("NoCollision");comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION);comp.set_editor_property("can_ever_affect_navigation",False);comp.set_editor_property("generate_overlap_events",False)
 actor.tags=[unreal.Name(v) for v in (f"LB.PressTrain.Train{train}.ProDetailLayoutPreview.v356","LB.Asset.CandidateNotPromoted","LB.Collision.NoCollision.VisualOnly","LB.Navigation.None","LB.RuntimeAuthority.None","LB.Identity.TrainSignTBC")]
 origin,extent=actor.get_actor_bounds(False)
 actor.add_actor_world_offset(unreal.Vector(3850-origin.x,targets[train]-origin.y,-(origin.z-extent.z)),False,False)
 visuals.append(actor)

visual_bounds={};fail=[]
for train,actor in zip("ABCD",visuals):
 origin,extent=actor.get_actor_bounds(False);size=[extent.x*2,extent.y*2,extent.z*2];floor=origin.z-extent.z
 visual_bounds[train]={"origin_cm":list(origin.to_tuple()),"size_cm":size,"floor_z_cm":floor}
 if abs(origin.y-targets[train])>1 or abs(floor)>1:fail.append(f"{train} alignment")
 if not (5650<=size[0]<=5900 and 1250<=size[1]<=1500 and 900<=size[2]<=1030):fail.append(f"{train} bounds {size}")
clear_gap=2200.0-visual_bounds["A"]["size_cm"][1]
if clear_gap<800:fail.append(f"clear gap {clear_gap}")
if native_collision<480:fail.append(f"native collision {native_collision}")
if fail:raise RuntimeError("v356 hard gate failed: "+"; ".join(fail))
if not levels.save_current_level():raise RuntimeError("v356 save failed")
payload={"$schema":"cairnwell/audit/press-shop-expanded-train-pitch-build-v356/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__ISOLATED_22M_FOUR_TRAIN_LAYOUT_STUDY__FRESH_VISUAL_AND_ROUTE_GATES_REQUIRED__NOT_PROMOTED","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE),"centre_pitch_cm":2200.0,"completed_visual_envelope_width_cm":visual_bounds["A"]["size_cm"][1],"adjacent_clear_gap_cm":clear_gap,"train_inventory":inventory,"visual_bounds":visual_bounds,"native_collision_components_preserved":native_collision,"exterior_shell_enlarged":False,"reason_shell_not_enlarged":"existing floor envelope contains proposed centres; route and column gates remain open","identity_signs":"TBC_SEPARATE_PER_TRAIN","runtime_authority":"NATIVE_PRESERVED","promotion_authorized":False,"failures":fail}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8");print(json.dumps(payload,indent=2));unreal.SystemLibrary.quit_editor()
