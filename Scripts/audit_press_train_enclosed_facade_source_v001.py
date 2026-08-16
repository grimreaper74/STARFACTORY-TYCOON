"""Audit the reusable enclosed press facade Blender/FBX source package."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/EnclosedFacade_v001"
MANIFEST = SOURCE / "PRESS_TRAIN_ENCLOSED_FACADE_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_enclosed_facade_source_audit_v001.json"
EXPECTED = {
    "SM_CA_MW_PT_MidPressEnclosedFacade_v001": [6500, 6500, 8500],
    "SM_CA_MW_PT_DrawPressEnclosedFacade_v001": [7000, 7000, 11000],
    "SM_CA_MW_PT_S01DestackEnclosedFacade_v001": [6500, 6500, 6500],
    "SM_CA_MW_PT_S07UnloadInspectEnclosedFacade_v001": [9000, 7500, 7000],
}
failures = []
if not MANIFEST.is_file():
    raise SystemExit(f"missing manifest: {MANIFEST}")
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
rows = {row["asset"]: row for row in data.get("assets", [])}
if set(rows) != set(EXPECTED):
    failures.append(f"asset set mismatch expected={sorted(EXPECTED)} actual={sorted(rows)}")
for name, envelope in EXPECTED.items():
    row = rows.get(name)
    if not row:
        continue
    path = SOURCE / row["file"]
    if not path.is_file() or path.stat().st_size < 1024:
        failures.append(f"missing/empty FBX {name}")
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if digest != row.get("sha256") or path.stat().st_size != row.get("bytes"):
        failures.append(f"hash/size mismatch {name}")
    measured = row.get("measured_dimensions_mm", [])
    if len(measured) != 3 or any(value > limit + 5 for value, limit in zip(measured, envelope)):
        failures.append(f"{name} exceeds planning envelope measured={measured} envelope={envelope}")
    bounds = row.get("local_aabb_mm", {})
    if len(bounds.get("min", [])) != 3 or len(bounds.get("max", [])) != 3 or bounds["min"][2] < -5:
        failures.append(f"{name} invalid floor-centred local bounds: {bounds}")
    materials = set(row.get("material_slots", []))
    if not {"CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen", "CA_MW_LabelWhite"}.issubset(materials):
        failures.append(f"{name} missing enclosure/identity material hierarchy: {sorted(materials)}")
if data.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement authority is not TBC_NOT_INVENTED")
blend = SOURCE / data.get("source_blend", "")
if not blend.is_file() or blend.stat().st_size < 1024:
    failures.append("source Blend missing or empty")
report = {
    "$schema": "cairnwell/audit/press-train-enclosed-facade-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_ENCLOSED_FACADE_V001_DIMENSIONS_HASHES_MATERIALS_PIVOTS_AND_TBC_AUTHORITY__UNREAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_ENCLOSED_FACADE_V001_SOURCE__NOT_PROMOTED"),
    "source_root": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "asset_count": len(rows), "assets": list(rows.values()),
    "world_placement": data.get("world_placement"), "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
