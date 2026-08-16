"""Capture the isolated restored Press Shop without saving or mutating any map."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001"
MAP_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
SOURCE_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
CLEAN_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
EXPECTED_SOURCE_SHA256 = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
EXPECTED_CLEAN_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
OUT_DIR = PROJECT / "Saved/ValidationScreenshots/PressShop/FullFactoryRestored_v001"
RECEIPT = PROJECT / "Saved/Audits/PressShop/FullFactoryRestored_v001/capture_receipt_v001.json"
VALIDATION_RECEIPT = PROJECT / "Saved/Audits/PressShopRestoration/FullFactoryRestored_v001/independent_validation_v001.json"
VALIDATION_SCHEMA = "cairnwell/audit/press-shop-full-factory-restoration-validation-v001/v1"
VALIDATION_STATUS = "PASS__FRESH_LOAD_WORLD_PREFIX_NORMALIZED_ACTOR_SIGNATURE_AND_KEY_PRESS_FAMILIES_MATCH_V438__READ_ONLY"

SHOTS = (
    (
        "01_recovered_full_press_shop.png",
        unreal.Vector(-12000.0, -11000.0, 13500.0),
        unreal.Vector(0.0, -1300.0, 350.0),
        54.0,
    ),
    (
        "02_recovered_coil_inbound_and_storage.png",
        unreal.Vector(-11800.0, -7200.0, 5200.0),
        unreal.Vector(-6500.0, -2000.0, 350.0),
        50.0,
    ),
    (
        "03_recovered_four_press_trains.png",
        unreal.Vector(10800.0, -8800.0, 7600.0),
        unreal.Vector(3500.0, -1000.0, 480.0),
        52.0,
    ),
    (
        "04_recovered_press_train_detail.png",
        unreal.Vector(9200.0, -7300.0, 3000.0),
        unreal.Vector(3850.0, -4300.0, 450.0),
        48.0,
    ),
)


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().upper()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


require(MAP_FILE.is_file(), f"Restored Press map is missing: {MAP_FILE}")
require(SOURCE_FILE.is_file(), f"Protected full Press source is missing: {SOURCE_FILE}")
require(CLEAN_FILE.is_file(), f"Protected clean Press map is missing: {CLEAN_FILE}")
require(VALIDATION_RECEIPT.is_file(), f"Fresh restored-map validation is missing: {VALIDATION_RECEIPT}")
require(digest(SOURCE_FILE) == EXPECTED_SOURCE_SHA256, "Protected full Press v438 hash drift")
require(digest(CLEAN_FILE) == EXPECTED_CLEAN_SHA256, "Protected clean Press v913 hash drift")
require(not RECEIPT.exists(), f"Capture receipt already exists: {RECEIPT}")
require(not OUT_DIR.exists(), f"Capture output already exists: {OUT_DIR}")

validation = json.loads(VALIDATION_RECEIPT.read_text(encoding="utf-8"))
require(validation.get("$schema") == VALIDATION_SCHEMA, "Restored-map validation schema drift")
require(validation.get("status") == VALIDATION_STATUS, "Restored-map validation is not PASS")
require(validation.get("normalized_actor_signature_equal") is True, "Restored-map normalized actor signature is not exact")
require(validation.get("failures") == [], "Restored-map validation contains failures")
require(validation.get("restored_sha256") == digest(MAP_FILE), "Restored map changed after validation")

OUT_DIR.mkdir(parents=True)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)

map_sha_before = digest(MAP_FILE)
require(unreal.EditorLoadingAndSavingUtils.load_map(MAP), f"Could not load {MAP}")

actor_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
hidden_actors = []
for actor in actor_api.get_all_level_actors():
    label = actor.get_actor_label().lower()
    tags = {str(tag).lower() for tag in actor.tags}
    is_upper_cover = (
        "roofliner" in label
        or "roofbeam" in label
        or "ceilingpanel" in label
        or "roof_panel" in label
        or "lb.module.factoryroofliner" in tags
    )
    if is_upper_cover:
        actor.set_is_temporarily_hidden_in_editor(True)
        hidden_actors.append(actor)

camera = actor_api.spawn_actor_from_class(unreal.CameraActor, SHOTS[0][1], unreal.Rotator())
require(camera is not None, "Could not spawn transient recovery camera")
camera.set_actor_label("TEMP_LB_PressShop_FullFactoryRestored_Camera_v001")
camera_component = camera.get_editor_property("camera_component")

state = {
    "index": 0,
    "requested": False,
    "settle": 120,
    "records": [],
    "callback": None,
}


def abort_capture(message: str) -> None:
    unreal.log_error(f"Press Shop restored capture failed: {message}")
    for actor in hidden_actors:
        if unreal.SystemLibrary.is_valid(actor):
            actor.set_is_temporarily_hidden_in_editor(False)
    if unreal.SystemLibrary.is_valid(camera):
        actor_api.destroy_actor(camera)
    if state["callback"] is not None:
        unreal.unregister_slate_post_tick_callback(state["callback"])
        state["callback"] = None
    payload = {
        "$schema": "lineboss/audit/press-shop/full-factory-restored-capture-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FAIL__FRESH_RESTORED_FULL_PRESS_SHOP_CAPTURES_V001",
        "map": MAP,
        "map_sha256_before": map_sha_before,
        "map_sha256_after": digest(MAP_FILE),
        "captures": state["records"],
        "map_saved": False,
        "failures": [message],
    }
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def finish() -> None:
    for actor in hidden_actors:
        if unreal.SystemLibrary.is_valid(actor):
            actor.set_is_temporarily_hidden_in_editor(False)
    if unreal.SystemLibrary.is_valid(camera):
        actor_api.destroy_actor(camera)

    map_sha_after = digest(MAP_FILE)
    require(map_sha_after == map_sha_before, "Restored Press map changed during capture")
    require(digest(SOURCE_FILE) == EXPECTED_SOURCE_SHA256, "Protected full Press v438 changed during capture")
    require(digest(CLEAN_FILE) == EXPECTED_CLEAN_SHA256, "Protected clean Press v913 changed during capture")

    payload = {
        "$schema": "lineboss/audit/press-shop/full-factory-restored-capture-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RESTORED_FULL_PRESS_SHOP_CAPTURES_V001",
        "map": MAP,
        "map_sha256_before": map_sha_before,
        "map_sha256_after": map_sha_after,
        "protected_source_v438_sha256": EXPECTED_SOURCE_SHA256,
        "protected_clean_v913_sha256": EXPECTED_CLEAN_SHA256,
        "independent_validation_receipt": str(VALIDATION_RECEIPT),
        "independent_validation_receipt_sha256": digest(VALIDATION_RECEIPT),
        "temporarily_hidden_upper_cover_actor_count": len(hidden_actors),
        "captures": state["records"],
        "map_saved": False,
        "failures": [],
    }
    RECEIPT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log("LINE_BOSS_PRESS_FULL_FACTORY_RESTORED_CAPTURE_V001_PASS")
    if state["callback"] is not None:
        unreal.unregister_slate_post_tick_callback(state["callback"])
        state["callback"] = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def tick_impl(_delta_seconds: float) -> None:
    if state["settle"] > 0:
        state["settle"] -= 1
        return

    index = state["index"]
    if index >= len(SHOTS):
        finish()
        return

    filename, location, target, field_of_view = SHOTS[index]
    output = OUT_DIR / filename

    if not state["requested"]:
        rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
        require(
            all(math.isfinite(value) for value in (rotation.pitch, rotation.yaw, rotation.roll)),
            f"Non-finite camera rotation for {filename}",
        )
        camera.set_actor_location_and_rotation(location, rotation, False, False)
        camera_component.set_editor_property("field_of_view", field_of_view)
        camera_component.set_editor_property("aspect_ratio", 16.0 / 9.0)
        camera_component.set_editor_property("constrain_aspect_ratio", True)
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920,
            1080,
            str(output),
            camera=camera,
            mask_enabled=False,
            capture_hdr=False,
            delay=0.0,
            force_game_view=True,
        )
        require(task is not None, f"Screenshot task was not created for {filename}")
        state["requested"] = True
        return

    if output.is_file() and output.stat().st_size > 10000:
        state["records"].append(
            {
                "filename": filename,
                "path": str(output),
                "bytes": output.stat().st_size,
                "sha256": digest(output),
                "resolution": [1920, 1080],
            }
        )
        state["index"] += 1
        state["requested"] = False
        state["settle"] = 60


def tick(delta_seconds: float) -> None:
    try:
        tick_impl(delta_seconds)
    except Exception as exc:
        abort_capture(f"{type(exc).__name__}: {exc}")


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
state["callback"] = unreal.register_slate_post_tick_callback(tick)
