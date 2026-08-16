"""Read-only diagnostics for the v056 static-gate failures."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v056"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_v056_gate_failure_diagnostics.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

scope = []
missing_tbc = []
rows = []
for actor in actors_api.get_all_level_actors():
    tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" not in tags:
        continue
    scope.append(actor)
    if "LB.Authority.WorldPlacement.TBC_NOT_INVENTED" not in tags:
        missing_tbc.append({"actor": actor.get_actor_label(), "class": actor.get_class().get_name(), "tags": sorted(tags)})
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "actor": actor.get_actor_label(),
        "class": actor.get_class().get_name(),
        "origin_cm": [origin.x, origin.y, origin.z],
        "extent_cm": [extent.x, extent.y, extent.z],
        "min_x_cm": origin.x - extent.x,
        "max_x_cm": origin.x + extent.x,
        "min_y_cm": origin.y - extent.y,
        "max_y_cm": origin.y + extent.y,
        "coupling": "LB.PressTrain.Fixed.DockCouplingEvidence" in tags,
    })

mesh_rows = [row for row in rows if row["class"] == "StaticMeshActor"]
min_x = min(row["min_x_cm"] for row in mesh_rows)
max_x = max(row["max_x_cm"] for row in mesh_rows)
min_y = min(row["min_y_cm"] for row in mesh_rows)
max_y = max(row["max_y_cm"] for row in mesh_rows)
report = {
    "$schema": "cairnwell/audit/press-train-a-v056-gate-failure-diagnostics/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "READ_ONLY_DIAGNOSTIC__V056_UNCHANGED__NOT_PROMOTED",
    "map": MAP,
    "scope_count": len(scope),
    "missing_tbc": missing_tbc,
    "aggregate_xy_cm": {"min_x": min_x, "max_x": max_x, "size_x": max_x-min_x, "min_y": min_y, "max_y": max_y, "size_y": max_y-min_y},
    "x_min_contributors": sorted(mesh_rows, key=lambda row: row["min_x_cm"])[:12],
    "x_max_contributors": sorted(mesh_rows, key=lambda row: row["max_x_cm"], reverse=True)[:12],
    "couplings": [row for row in rows if row["coupling"]],
    "map_modified": False,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
