"""PIE proof that the native 2126 automation sequence actually evaluates."""
import hashlib
import json
from pathlib import Path
import time
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "native_automation_pie_v001.json"
TARGETS = (
    "2126 TRANSFER | magnetic panel shuttle sprite 1",
    "2126 TRANSFER | magnetic panel shuttle sprite 2",
    "2126 TRANSFER | magnetic panel shuttle sprite 3",
    "2126 FRONT END | active feed coil",
    "2126 OUTBOUND | hover pallet A collision base",
    "2126 OUTBOUND | hover pallet B collision base",
    "2126 OUTBOUND | hover pallet C collision base",
)
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()

def sample(world):
    actors = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
    by_label = {actor.get_actor_label(): actor for actor in actors}
    rows = {}
    for label in TARGETS:
        actor = by_label.get(label)
        if actor is None:
            raise RuntimeError("PIE target missing: " + label)
        loc = actor.get_actor_location()
        rot = actor.get_actor_rotation()
        rows[label] = {
            "location_cm": [loc.x, loc.y, loc.z],
            "rotation_deg": [rot.pitch, rot.yaw, rot.roll],
        }
    return rows

before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: " + str(path))
if OUT.exists():
    raise RuntimeError("refusing to overwrite PIE automation evidence")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated FullHall candidate")

level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor_worlds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
samples = []
started = time.monotonic()
pie_started = None
handle = None
ended = False
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
level_editor.editor_play_simulate()

def finish(status, **extra):
    global handle, ended
    if not ended:
        try:
            level_editor.editor_request_end_play()
        except Exception:
            pass
        ended = True
    after = {str(path): digest(path) for path in PROTECTED}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "status": status,
        "map": MAP,
        "samples": samples,
        "protected_sha256_before": before,
        "protected_sha256_after": after,
        **extra,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global pie_started
    try:
        now = time.monotonic()
        world = editor_worlds.get_game_world()
        if world is None:
            if now - started > 40.0:
                finish("FAIL_PIE_WORLD_TIMEOUT")
            return
        if pie_started is None:
            pie_started = now
        elapsed = now - pie_started
        thresholds = (0.50, 2.60, 4.80)
        if len(samples) < len(thresholds) and elapsed >= thresholds[len(samples)]:
            samples.append({"elapsed_seconds": round(elapsed, 3), "actors": sample(world)})
        if len(samples) == 3:
            first = samples[0]["actors"]
            max_shuttle_delta_y = max(
                abs(samples[index]["actors"][label]["location_cm"][1] - first[label]["location_cm"][1])
                for index in (1, 2)
                for label in TARGETS[:3])
            max_coil_delta_roll = max(
                abs(samples[index]["actors"][TARGETS[3]]["rotation_deg"][2] - first[TARGETS[3]]["rotation_deg"][2])
                for index in (1, 2))
            max_pallet_delta_x = max(
                abs(samples[index]["actors"][label]["location_cm"][0] - first[label]["location_cm"][0])
                for index in (1, 2)
                for label in TARGETS[4:])
            metrics = {
                "max_transfer_shuttle_delta_y_cm": max_shuttle_delta_y,
                "max_active_coil_delta_roll_deg": max_coil_delta_roll,
                "max_outbound_pallet_delta_x_cm": max_pallet_delta_x,
            }
            if max_shuttle_delta_y <= 100.0:
                finish("FAIL_SHUTTLES_DID_NOT_MOVE", metrics=metrics)
            elif max_coil_delta_roll <= 30.0:
                finish("FAIL_ACTIVE_COIL_DID_NOT_ROTATE", metrics=metrics)
            elif max_pallet_delta_x <= 100.0:
                finish("FAIL_OUTBOUND_PALLETS_DID_NOT_MOVE", metrics=metrics)
            elif {str(path): digest(path) for path in PROTECTED} != before:
                finish("FAIL_PROTECTED_MAP_CHANGED", metrics=metrics)
            else:
                finish("PASS__PIE_NATIVE_AUTOMATION_EVALUATED", metrics=metrics,
                       target_count=len(TARGETS), runtime_seconds_observed=round(elapsed, 3))
        elif now - started > 70.0:
            finish("FAIL_PIE_AUTOMATION_TIMEOUT")
    except Exception as exc:
        finish("FAIL_PIE_AUTOMATION_EXCEPTION", error=repr(exc))

handle = unreal.register_slate_post_tick_callback(tick)
