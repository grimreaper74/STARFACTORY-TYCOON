"""Capture one fixed camera from the isolated CR01 v065 PR-004 lighting proof map."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v065_PR004Lighting"
CAPTURES = {
    "mothballed_oblique": "LB_CR01_v065_PR004_CAM_Mothballed_Oblique",
    "mothballed_left": "LB_CR01_v065_PR004_CAM_Mothballed_Left",
    "restored_oblique": "LB_CR01_v065_PR004_CAM_Restored_Oblique",
    "restored_front": "LB_CR01_v065_PR004_CAM_Restored_Front",
}
capture_id = os.environ.get("LB_CR01_V065_PR004_CAPTURE", "").strip().lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Set LB_CR01_V065_PR004_CAPTURE to one of {sorted(CAPTURES)}")

saved = Path(unreal.Paths.project_saved_dir())
out = saved / "ValidationScreenshots/SupportRobots/CR01/Candidate_v065_PR004Lighting" / f"lb_cr01_v065_pr004_{capture_id}.png"
receipt = saved / "Audits" / f"lb_cr01_v065_pr004_capture_{capture_id}.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAPTURES[capture_id]), None)
if camera is None:
    raise RuntimeError(f"Missing camera {CAPTURES[capture_id]}")

out.parent.mkdir(parents=True, exist_ok=True)
receipt.parent.mkdir(parents=True, exist_ok=True)
if out.exists():
    out.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 25")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=camera, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Invalid screenshot task")

started = time.monotonic()
tick_handle = None


def finish(_delta):
    global tick_handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and out.exists() and out.stat().st_size >= 1024:
        digest = hashlib.sha256(out.read_bytes()).hexdigest().upper()
        receipt.write_text(json.dumps({
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "map": MAP,
            "capture_id": capture_id,
            "camera": CAPTURES[capture_id],
            "image": str(out),
            "sha256": digest,
            "status": "FRESH_UNREAL_FIXED_CAMERA_CAPTURE_PASS__VISUAL_REVIEW_REQUIRED",
        }, indent=2) + "\n", encoding="utf-8")
        unreal.log(f"LINE_BOSS_CR01_V065_PR004_CAPTURE_PASS id={capture_id} path={out}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LINE_BOSS_CR01_V065_PR004_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
