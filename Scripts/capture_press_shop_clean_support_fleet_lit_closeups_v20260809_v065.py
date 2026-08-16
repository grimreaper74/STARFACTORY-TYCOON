from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059"
ROOT = Path(unreal.Paths.project_dir())
OUT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/clean_support_fleet_mr01_01_alt_lit_v20260809_v068"
AUDIT = ROOT / "Saved/Audits/PressShopIntegration/clean_support_fleet_mr01_01_alt_lit_v20260809_v068.json"
LABELS = ["LB_CLEAN_Robot_MR01_01"]

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load current clean press-shop map")
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()

for actor in actors.get_all_level_actors():
    label = actor.get_actor_label().lower()
    if "roof" in label or "ceiling" in label:
        actor.set_actor_hidden_in_game(True)

by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
missing = [label for label in LABELS if label not in by_label]
if missing:
    raise RuntimeError("Missing support fleet actors: " + ", ".join(missing))

targets = []
cameras = []
lights = []
for index, label in enumerate(LABELS):
    robot = by_label[label]
    origin, extent = robot.get_actor_bounds(False)
    target = unreal.Vector(origin.x, origin.y, origin.z + max(40.0, extent.z * 0.18))
    # Dock-side front-three-quarter view, close enough to inspect materials and floor contact.
    camera_location = unreal.Vector(
        origin.x - max(430.0, extent.x * 2.6),
        origin.y + max(600.0, extent.y * 3.2),
        origin.z + max(235.0, extent.z * 1.65),
    )
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
    camera.set_actor_label(f"LB_CAM_SupportFleetCloseup_v066_{index + 1:02d}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, target), False)
    camera.camera_component.set_editor_property("field_of_view", 42.0)
    cameras.append(camera)

    key_location = unreal.Vector(origin.x - 180.0, origin.y + 260.0, origin.z + 420.0)
    key = actors.spawn_actor_from_class(unreal.PointLight, key_location, unreal.Rotator())
    key.set_actor_label(f"LB_REVIEW_SupportFleetKey_v066_{index + 1:02d}")
    key.point_light_component.set_editor_property("intensity", 350.0)
    key.point_light_component.set_editor_property("attenuation_radius", 1400.0)
    key.point_light_component.set_editor_property("cast_shadows", False)
    lights.append(key)
    targets.append({
        "label": label,
        "class": robot.get_class().get_name(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "camera_cm": [camera_location.x, camera_location.y, camera_location.z],
    })

unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.ExposureOffset -0.5")
unreal.SystemLibrary.execute_console_command(world, "r.Tonemapper.Sharpen 0.5")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
task = None
started = 0.0
handle = None
records = []

def filename_for(i):
    return f"{i + 1:02d}_{LABELS[i].replace('LB_CLEAN_Robot_', '').lower()}_dock_lit.png"

def begin_capture():
    global task, started
    path = OUT / filename_for(index)
    if path.exists():
        path.unlink()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1600, 1200, str(path), camera=cameras[index], mask_enabled=False,
        capture_hdr=False, delay=2, force_game_view=True
    )
    if not task.is_valid_task():
        raise RuntimeError("Invalid screenshot task: " + str(path))
    started = time.monotonic()

def tick(_delta):
    global index, handle
    path = OUT / filename_for(index)
    exists = path.exists() and path.stat().st_size > 1024
    if not exists and time.monotonic() - started < 90:
        return
    records.append({
        "unit": LABELS[index], "file": str(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "status": "CAPTURE_PASS" if exists else "CAPTURE_FAIL",
    })
    index += 1
    if index < len(LABELS):
        begin_capture()
        return
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    passed = all(record["status"] == "CAPTURE_PASS" for record in records)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps({
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FRESH_LIT_SUPPORT_FLEET_CLOSEUPS__VISUAL_REVIEW_REQUIRED" if passed else "CAPTURE_FAIL",
        "map": MAP,
        "targets": targets,
        "captures": records,
        "review_lighting": "TRANSIENT_ONLY__MAP_NOT_SAVED",
        "meshy_credits_used": 0,
    }, indent=2), encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

begin_capture()
handle = unreal.register_slate_post_tick_callback(tick)
