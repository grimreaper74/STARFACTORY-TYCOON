"""Capture fresh, in-editor review frames for the roofless 2126 candidate.

Execute from the existing Unreal Editor via Tools > Execute Python Script.
It loads only the fresh candidate and takes three camera-actor screenshots;
it neither saves maps nor exits the editor.
"""

import hashlib
import json
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_v001/Maps/LB_PressShop_2126_Steam_v001"
ROOT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots" / "PressShop2126" / "MeshyCandidate_v001"
RECEIPT = ROOT / "pressshop_2126_meshy_review_v001.json"
SHOTS = (
    ("CAM | 2126 Steam hero overview", "01_hero_overview.png"),
    ("CAM | 2126 operator line", "02_operator_line.png"),
    ("CAM | 2126 draw nexus", "03_draw_nexus.png"),
)
SIZE = (1920, 1080)


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


if RECEIPT.exists():
    raise RuntimeError("Refusing to overwrite review receipt: " + str(RECEIPT))
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("Could not load candidate map")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
missing = [label for label, _ in SHOTS if label not in actors]
if missing:
    raise RuntimeError("Missing named review cameras: " + ", ".join(missing))
ROOT.mkdir(parents=True, exist_ok=True)

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

tasks = []
for camera_label, filename in SHOTS:
    path = ROOT / filename
    if path.exists():
        raise RuntimeError("Refusing to overwrite review image: " + str(path))
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        SIZE[0], SIZE[1], str(path), camera=actors[camera_label],
        mask_enabled=False, capture_hdr=False,
        comparison_tolerance=unreal.ComparisonTolerance.LOW,
        comparison_notes="PressShop 2126 Meshy candidate fresh in-editor review: " + camera_label,
        delay=0.0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError("Unreal rejected screenshot task for " + camera_label)
    tasks.append((camera_label, path, task))

started = time.monotonic()
tick_handle = None


def finish(_delta):
    global tick_handle
    if not all(task.is_task_done() for _, _, task in tasks) and time.monotonic() - started < 60.0:
        return
    rows = []
    for camera_label, path, task in tasks:
        if not task.is_task_done() or not path.is_file() or path.stat().st_size < 4096:
            payload = {
                "status": "FAIL__FRESH_UNREAL_REVIEW_CAPTURE",
                "map": MAP,
                "error": "missing or incomplete screenshot: " + str(path),
                "no_map_save": True,
            }
            break
        rows.append({"camera": camera_label, "path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)})
    else:
        payload = {
            "status": "PASS__FRESH_UNREAL_MESHY_CANDIDATE_REVIEW_CAPTURE",
            "map": MAP,
            "resolution": list(SIZE),
            "captures": rows,
            "no_map_save": True,
            "no_protected_map_loaded_or_saved": True,
        }
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log("PRESSSHOP_2126_MESHY_REVIEW_CAPTURE_" + payload["status"])


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
tick_handle = unreal.register_slate_post_tick_callback(finish)
