"""Fresh inside-hall four-train evidence cameras after rejecting v702 exterior occlusions."""
from pathlib import Path
import json,unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Visual_v702"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CompleteTrainsABCD_Cameras_v704";OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_complete_trains_cameras_build_v704.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v704")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive failed")
def camera(label,loc,target,fov):
 a=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label);a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False);a.camera_component.set_editor_property("field_of_view",fov);a.tags=[unreal.Name("LB.VisualGate.FixedCamera.v704"),unreal.Name("LB.Asset.CandidateNotPromoted")];return a
cams=[camera("LB_V704_CAM_FourTrainEastEnd",(8800,-1000,1150),(3900,-1000,430),88),
      camera("LB_V704_CAM_FourTrainEastHigh",(8200,-1000,1700),(3900,-1000,350),94),
      camera("LB_V704_CAM_FourTrainSouthEast",(7600,-5400,1450),(3900,-800,420),96)]
for i,y in enumerate((-4300,-2100,100,2300),1):
 light=api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(6900,y,1250),unreal.Rotator());light.set_actor_label(f"LB_V704_LIGHT_Train{i}_EndFill");light.point_light_component.set_editor_property("intensity",2200.0);light.point_light_component.set_editor_property("attenuation_radius",2200.0);light.tags=[unreal.Name("LB.Validation.Lighting.v704"),unreal.Name("LB.Asset.CandidateNotPromoted")]
if not levels.save_current_level():raise RuntimeError("save failed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v704","status":"PASS__INSIDE_HALL_CAMERAS__CAPTURE_PENDING","map":MAP,"cameras":[a.get_actor_label() for a in cams],"rejected_v702_cameras":["LB_V702_CAM_FourTrainSouthOverview","LB_V702_CAM_FourTrainHighSouth"]},indent=2),encoding="utf-8");unreal.log("LINE_BOSS_PRESS_SHOP_COMPLETE_TRAINS_CAMERAS_V704_PASS")
