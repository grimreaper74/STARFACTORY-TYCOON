"""Validate and record the authoritative PR-010 design intake."""

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
PACK = ROOT / "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0"
OUT = ROOT / "Saved/Audits/PR010_Intake/pr010_authority_intake_v001.json"
OUT.parent.mkdir(parents=True, exist_ok=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


authority = json.loads((PACK / "data/authority_and_assumptions.json").read_text(encoding="utf-8-sig"))
states = json.loads((PACK / "data/state_models.json").read_text(encoding="utf-8-sig"))
with (PACK / "data/station_dimensions_and_datums.csv").open(encoding="utf-8-sig", newline="") as handle:
    station = next(row for row in csv.DictReader(handle) if row["area_id"] == "PR010")
with (PACK / "data/module_register.csv").open(encoding="utf-8-sig", newline="") as handle:
    modules = [row for row in csv.DictReader(handle) if row["area_id"] == "PR010"]
with (PACK / "data/moving_parts_and_pivots.csv").open(encoding="utf-8-sig", newline="") as handle:
    movers = [row for row in csv.DictReader(handle) if row["area_id"] == "PR010"]
with (PACK / "data/fault_matrix.csv").open(encoding="utf-8-sig", newline="") as handle:
    faults = [row for row in csv.DictReader(handle) if row["area_id"] == "PR010"]

failures = []
fixed = authority["fixed"]
if fixed.get("PR010_world_datum_cm") != [1350, -2000, 0]: failures.append("world datum mismatch")
if fixed.get("PR010_lane_centres_x_mm") != [-4500, -1500, 1500, 4500]: failures.append("lane centres mismatch")
if station.get("overall_width_mm") != "14000" or station.get("overall_length_mm") != "8400" or station.get("overall_height_mm") != "3600":
    failures.append("station EST envelope mismatch")
if len(modules) != 10: failures.append(f"expected 10 PR010 modules, found {len(modules)}")
if len(movers) != 6: failures.append(f"expected 6 PR010 mover contracts, found {len(movers)}")
if len(faults) != 5: failures.append(f"expected 5 scheduled PR010 faults, found {len(faults)}")
expected_states = ["RESERVATION_WAIT", "LANE_SELECT", "TRANSFER", "STORED", "TRAIN_RESERVED", "VEHICLE_HANDOFF"]
if states.get("pr010_runtime") != expected_states: failures.append("runtime-state sequence mismatch")

source_files = [
    "README_FIRST.md",
    "data/authority_and_assumptions.json",
    "data/station_dimensions_and_datums.csv",
    "data/module_register.csv",
    "data/moving_parts_and_pivots.csv",
    "data/fault_matrix.csv",
    "data/interaction_points_and_clearances.csv",
    "data/lod_collision_schedule.csv",
    "data/state_models.json",
    "data/unreal_asset_manifest.csv",
    "docs/PRESS_SHOP_REMAINING_MACHINERY_ENGINEERING_SPEC_v1.0.md",
    "visuals/SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png",
]
result = {
    "$schema": "cairnwell/audit/pr010-authority-intake-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_AUTHORITY_INTAKE__BLOCKOUT_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_AUTHORITY_INTAKE",
    "authority_document": "Docs/PR010_IMPLEMENTATION_AUTHORITY.md",
    "world_datum_cm": fixed.get("PR010_world_datum_cm"),
    "lane_centres_x_mm": fixed.get("PR010_lane_centres_x_mm"),
    "lane_pitch_mm": 3000,
    "estimated_envelope_mm": [14000, 8400, 3600],
    "module_count": len(modules),
    "mover_contract_count": len(movers),
    "scheduled_fault_count": len(faults),
    "runtime_states": states.get("pr010_runtime"),
    "owner_overrides": {
        "player": "control-room-only",
        "workers": "no worker NPC requirement",
        "vehicle_handoff": "autonomous AGV-compatible normal operation",
        "walkway": "certified service/robot and emergency-access allowance, not player route",
        "enclosure": "enclosed shuttle/utility spine with readable guarded lane apertures; no redundant perimeter cage",
    },
    "open_authority": [
        "Confirm PR010 local-to-world rotation from accepted master-plan context.",
        "Press Train A-D world datums remain TBC and must not be invented.",
        "Capacity and overall footprint remain EST until Unreal blockout validation.",
    ],
    "source_hashes": {name: sha256(PACK / name) for name in source_files},
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "output": str(OUT), "failures": failures}, indent=2))
if failures:
    raise SystemExit(1)

