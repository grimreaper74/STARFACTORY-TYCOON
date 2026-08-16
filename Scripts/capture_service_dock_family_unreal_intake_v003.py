"""Capture one fixed camera from the isolated service-dock Unreal intake map."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
CAPTURES = {
    "family": "LB_DOCK_INTAKE_CAM_Family",
    "mr01": "LB_DOCK_INTAKE_CAM_MR01",
    "cr01": "LB_DOCK_INTAKE_CAM_CR01",
}
capture_id = os.environ.get("LB_SERVICE_DOCK_CAPTURE", "").strip().lower()
if capture_id not in CAPTURES:
    raise RuntimeError(f"Set LB_SERVICE_DOCK_CAPTURE to one of {sorted(CAPTURES)}")

saved = Path(unreal.Paths.project_saved_dir())
out_dir = saved / "ValidationScreenshots/SupportRobots/ServiceDocks/Visual_v005"
audit_dir = saved / "Audits/SupportRobots"
output = out_dir / f"service_dock_family_visual_v005_{capture_id}.png"
receipt = audit_dir / f"service_dock_family_visual_v005_capture_{capture_id}.json"
aggregate = audit_dir / "service_dock_family_visual_v005_capture.json"
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
    rows = []
    for item in CAPTURES:
        image_path = out_dir / f"service_dock_family_visual_v005_{item}.png"
        receipt_path = audit_dir / f"service_dock_family_visual_v005_capture_{item}.json"
        if not image_path.is_file() or not receipt_path.is_file():
            return False
        row = json.loads(receipt_path.read_text(encoding="utf-8"))
        if row.get("status") != "CAPTURE_PASS" or row.get("sha256") != sha256(image_path):
            return False
        rows.append(row)
    write_json(aggregate, {
        "$schema": "cairnwell/audit/service-dock-family-visual-v005-capture/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FRESH_UNREAL_SCREENSHOTS_CAPTURED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
        "map": MAP,
        "resolution": [1920, 1080],
        "captures": rows,
        "visual_gate_passed": False,
        "promotion_authorized": False,
    })
    return True


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError(f"One-map rule violation: opened {current}, expected {MAP}")
camera = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}.get(CAPTURES[capture_id])
if camera is None:
    raise RuntimeError(f"Missing camera {CAPTURES[capture_id]}")

out_dir.mkdir(parents=True, exist_ok=True)
audit_dir.mkdir(parents=True, exist_ok=True)
for path in (output, receipt, aggregate):
    if path.exists():
        path.unlink()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Line Boss isolated service dock visual v005: {capture_id}",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError(f"Could not create screenshot task for {capture_id}")

started = time.monotonic()
tick_handle = None


def finish(_delta_seconds):
    global tick_handle
    elapsed = time.monotonic() - started
    passed = elapsed >= 3.0 and output.is_file() and output.stat().st_size >= 1024
    if not passed and elapsed < 55.0:
        return
    row = {
        "id": capture_id,
        "camera": CAPTURES[capture_id],
        "path": str(output),
        "bytes": output.stat().st_size if output.exists() else 0,
        "elapsed_seconds": round(elapsed, 3),
        "status": "CAPTURE_PASS" if passed else "CAPTURE_FAIL",
    }
    if passed:
        row["sha256"] = sha256(output)
    write_json(receipt, row)
    complete = aggregate_if_complete() if passed else False
    if passed:
        unreal.log(f"LINE_BOSS_SERVICE_DOCK_CAPTURE_PASS id={capture_id} aggregate={'PASS' if complete else 'PENDING'}")
    else:
        unreal.log_error(f"LINE_BOSS_SERVICE_DOCK_CAPTURE_FAIL id={capture_id}")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
