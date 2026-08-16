"""Audit reusable press-train stage-detail source before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/StageDetail_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_STAGE_DETAIL_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_stage_detail_source_audit_v001.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
failures = []
required = {
    "SM_CA_MW_PT_StageServicePack_v001",
    "SM_CA_MW_PT_S01DestackDetail_v001",
    "SM_CA_MW_PT_S07UnloadInspectDetail_v001",
    "SM_CA_MW_PT_MidTrainProcessService_v001",
}
rows = {row["asset"]: row for row in manifest.get("assets", [])}
if set(rows) != required:
    failures.append(f"asset set mismatch: {sorted(set(rows) ^ required)}")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement was invented")
if "hidden mechanism is not simulated" not in manifest.get("design_model", ""):
    failures.append("CCTV-first presentation contract is missing")
for name, row in rows.items():
    path = SOURCE / row["file"]
    if not path.is_file():
        failures.append(f"missing FBX: {name}")
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if digest != row.get("sha256"):
        failures.append(f"hash mismatch: {name}")
    if path.stat().st_size != row.get("bytes"):
        failures.append(f"size mismatch: {name}")
    dims = row.get("measured_dimensions_mm", [])
    envelope = row.get("planning_envelope_mm", [])
    if len(dims) != 3 or len(envelope) != 3 or any(d > e + 0.5 for d, e in zip(dims, envelope)):
        failures.append(f"envelope exceeded: {name} {dims} > {envelope}")
    if row.get("collision_role") != "no_collision_presentation":
        failures.append(f"unsafe source collision role: {name}")
    if not row.get("material_slots"):
        failures.append(f"no material slots: {name}")
blend = SOURCE / manifest.get("source_blend", "")
if not blend.is_file():
    failures.append("source blend missing")
report = {
    "$schema": "cairnwell/audit/press-train-stage-detail-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_STAGE_DETAIL_V001_DIMENSIONS_HASHES_MATERIALS_PIVOTS_AND_TBC_AUTHORITY__UNREAL_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_STAGE_DETAIL_V001_SOURCE__NOT_PROMOTED",
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
