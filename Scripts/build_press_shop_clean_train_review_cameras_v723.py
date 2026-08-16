"""Add review-only cameras and fill lights to the clean new-trains map."""
from pathlib import Path
import json, unreal
ROOT=Path(unreal.Paths.project_dir());BASE="/Game/LineBoss/Maps/LB_PressShop_CleanMeshyTrains_v722"
MAP="/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CleanMeshyTrainsReview_v723"
OUT=ROOT/"Saved/Audits/PressShopIntegration/press_shop_clean_train_review_cameras_build_v723.json"
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);lib=unreal.EditorAssetLibrary
if OUT.exists() or lib.does_asset_exist(MAP):raise RuntimeError("Refusing overwrite v723")
if not levels.new_level_from_template(MAP,BASE):raise RuntimeError("derive v723 failed")
def camera(label,loc,target,fov):
 a=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label)
 a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc),unreal.Vector(*target)),False);a.camera_component.set_editor_property("field_of_view",fov)
 a.tags=[unreal.Name("LB.VisualGate.CleanNewTrainCamera.v723")];return a
cams=[camera("LB_V723_CAM_EastEnd",(9800,-1000,1150),(3900,-1000,430),88),camera("LB_V723_CAM_EastHigh",(8800,-1000,1850),(3900,-1000,350),94),camera("LB_V723_CAM_SouthEast",(8200,-6000,1500),(3900,-800,420),96)]
for i,y in enumerate((-4300,-2100,100,2300),1):
 l=api.spawn_actor_from_class(unreal.PointLight,unreal.Vector(6500,y,1100),unreal.Rotator());l.set_actor_label(f"LB_V723_LIGHT_Train{i}")
 l.point_light_component.set_editor_property("intensity",3200.0);l.point_light_component.set_editor_property("attenuation_radius",2600.0);l.tags=[unreal.Name("LB.Validation.Lighting.v723")]
if not levels.save_current_level():raise RuntimeError("save v723 failed")
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({"revision":"v723","status":"PASS__CLEAN_NEW_TRAINS_REVIEW_CAMERAS","map":MAP,"cameras":[a.get_actor_label() for a in cams]},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_CLEAN_TRAIN_REVIEW_CAMERAS_V723_PASS")
