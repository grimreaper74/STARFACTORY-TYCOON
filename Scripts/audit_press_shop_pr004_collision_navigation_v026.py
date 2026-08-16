"""Read-only PR-004 collision/navigation and operator-access gate."""

import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


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
OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_collision_navigation_{CANDIDATE}.json"
RUNTIME_NAV_OUT = Path(unreal.Paths.project_saved_dir()) / f"Audits/press_shop_pr004_navigation_runtime_{CANDIDATE}.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

level_actors = actors_api.get_all_level_actors()
by_label = {actor.get_actor_label(): actor for actor in level_actors}
failures = []


def primitive_row(label, component):
    collision_enabled = component.get_editor_property("body_instance").get_editor_property("collision_enabled")
    return {
        "actor": label,
        "component": component.get_name(),
        "collision_profile": str(component.get_collision_profile_name()),
        "collision_enabled": str(collision_enabled),
        "has_collision": collision_enabled != unreal.CollisionEnabled.NO_COLLISION,
        "can_ever_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
    }


floor_rows = []
for label, actor in by_label.items():
    if not label.startswith("LB_PR004_V025_"):
        continue
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    if component is None:
        failures.append(f"Floor marking has no primitive component: {label}")
        continue
    row = primitive_row(label, component)
    floor_rows.append(row)
    if row["has_collision"]:
        failures.append(f"Floor marking collision enabled: {label}={row['collision_enabled']}")
    if row["can_ever_affect_navigation"]:
        failures.append(f"Floor marking affects navigation: {label}")

bin_labels = [
    "LB_INT_PR004_V009_DRESS08_BandCompactorBin",
    "LB_PR004_V026_PackagingWaste_WrapCardBin",
]
bin_rows = []
for label in bin_labels:
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"Missing packaging bin: {label}")
        continue
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    row = primitive_row(label, component)
    location = actor.get_actor_location()
    row["location_cm"] = [location.x, location.y, location.z]
    bin_rows.append(row)
    if not row["has_collision"]:
        failures.append(f"Packaging bin has no collision: {label}")
    if not row["can_ever_affect_navigation"]:
        failures.append(f"Packaging bin is navigation-irrelevant: {label}")

hmi_labels = ["LB_PR004_V026_HMI_Base", "LB_PR004_V026_HMI_Post", "LB_PR004_V026_HMI_Bezel"]
hmi_rows = []
for label in hmi_labels:
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"Missing HMI support actor: {label}")
        continue
    component = actor.get_component_by_class(unreal.PrimitiveComponent)
    row = primitive_row(label, component)
    location = actor.get_actor_location()
    row["location_cm"] = [location.x, location.y, location.z]
    hmi_rows.append(row)
    if not row["has_collision"]:
        failures.append(f"HMI support has no collision: {label}")
    expected_nav = label != "LB_PR004_V026_HMI_Bezel"
    if row["can_ever_affect_navigation"] != expected_nav:
        failures.append(f"HMI navigation flag mismatch: {label}")

station = by_label.get("LB_INT_PR004_V024_InteractiveUnpackageStation")
if station is None:
    failures.append("Missing native PR-004 station")
    station_rows = []
else:
    station_rows = []
    for component in station.get_components_by_class(unreal.PrimitiveComponent):
        if component.get_name() in {
            "PR004_OperatorHMI", "PR004_WrappedCoilVisual", "PR004_BareCoilVisual",
            "PR004_HMI_BrandText", "PR004_HMI_StationText", "PR004_HMI_StateText",
            "PR004_HMI_CoilText", "PR004_HMI_RecipeText", "PR004_HMI_ChecklistText",
            "PR004_HMI_ActionText",
        }:
            station_rows.append(primitive_row(station.get_actor_label(), component))
    widget = next((row for row in station_rows if row["component"] == "PR004_OperatorHMI"), None)
    if widget is None or not widget["has_collision"]:
        failures.append("HMI touch surface is not query-collidable")
    for row in station_rows:
        if row["component"].startswith("PR004_HMI_") and row["component"] != "PR004_OperatorHMI":
            if row["has_collision"]:
                failures.append(f"HMI text blocks cursor trace: {row['component']}")

# The approved operator pad is x[-5260,-4840], y[-1575,-1405]. The HMI is
# deliberately on its north-west edge; the segregated bins remain east of it.
operator_pad = {"x": [-5260.0, -4840.0], "y": [-1575.0, -1405.0]}
minimum_clearance_cm = None
if len(bin_rows) == 2:
    hmi_xy = (-5295.0, -1490.0)
    minimum_clearance_cm = min(math.dist(hmi_xy, row["location_cm"][:2]) for row in bin_rows)
    if minimum_clearance_cm < 300.0:
        failures.append(f"Bins are too close to HMI/operator approach: {minimum_clearance_cm:.1f} cm")

nav_actor_rows = []
for actor in level_actors:
    class_name = actor.get_class().get_name()
    if "Nav" in class_name or "Recast" in class_name:
        nav_actor_rows.append({"label": actor.get_actor_label(), "class": class_name})

runtime_navigation_path_passed = False
runtime_navigation_evidence = None
if RUNTIME_NAV_OUT.exists():
    runtime_navigation_evidence = json.loads(RUNTIME_NAV_OUT.read_text(encoding="utf-8"))
    runtime_navigation_path_passed = (
        runtime_navigation_evidence.get("map") == MAP
        and runtime_navigation_evidence.get("status") == "RUNTIME_NAVIGATION_PATH_PASS__NOT_PROMOTED"
        and runtime_navigation_evidence.get("path_valid") is True
        and runtime_navigation_evidence.get("path_partial") is False
        and float(runtime_navigation_evidence.get("path_length_cm", -1.0)) >= 1200.0
    )
if not runtime_navigation_path_passed:
    failures.append("Fresh complete PR-004 runtime navigation path evidence is missing or failed")

visual_context_rows = []
if CANDIDATE in ("v028", "v029", "v030", "v031", "v032", "v033"):
    prefixes = (("LB_PR004_V028_", "LB_PR004_V031_", "LB_PR004_V033_") if CANDIDATE == "v033"
                else ("LB_PR004_V028_", "LB_PR004_V031_", "LB_PR004_V032_") if CANDIDATE == "v032"
                else ("LB_PR004_V028_", "LB_PR004_V031_") if CANDIDATE == "v031"
                else ("LB_PR004_V028_",))
    for label, actor in by_label.items():
        if not label.startswith(prefixes):
            continue
        if not any(token in label for token in (
                "Roof", "WallLiner", "BridgeCrossTie", "CraneIdentity", "Splice", "Rail",
                "Festoon", "TrolleyService", "WestIdentity", "CHookCameraFill",
                "Yoke", "BoreLance", "ReevingFall", "HallTaskFill", "PurposeBuilt")):
            continue
        component = actor.get_component_by_class(unreal.PrimitiveComponent)
        if component is None:
            failures.append(f"Visual context actor has no primitive component: {label}")
            continue
        row = primitive_row(label, component)
        visual_context_rows.append(row)
        if row["has_collision"]:
            failures.append(f"Overhead/cutaway visual context unexpectedly collides: {label}")
        if row["can_ever_affect_navigation"]:
            failures.append(f"Overhead/cutaway visual context affects navigation: {label}")

result = {
    "$schema": f"line-boss/audit/press-shop-pr004-collision-navigation-{CANDIDATE}/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "status": "COLLISION_AND_RUNTIME_NAVIGATION_PASS__NOT_PROMOTED" if not failures
              else "COLLISION_OR_NAV_RELEVANCE_FAIL__NOT_PROMOTED",
    "floor_marking_count": len(floor_rows),
    "floor_markings": sorted(floor_rows, key=lambda row: row["actor"]),
    "packaging_bins": bin_rows,
    "hmi_support": hmi_rows,
    "station_touch_and_text": station_rows,
    "operator_pad_bounds_cm": operator_pad,
    "minimum_bin_to_hmi_clearance_cm": minimum_clearance_cm,
    "navigation_actors": nav_actor_rows,
    "runtime_navigation_path_passed": runtime_navigation_path_passed,
    "runtime_navigation_evidence": str(RUNTIME_NAV_OUT),
    "overhead_cutaway_and_crane_fabrication_visual_context": visual_context_rows,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError(f"PR-004 collision/navigation audit failed: {failures}")
unreal.log(f"LINE_BOSS_PR004_COLLISION_NAV_SOURCE_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
