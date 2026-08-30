"""Serial live-editor capture of existing v438 cameras; never saves the map."""

import hashlib
import json
from pathlib import Path
import time
import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop438" / "Baseline_v001"
RECEIPT = ROOT / "pressshop_v438_readonly_capture_v001.json"
SHOTS = (
    ("LB_CAM_PressShop_ManagementOverview", "01_management_overview.png"),
    ("LB_WHOLE_V223_CAM_FrontEndToTrains", "02_frontend_to_trains.png"),
    ("LB_V301_CAM_FourTrainWideSpan", "03_four_train_wide.png"),
)
SIZE = (1920, 1080)
MIN_BYTES = 4096
TIMEOUT = 60.0
SETTLE_SECONDS = 2.0
WARMUP_SECONDS = 8.0


def digest(path):
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


if RECEIPT.exists():
    raise RuntimeError("Refusing to overwrite receipt")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load protected v438")
actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label, _ in SHOTS if label not in actors]
if missing:
    raise RuntimeError("Missing existing v438 cameras: " + ", ".join(missing))
ROOT.mkdir(parents=True, exist_ok=True)
for _, filename in SHOTS:
    if (ROOT / filename).exists():
        raise RuntimeError("Refusing to overwrite screenshot")

world = unreal.EditorLevelLibrary.get_editor_world()
for command in ("viewmode lit", "sg.ViewDistanceQuality 3", "sg.AntiAliasingQuality 4", "sg.ShadowQuality 3", "sg.GlobalIlluminationQuality 3", "sg.ReflectionQuality 3", "sg.PostProcessQuality 3", "r.Tonemapper.Quality 5"):
    unreal.SystemLibrary.execute_console_command(world, command)
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

state = {"index": 0, "task": None, "started": 0.0, "finished": 0.0, "warmup_until": time.monotonic() + WARMUP_SECONDS, "rows": [], "error": None}
tick = None


def finish(status):
    global tick
    RECEIPT.write_text(json.dumps({"status": status, "map": MAP, "captures": state["rows"], "error": state["error"], "no_map_save": True, "protected_map_read_only": True}, indent=2), encoding="utf-8")
    if tick is not None:
        unreal.unregister_slate_post_tick_callback(tick)
        tick = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log("PRESSSHOP_V438_READONLY_CAPTURE_V001_" + status)


def advance(_delta):
    try:
        if time.monotonic() < state["warmup_until"]:
            return
        if state["task"] is None:
            if state["index"] >= len(SHOTS):
                finish("PASS__PROTECTED_V438_READ_ONLY_SERIAL_CAPTURE")
                return
            label, filename = SHOTS[state["index"]]
            task = unreal.AutomationLibrary.take_high_res_screenshot(SIZE[0], SIZE[1], str(ROOT / filename), camera=actors[label], mask_enabled=False, capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW, comparison_notes="Protected v438 read-only review", delay=0.0, force_game_view=True)
            if not task.is_valid_task():
                raise RuntimeError("Unreal rejected shot: " + label)
            state["task"] = task
            state["started"] = time.monotonic()
            return
        label, filename = SHOTS[state["index"]]
        path = ROOT / filename
        elapsed = time.monotonic() - state["started"]
        if not state["task"].is_task_done():
            if elapsed > TIMEOUT:
                state["error"] = "timeout: " + filename
                finish("FAIL__PROTECTED_V438_READ_ONLY_SERIAL_CAPTURE")
            return
        if not path.is_file() or path.stat().st_size < MIN_BYTES:
            if elapsed > TIMEOUT:
                state["error"] = "missing file: " + filename
                finish("FAIL__PROTECTED_V438_READ_ONLY_SERIAL_CAPTURE")
            return
        if not state["finished"]:
            state["finished"] = time.monotonic()
            return
        if time.monotonic() - state["finished"] < SETTLE_SECONDS:
            return
        state["rows"].append({"camera": label, "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
        state["index"] += 1
        state["task"] = None
        state["finished"] = 0.0
    except Exception as error:
        state["error"] = repr(error)
        finish("FAIL__PROTECTED_V438_READ_ONLY_SERIAL_CAPTURE")


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
tick = unreal.register_slate_post_tick_callback(advance)
