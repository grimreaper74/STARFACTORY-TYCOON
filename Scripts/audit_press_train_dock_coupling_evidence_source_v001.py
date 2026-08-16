"""Independent file/contract audit for DockCouplingEvidence_v001."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/DockCouplingEvidence_v001"
MANIFEST = SOURCE / "PRESS_TRAIN_DOCK_COUPLING_EVIDENCE_MANIFEST_v001.json"
AUDIT = ROOT / "Saved/Audits/PressTrains/press_train_dock_coupling_evidence_source_audit_v001.json"

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
failures = []
assets = manifest.get("assets", [])
if len(assets) != 1:
    failures.append(f"expected one asset, found {len(assets)}")

required_materials = {
    "CA_MW_FoundryCharcoal", "CA_MW_CairnwellGreen", "CA_MW_SafetyYellow",
    "CA_MW_ServiceGrey", "CA_MW_WorkedSteel", "CA_MW_DarkRubber",
    "CA_MW_TrainAAccent", "CA_MW_StateGreen", "CA_MW_LabelWhite",
}

checked = []
for row in assets:
    path = SOURCE / row["file"]
    exists = path.is_file()
    actual_hash = hashlib.sha256(path.read_bytes()).hexdigest().upper() if exists else None
    dimensions = row.get("measured_dimensions_mm", [])
    envelope = row.get("planning_envelope_mm", [])
    features = row.get("features", {})
    if not exists:
        failures.append(f"missing FBX {row['file']}")
    elif actual_hash != row.get("sha256"):
        failures.append(f"hash mismatch {row['asset']}")
    if len(dimensions) != 3 or len(envelope) != 3 or any(d > e + 1.0 for d, e in zip(dimensions, envelope)):
        failures.append(f"planning envelope exceeded {row['asset']}: {dimensions} vs {envelope}")
    if not required_materials.issubset(set(row.get("material_slots", []))):
        failures.append(f"required material separation missing {row['asset']}")
    expected_features = {
        "hydraulic_lock_bridges": 2,
        "mated_service_connectors": 3,
        "articulated_cable_chain_links": 6,
        "tow_capture": 1,
        "engagement_permissive_witnesses": 3,
    }
    if features != expected_features:
        failures.append(f"feature contract mismatch {features}")
    checked.append({
        "asset": row.get("asset"),
        "file_exists": exists,
        "sha256_matches": actual_hash == row.get("sha256"),
        "measured_dimensions_mm": dimensions,
        "planning_envelope_mm": envelope,
        "material_slots": row.get("material_slots", []),
        "features": features,
    })

if manifest.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement authority changed")
if manifest.get("promotion_authorized") is not False:
    failures.append("source manifest incorrectly authorizes promotion")
if "Line Boss" in MANIFEST.read_text(encoding="utf-8"):
    failures.append("working title found in diegetic source manifest")
blend = SOURCE / manifest.get("source_blend", "")
if not blend.is_file():
    failures.append("source blend missing")

payload = {
    "$schema": "cairnwell/audit/press-train-dock-coupling-evidence-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DIMENSION_HASH_MATERIAL_FEATURE_AND_AUTHORITY_GATES__UNREAL_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__SOURCE_GATE",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "checked_assets": checked,
    "source_blend_exists": blend.is_file(),
    "world_placement": manifest.get("world_placement"),
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise SystemExit(1)
