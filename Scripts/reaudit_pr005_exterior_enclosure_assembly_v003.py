"""Correctly derive PR-005 v003 aggregate assembly bounds from all nine modules."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorEnclosureAssemblyCandidate_v003"
MANIFEST = json.loads((ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003/PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json").read_text(encoding="utf-8"))
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_assembly_reaudit_v003.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

expected_min = [1e9, 1e9, 1e9]
expected_max = [-1e9, -1e9, -1e9]
for row in MANIFEST["assets"]:
    source_min = [float(v) / 10.0 for v in row["bounds_min_mm"]]
    source_max = [float(v) / 10.0 for v in row["bounds_max_mm"]]
    ue_min = [source_min[0], -source_max[1], source_min[2]]
    ue_max = [source_max[0], -source_min[1], source_max[2]]
    for i in range(3):
        expected_min[i] = min(expected_min[i], ue_min[i])
        expected_max[i] = max(expected_max[i], ue_max[i])

modules = [actor for actor in actors_api.get_all_level_actors()
           if isinstance(actor, unreal.StaticMeshActor) and "LB.PR005.ExteriorEnclosure.AssemblyStudy" in {str(tag) for tag in actor.tags}
           and actor.get_actor_label() != "LB_PR005_V003_ValidationFloor"]
measured_min = [1e9, 1e9, 1e9]
measured_max = [-1e9, -1e9, -1e9]
rows, failures = [], []
by_label = {actor.get_actor_label(): actor for actor in modules}
for source_row in MANIFEST["assets"]:
    label = "LB_PR005_V003_" + source_row["asset_name"].replace("SM_CA_MW_PR005_", "")
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"missing actor {label}")
        continue
    px, py, pz = source_row["pivot_m"]
    expected_location = [float(px) * 100.0, -float(py) * 100.0, float(pz) * 100.0]
    location = actor.get_actor_location()
    location_delta = [location.x - expected_location[0], location.y - expected_location[1], location.z - expected_location[2]]
    if max(abs(v) for v in location_delta) > 0.02:
        failures.append(f"pivot placement drift {label}")
    origin, extent = actor.get_actor_bounds(False, False)
    actor_min = [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z]
    actor_max = [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z]
    for i in range(3):
        measured_min[i] = min(measured_min[i], actor_min[i])
        measured_max[i] = max(measured_max[i], actor_max[i])
    rows.append({"actor": label, "expected_location_cm": expected_location, "measured_location_cm": [location.x, location.y, location.z], "max_location_delta_cm": max(abs(v) for v in location_delta)})

aggregate_delta = [measured_min[i] - expected_min[i] for i in range(3)] + [measured_max[i] - expected_max[i] for i in range(3)]
if len(modules) != 9:
    failures.append(f"expected 9 modules, found {len(modules)}")
if max(abs(v) for v in aggregate_delta) > 0.2:
    failures.append(f"aggregate drift {aggregate_delta}")

report = {
    "$schema": "cairnwell/audit/press-shop-pr005-exterior-enclosure-assembly-reaudit-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NINE_MODULE_LOCAL_ORIGIN_ASSEMBLY_AND_MANIFEST_PIVOT_PLACEMENT_EXACT__VISUAL_GATE_REQUIRED__NOT_INTEGRATED_NOT_PROMOTED" if not failures else "FAIL__PR005_V003_ASSEMBLY_REAUDIT__NOT_INTEGRATED_NOT_PROMOTED",
    "map": MAP,
    "corrects_expected_extent_only": "Initial build audit used shell max X 286.95 cm and omitted utilities-side service-door max X 298.0 cm; map geometry was not changed.",
    "expected_bounds_min_cm": [round(v, 4) for v in expected_min],
    "expected_bounds_max_cm": [round(v, 4) for v in expected_max],
    "measured_bounds_min_cm": [round(v, 4) for v in measured_min],
    "measured_bounds_max_cm": [round(v, 4) for v in measured_max],
    "assembly_dimensions_mm": [round((measured_max[i] - measured_min[i]) * 10.0, 3) for i in range(3)],
    "actors": rows, "world_placement": "LOCAL_ORIGIN_STUDY_ONLY__TBC_NOT_INVENTED",
    "v053_or_runtime_authority_changed": False, "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "dimensions_mm": report["assembly_dimensions_mm"], "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
