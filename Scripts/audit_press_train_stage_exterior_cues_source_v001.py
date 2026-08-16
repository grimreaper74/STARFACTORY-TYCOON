"""Audit the four dimensioned stage-exterior cue FBX sources before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/StageExteriorCues_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_STAGE_EXTERIOR_CUES_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_stage_exterior_cues_source_audit_v001.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
failures = []
expected_roles = {
    "s03_secondary_form_operator_process_cue",
    "s04_trim_press_operator_process_cue",
    "s05_pierce_press_operator_process_cue",
    "s06_final_restrike_operator_process_cue",
}
roles = {row.get("role") for row in manifest.get("assets", [])}
if roles != expected_roles:
    failures.append(f"role set mismatch: {sorted(str(role) for role in roles)}")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement authority was invented")
if len(manifest.get("assets", [])) != 4:
    failures.append(f"expected four assets, got {len(manifest.get('assets', []))}")
for row in manifest.get("assets", []):
    path = SOURCE / row["file"]
    if not path.is_file():
        failures.append(f"missing FBX: {row['file']}")
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if digest != row.get("sha256"):
        failures.append(f"hash mismatch: {row['asset']}")
    dims = row.get("measured_dimensions_mm", [])
    if len(dims) != 3 or any(value <= 0 for value in dims):
        failures.append(f"invalid dimensions: {row['asset']} {dims}")
    if not row.get("visual_process_cue"):
        failures.append(f"missing process explanation: {row['asset']}")
    if len(row.get("material_slots", [])) < 4:
        failures.append(f"insufficient material separation: {row['asset']}")

report = {
    "$schema": "cairnwell/audit/press-train-stage-exterior-cues-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__FOUR_DIMENSIONED_STAGE_SPECIFIC_EXTERIOR_CUE_SOURCES_HASH_MATERIAL_PIVOT_AND_TBC_AUTHORITY_GATE__UNREAL_IMPORT_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_STAGE_EXTERIOR_CUE_SOURCE_GATE__NOT_PROMOTED"),
    "manifest": str(MANIFEST_PATH),
    "asset_count": len(manifest.get("assets", [])),
    "assets": [{
        "asset": row.get("asset"), "role": row.get("role"),
        "dimensions_mm": row.get("measured_dimensions_mm"),
        "materials": row.get("material_slots"),
    } for row in manifest.get("assets", [])],
    "world_placement": manifest.get("world_placement"),
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
