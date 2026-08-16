"""Audit the seven explicit-segment identity FBX sources before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/SegmentedIdentityPlates_v002"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_SEGMENTED_IDENTITY_PLATES_MANIFEST_v002.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_segmented_identity_plates_source_audit_v002.json"
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
assets = manifest.get("assets", [])
failures = []
if len(assets) != 7 or {row.get("stage_code") for row in assets} != {f"S{i:02d}" for i in range(1, 8)}:
    failures.append("exact S01-S07 asset set missing")
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
    if len(dims) != 3 or not (95 <= dims[0] <= 105 and 1170 <= dims[1] <= 1190 and 380 <= dims[2] <= 400):
        failures.append(f"unexpected plate envelope: {row['asset']} {dims}")
    if set(row.get("material_slots", [])) != {"CA_MW_TrainAccent", "CA_MW_WorkedSteel", "CA_MW_LabelWhite"}:
        failures.append(f"material separation mismatch: {row['asset']}")
    if not str(row.get("glyph_construction", "")).startswith("explicit bevelled cuboids"):
        failures.append(f"non-robust glyph authority: {row['asset']}")

report = {
    "$schema": "cairnwell/audit/press-train-segmented-identity-plates-source-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__SEVEN_EXPLICIT_SEGMENT_STAGE_PLATES_DIMENSION_HASH_MATERIAL_PIVOT_AND_TBC_AUTHORITY_GATE__UNREAL_IMPORT_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_SEGMENTED_IDENTITY_SOURCE_GATE__NOT_PROMOTED"),
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
