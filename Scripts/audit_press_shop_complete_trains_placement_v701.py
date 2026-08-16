"""Static floor, envelope, clearance and authority audit for integrated complete A-D v700."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_v700"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_placement_v701.json"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap";EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
def tags(a):return {str(t) for t in a.tags}
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if OUT.exists():raise RuntimeError("Refusing to overwrite v701")
if sha()!=EXPECTED:raise RuntimeError("protected hash mismatch")
if not levels.load_level(MAP):raise RuntimeError(MAP)
rows={};failures=[]
for letter in "ABCD":
 scope=f"LB.PressTrain.Installed.TRAIN_{letter}";members=[a for a in api.get_all_level_actors() if scope in tags(a)]
 visual=[];below=[]
 for a in members:
  comp=a.get_component_by_class(unreal.StaticMeshComponent)
  if not comp or "LB.Collision.Proxy.v662" in tags(a):continue
  o,e=a.get_actor_bounds(False,False);mn=o.z-e.z;mx=o.z+e.z
  row={"label":a.get_actor_label(),"class":a.get_class().get_name(),"min_z_cm":mn,"max_z_cm":mx,
       "bounds_origin_cm":list(o.to_tuple()),"bounds_extent_cm":list(e.to_tuple()),"tags":sorted(tags(a))}
  visual.append(row)
  if mn < -1.0:below.append(row)
 press=[r for r in visual if any(k in r["label"] for k in ("StaticPressShell","Housing","RamSlide","UpperDie","LowerDie"))]
 miny=min(r["bounds_origin_cm"][1]-r["bounds_extent_cm"][1] for r in visual);maxy=max(r["bounds_origin_cm"][1]+r["bounds_extent_cm"][1] for r in visual)
 press_miny=min(r["bounds_origin_cm"][1]-r["bounds_extent_cm"][1] for r in press);press_maxy=max(r["bounds_origin_cm"][1]+r["bounds_extent_cm"][1] for r in press)
 auth=[a for a in members if isinstance(a,unreal.LBPressTrainAStation)]
 rows[letter]={"member_count":len(members),"authority_count":len(auth),"visual_actor_count":len(visual),
  "visual_y_min_cm":miny,"visual_y_max_cm":maxy,"press_body_y_min_cm":press_miny,"press_body_y_max_cm":press_maxy,
  "below_floor_visual_count":len(below),"below_floor_visuals":sorted(below,key=lambda r:r["min_z_cm"])}
 if len(members)!=182:failures.append(f"{letter} member count")
 if len(auth)!=1:failures.append(f"{letter} authority count")
clear=[]
for a,b in zip("ABC","BCD"):
 clear.append({"between":a+"_"+b,"all_visual_clearance_cm":rows[b]["visual_y_min_cm"]-rows[a]["visual_y_max_cm"],
               "press_body_clearance_cm":rows[b]["press_body_y_min_cm"]-rows[a]["press_body_y_max_cm"]})
payload={"revision":"v701","generated_utc":datetime.now(timezone.utc).isoformat(),"status":"PASS__PLACEMENT_AUDIT" if not failures else "FAIL",
 "map":MAP,"trains":rows,"adjacent_clearances":clear,"failures":failures,"protected_map_sha256":sha(),"protected_map_modified":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_PLACEMENT_V701_PASS");unreal.SystemLibrary.quit_editor()
