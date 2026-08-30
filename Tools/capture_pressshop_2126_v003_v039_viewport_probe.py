"""One viewport-based in-engine capture to validate the v039 hero composition."""
import hashlib
import json
from pathlib import Path
import time

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
CAMERA_LABEL = "CAM v003 | compact press hero"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "CompactV003_hero_story_v039_viewport_probe" / "hero_viewport.png"
RECEIPT = OUT.parent / "hero_viewport_receipt.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
EXPECTED = {
    PROTECTED: "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    V002: "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
START = time.monotonic()
HANDLE = None
TASK = None
REQUESTED = False


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def finish(status, **extra):
    global HANDLE
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            status = "FAIL__PROTECTED_MAP_CHANGED_DURING_VIEWPORT_PROBE"
            extra["protected_map_mismatch"] = str(path)
    RECEIPT.write_text(json.dumps({"status": status, "map": MAP, "camera": CAMERA_LABEL, "output": str(OUT), **extra}, indent=2), encoding="utf-8")
    if HANDLE is not None:
        unreal.unregister_slate_post_tick_callback(HANDLE)
        HANDLE = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


try:
    if OUT.exists() or RECEIPT.exists():
        raise RuntimeError("Refusing to overwrite v039 viewport evidence")
    for path, expected in EXPECTED.items():
        if digest(path) != expected:
            raise RuntimeError("Protected baseline changed before viewport probe: " + str(path))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load v003 candidate")
    camera = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == CAMERA_LABEL), None)
    if not isinstance(camera, unreal.CineCameraActor):
        raise RuntimeError("Named v039 camera unavailable")
    world = unreal.EditorLevelLibrary.get_editor_world()
    for command in ("viewmode lit", "r.ForceDebugViewModes 0", "r.Streaming.FullyLoadUsedTextures 1", "r.HighResScreenshotDelay 12", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 3", "sg.GlobalIlluminationQuality 3"):
        unreal.SystemLibrary.execute_console_command(world, command)
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera.get_actor_location(), camera.get_actor_rotation())
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)

    def tick(_delta):
        global TASK, REQUESTED
        elapsed = time.monotonic() - START
        if not REQUESTED and elapsed >= 12.0:
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            TASK = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), mask_enabled=False, capture_hdr=False, delay=0.0, force_game_view=True)
            if not TASK.is_valid_task():
                finish("FAIL__V039_VIEWPORT_PROBE", error="Unreal rejected viewport screenshot task")
                return
            REQUESTED = True
            unreal.log("PRESSSHOP_V039_VIEWPORT_CAPTURE_REQUESTED")
        elif REQUESTED and TASK.is_task_done() and OUT.is_file() and OUT.stat().st_size >= 4096:
            finish("PASS__V039_VIEWPORT_PROBE", bytes=OUT.stat().st_size, sha256=hashlib.sha256(OUT.read_bytes()).hexdigest(), elapsed_seconds=round(elapsed, 2))
        elif elapsed >= 120.0:
            finish("FAIL__V039_VIEWPORT_PROBE", error="Viewport screenshot task did not produce an image", elapsed_seconds=round(elapsed, 2))

    HANDLE = unreal.register_slate_post_tick_callback(tick)
except Exception as exc:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    finish("FAIL__V039_VIEWPORT_PROBE", error=repr(exc))
