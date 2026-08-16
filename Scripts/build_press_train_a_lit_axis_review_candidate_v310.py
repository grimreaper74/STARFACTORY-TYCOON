"""Add neutral review lighting to the upright v309 Train A studio successor."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309";MAP="/Game/LineBoss/Maps/LB_PressTrainA_LitAxisReviewCandidate_v310";BASE_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_AxisCorrectedStudioCandidate_v309.umap";MAP_FILE=ROOT/"Content/LineBoss/Maps/LB_PressTrainA_LitAxisReviewCandidate_v310.umap";BASE_SHA="EDABB0950A6D9D94C00E40F88E1BD4D6A7E63C94FD6A992ED1830A2480E25542";OUT=ROOT/"Saved/Audits/PressTrains/press_train_a_lit_axis_review_build_v310.json"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
if sha(BASE_FILE)!=BASE_SHA:raise RuntimeError("v309 hash drift")
lib=unreal.EditorAssetLibrary;levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if lib.does_asset_exist(MAP) or OUT.exists():raise RuntimeError("refusing to overwrite v310")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("fresh v309 child failed")
actors=api.get_all_level_actors();candidate=next((a for a in actors if "LB.PressTrain.TrainA.ModularSource.v037" in {str(t) for t in a.tags}),None)
if candidate is None:raise RuntimeError("candidate missing")
o,e=candidate.get_actor_bounds(False)
lights=[]
for i,x in enumerate((o.x-2200,o.x-750,o.x+750,o.x+2200),1):
 for side,y in (("front",o.y-900),("rear",o.y+900)):
  light=api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(x,y,o.z+650),unreal.Rotator());light.set_actor_label(f"LB_V310_NEUTRAL_{side.upper()}_{i:02d}");comp=light.point_light_component;comp.set_editor_properties({"intensity":45000.0,"attenuation_radius":2600.0,"source_radius":120.0,"soft_source_radius":260.0,"cast_shadows":False,"light_color":unreal.Color(235,242,255,255)});lights.append(light.get_actor_label())
fail=[]
if len(lights)!=8:fail.append(f"light count {len(lights)}")
if not levels.save_current_level():fail.append("save failed")
if sha(BASE_FILE)!=BASE_SHA:fail.append("v309 changed")
payload={"$schema":"cairnwell/audit/press-train-a-lit-axis-review-v310/v1","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__UPRIGHT_NEUTRAL_LIGHTING_REVIEW_READY__NOT_PROMOTED" if not fail else "FAIL__V310_NOT_EVIDENCE","base":BASE,"base_sha256":BASE_SHA,"map":MAP,"map_sha256":sha(MAP_FILE) if MAP_FILE.exists() else None,"neutral_review_lights":lights,"geometry_changed":False,"runtime_authority_changed":False,"promotion_authorized":False,"failures":fail};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8");print(json.dumps(payload,indent=2))
if fail:raise RuntimeError("; ".join(fail))
unreal.SystemLibrary.quit_editor()
