"""Real-RHI native photo probes for the live S01-S07 Press Shop.

This is intentionally a PIE-only lane: it invokes the normal player-facing
press build, then frames four transient native ACameraActor poses from inside
the Press cell. The native camera applies a fail-closed, capture-only
occluder cutaway (two audited legacy walls, five shell posts and 67 audited
legacy foreground posts). It never saves a map or writes Content. Every
output is a new 2560x1440 PNG and one evidence receipt under
Saved/ValidationScreenshots.
"""

import hashlib
import json
from pathlib import Path
import time

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
OUTPUT = ROOT / "Saved/ValidationScreenshots/OneFactory/NativePressShopSteamPhotoLane_v005"
RECEIPT = OUTPUT / "press_shop_steam_photo_lane_v005.json"
MATERIALFLOW_RECEIPT = ROOT / (
    "Saved/ValidationScreenshots/OneFactory/NativePressTrainMaterialFlow_v005/"
    "press_train_native_v005_runtime.json"
)
SIZE = (2560, 1440)
EXPOSURE_BIAS = -0.75

# Poses are in UE world centimetres and refer to the v005-proven press datum:
# S01/S02 begin around (-8991, 6018/7468), S07 ends at (-8991, 14718).
# They deliberately stay inside the Press bay; the prior generic department
# solver was correct for open factory tours but placed its eye beyond the wall.
SHOTS = (
    {
        "filename": "01_press_full_operator_hero.png",
        "eye_cm": (-22000.0, 3600.0, 1500.0),
        "target_cm": (-8991.0, 10368.0, 600.0),
        "fov_degrees": 55.0,
        "purpose": "S01-S07 diagonal: coil-to-outfeed production story",
    },
    {
        "filename": "02_press_s01_s02_detail_hero.png",
        "eye_cm": (-15800.0, 5000.0, 800.0),
        "target_cm": (-8991.0, 7450.0, 650.0),
        "fov_degrees": 46.0,
        "purpose": "coil rack, decoiler, feed bridge and S02 Deep Draw",
    },
    {
        "filename": "03_press_midline_service_hero.png",
        "eye_cm": (-1800.0, 7600.0, 950.0),
        "target_cm": (-8991.0, 11200.0, 600.0),
        "fov_degrees": 50.0,
        "purpose": "service profile across S03-S05",
    },
    {
        "filename": "04_press_s07_outfeed_hero.png",
        "eye_cm": (-2000.0, 12700.0, 850.0),
        "target_cm": (-8991.0, 14000.0, 500.0),
        "fov_degrees": 47.0,
        "purpose": "inspection cell, exit conveyor and dunnage",
    },
)

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
started = time.monotonic()
phase = "wait_world"
phase_started = started
tick_handle = None
capture_task = None
shot_index = 0
captures = []
lighting_reason = "not requested"
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
        unreal.log_warning("PRESS_STEAM_PHOTO_LANE_END_PIE_WARN " + str(error))
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def configure_photo_camera(world):
    global phase, phase_started
    shot = SHOTS[shot_index]
    destination = OUTPUT / shot["filename"]
    if destination.exists():
        raise RuntimeError(f"Refusing to overwrite a photo probe: {destination}")
    reason = unreal.LBOneFactoryDevFactory.frame_transient_photo_camera(
        world,
        unreal.Vector(*shot["eye_cm"]),
        unreal.Vector(*shot["target_cm"]),
        shot["fov_degrees"],
        EXPOSURE_BIAS,
    )
    if reason is None:
        raise RuntimeError(f"Native photo camera rejected {shot['filename']}")
    captures.append({
        **shot,
        "path": str(destination),
        "native_camera_reason": str(reason),
    })
    phase = "settle_photo"
    phase_started = time.monotonic()


def begin_screenshot():
    global phase, phase_started, capture_task
    destination = OUTPUT / SHOTS[shot_index]["filename"]
    # Enter a non-handling phase before calling the screenshot API.  The API
    # can pump Slate synchronously, so this prevents a nested tick from
    # scheduling the same photo twice.
    phase = "scheduling_screenshot"
    phase_started = time.monotonic()
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    capture_task = unreal.AutomationLibrary.take_high_res_screenshot(
        SIZE[0], SIZE[1], str(destination), force_game_view=False)
    if not capture_task.is_valid_task():
        raise RuntimeError(f"Unreal rejected photo screenshot {destination.name}")
    phase = "wait_screenshot"
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
            configure_photo_camera(world)
            return
        if phase == "settle_photo":
            if now - phase_started < 0.8:
                return
            begin_screenshot()
            return
        if phase == "scheduling_screenshot":
            return
        if phase == "wait_screenshot":
            if now - phase_started < 1.5 or not capture_task.is_task_done():
                return
            destination = OUTPUT / SHOTS[shot_index]["filename"]
            if not destination.is_file() or destination.stat().st_size < 4096:
                raise RuntimeError(f"Photo screenshot was not written: {destination.name}")
            captures[-1]["bytes"] = destination.stat().st_size
            captures[-1]["sha256"] = sha256(destination)
            shot_index += 1
            if shot_index < len(SHOTS):
                configure_photo_camera(world)
                return
            finish({
                "$schema": "lineboss/evidence/onefactory/native-press-steam-photo-lane-v005/v1",
                "status": "PASS__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES",
                "real_rhi": True,
                "resolution": list(SIZE),
                "exposure_bias": EXPOSURE_BIAS,
                "runtime_only_lighting": str(lighting_reason),
                "materialflow_v005_receipt_sha256": sha256(MATERIALFLOW_RECEIPT),
                "captures": captures,
                "map_loaded_or_saved": [],
                "content_writes": [],
            })
    except Exception as error:
        unreal.log_error("PRESS_STEAM_PHOTO_LANE_FAIL " + str(error))
        finish({
            "$schema": "lineboss/evidence/onefactory/native-press-steam-photo-lane-v005/v1",
            "status": "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES",
            "error": str(error),
            "captures": captures,
            "map_loaded_or_saved": [],
            "content_writes": [],
        })


try:
    if RECEIPT.exists():
        raise RuntimeError(f"Refusing to overwrite prior photo-lane receipt: {RECEIPT}")
    if not MATERIALFLOW_RECEIPT.is_file():
        raise RuntimeError("MaterialFlow v005 PIE receipt is required before photo probing")
    if not LEVELS.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as error:
    unreal.log_error("PRESS_STEAM_PHOTO_LANE_START_FAIL " + str(error))
    finish({
        "$schema": "lineboss/evidence/onefactory/native-press-steam-photo-lane-v005/v1",
        "status": "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES",
        "error": str(error),
        "captures": captures,
        "map_loaded_or_saved": [],
        "content_writes": [],
    })

