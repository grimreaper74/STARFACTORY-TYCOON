from pathlib import Path
from datetime import datetime, timezone
import json, time, unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = '/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032'
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / 'Saved/ValidationScreenshots/PressShopIntegration/clean_full_floor_paint_v20260809_v033'
AUDIT = ROOT / 'Saved/Audits/PressShopIntegration/clean_full_floor_paint_capture_v20260809_v033.json'
VIEWS = [
    ('whole_shop_overhead.png', unreal.Vector(0, -1000, 10500), unreal.Vector(0, 0, 0), 78.0),
    ('inbound_storage_oblique.png', unreal.Vector(-10300, -4200, 3300), unreal.Vector(-4200, 0, 250), 68.0),
    ('press_trains_oblique.png', unreal.Vector(9800, -4700, 3400), unreal.Vector(4800, 0, 350), 70.0),
    ('south_walkway_robot_docks.png', unreal.Vector(2500, -4750, 1050), unreal.Vector(0, -4050, 250), 66.0),
]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError('Could not load full floor paint map')
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
# Review-only roof hiding: do not save these transient visibility changes.
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label().lower()
    if 'roof' in label or 'ceiling' in label:
        actor.set_actor_hidden_in_game(True)
unreal.SystemLibrary.execute_console_command(world, 'viewmode unlit')
unreal.SystemLibrary.execute_console_command(world, 'r.Streaming.FullyLoadUsedTextures 1')
unreal.SystemLibrary.execute_console_command(world, 'r.ExposureOffset 0.0')
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
cameras=[]
for i, (_, loc, target, fov) in enumerate(VIEWS):
    cam=actors.spawn_actor_from_class(unreal.CameraActor,loc,unreal.Rotator())
    cam.set_actor_label(f'LB_CAM_FloorPaint_v033_{i}')
    cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(loc,target),False)
    cam.camera_component.set_editor_property('field_of_view',fov)
    cameras.append(cam)
index=0; task=None; started=0.0; handle=None; records=[]
def begin():
    global task,started
    filename,_,_,_=VIEWS[index]; path=OUT/filename
    if path.exists(): path.unlink()
    task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(path),camera=cameras[index],mask_enabled=False,capture_hdr=False,delay=0,force_game_view=True)
    if not task.is_valid_task(): raise RuntimeError('Invalid screenshot task '+filename)
    started=time.monotonic()
def tick(_):
    global index,handle
    filename,_,_,_=VIEWS[index]; path=OUT/filename
    if not (path.exists() and path.stat().st_size>1024) and time.monotonic()-started<90: return
    ok=path.exists() and path.stat().st_size>1024
    records.append({'file':str(path),'bytes':path.stat().st_size if path.exists() else 0,'status':'CAPTURE_PASS' if ok else 'CAPTURE_FAIL'})
    index+=1
    if index<len(VIEWS): begin(); return
    if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
    passed=all(r['status']=='CAPTURE_PASS' for r in records)
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    AUDIT.write_text(json.dumps({'generated_utc':datetime.now(timezone.utc).isoformat(),'status':'FRESH_UNREAL_CAPTURES__VISUAL_REVIEW_REQUIRED' if passed else 'CAPTURE_FAIL','map':MAP,'captures':records,'meshy_credits_used':0},indent=2),encoding='utf-8')
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()
begin(); handle=unreal.register_slate_post_tick_callback(tick)
