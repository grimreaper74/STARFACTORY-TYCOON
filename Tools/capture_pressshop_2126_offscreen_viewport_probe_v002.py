"""Delayed off-screen viewport probe for the fresh 2126 candidate.

The v001 commandlet image was a blue empty frame despite a completed task.
This test waits for the map to render, explicitly sets the editor viewport from
the hero camera, then captures the viewport rather than relying on camera-task
selection in a commandlet.
"""

import hashlib
import json
from pathlib import Path
import time
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "OffscreenViewportProbe_v002" / "hero_viewport_probe.png"
RECEIPT = OUT.parent / "hero_viewport_probe_receipt.json"
CAMERA_LABEL = "CAM | 2126 Steam hero overview"
STARTED = time.monotonic()
HANDLE = None
TASK = None
REQUESTED = False


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finish(status, **extra):
    global HANDLE
    payload = {"status": status, "map": MAP, "camera": CAMERA_LABEL, "offscreen_viewport_probe": True, **extra}
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("Refusing to overwrite off-screen viewport probe evidence")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("could not load fresh candidate map")
    camera = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
    if camera is None:
        raise RuntimeError("missing named hero camera")
    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 48")
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global TASK, REQUESTED
        elapsed = time.monotonic() - STARTED
        if not REQUESTED and elapsed >= 12.0:
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            TASK = unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, str(OUT), mask_enabled=False, capture_hdr=False, delay=12.0, force_game_view=True)
            if not TASK.is_valid_task():
                finish("FAIL__OFFSCREEN_VIEWPORT_PROBE", error="Unreal rejected delayed viewport screenshot task")
                return
            REQUESTED = True
        elif REQUESTED and TASK.is_task_done() and OUT.is_file() and OUT.stat().st_size >= 4096:
            finish("PASS__OFFSCREEN_VIEWPORT_PROBE", bytes=OUT.stat().st_size, sha256=sha256(OUT), elapsed_seconds=round(elapsed, 2))
        elif elapsed >= 120.0:
            finish("FAIL__OFFSCREEN_VIEWPORT_PROBE", error="delayed viewport screenshot task did not yield a valid image", elapsed_seconds=round(elapsed, 2))

    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as error:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    finish("FAIL__OFFSCREEN_VIEWPORT_PROBE", error=str(error))
