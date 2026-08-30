"""Capture serial in-editor review frames for the roofless 2126 Press Shop.

v001 queued three HighResShot requests at once. Unreal owns one high-resolution
capture request at a time, so only its final frame was written. This version
waits for each completed PNG before asking for the next one. It loads only the
fresh candidate, never saves a map, and leaves the editor open for review.
"""

import hashlib
import json
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "MeshyCandidate_v002"
RECEIPT = ROOT / "pressshop_2126_meshy_review_v002.json"
SHOTS = (
    ("CAM | 2126 Steam hero overview", "01_hero_overview.png"),
    ("CAM | 2126 operator line", "02_operator_line.png"),
    ("CAM | 2126 draw nexus", "03_draw_nexus.png"),
)
SIZE = (1920, 1080)
MIN_BYTES = 4096
PER_SHOT_TIMEOUT_SECONDS = 60.0
SETTLE_SECONDS = 1.5


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if RECEIPT.exists():
    raise RuntimeError("Refusing to overwrite review receipt: " + str(RECEIPT))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load fresh candidate map")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label, _ in SHOTS if label not in actors]
if missing:
    raise RuntimeError("Missing named review cameras: " + ", ".join(missing))

ROOT.mkdir(parents=True, exist_ok=True)
for _, filename in SHOTS:
    if (ROOT / filename).exists():
        raise RuntimeError("Refusing to overwrite review image: " + str(ROOT / filename))

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

state = {
    "index": 0,
    "task": None,
    "started": 0.0,
    "finished": 0.0,
    "rows": [],
    "error": None,
}
tick_handle = None


def start_shot():
    camera_label, filename = SHOTS[state["index"]]
    path = ROOT / filename
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        SIZE[0], SIZE[1], str(path), camera=actors[camera_label],
        mask_enabled=False, capture_hdr=False,
        comparison_tolerance=unreal.ComparisonTolerance.LOW,
        comparison_notes="PressShop 2126 Meshy candidate serial review: " + camera_label,
        delay=0.0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError("Unreal rejected screenshot task for " + camera_label)
    state["task"] = task
    state["started"] = time.monotonic()
    state["finished"] = 0.0
    unreal.log("PRESSSHOP_2126_SERIAL_CAPTURE_STARTED__" + filename)


def finish(status):
    global tick_handle
    payload = {
        "status": status,
        "map": MAP,
        "resolution": list(SIZE),
        "captures": state["rows"],
        "error": state["error"],
        "no_map_save": True,
        "no_protected_map_loaded_or_saved": True,
        "capture_mode": "serial_high_res_screenshot",
    }
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log("PRESSSHOP_2126_MESHY_REVIEW_V002_" + status)


def advance(_delta):
    try:
        if state["task"] is None:
            if state["index"] >= len(SHOTS):
                finish("PASS__FRESH_UNREAL_MESHY_CANDIDATE_SERIAL_REVIEW_CAPTURE")
                return
            start_shot()
            return

        camera_label, filename = SHOTS[state["index"]]
        path = ROOT / filename
        elapsed = time.monotonic() - state["started"]
        if not state["task"].is_task_done():
            if elapsed > PER_SHOT_TIMEOUT_SECONDS:
                state["error"] = "screenshot task timeout: " + filename
                finish("FAIL__FRESH_UNREAL_MESHY_CANDIDATE_SERIAL_REVIEW_CAPTURE")
            return

        if not path.is_file() or path.stat().st_size < MIN_BYTES:
            if elapsed > PER_SHOT_TIMEOUT_SECONDS:
                state["error"] = "missing or incomplete screenshot: " + str(path)
                finish("FAIL__FRESH_UNREAL_MESHY_CANDIDATE_SERIAL_REVIEW_CAPTURE")
            return

        if not state["finished"]:
            state["finished"] = time.monotonic()
            return
        if time.monotonic() - state["finished"] < SETTLE_SECONDS:
            return

        state["rows"].append({
            "camera": camera_label,
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        })
        unreal.log("PRESSSHOP_2126_SERIAL_CAPTURE_COMPLETED__" + filename)
        state["index"] += 1
        state["task"] = None
    except Exception as exc:
        state["error"] = repr(exc)
        finish("FAIL__FRESH_UNREAL_MESHY_CANDIDATE_SERIAL_REVIEW_CAPTURE")


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
tick_handle = unreal.register_slate_post_tick_callback(advance)
