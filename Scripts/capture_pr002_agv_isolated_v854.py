from pathlib import Path
from datetime import datetime, timezone
import json, time, unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_PR002_AGV_IsolatedValidation_v853"
ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/r"Saved\ValidationScreenshots\PressShopIntegration\pr002_agv_isolated_v862"
AUDIT=ROOT/r"Saved\Audits\PressShopIntegration\pr002_agv_capture_v862.json"
VIEWS=[
 ("01_AGV_Hero_Unreal_v862.png",(650,-520,275),(350,0,35),52.0),
 ("02_AGV_Front_Unreal_v862.png",(350,-550,150),(350,0,35),48.0),
 ("03_PR002_Loaded_Hero_Unreal_v862.png",(-30,-640,390),(-300,0,155),55.0),
 ("04_PR002_Loaded_Front_Unreal_v862.png",(-300,-720,230),(-300,0,150),48.0),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
OUT.mkdir(parents=True,exist_ok=True); world=unreal.EditorLevelLibrary.get_editor_world()

# Transient presentation floor and lighting; the validation map remains unchanged.
cube=unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(25,0,-12),unreal.Rotator())
floor.static_mesh_component.set_static_mesh(cube); floor.set_actor_scale3d(unreal.Vector(9,8,0.1))
floor.static_mesh_component.set_cast_shadow(False)
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,700),unreal.Rotator(pitch=-45,yaw=-35,roll=0)); sun.light_component.set_editor_property("intensity",0.4)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500),unreal.Rotator()); sky.light_component.set_editor_property("intensity",0.15)
for loc,intensity,radius in [((-250,-350,450),600,800),((500,-250,350),450,700),((0,400,350),350,700)]:
 p=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*loc),unreal.Rotator()); p.light_component.set_editor_properties({"intensity":intensity,"attenuation_radius":radius})

unreal.SystemLibrary.execute_console_command(world,"viewmode lit")
unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator()); c.set_actor_label(f"LB_TRANSIENT_v862_CAM_{i+1:02d}")
 c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False)
 c.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16/9,"constrain_aspect_ratio":True,"post_process_blend_weight":1.0})
 pp=c.camera_component.get_editor_property("post_process_settings")
 pp.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":-6.0})
 c.camera_component.set_editor_property("post_process_settings",pp); cams.append(c)
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 name,_,_,_=VIEWS[index]; path=OUT/name
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cams[index],mask_enabled=False,capture_hdr=False,delay=0.3,force_game_view=True); started=time.monotonic()
def tick(_):
 global index,handle
 name,_,_,_=VIEWS[index]; path=OUT/name
 # The offscreen renderer can report task completion before the PNG writer has
 # flushed the file. Wait for the actual evidence instead of racing the writer.
 if (not path.exists() or path.stat().st_size<=1024) and time.monotonic()-started<60:return
 ok=path.exists() and path.stat().st_size>1024
 records.append({"file":str(path),"bytes":path.stat().st_size if path.exists() else 0,"status":"CAPTURE_PASS" if ok else "CAPTURE_FAIL"}); index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r["status"]=="CAPTURE_PASS" for r in records); AUDIT.parent.mkdir(parents=True,exist_ok=True)
 AUDIT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"UNREAL_VISUAL_CAPTURES_READY_FOR_REVIEW" if passed else "CAPTURE_FAIL","map":MAP,"captures":records,"map_saved_during_capture":False},indent=2),encoding="utf-8")
 unreal.EditorPythonScripting.set_keep_python_script_alive(False); unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
