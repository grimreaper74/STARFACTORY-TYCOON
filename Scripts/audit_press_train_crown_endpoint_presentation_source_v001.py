"""Audit crown/endpoint presentation source before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/CrownEndpointPresentation_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_crown_endpoint_presentation_source_audit_v001.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
required = {
    "SM_CA_MW_PT_HeavyCrownMass_v001",
    "SM_CA_MW_PT_S01VisibleBlankFeed_v001",
    "SM_CA_MW_PT_S07VisiblePanelDischarge_v001",
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
    elif minimum[0] < -4500.5 or maximum[0] > 3500.5:
        failures.append(f"across-train local bound exceeded: {name} {minimum[0]}..{maximum[0]}")
    if name == "SM_CA_MW_PT_S01VisibleBlankFeed_v001" and (minimum[1] < -1000.5 or maximum[1] > 3250.5):
        failures.append(f"S01 local feed bound exceeded: {minimum[1]}..{maximum[1]}")
    if name == "SM_CA_MW_PT_S07VisiblePanelDischarge_v001" and (minimum[1] < -6000.5 or maximum[1] > 0.5):
        failures.append(f"S07 local discharge bound exceeded: {minimum[1]}..{maximum[1]}")
    if row.get("collision_role") != "no_collision_presentation" or not row.get("material_slots"):
        failures.append(f"presentation/material contract missing: {name}")
if not (SOURCE / manifest.get("source_blend", "")).is_file():
    failures.append("source Blend missing")
report = {
    "$schema": "cairnwell/audit/press-train-crown-endpoint-presentation-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_V001_DIMENSIONS_HASHES_MATERIALS_LOCAL_BOUNDS_AND_TBC_AUTHORITY__UNREAL_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_CROWN_ENDPOINT_PRESENTATION_V001_SOURCE__NOT_PROMOTED"
    ),
    "source_manifest": str(MANIFEST_PATH.relative_to(ROOT)).replace("\\", "/"),
    "asset_count": len(rows),
    "assets": list(rows.values()),
    "world_placement": manifest.get("world_placement"),
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
