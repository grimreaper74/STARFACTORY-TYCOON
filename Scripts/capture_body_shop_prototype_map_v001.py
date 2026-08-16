"""Capture fixed visual evidence for the isolated, empty Body Shop prototype map.

Read-only with respect to Content and Config: this script loads the map, uses
its two authored review cameras, captures a high-resolution image for each,
then writes an evidence receipt in Saved.  It does not spawn, destroy, save, or
otherwise alter any map actor.  Run only after the independent map validator
has passed.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/BodyShop/v001"
AUDIT = ROOT / "Saved/Audits/BodyShop/v001/body_shop_prototype_map_capture_v001.json"
CAMERAS = {
    "overview": "LB_BodyShop_Prototype_ReviewCamera_Overview_v001",
    "flow": "LB_BodyShop_Prototype_ReviewCamera_Flow_v001",
}
MAP_TAG = "LB.BodyShop.Experimental.v001"
FORBIDDEN_FRAGMENTS = (
    "LBBodyShopCellActor",
    "LBBodyShopBuildAuthority",
    "LBBodyShopPrototypeRuntime",
    "LBBodyWeldLineActor",
    "LBPressShop",
    "LBGameMode",
    "LBECoatLineActor",
)


def output_path(capture_id: str) -> Path:
    return CAPTURE_DIR / f"body_shop_prototype_map_v001_{capture_id}.png"


def fail(message: str):
    raise RuntimeError(message)


def class_name(actor):
    return actor.get_class().get_name()


def is_engine_foundation_actor(actor):
    return class_name(actor) in {"WorldSettings", "DefaultPhysicsVolume"}


def main():
    # High-res screenshots finish on subsequent Slate ticks. Retain this
    # script's closure until both captures have completed and quit_editor()
    # has run, matching the project's established capture-script convention.
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    library = unreal.EditorAssetLibrary
    if not library.does_asset_exist(MAP):
        fail(f"Prototype map does not exist: {MAP}")
    if not levels.load_level(MAP):
        fail(f"Could not load prototype map: {MAP}")

    actors = list(actors_api.get_all_level_actors())
    forbidden = [
        {"label": actor.get_actor_label(), "class": class_name(actor)}
        for actor in actors
        if any(fragment in class_name(actor) for fragment in FORBIDDEN_FRAGMENTS)
    ]
    if forbidden:
        fail("Refusing capture: map is not empty/isolated: " + json.dumps(forbidden))
    if any(
        not is_engine_foundation_actor(actor)
        and MAP_TAG not in [str(tag) for tag in actor.get_editor_property("tags")]
        for actor in actors
    ):
        fail("Refusing capture: map contains untagged actors")

    camera_by_label = {actor.get_actor_label(): actor for actor in actors}
    resolved = {}
    for capture_id, label in CAMERAS.items():
        camera = camera_by_label.get(label)
        if camera is None or not isinstance(camera, unreal.CameraActor):
            fail(f"Missing authored Body Shop review camera: {label}")
        resolved[capture_id] = camera

    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    for path in (output_path(key) for key in CAMERAS):
        if path.exists():
            fail(f"Refusing to overwrite prior evidence image: {path}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.EditorLevelLibrary.editor_set_game_view(True)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()

    ordered_capture_ids = list(CAMERAS)
    current_index = 0
    current_task = None
    current_started = 0.0
    evidence = []
    started = time.monotonic()
    tick_handle = None

    def finish_when_ready(_delta_seconds):
        nonlocal tick_handle, current_index, current_task, current_started
        if current_task is None and current_index < len(ordered_capture_ids):
            capture_id = ordered_capture_ids[current_index]
            path = output_path(capture_id)
            current_task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(path), camera=resolved[capture_id], force_game_view=True
            )
            current_started = time.monotonic()
            if not current_task.is_valid_task():
                fail(f"Unreal did not create a valid screenshot task for {capture_id}")
            return
        if current_task is not None and not current_task.is_task_done():
            if time.monotonic() - current_started < 60.0:
                return
            fail(f"Timed out capturing {ordered_capture_ids[current_index]}")
        if current_task is not None:
            capture_id = ordered_capture_ids[current_index]
            path = output_path(capture_id)
            valid = path.exists() and path.stat().st_size >= 1024
            evidence.append({
                "id": capture_id,
                "camera": CAMERAS[capture_id],
                "image": str(path),
                "exists": valid,
                "bytes": path.stat().st_size if path.exists() else 0,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()
                if valid else None,
            })
            current_task = None
            current_index += 1
            return
        if current_index < len(ordered_capture_ids):
            return
        passed = all(row["exists"] for row in evidence)
        payload = {
            "$schema": "cairnwell/body-shop/prototype-map-v001/capture/v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": (
                "PASS__FIXED_CAMERA_EMPTY_ISOLATED_BODY_SHOP_SHELL_EVIDENCE"
                if passed else "FAIL"
            ),
            "map": MAP,
            "captures": evidence,
            "production_cells_baked_into_map": 0,
            "legacy_authorities_baked_into_map": 0,
            "meshy_credits_used": 0,
            "writes_to_content_or_config": False,
        }
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        if passed:
            unreal.log(
                "LINE_BOSS_BODY_SHOP_PROTOTYPE_MAP_CAPTURE_V001_PASS "
                f"audit={AUDIT}"
            )
        else:
            unreal.log_error(
                "LINE_BOSS_BODY_SHOP_PROTOTYPE_MAP_CAPTURE_V001_FAIL "
                f"audit={AUDIT}"
            )
        if tick_handle is not None:
            unreal.unregister_slate_post_tick_callback(tick_handle)
            tick_handle = None
        unreal.SystemLibrary.quit_editor()

    tick_handle = unreal.register_slate_post_tick_callback(finish_when_ready)


main()
