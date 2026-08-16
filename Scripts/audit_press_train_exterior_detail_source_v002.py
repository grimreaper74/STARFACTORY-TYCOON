"""Audit Press Train exterior-detail v002 before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/ExteriorDetail_v002"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_EXTERIOR_DETAIL_MANIFEST_v002.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_exterior_detail_source_audit_v002.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
required = {
    "SM_CA_MW_PT_CrownDriveDress_v002", "SM_CA_MW_PT_ServiceDoorVentPack_v002",
    "SM_CA_MW_PT_AccessPlatformLadder_v002", "SM_CA_MW_PT_S01FeederDress_v002",
    "SM_CA_MW_PT_S07InspectionStillageDress_v002",
}
rows = {row["asset"]: row for row in manifest.get("assets", [])}
failures = []
if set(rows) != required:
    failures.append(f"asset set mismatch: {sorted(set(rows) ^ required)}")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement was invented")
if not str(manifest.get("coordinate_system", "")).startswith("+X operator/HMI/CCTV side, -X die-change side"):
    failures.append("operator/die-change side authority is missing")
for name, row in rows.items():
    path = SOURCE / row["file"]
    if not path.is_file():
        failures.append(f"missing FBX: {name}")
        continue
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != row.get("sha256"):
        failures.append(f"hash mismatch: {name}")
    if path.stat().st_size != row.get("bytes"):
        failures.append(f"size mismatch: {name}")
    dims = row.get("measured_dimensions_mm", [])
    envelope = row.get("planning_envelope_mm", [])
    if len(dims) != 3 or len(envelope) != 3 or any(value > limit + 0.5 for value, limit in zip(dims, envelope)):
        failures.append(f"envelope exceeded: {name} {dims} > {envelope}")
    bounds = row.get("local_aabb_mm", {})
    minimum, maximum = bounds.get("min", []), bounds.get("max", [])
    if len(minimum) != 3 or len(maximum) != 3:
        failures.append(f"local AABB missing: {name}")
    elif maximum[0] > 3500.5 or minimum[0] < -4500.5:
        failures.append(f"across-train local bound exceeded: {name} {minimum[0]}..{maximum[0]}")
    if name == "SM_CA_MW_PT_S01FeederDress_v002" and minimum[1] < -5500.5:
        failures.append(f"S01 infeed local bound exceeded: {minimum[1]} mm")
    if name == "SM_CA_MW_PT_S07InspectionStillageDress_v002" and maximum[1] > 5500.5:
        failures.append(f"S07 outfeed local bound exceeded: {maximum[1]} mm")
    if row.get("collision_role") != "no_collision_presentation" or not row.get("material_slots"):
        failures.append(f"presentation/material contract missing: {name}")
if not (SOURCE / manifest.get("source_blend", "")).is_file():
    failures.append("source Blend missing")
report = {
    "$schema": "cairnwell/audit/press-train-exterior-detail-source-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_EXTERIOR_DETAIL_V002_DIMENSIONS_LOCAL_BOUNDS_HASHES_MATERIALS_OPERATOR_SIDE_AND_TBC_AUTHORITY__UNREAL_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_EXTERIOR_DETAIL_V002_SOURCE__NOT_PROMOTED"),
    "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
    "asset_count": len(rows), "assets": list(rows.values()),
    "world_placement": manifest.get("world_placement"), "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
