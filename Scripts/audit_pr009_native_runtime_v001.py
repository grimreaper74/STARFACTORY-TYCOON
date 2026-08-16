"""Record the focused native PR-009 runtime/save automation gate."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Saved/Automation/PR009_Runtime_v001/index.json"
AUDIT = ROOT / "Saved/Audits/press_shop_pr009_native_runtime_source_v001.json"
report_data = REPORT.read_bytes()
report = json.loads(report_data)
test = next((item for item in report.get("tests", []) if item.get("fullTestPath") == "LineBoss.PressShop.PR009.RuntimeAndSave"), None)
if report.get("failed") != 0 or report.get("succeeded") != 1 or not test or test.get("state") != "Success":
    raise RuntimeError("Focused PR-009 runtime/save automation did not pass 1/1")

source_files = []
for relative in (
    "Source/LineBossCarFactory/LBPR009Station.h",
    "Source/LineBossCarFactory/LBPR009Station.cpp",
    "Source/LineBossCarFactory/LBPR009StationTests.cpp",
    "Source/LineBossCarFactory/LBPressShopSaveGame.h",
):
    path = ROOT / relative
    data = path.read_bytes()
    source_files.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest().upper()})

payload = {
    "$schema": "line-boss/audit/press-shop-pr009-native-runtime-source-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "NATIVE_PR009_REMOTE_AUTHORITY_PROCESS_FAULT_ISOLATION_TRACEABILITY_AND_SAFE_SAVE_RESTORE_AUTOMATION_PASS__MAP_BINDING_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
    "automation": {
        "path": str(REPORT.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(report_data).hexdigest().upper(),
        "test": test["fullTestPath"], "state": test["state"], "warnings": test["warnings"], "errors": test["errors"],
    },
    "save_format_version": 8,
    "covered": [
        "trusted Moorcross control-room command authority",
        "receiving, centring, stacking, separator-placement and carrier-release sequence",
        "blank/carrier traceability counters and stack genealogy state",
        "machine interlocks and latched guard fault acknowledgement/reset",
        "automated isolation, zero-motion/pneumatic zero-energy evidence and release",
        "safe stationary restore of moving production with explicit restart required",
    ],
    "holds": [
        "No v083 map actor or staged mesh decomposition is bound yet.",
        "No live PR-008-to-PR-009 blank transfer, collision, navigation or screenshot evidence exists yet.",
    ],
    "sources": source_files,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
