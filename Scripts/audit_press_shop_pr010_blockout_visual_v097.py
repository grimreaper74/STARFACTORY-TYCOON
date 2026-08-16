"""Record the manually inspected PR-010 v097 early visual gate."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
AUDIT = ROOT / "Saved/Audits/PR010_Blockout"
CAPTURES = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v097_pr010_blockout"
OUT = AUDIT / "pr010_visual_review_v097.json"
source = json.loads((AUDIT / "pr010_dimensioned_source_v001.json").read_text(encoding="utf-8"))
build = json.loads((AUDIT / "pr010_unreal_blockout_build_v097.json").read_text(encoding="utf-8"))
static = json.loads((AUDIT / "pr010_static_gate_v097.json").read_text(encoding="utf-8"))

failures = []
for name, payload in (("source", source), ("build", build), ("static", static)):
    if not str(payload.get("status", "")).startswith("PASS") or payload.get("failures"):
        failures.append(f"{name} gate did not pass")
names = [
    "press_shop_v097_pr010_blockout_overview.png",
    "press_shop_v097_pr010_blockout_infeed.png",
    "press_shop_v097_pr010_blockout_handoff.png",
    "press_shop_v097_pr010_blockout_elevated.png",
]
captures = []
for name in names:
    path = CAPTURES / name
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    captures.append({"path": str(path.relative_to(ROOT)), "exists": exists, "bytes": size})
    if not exists or size < 100_000: failures.append(f"missing or undersized capture: {name}")

result = {
    "$schema": "cairnwell/audit/pr010-blockout-visual-v097/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V097_DIMENSION_LAYOUT_AND_ENCLOSURE_DIRECTION__RETAINED_BLOCKOUT__NOT_PROMOTED" if not failures else "FAIL__PR010_V097_VISUAL_BLOCKOUT__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097",
    "reference": "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png",
    "captures": captures,
    "manual_review": {
        "passes": [
            "Exactly four lanes and two identified stack positions per lane read from overview and elevated CCTV.",
            "PR-009-to-PR-010 material direction and the transverse infeed shuttle are legible without moving fixed datums.",
            "Four-bay upper fascia and inspection apertures communicate an enclosed high-energy shuttle without hiding the lane process.",
            "Cairnwell green, safety yellow, oiled blank steel, status indicators, HMI and lane pylons establish the approved exterior language.",
            "The handoff apron remains open and no Press Train A-D world positions were invented.",
        ],
        "holds_before_detail_or_promotion": [
            "Blockout geometry is intentionally coarse and has no release collision, navigation or native runtime authority.",
            "PR-010 identity is present at the service-side HMI but remains too faint for final CCTV readability.",
            "The shared hall lighting is uneven and leaves several stored stacks too dark.",
            "Approved open-mesh lane-end protection, scanners, tow points, service routing and detailed HMI remain to be authored.",
            "Cameras are suitable for blockout review only; final compositions must avoid all hall-column tangencies.",
        ],
        "decision": "RETAIN_V097_AS_DIMENSIONED_BLOCKOUT_PARENT_ONLY__DO_NOT_PROMOTE",
    },
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({"status": result["status"], "output": str(OUT), "failures": failures}, indent=2))
if failures: raise SystemExit(1)
