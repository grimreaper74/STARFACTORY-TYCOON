"""PIE proof for clean-map support-fleet egress and representative AGV circulation."""
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
ROOT = Path(unreal.Paths.project_dir())
TARGET = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_runtime_navigation_pie_v20260809_v050.json"
ROUTES = {
    "CR01_01_egress": ((-750, -3820, 25), (-750, -3500, 25)),
    "CR01_02_egress": ((-250, -3820, 25), (-250, -3500, 25)),
    "MR01_01_egress": ((250, -3820, 25), (250, -3500, 25)),
    "MR01_02_egress": ((-1250, -3820, 25), (-1250, -3500, 25)),
    "agv_south": ((-9000, -4450, 25), (9000, -4450, 25)),
    "agv_north": ((-9000, 4450, 25), (9000, 4450, 25)),
    "agv_west": ((-9500, -3900, 25), (-9500, 3900, 25)),
    "agv_east": ((9500, -3900, 25), (9500, 3900, 25)),
    "agv_storage_west": ((-6200, -3300, 25), (-6200, 3300, 25)),
    "agv_storage_east": ((1400, -3300, 25), (1400, 3300, 25)),
}
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(TARGET):
    raise RuntimeError("could not load v038")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None

def vec(row):
    return unreal.Vector(float(row[0]), float(row[1]), float(row[2]))

def finish(rows, failures):
    global handle
    if handle:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "status": "PASS_RUNTIME_NAVIGATION__NOT_PROMOTED" if not failures else "FAIL_RUNTIME_NAVIGATION__NOT_PROMOTED",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "map": TARGET,
        "routes": rows,
        "failures": failures,
        "promotion_authorized": False,
        "meshy_credits_used": 0
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (unreal.log if not failures else unreal.log_error)("LINE_BOSS_CLEAN_RUNTIME_NAV_V039_" + ("PASS" if not failures else "FAIL"))
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()

def tick(_):
    elapsed = time.monotonic() - started
    if elapsed > 75:
        finish({}, ["timeout waiting for runtime navigation"])
        return
    if elapsed < 7:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    boots = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopNavigationBootstrap)
    if len(boots) != 1:
        finish({}, [f"expected one native navigation bootstrap, found {len(boots)}"])
        return
    rows, failures = {}, []
    boot = boots[0]
    for name, (start, end) in ROUTES.items():
        valid = bool(boot.validate_path(vec(start), vec(end)))
        points = list(boot.get_validated_path_points()) if valid else []
        length = float(boot.get_validated_path_length()) if valid else None
        rows[name] = {
            "start_cm": list(start), "end_cm": list(end), "valid": valid,
            "path_length_cm": length,
            "point_count": len(points),
            "path_points_cm": [[round(p.x, 2), round(p.y, 2), round(p.z, 2)] for p in points]
        }
        if not valid:
            failures.append(name + ": invalid or partial path")
    finish(rows, failures)

handle = unreal.register_slate_post_tick_callback(tick)
