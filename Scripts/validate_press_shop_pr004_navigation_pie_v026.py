"""PIE navigation-path gate through the PR-004 operator/transfer approach."""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)


CANDIDATE = os.environ.get("LB_PR004_COLLISION_CANDIDATE", "v026").lower()
MAPS = {
    "v026": "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026",
    "v028": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028",
    "v029": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029",
    "v030": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030",
    "v031": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031",
    "v032": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032",
    "v033": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033",
    "v034": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034",
    "v035": "/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035",
    "v036": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportCraneCandidate_v036",
    "v037": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v037",
    "v038": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHookCandidate_v038",
    "v039": "/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039",
    "v040": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040",
    "v041": "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041",
    "v042": "/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042",
    "v108": "/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108",
    "v109": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109",
    "v110": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v110",
    "v113": "/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113",
    "v116": "/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116",
    "v117": "/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117",
    "v118": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118",
    "v119": "/Game/LineBoss/Maps/LB_PressShop_PR004HallFinishCandidate_v119",
    "v124": "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124",
    "v135": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVRuntimeCandidate_v135",
    "v136": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136",
    "v141": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v141",
    "v142": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v142",
    "v180": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180",
    "v190": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190",
    "v140": "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140",
    "v043": "/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043",
    "v044": "/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044",
    "v045": "/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045",
    "v046": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046",
    "v047": "/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047",
    "v048": "/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048",
    "v049": "/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049",
    "v050": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050",
    "v051": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051",
    "v052": "/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052",
    "v053": "/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053",
    "v054": "/Game/LineBoss/Maps/LB_PressShop_PR006LevellerCandidate_v054",
    "v055": "/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055",
    "v056": "/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056",
    "v057": "/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057",
    "v058": "/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058",
    "v059": "/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059",
    "v060": "/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060",
    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",
}
if CANDIDATE not in MAPS:
    raise RuntimeError(f"Unknown LB_PR004_COLLISION_CANDIDATE={CANDIDATE!r}")
MAP = MAPS[CANDIDATE]
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_navigation_runtime_{CANDIDATE}.json"
START = unreal.Vector(-5600.0, -1300.0, 30.0)
END = unreal.Vector(-4400.0, -2000.0, 30.0)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def finish(status, failure, path_length=None, path_points=None, partial=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    points = [] if path_points is None else [
        [point.x, point.y, point.z] for point in path_points]
    valid = failure is None and path_length is not None
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "$schema": f"line-boss/audit/press-shop-pr004-navigation-runtime-{CANDIDATE}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "start_cm": [START.x, START.y, START.z],
        "end_cm": [END.x, END.y, END.z],
        "path_valid": valid,
        "path_partial": partial,
        "path_length_cm": path_length,
        "path_points_cm": points,
        "failure": failure,
        "promotion_authorized": False,
    }, indent=2), encoding="utf-8")
    if failure:
        unreal.log_error(f"LINE_BOSS_PR004_NAV_RUNTIME_FAIL failure={failure} output={OUT}")
    else:
        unreal.log(f"LINE_BOSS_PR004_NAV_RUNTIME_PASS length={path_length} points={len(points)} output={OUT}")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds):
    elapsed = time.monotonic() - started
    if elapsed > 60.0:
        finish("RUNTIME_NAVIGATION_TIMEOUT__NOT_PROMOTED", "timeout")
        return
    if elapsed < 4.0:
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    try:
        bootstrap = next((actor for actor in unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBPressShopNavigationBootstrap)), None)
        if bootstrap is None:
            finish("RUNTIME_NAVIGATION_PATH_FAIL__NOT_PROMOTED", "bootstrap_actor_missing")
            return
        if not bootstrap.validate_path(START, END):
            finish("RUNTIME_NAVIGATION_PATH_FAIL__NOT_PROMOTED", "invalid_or_partial_native_path")
            return
        path_length = float(bootstrap.get_validated_path_length())
        path_points = list(bootstrap.get_validated_path_points())
        if path_length < 1200.0:
            finish("RUNTIME_NAVIGATION_PATH_FAIL__NOT_PROMOTED", "path_length_shorter_than_endpoint_distance")
            return
        finish("RUNTIME_NAVIGATION_PATH_PASS__NOT_PROMOTED", None,
               path_length, path_points, False)
    except Exception as exc:
        finish("RUNTIME_NAVIGATION_API_FAIL__NOT_PROMOTED", f"exception={exc}")


handle = unreal.register_slate_post_tick_callback(tick)
