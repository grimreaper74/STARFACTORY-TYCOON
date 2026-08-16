"""Audit dimensioned PR-010 v103 Blender/FBX source before Unreal intake."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103"
MANIFEST = SOURCE / "PR010_RELEASE_ART_MANIFEST_v103.json"
OUT = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/pr010_release_art_source_audit_v103.json"
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
failures = []
assets = []
for row in data.get("assets", []):
    expected = row["expected_dimensions_mm"]
    measured = row["measured_dimensions_mm"]
    deltas = [abs(float(value) - float(target)) for value, target in zip(measured, expected)]
    path = SOURCE / row["file"]
    if not path.is_file() or path.stat().st_size < 1024:
        failures.append(f"missing/undersized FBX: {row['file']}")
    if max(deltas) > 0.5:
        failures.append(f"dimension mismatch {row['asset']}: {measured} vs {expected}")
    if not row.get("material_slots"):
        failures.append(f"missing material slots: {row['asset']}")
    if "LINEBOSS" in row["asset"].upper() or "LINE BOSS" in row["asset"].upper():
        failures.append(f"working-title branding in source: {row['asset']}")
    assets.append({"asset": row["asset"], "measured_dimensions_mm": measured, "expected_dimensions_mm": expected, "max_delta_mm": max(deltas), "fbx_bytes": path.stat().st_size if path.exists() else 0})
if len(assets) != 3:
    failures.append(f"expected three v103 modules, found {len(assets)}")
if not (SOURCE / data.get("source_blend", "")).is_file():
    failures.append("source blend missing")
report = {
    "$schema": "cairnwell/audit/pr010-release-art-source-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V103_INSTALLED_SERVICE_IDENTITY_SOURCE_DIMENSIONS_MATERIALS_AUTHORITY__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR010_V103_SOURCE__NOT_PROMOTED",
    "source": str(SOURCE), "asset_count": len(assets), "assets": assets,
    "failures": failures, "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
