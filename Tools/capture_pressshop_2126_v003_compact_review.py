"""Serial Unreal screenshots of the isolated compact v003 candidate; no map save."""
import hashlib
import json
from pathlib import Path
import time

import unreal

MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v003/Maps/LB_PressShop_2126_Steam_v003"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "CompactV003_hero_nocoil_v038_dx12"
RECEIPT = ROOT / "pressshop_2126_v003_hero_nocoil_v038_review.json"
SHOTS = (
    ("CAM v003 | compact whole-flow overview", "01_compact_whole_flow.png"),
    ("CAM v003 | compact press hero", "02_compact_press_hero.png"),
    ("CAM v003 | coil to first press story", "03_coil_to_first_press.png"),
    ("CAM v003 | inspection to stillage story", "04_inspection_to_stillage.png"),
)
SIZE = (1920, 1080)
WARMUP_SECONDS = 8.0
SETTLE_SECONDS = 2.0
TIMEOUT_SECONDS = 60.0
MIN_BYTES = 4096


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if RECEIPT.exists():
    raise RuntimeError("Refusing to overwrite review receipt")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load compact v003 map")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label, _filename in SHOTS if label not in actors]
if missing:
    raise RuntimeError("Missing v003 cameras: " + ", ".join(missing))
ROOT.mkdir(parents=True, exist_ok=True)
for _label, filename in SHOTS:
    if (ROOT / filename).exists():
        raise RuntimeError("Refusing to overwrite v003 screenshot " + filename)
world = unreal.EditorLevelLibrary.get_editor_world()
for command in (
    "viewmode lit",
    "r.Streaming.FullyLoadUsedTextures 1",
    "r.HighResScreenshotDelay 1",
    "sg.ViewDistanceQuality 3",
    "sg.AntiAliasingQuality 4",
    "sg.ShadowQuality 3",
    "sg.GlobalIlluminationQuality 3",
    "sg.ReflectionQuality 3",
    "sg.PostProcessQuality 3",
    "r.Tonemapper.Quality 5",
):
    unreal.SystemLibrary.execute_console_command(world, command)
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
state = {"index": 0, "task": None, "started": 0.0, "settled": 0.0, "rows": [], "error": None, "warmup": time.monotonic() + WARMUP_SECONDS}
tick_handle = None


def close(status):
    global tick_handle
    RECEIPT.write_text(json.dumps({"status": status, "map": MAP, "resolution": list(SIZE), "captures": state["rows"], "error": state["error"], "no_map_save": True, "capture_mode": "serial_high_resolution_unreal_editor"}, indent=2), encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log("PRESSSHOP_2126_V003_CAPTURE_" + status)


def launch():
    label, filename = SHOTS[state["index"]]
    task = unreal.AutomationLibrary.take_high_res_screenshot(SIZE[0], SIZE[1], str(ROOT / filename), camera=actors[label], mask_enabled=False, capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW, comparison_notes="Compact v003 review " + label, delay=0.0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError("Unreal rejected screenshot " + filename)
    state["task"], state["started"], state["settled"] = task, time.monotonic(), 0.0


def advance(_delta):
    try:
        if time.monotonic() < state["warmup"]:
            return
        if state["task"] is None:
            if state["index"] == len(SHOTS):
                close("PASS__COMPACT_V003_IN_ENGINE_REVIEW")
                return
            launch()
            return
        _label, filename = SHOTS[state["index"]]
        path, elapsed = ROOT / filename, time.monotonic() - state["started"]
        if not state["task"].is_task_done():
            if elapsed > TIMEOUT_SECONDS:
                state["error"] = "Screenshot task timed out: " + filename
                close("FAIL__COMPACT_V003_IN_ENGINE_REVIEW")
            return
        if not path.is_file() or path.stat().st_size < MIN_BYTES:
            if elapsed > TIMEOUT_SECONDS:
                state["error"] = "Screenshot absent or incomplete: " + filename
                close("FAIL__COMPACT_V003_IN_ENGINE_REVIEW")
            return
        if not state["settled"]:
            state["settled"] = time.monotonic()
            return
        if time.monotonic() - state["settled"] < SETTLE_SECONDS:
            return
        state["rows"].append({"camera": SHOTS[state["index"]][0], "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
        state["index"] += 1
        state["task"] = None
    except Exception as exc:
        state["error"] = repr(exc)
        close("FAIL__COMPACT_V003_IN_ENGINE_REVIEW")


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
tick_handle = unreal.register_slate_post_tick_callback(advance)
