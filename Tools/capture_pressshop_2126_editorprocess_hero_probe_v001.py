"""Probe a real editor viewport in a hidden separate Unreal Editor process.

Unlike the rejected commandlet capture, this starts the full existing editor
binary off-screen and captures through its level viewport. It opens only the
fresh candidate and exits when the frame is saved.
"""

import hashlib
import json
from pathlib import Path
import time
import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "EditorProcessProbe_v001" / "hero_probe.png"
RECEIPT = OUT.parent / "hero_probe_receipt.json"
CAMERA_LABEL = "CAM | 2126 Steam hero overview"
STARTED = time.monotonic()
HANDLE = None


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finish(status, **extra):
    global HANDLE
    payload = {"status": status, "map": MAP, "camera": CAMERA_LABEL, "full_editor_real_rhi_probe": True, **extra}
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("Refusing to overwrite editor-process probe evidence")
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
    unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False, delay=0.0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError("Unreal rejected editor-process screenshot task")

    def tick(_delta):
        elapsed = time.monotonic() - STARTED
        if task.is_task_done() and OUT.is_file() and OUT.stat().st_size >= 4096:
            finish("PASS__FULL_EDITOR_REAL_RHI_HERO_PROBE", bytes=OUT.stat().st_size, sha256=sha256(OUT), elapsed_seconds=round(elapsed, 2))
        elif elapsed >= 90.0:
            finish("FAIL__FULL_EDITOR_REAL_RHI_HERO_PROBE", error="screenshot task did not yield a valid image", elapsed_seconds=round(elapsed, 2))

    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as error:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    finish("FAIL__FULL_EDITOR_REAL_RHI_HERO_PROBE", error=str(error))
