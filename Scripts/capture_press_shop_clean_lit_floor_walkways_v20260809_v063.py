from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)

MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/clean_lit_floor_walkways_v20260809_v064"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/clean_lit_floor_walkways_capture_v20260809_v064.json"

VIEWS = [
    ("01_whole_shop_overhead_lit.png", unreal.Vector(0, -1200, 12800), unreal.Vector(0, 0, 0), 86.0),
    ("02_inbound_storage_walkways_lit.png", unreal.Vector(-10400, -5000, 3900), unreal.Vector(-4800, -200, 250), 68.0),
    ("03_press_trains_walkways_lit.png", unreal.Vector(10300, -5000, 3900), unreal.Vector(4900, 0, 350), 68.0),
    ("04_south_walkway_robot_docks_lit.png", unreal.Vector(2100, -5250, 1450), unreal.Vector(-250, -3950, 220), 65.0),
]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load current clean press-shop continuation")

OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()

# Review-only visibility and lighting. None of these transient changes are saved.
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label().lower()
    if "roof" in label or "ceiling" in label:
        actor.set_actor_hidden_in_game(True)

def aim(actor, target):
    actor.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(actor.get_actor_location(), target), False
    )

light_records = []
for index, (location, target, intensity, radius) in enumerate([
    (unreal.Vector(-7500, -1500, 7000), unreal.Vector(-5000, 0, 0), 9000.0, 11000.0),
    (unreal.Vector(0, -1000, 7800), unreal.Vector(0, 0, 0), 12000.0, 14000.0),
    (unreal.Vector(7500, -1500, 7000), unreal.Vector(5000, 0, 0), 9000.0, 11000.0),
    (unreal.Vector(0, -5200, 4200), unreal.Vector(0, -3600, 0), 7000.0, 9000.0),
]):
    light = actors.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label(f"LB_REVIEW_Light_v064_{index + 1:02d}")
    component = light.point_light_component
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("cast_shadows", False)
    light_records.append({"label": light.get_actor_label(), "intensity": intensity, "radius": radius})

unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.ExposureOffset -0.25")
unreal.SystemLibrary.execute_console_command(world, "r.Tonemapper.Sharpen 0.5")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

cameras = []
for index, (_, location, target, fov) in enumerate(VIEWS):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, location, unreal.Rotator())
    camera.set_actor_label(f"LB_CAM_LitFloorWalkway_v064_{index + 1:02d}")
    aim(camera, target)
    camera.camera_component.set_editor_property("field_of_view", fov)
    cameras.append(camera)

index = 0
task = None
started = 0.0
handle = None
records = []

def begin_capture():
    global task, started
    filename, _, _, _ = VIEWS[index]
    path = OUT / filename
    if path.exists():
        path.unlink()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(path), camera=cameras[index], mask_enabled=False,
        capture_hdr=False, delay=0, force_game_view=True
    )
    if not task.is_valid_task():
        raise RuntimeError("Invalid screenshot task: " + filename)
    started = time.monotonic()

def tick(_delta):
    global index, handle
    filename, _, _, _ = VIEWS[index]
    path = OUT / filename
    exists = path.exists() and path.stat().st_size > 1024
    if not exists and time.monotonic() - started < 90:
        return
    records.append({
        "file": str(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "status": "CAPTURE_PASS" if exists else "CAPTURE_FAIL",
    })
    index += 1
    if index < len(VIEWS):
        begin_capture()
        return
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    passed = all(record["status"] == "CAPTURE_PASS" for record in records)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FRESH_LIT_CAPTURES__VISUAL_REVIEW_REQUIRED" if passed else "CAPTURE_FAIL",
        "map": MAP,
        "review_only_transient_lights": light_records,
        "captures": records,
        "meshy_credits_used": 0,
    }, indent=2), encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

begin_capture()
handle = unreal.register_slate_post_tick_callback(tick)
