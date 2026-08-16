"""Audit the seven raised-geometry stage identity sources."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/RaisedIdentityPlates_v001"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_RAISED_IDENTITY_PLATES_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_raised_identity_plates_source_audit_v001.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
failures = []
assets = manifest.get("assets", [])
if len(assets) != 7:
    failures.append(f"expected seven assets, got {len(assets)}")
if {row.get("stage_code") for row in assets} != {f"S{i:02d}" for i in range(1, 8)}:
    failures.append("S01-S07 stage-code set mismatch")
if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement authority was invented")
for row in assets:
    path = SOURCE / row["file"]
    if not path.is_file():
        failures.append(f"missing FBX: {row['file']}")
        continue
    if hashlib.sha256(path.read_bytes()).hexdigest().upper() != row.get("sha256"):
        failures.append(f"hash mismatch: {row['asset']}")
    dims = row.get("measured_dimensions_mm", [])
    if len(dims) != 3 or not (60 <= dims[0] <= 100 and 1180 <= dims[1] <= 1220 and 380 <= dims[2] <= 420):
        failures.append(f"unexpected plate envelope: {row['asset']} {dims}")
    if set(row.get("material_slots", [])) != {"CA_MW_TrainAccent", "CA_MW_WorkedSteel", "CA_MW_LabelWhite"}:
        failures.append(f"material separation mismatch: {row['asset']}")

report = {
    "$schema": "cairnwell/audit/press-train-raised-identity-plates-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__SEVEN_RAISED_GEOMETRY_STAGE_PLATES_DIMENSION_HASH_MATERIAL_PIVOT_AND_TBC_AUTHORITY_GATE__UNREAL_IMPORT_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_RAISED_IDENTITY_SOURCE_GATE__NOT_PROMOTED"),
    "manifest": str(MANIFEST_PATH), "asset_count": len(assets),
    "assets": [{"asset": row.get("asset"), "stage_code": row.get("stage_code"), "dimensions_mm": row.get("measured_dimensions_mm")} for row in assets],
    "world_placement": manifest.get("world_placement"), "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
