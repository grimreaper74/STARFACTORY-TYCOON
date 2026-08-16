from pathlib import Path
from datetime import datetime, timezone
import json, time, unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/clean_support_dock_contact_v20260809_v071"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/clean_support_dock_contact_capture_v20260809_v071.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError("load failed")
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
for actor in actors.get_all_level_actors():
    if "roof" in actor.get_actor_label().lower() or "ceiling" in actor.get_actor_label().lower():
        actor.set_actor_hidden_in_game(True)

for index, (location, intensity, radius) in enumerate([
    (unreal.Vector(-900, -3200, 1600), 2500.0, 3000.0),
    (unreal.Vector(900, -3200, 1600), 2500.0, 3000.0),
]):
    light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label(f"LB_REVIEW_DockContact_v071_{index + 1:02d}")
    light.point_light_component.set_editor_property("intensity", intensity)
    light.point_light_component.set_editor_property("attenuation_radius", radius)
    light.point_light_component.set_editor_property("cast_shadows", False)

camera_location = unreal.Vector(1800, -3150, 1050)
target = unreal.Vector(-350, -4170, 75)
camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
camera.set_actor_label("LB_CAM_DockContact_v071")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, target), False)
camera.camera_component.set_editor_property("field_of_view", 58.0)
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.ExposureOffset -0.5")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
path = OUT / "support_fleet_four_docks_contact_lit.png"
if path.exists(): path.unlink()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(path), camera=camera, mask_enabled=False, capture_hdr=False, delay=2, force_game_view=True)
if not task.is_valid_task(): raise RuntimeError("invalid screenshot")
started=time.monotonic(); handle=None
def tick(_):
    global handle
    exists=path.exists() and path.stat().st_size>1024
    if not exists and time.monotonic()-started<90:return
    if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
    AUDIT.parent.mkdir(parents=True,exist_ok=True)
    AUDIT.write_text(json.dumps({"generated_utc":datetime.now(timezone.utc).isoformat(),"status":"FRESH_LIT_DOCK_CONTACT__VISUAL_REVIEW_REQUIRED" if exists else "CAPTURE_FAIL","map":MAP,"capture":str(path),"bytes":path.stat().st_size if path.exists() else 0,"review_lighting":"TRANSIENT_ONLY__MAP_NOT_SAVED","meshy_credits_used":0},indent=2),encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False); unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
