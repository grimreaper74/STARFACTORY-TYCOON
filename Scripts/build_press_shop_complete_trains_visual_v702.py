"""Remove isolated review floors and add non-gameplay whole-shop evidence rig to v700 successor."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_v700"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Visual_v702"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_visual_build_v702.json"
PROTECTED=ROOT/"Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap";EXPECTED="5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
def sha():return hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing to overwrite v702")
if sha()!=EXPECTED:raise RuntimeError("protected hash mismatch")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive v702 failed")
all_actors=api.get_all_level_actors();floors=[a for a in all_actors if "ReviewFloor" in a.get_actor_label()]
if len(floors)!=4 or not api.destroy_actors(floors):raise RuntimeError(f"review floor removal failed: {len(floors)}")
for a in api.get_all_level_actors():
 vals=[str(t) for t in a.tags if str(t)!="LB.Authority.WorldPlacement.TBCNotInvented"]
 if any(f"LB.PressTrain.Installed.TRAIN_{x}" in vals for x in "ABCD"):
  if "LB.WorldPlacement.CurrentWidenedDatum.v702" not in vals:vals.append("LB.WorldPlacement.CurrentWidenedDatum.v702")
  a.tags=[unreal.Name(v) for v in vals]
def camera(label,loc,target,fov):
 a=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label)
 a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False)
 a.camera_component.set_editor_property("field_of_view",fov);a.tags=[unreal.Name("LB.VisualGate.FixedCamera.v702"),unreal.Name("LB.Asset.CandidateNotPromoted")];return a
cameras=[camera("LB_V702_CAM_FourTrainSouthOverview",(8200,-6800,1500),(3800,-1000,450),78),
         camera("LB_V702_CAM_FourTrainHighSouth",(7200,-6100,1750),(3600,-900,350),82),
         camera("LB_V702_CAM_TrainAOperator",(7000,-5550,900),(3900,-4300,430),72)]
for i,y in enumerate((-4300,-2100,100,2300),1):
 light=api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(4200,y-350,1250),unreal.Rotator());light.set_actor_label(f"LB_V702_LIGHT_Train{i}_EvidenceFill")
 light.point_light_component.set_editor_property("intensity",2600.0);light.point_light_component.set_editor_property("attenuation_radius",2600.0)
 light.point_light_component.set_editor_property("light_color",unreal.Color(235,242,255,255));light.tags=[unreal.Name("LB.Validation.Lighting.v702"),unreal.Name("LB.Asset.CandidateNotPromoted")]
if not levels.save_current_level():raise RuntimeError("save v702 failed")
if sha()!=EXPECTED:raise RuntimeError("protected changed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v702","generated_utc":datetime.now(timezone.utc).isoformat(),
 "status":"PASS__REAL_SHOP_FLOOR_ONLY__CURRENT_WIDENED_DATUMS__VISUAL_CAPTURE_PENDING","map":MAP,"source_map":BASE,
 "isolated_review_floors_removed":len(floors),"fixed_cameras":[a.get_actor_label() for a in cameras],"evidence_lights":4,
 "gameplay_geometry_changed":False,"meshy_credits_used":0,"protected_map_sha256":sha(),"protected_map_modified":False},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_VISUAL_V702_PASS")
