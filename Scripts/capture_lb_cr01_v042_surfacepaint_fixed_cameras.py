"""Capture one direct-map CR01 v042 Surface Paint fixed review camera per editor run.

Set LB_CR01_V042_CAPTURE to one of the capture IDs below.  Keeping the screenshot
request in the top-level script matches Unreal's ExecutePythonScript lifetime and
avoids deferred multi-request re-entry.  The final run aggregates all six receipts.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v042_SurfacePaintTechnical"
CAPTURES = {
    "mothballed_oblique": "LB_CR01_v042_CAM_Mothballed_Oblique",
    "mothballed_left": "LB_CR01_v042_CAM_Mothballed_Left",
    "restored_oblique": "LB_CR01_v042_CAM_Restored_Oblique",
    "restored_right": "LB_CR01_v042_CAM_Restored_Right",
    "restored_front": "LB_CR01_v042_CAM_Restored_Front",
    "restored_top": "LB_CR01_v042_CAM_Restored_Top",
}
CAPTURE_ID = os.environ.get("LB_CR01_V042_CAPTURE", "").strip().lower()
if CAPTURE_ID not in CAPTURES:
    raise RuntimeError(
        f"Set LB_CR01_V042_CAPTURE to one of {sorted(CAPTURES)}; received {CAPTURE_ID!r}"
    )

ROOT = Path(unreal.Paths.project_saved_dir())
OUT = ROOT / "ValidationScreenshots/SupportRobots/CR01/Candidate_v042_SurfacePaint"
AUDIT_ROOT = ROOT / "Audits"
AUDIT = AUDIT_ROOT / "lb_cr01_v042_surfacepaint_capture.json"
RECEIPT = AUDIT_ROOT / f"lb_cr01_v042_surfacepaint_capture_{CAPTURE_ID}.json"
OUTPUT = OUT / f"lb_cr01_v042_surfacepaint_{CAPTURE_ID}.png"
CAMERA_LABEL = CAPTURES[CAPTURE_ID]
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def aggregate_if_complete():
    records = []
    for capture_id, camera_label in CAPTURES.items():
        receipt_path = AUDIT_ROOT / f"lb_cr01_v042_surfacepaint_capture_{capture_id}.json"
        output_path = OUT / f"lb_cr01_v042_surfacepaint_{capture_id}.png"
        if not receipt_path.exists() or not output_path.exists() or output_path.stat().st_size < 1024:
            return False
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("status") != "CAPTURE_PASS" or receipt.get("sha256") != sha256(output_path):
            return False
        records.append(receipt)
    write_json(
        AUDIT,
        {
            "$schema": "line-boss/audit/lb-cr01-v042-surfacepaint-capture",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FRESH_UNREAL_SCREENSHOTS_CAPTURED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
            "map": MAP,
            "resolution": [1920, 1080],
            "captures": records,
            "visual_gate_passed": False,
            "promotion_authorized": False,
        },
    )
    return True


world = unreal.EditorLevelLibrary.get_editor_world()
current_package = world.get_outermost().get_name() if world is not None else ""
if current_package != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current_package}, expected {MAP}")
camera_by_label = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
camera = camera_by_label.get(CAMERA_LABEL)
if camera is None:
    raise RuntimeError(f"Missing CR01 v042 fixed camera: {CAMERA_LABEL}")

OUT.mkdir(parents=True, exist_ok=True)
AUDIT_ROOT.mkdir(parents=True, exist_ok=True)
if OUTPUT.exists():
    OUTPUT.unlink()
if RECEIPT.exists():
    RECEIPT.unlink()
if AUDIT.exists():
    AUDIT.unlink()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    str(OUTPUT),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss CR01 v042 Surface Paint fixed review: {CAPTURE_ID}",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(f"Could not create screenshot task for {CAPTURE_ID}")

started = time.monotonic()
tick_handle = None


def finish(_delta_seconds):
    global tick_handle
    elapsed = time.monotonic() - started
    passed = elapsed >= 3.0 and OUTPUT.exists() and OUTPUT.stat().st_size >= 1024
    if not passed and elapsed < 55.0:
        return
    if passed:
        receipt = {
            "id": CAPTURE_ID,
            "camera": CAMERA_LABEL,
            "path": str(OUTPUT),
            "bytes": OUTPUT.stat().st_size,
            "sha256": sha256(OUTPUT),
            "elapsed_seconds": round(elapsed, 3),
            "status": "CAPTURE_PASS",
        }
        write_json(RECEIPT, receipt)
        aggregated = aggregate_if_complete()
        unreal.log(
            f"LINE_BOSS_CR01_V042_CAPTURE_PASS id={CAPTURE_ID} "
            f"aggregate={'PASS' if aggregated else 'PENDING'} path={OUTPUT}"
        )
    else:
        write_json(
            RECEIPT,
            {
                "id": CAPTURE_ID,
                "camera": CAMERA_LABEL,
                "path": str(OUTPUT),
                "bytes": OUTPUT.stat().st_size if OUTPUT.exists() else 0,
                "elapsed_seconds": round(elapsed, 3),
                "status": "CAPTURE_FAIL",
            },
        )
        unreal.log_error(f"LINE_BOSS_CR01_V042_CAPTURE_FAIL id={CAPTURE_ID} path={OUTPUT}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
