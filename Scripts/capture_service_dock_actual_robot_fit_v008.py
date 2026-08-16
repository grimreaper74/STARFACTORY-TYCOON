"""Capture one fixed-camera view from the isolated correct-yaw v008 fit map."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time

import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v008"
CAPTURES = {
    "family": "LB_DOCK_FIT_CAM_FamilyActual",
    "mr01_oblique": "LB_DOCK_FIT_CAM_MR01_Oblique",
    "mr01_portal": "LB_DOCK_FIT_CAM_MR01_Portal",
    "cr01_oblique": "LB_DOCK_FIT_CAM_CR01_Oblique",
    "cr01_portal": "LB_DOCK_FIT_CAM_CR01_Portal",
}
capture_id = os.environ.get("LB_SERVICE_DOCK_CAPTURE", "").strip().lower()
if capture_id not in CAPTURES:
    raise RuntimeError("Set LB_SERVICE_DOCK_CAPTURE to one of {}".format(sorted(CAPTURES)))

saved = Path(unreal.Paths.project_saved_dir())
out_dir = saved / "ValidationScreenshots/SupportRobots/ServiceDocks/ActualRobotFit_v008"
audit_dir = saved / "Audits/SupportRobots"
output = out_dir / "service_dock_actual_robot_fit_v008_{}.png".format(capture_id)
receipt = audit_dir / "service_dock_actual_robot_fit_v008_capture_{}.json".format(capture_id)
aggregate = audit_dir / "service_dock_actual_robot_fit_v008_capture.json"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def tagged_component(actor, cls, tag):
    for item in actor.get_components_by_class(cls):
        if unreal.Name(tag) in item.get_editor_property("component_tags"):
            return item
    return None


def pose_mr01_service_stow(actor):
    arm = tagged_component(actor, unreal.PoseableMeshComponent, "LB.MR01.ArmPoseable")
    if arm is None:
        raise RuntimeError("MR01 poseable arm unavailable")
    names = [
        "root", "lift", "j1_base", "j2_shoulder", "j3_elbow", "j4_wrist_roll",
        "j5_wrist_pitch", "j6_tool_roll", "tool_coupler", "tcp",
    ]
    for name in names:
        arm.reset_bone_transform_by_name(unreal.Name(name))
    refs = {
        name: arm.get_bone_transform_by_name(unreal.Name(name), unreal.BoneSpaces.COMPONENT_SPACE)
        for name in names
    }
    posed = {"root": refs["root"], "lift": refs["lift"]}
    commands = [
        ("j1_base", "lift", unreal.Rotator(0.0, 0.0, 0.0)),
        ("j2_shoulder", "j1_base", unreal.Rotator(-35.0, 0.0, 0.0)),
        ("j3_elbow", "j2_shoulder", unreal.Rotator(130.0, 0.0, 0.0)),
        ("j4_wrist_roll", "j3_elbow", unreal.Rotator()),
        ("j5_wrist_pitch", "j4_wrist_roll", unreal.Rotator(-95.0, 0.0, 0.0)),
        ("j6_tool_roll", "j5_wrist_pitch", unreal.Rotator()),
        ("tool_coupler", "j6_tool_roll", unreal.Rotator()),
        ("tcp", "tool_coupler", unreal.Rotator()),
    ]
    for name, parent, delta in commands:
        local = unreal.MathLibrary.make_relative_transform(refs[name], refs[parent])
        local.rotation = unreal.MathLibrary.multiply_quat_quat(delta.quaternion(), local.rotation)
        value = unreal.MathLibrary.compose_transforms(local, posed[parent])
        posed[name] = value
        arm.set_bone_transform_by_name(unreal.Name(name), value, unreal.BoneSpaces.COMPONENT_SPACE)


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
        image = out_dir / "service_dock_actual_robot_fit_v008_{}.png".format(item)
        item_receipt = audit_dir / "service_dock_actual_robot_fit_v008_capture_{}.json".format(item)
        if not image.is_file() or not item_receipt.is_file():
            return False
        row = json.loads(item_receipt.read_text(encoding="utf-8"))
        if row.get("status") != "CAPTURE_PASS" or row.get("sha256") != sha256(image):
            return False
        rows.append(row)
    write_json(
        aggregate,
        {
            "$schema": "cairnwell/audit/service-dock-actual-robot-fit-v008-capture/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": "FRESH_UNREAL_SCREENSHOTS_CAPTURED__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED",
            "map": MAP,
            "resolution": [1920, 1080],
            "captures": rows,
            "visual_gate_passed": False,
            "promotion_authorized": False,
        },
    )
    return True


world = unreal.EditorLevelLibrary.get_editor_world()
current = world.get_outermost().get_name() if world is not None else ""
if current != MAP:
    raise RuntimeError("One-map rule violation: opened {}, expected {}".format(current, MAP))
camera = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}.get(
    CAPTURES[capture_id]
)
if camera is None:
    raise RuntimeError("Missing camera {}".format(CAPTURES[capture_id]))
if capture_id.startswith("mr01_"):
    mr01 = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}.get(
        "LB_DOCK_FIT_MR01_v021_ActualAuthority"
    )
    if mr01 is None:
        raise RuntimeError("Docked MR01 authority unavailable")
    pose_mr01_service_stow(mr01)

# Correct two review viewpoints transiently. The saved MR portal camera sits
# inside the neighbouring CR dock; neither change is saved back to v008.
review_overrides = {
    "family": ((-760.0, 0.0, 430.0), (0.0, 0.0, 55.0), 58.0),
    "mr01_portal": ((0.0, 5.0, 145.0), (0.0, -230.0, 65.0), 58.0),
}
if capture_id in review_overrides:
    location, target, fov = review_overrides[capture_id]
    position = unreal.Vector(*location)
    camera.set_actor_location(position, False, False)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False
    )
    camera.camera_component.set_editor_property("field_of_view", fov)

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
    1920,
    1080,
    str(output),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Line Boss isolated service dock actual robot fit v008: {}".format(capture_id),
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Could not create screenshot task")

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
        unreal.log(
            "LINE_BOSS_SERVICE_DOCK_V008_CAPTURE_PASS id={} aggregate={}".format(
                capture_id, "PASS" if complete else "PENDING"
            )
        )
    else:
        unreal.log_error("LINE_BOSS_SERVICE_DOCK_V008_CAPTURE_FAIL id={}".format(capture_id))
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.SystemLibrary.quit_editor()


tick_handle = unreal.register_slate_post_tick_callback(finish)
