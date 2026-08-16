"""Audit the reusable mechanical-bay Blender/FBX source before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/MechanicalBay_v001"
MANIFEST = SOURCE / "PRESS_TRAIN_MECHANICAL_BAY_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_mechanical_bay_source_audit_v001.json"
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
failures = []
assets = data.get("assets", [])
if len(assets) != 1:
    failures.append(f"expected one reusable module, found {len(assets)}")
if data.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement was invented")
records = []
for asset in assets:
    path = SOURCE / asset["file"]
    measured = [float(value) for value in asset["measured_dimensions_mm"]]
    envelope = [float(value) for value in asset["planning_envelope_mm"]]
    within = all(value <= limit + 0.5 for value, limit in zip(measured, envelope))
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.is_file() else None
    if not path.is_file() or path.stat().st_size < 1024:
        failures.append("mechanical-bay FBX missing or empty")
    if digest != asset.get("sha256"):
        failures.append("mechanical-bay FBX hash mismatch")
    if not within:
        failures.append(f"mechanical-bay dimensions exceed envelope: measured={measured} envelope={envelope}")
    if any("LINEBOSS" in value.upper().replace(" ", "") for value in asset.get("material_slots", [])):
        failures.append("working-title material identity found")
    records.append({"asset": asset.get("asset"), "measured_dimensions_mm": measured, "planning_envelope_mm": envelope, "within_planning_envelope": within, "fbx_sha256": digest})
blend = SOURCE / data.get("source_blend", "")
if not blend.is_file() or blend.stat().st_size < 1024:
    failures.append("Blender source missing or empty")
report = {
    "$schema": "cairnwell/audit/press-train-mechanical-bay-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_MECHANICAL_BAY_V001_DIMENSIONS_HASH_PIVOT_MATERIALS_LOCAL_AUTHORITY__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_MECHANICAL_BAY_SOURCE_V001__NOT_PROMOTED",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "records": records,
    "world_placement": data.get("world_placement"),
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
