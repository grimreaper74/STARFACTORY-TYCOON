from pathlib import Path
from datetime import datetime, timezone
import json,time,unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP='/Game/LineBoss/Maps/LB_PressShop_PR009_PR010_OriginalGLB_Isolated_v881';ROOT=Path(unreal.Paths.project_dir())
OUT=ROOT/r'Saved\ValidationScreenshots\PressShopIntegration\pr009_pr010_original_glb_v882';AUDIT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_original_glb_capture_v882.json'
VIEWS=[
 ('01_PR009_Hero_v882.png',(-180,-760,360),(-650,0,150),54.0),
 ('02_PR009_Front_v882.png',(-650,-850,210),(-650,0,150),50.0),
 ('03_PR010_Hero_v882.png',(1180,-1220,520),(650,0,130),56.0),
 ('04_PR010_Front_v882.png',(650,-1350,260),(650,0,120),52.0),
]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(MAP)
OUT.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world();cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(160,0,-12),unreal.Rotator());floor.static_mesh_component.set_static_mesh(cube);floor.set_actor_scale3d(unreal.Vector(16,10,.1));floor.static_mesh_component.set_cast_shadow(False)
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,900),unreal.Rotator(pitch=-45,yaw=-35,roll=0));sun.light_component.set_editor_property('intensity',.22)
sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500),unreal.Rotator());sky.light_component.set_editor_property('intensity',.12)
cube_map=unreal.EditorAssetLibrary.load_asset('/Engine/EngineSky/DefaultTextureCube.DefaultTextureCube')
if cube_map:
 sky.light_component.set_editor_properties({'source_type':unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP,'cubemap':cube_map,'intensity':.55})
for loc,intensity,radius in [((-600,-450,650),180,1100),((650,-500,650),180,1300),((300,600,500),120,1200)]:
 p=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*loc),unreal.Rotator());p.light_component.set_editor_properties({'intensity':intensity,'attenuation_radius':radius})
unreal.SystemLibrary.execute_console_command(world,'viewmode lit');unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1');unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
cams=[]
for i,(_,loc,target,fov) in enumerate(VIEWS):
 c=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator());c.set_actor_label(f'LB_TRANSIENT_v865_CAM_{i+1:02d}');c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(c.get_actor_location(),unreal.Vector(*target)),False);c.camera_component.set_editor_properties({'field_of_view':fov,'aspect_ratio':16/9,'constrain_aspect_ratio':True,'post_process_blend_weight':1.0});cams.append(c)
index=0;task=None;started=0;handle=None;records=[]
def begin():
 global task,started
 name,_,_,_=VIEWS[index];path=OUT/name
 if path.exists():path.unlink()
 task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cams[index],mask_enabled=False,capture_hdr=False,delay=.4,force_game_view=True);started=time.monotonic()
def tick(_):
 global index,handle
 name,_,_,_=VIEWS[index];path=OUT/name
 if (not path.exists() or path.stat().st_size<=1024) and time.monotonic()-started<60:return
 ok=path.exists() and path.stat().st_size>1024;records.append({'file':str(path),'bytes':path.stat().st_size if path.exists() else 0,'status':'CAPTURE_PASS' if ok else 'CAPTURE_FAIL'});index+=1
 if index<len(VIEWS):begin();return
 if handle:unreal.unregister_slate_post_tick_callback(handle);handle=None
 passed=all(r['status']=='CAPTURE_PASS' for r in records);AUDIT.parent.mkdir(parents=True,exist_ok=True);AUDIT.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'UNREAL_VISUAL_CAPTURES_READY_FOR_REVIEW' if passed else 'CAPTURE_FAIL','map':MAP,'captures':records,'map_saved_during_capture':False},indent=2),encoding='utf-8');unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.quit_editor()
begin();handle=unreal.register_slate_post_tick_callback(tick)
