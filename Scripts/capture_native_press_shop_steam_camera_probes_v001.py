"""Real-RHI, non-destructive Steam camera and lighting probes for the native press shop.

The v005 MaterialFlow PIE receipt proves the runtime asset contract.  This lane
does not alter that actor, a map, or Content: it transiently builds the normal
player-facing press presentation, uses the project's native capture camera
solver and runtime-only lighting, then writes four 2560x1440 probe frames plus
one receipt under Saved/ValidationScreenshots.
"""

import hashlib
import json
from pathlib import Path
import time

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/NativePressShopSteamCameraProbes_v001"
RECEIPT = OUTPUT / "press_shop_steam_camera_probes_v001.json"
MATERIALFLOW_RECEIPT = ROOT / (
    "Saved/ValidationScreenshots/OneFactory/NativePressTrainMaterialFlow_v005/"
    "press_train_native_v005_runtime.json"
)
SIZE = (2560, 1440)

# The native Framing command takes Department@distanceScale~pitchDegrees.  A
# camera actor, FOV and exposure are solved in C++; Python only orchestrates
# official play/capture APIs.  The range deliberately spans reviewable full-
# train to low hero framing without claiming any one is a final store image.
SHOTS = (
    ("01_press_full_train_native.png", "Press@1.00~34"),
    ("02_press_three_quarter_native.png", "Press@0.72~24"),
    ("03_press_hero_core_native.png", "Press@0.52~17"),
    ("04_press_low_hero_native.png", "Press@0.45~12"),
)

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
phase = "wait_world"
phase_started = started
tick_handle = None
capture_task = None
shot_index = 0
lighting_reason = "not yet requested"
captures = []
finished = False


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_one(world, klass, label):
    rows = list(unreal.GameplayStatics.get_all_actors_of_class(world, klass))
    if len(rows) != 1:
        raise RuntimeError(f"Expected one {label}; found {len(rows)}")
    return rows[0]


def get_builder(world):
    rows = [obj for obj in unreal.ObjectIterator(unreal.LBOneFactoryPlayerBuilderSubsystem)
            if obj.get_world() == world]
    if len(rows) != 1:
        raise RuntimeError(f"Expected one player builder; found {len(rows)}")
    return rows[0]


def finish(payload):
    global tick_handle, finished
    if finished:
        return
    finished = True
    OUTPUT.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    try:
        unreal.EditorLevelLibrary.editor_end_play()
    except Exception as error:
        unreal.log_warning("PRESS_STEAM_CAMERA_PROBES_END_PIE_WARN " + str(error))
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def begin_shot(world):
    global phase, phase_started, capture_task
    filename, framing_request = SHOTS[shot_index]
    destination = OUTPUT / filename
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite a camera probe: {destination}")
    reason = unreal.LBOneFactoryDevFactory.frame_production_line(
        world, framing_request, True)
    if reason is None:
        raise RuntimeError(f"Native camera solver rejected {framing_request}")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    capture_task = unreal.AutomationLibrary.take_high_res_screenshot(
        SIZE[0], SIZE[1], str(destination), force_game_view=False)
    if not capture_task.is_valid_task():
        raise RuntimeError(f"Unreal rejected camera probe {filename}")
    captures.append({
        "filename": filename,
        "native_framing_request": framing_request,
        "native_framing_reason": str(reason),
        "path": str(destination),
    })
    phase = "wait_shot"
    phase_started = time.monotonic()


def tick(_delta):
    global phase, phase_started, shot_index, lighting_reason
    try:
        now = time.monotonic()
        if now - started > 220.0:
            raise RuntimeError(f"Timed out in phase {phase}")
        world = WORLDS.get_game_world()
        if world is None:
            return
        if phase == "wait_world":
            if now - phase_started < 5.0:
                return
            hud = require_one(world, unreal.LBControlRoomHUD, "control-room HUD")
            builder = get_builder(world)
            existing = list(unreal.GameplayStatics.get_all_actors_of_class(
                world, unreal.LBOneFactoryPressStarterPresentationActor))
            if not existing:
                hud.open_factory_build()
                accepted = hud.activate_management_action(0)
                reason = str(builder.get_last_action_reason())
                if not accepted and "PRESENTATIONS LIVE" not in reason:
                    raise RuntimeError("New Factory action rejected: " + reason)
            hud.close_management()
            phase = "wait_press"
            phase_started = now
            return
        if phase == "wait_press":
            if now - phase_started < 2.0:
                return
            require_one(world, unreal.LBOneFactoryPressStarterPresentationActor,
                        "native press presentation")
            lighting_reason = unreal.LBOneFactoryDevFactory.ensure_dev_lighting(world, 5.0)
            if lighting_reason is None:
                raise RuntimeError("Native runtime lighting setup was rejected")
            begin_shot(world)
            return
        if phase == "wait_shot":
            if now - phase_started < 1.5 or not capture_task.is_task_done():
                return
            destination = OUTPUT / SHOTS[shot_index][0]
            if not destination.is_file() or destination.stat().st_size < 4096:
                raise RuntimeError(f"Camera probe was not written: {destination.name}")
            captures[-1]["bytes"] = destination.stat().st_size
            captures[-1]["sha256"] = sha256(destination)
            shot_index += 1
            if shot_index < len(SHOTS):
                begin_shot(world)
                return
            finish({
                "$schema": "lineboss/evidence/onefactory/native-press-steam-camera-probes-v001/v1",
                "status": "PASS__NATIVE_PRESS_STEAM_CAMERA_PROBES",
                "real_rhi": True,
                "resolution": list(SIZE),
                "runtime_only_lighting": str(lighting_reason),
                "materialflow_v005_receipt_sha256": sha256(MATERIALFLOW_RECEIPT),
                "captures": captures,
                "map_loaded_or_saved": [],
                "content_writes": [],
            })
    except Exception as error:
        unreal.log_error("PRESS_STEAM_CAMERA_PROBES_FAIL " + str(error))
        finish({
            "$schema": "lineboss/evidence/onefactory/native-press-steam-camera-probes-v001/v1",
            "status": "FAIL__NATIVE_PRESS_STEAM_CAMERA_PROBES",
            "error": str(error),
            "captures": captures,
            "map_loaded_or_saved": [],
            "content_writes": [],
        })


try:
    if RECEIPT.exists():
        raise RuntimeError(f"Refusing to overwrite prior camera-probe receipt: {RECEIPT}")
    if not MATERIALFLOW_RECEIPT.is_file():
        raise RuntimeError("MaterialFlow v005 PIE receipt is required before visual probing")
    if not LEVELS.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as error:
    unreal.log_error("PRESS_STEAM_CAMERA_PROBES_START_FAIL " + str(error))
    finish({
        "$schema": "lineboss/evidence/onefactory/native-press-steam-camera-probes-v001/v1",
        "status": "FAIL__NATIVE_PRESS_STEAM_CAMERA_PROBES",
        "error": str(error),
        "captures": captures,
        "map_loaded_or_saved": [],
        "content_writes": [],
    })
