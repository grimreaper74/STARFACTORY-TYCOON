"""Read-only, serial Unreal capture of the retained roofless open-bay candidate.

This is an evidence review only.  It opens neither the active 2126 candidate
nor the protected v438 map and never saves a map.  The two camera actors were
authored with the open-bay candidate and show whether its real lorry-to-press
material story is a stronger visual foundation than the newer sparse layout.
"""

import json
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamOpenBay_v004"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop" / "SteamOpenBayReference_v001"
RECEIPT = ROOT / "steam_openbay_reference_v001.json"
SHOTS = (
    ("Steam wishlist full-process overview", "01_full_process_overview.png"),
    ("Steam wishlist press-line hero", "02_press_line_hero.png"),
)
SIZE = (1920, 1080)
MIN_BYTES = 4096
WARMUP_SECONDS = 8.0
SETTLE_SECONDS = 2.0
TIMEOUT_SECONDS = 60.0


if RECEIPT.exists():
    raise RuntimeError("Refusing to overwrite reference receipt: " + str(RECEIPT))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load roofless open-bay reference candidate")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label, _ in SHOTS if label not in actors]
if missing:
    raise RuntimeError("Reference candidate lacks camera(s): " + ", ".join(missing))

ROOT.mkdir(parents=True, exist_ok=True)
for _, filename in SHOTS:
    if (ROOT / filename).exists():
        raise RuntimeError("Refusing to overwrite reference image: " + str(ROOT / filename))

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
    "r.Lumen.ScreenProbeGather.Temporal.MaxFramesAccumulated 32",
    "r.Lumen.Reflections.Temporal 1",
    "r.Tonemapper.Quality 5",
):
    unreal.SystemLibrary.execute_console_command(world, command)
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

state = {"index": 0, "task": None, "started": 0.0, "finished": 0.0, "rows": [], "error": None, "warmup_until": time.monotonic() + WARMUP_SECONDS}
tick_handle = None


def sha256(path):
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def finish(status):
    global tick_handle
    RECEIPT.write_text(json.dumps({
        "status": status,
        "map": MAP,
        "capture_mode": "serial_high_res_screenshot",
        "resolution": list(SIZE),
        "captures": state["rows"],
        "error": state["error"],
        "no_map_save": True,
    }, indent=2), encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log("STEAM_OPENBAY_REFERENCE_V001_" + status)


def advance(_delta):
    try:
        if time.monotonic() < state["warmup_until"]:
            return
        if state["task"] is None:
            if state["index"] >= len(SHOTS):
                finish("PASS__READ_ONLY_OPENBAY_REFERENCE_CAPTURE")
                return
            label, filename = SHOTS[state["index"]]
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                SIZE[0], SIZE[1], str(ROOT / filename), camera=actors[label],
                mask_enabled=False, capture_hdr=False,
                comparison_tolerance=unreal.ComparisonTolerance.LOW,
                comparison_notes="Read-only Steam open-bay reference: " + label,
                delay=0.0, force_game_view=True)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected screenshot task: " + filename)
            state["task"] = task
            state["started"] = time.monotonic()
            state["finished"] = 0.0
            return

        label, filename = SHOTS[state["index"]]
        path = ROOT / filename
        elapsed = time.monotonic() - state["started"]
        if not state["task"].is_task_done():
            if elapsed > TIMEOUT_SECONDS:
                raise RuntimeError("screenshot task timed out: " + filename)
            return
        if not path.is_file() or path.stat().st_size < MIN_BYTES:
            if elapsed > TIMEOUT_SECONDS:
                raise RuntimeError("screenshot missing or incomplete: " + str(path))
            return
        if not state["finished"]:
            state["finished"] = time.monotonic()
            return
        if time.monotonic() - state["finished"] < SETTLE_SECONDS:
            return
        state["rows"].append({"camera": label, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)})
        state["index"] += 1
        state["task"] = None
    except Exception as exc:
        state["error"] = repr(exc)
        finish("FAIL__READ_ONLY_OPENBAY_REFERENCE_CAPTURE")


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
tick_handle = unreal.register_slate_post_tick_callback(advance)
