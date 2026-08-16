"""Audit the local-origin shared press-train source kit before Unreal import."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/PressTrains/Shared/Blockout_v001"
MANIFEST = SOURCE / "PRESS_TRAIN_SHARED_KIT_MANIFEST_v001.json"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_shared_source_audit_v001.json"
data = json.loads(MANIFEST.read_text(encoding="utf-8"))
assets = data.get("assets", [])
required = {
    "SM_CA_MW_PT_CommonPlatform_v001",
    "SM_CA_MW_PT_CommonUtilitySpine_v001",
    "SM_CA_MW_PT_TransferRail_v001",
    "SM_CA_MW_PT_PressFrame_Draw_v001",
    "SM_CA_MW_PT_PressFrame_Form_v001",
    "SM_CA_MW_PT_PressFrame_Trim_v001",
    "SM_CA_MW_PT_PressFrame_Pierce_v001",
    "SM_CA_MW_PT_PressFrame_Flange_v001",
    "SM_CA_MW_PT_DestackLoadCell_v001",
    "SM_CA_MW_PT_UnloadInspectCell_v001",
    "SM_CA_MW_PT_PressSlide_v001",
    "SM_CA_MW_PT_MovingBolster_v001",
    "SM_CA_MW_PT_StageDieSet_v001",
    "SM_CA_MW_PT_DieCart_v001",
    "SM_CA_MW_PT_TransferCrossbar_v001",
    "SM_CA_MW_PT_DestackLift_v001",
}
failures = []
if data.get("world_placement") != "TBC_NOT_INVENTED":
    failures.append("world placement was invented or altered")
if data.get("stage_centres_local_y_mm") != [0, 7500, 15000, 22500, 30000, 37500, 45000]:
    failures.append("seven-stage local centre contract mismatch")
names = {asset.get("asset") for asset in assets}
if names != required:
    failures.append(f"asset set mismatch missing={sorted(required - names)} unexpected={sorted(names - required)}")
if len(assets) != 16:
    failures.append(f"expected 16 modules, found {len(assets)}")

records = []
for asset in assets:
    path = SOURCE / asset["file"]
    measured = [float(value) for value in asset["measured_dimensions_mm"]]
    envelope = [float(value) for value in asset["planning_envelope_mm"]]
    delta = [round(value - limit, 3) for value, limit in zip(measured, envelope)]
    within = all(value <= limit + 0.5 for value, limit in zip(measured, envelope))
    if not path.is_file() or path.stat().st_size < 1024:
        failures.append(f"missing or empty FBX: {asset['asset']}")
        digest = None
    else:
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if not within:
        failures.append(f"planning envelope exceeded by {asset['asset']}: {delta}")
    if not asset.get("material_slots"):
        failures.append(f"no material slots: {asset['asset']}")
    if any("LINEBOSS" in value.upper().replace(" ", "") for value in asset.get("material_slots", [])):
        failures.append(f"working-title material branding: {asset['asset']}")
    records.append({
        "asset": asset["asset"],
        "measured_dimensions_mm": measured,
        "planning_envelope_mm": envelope,
        "measured_minus_envelope_mm": delta,
        "within_planning_envelope": within,
        "fbx_bytes": path.stat().st_size if path.is_file() else 0,
        "fbx_sha256": digest,
        "pivot": asset.get("pivot"),
        "collision_role": asset.get("collision_role"),
    })

blend = SOURCE / data.get("source_blend", "")
if not blend.is_file() or blend.stat().st_size < 1024:
    failures.append("Blender source missing or empty")
report = {
    "$schema": "cairnwell/audit/press-train-shared-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_SHARED_V001_SIXTEEN_MODULES_DIMENSIONS_PIVOTS_MATERIALS_HASHES_LOCAL_AUTHORITY__UNREAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_SHARED_SOURCE_V001__NOT_PROMOTED",
    "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
    "asset_count": len(assets),
    "fixed_or_shell_module_count": sum(not item.get("collision_role", "").startswith("query_only") for item in assets),
    "separate_moving_or_tooling_module_count": sum(item.get("collision_role", "").startswith("query_only") for item in assets),
    "stage_centres_local_y_mm": data.get("stage_centres_local_y_mm"),
    "world_placement": data.get("world_placement"),
    "records": records,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({key: report[key] for key in ("status", "asset_count", "fixed_or_shell_module_count", "separate_moving_or_tooling_module_count", "world_placement", "failures")}, indent=2))
if failures:
    raise SystemExit(1)
