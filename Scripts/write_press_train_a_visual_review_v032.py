"""Record the manually inspected v032 five-camera Pro comparison."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v032"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_visual_review_v032.json"
files = {
    "hero": "press_train_a_v032_hero.png",
    "overview": "press_train_a_v032_overview.png",
    "draw": "press_train_a_v032_draw_stage.png",
    "service": "press_train_a_v032_die_change_service.png",
    "cart": "press_train_a_v032_die_cart_detail.png",
}
evidence = {}
failures = []
for view, filename in files.items():
    path = CAPTURE_DIR / filename
    if not path.is_file():
        failures.append(f"missing {view}: {path}")
        continue
    payload = path.read_bytes()
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or len(payload) < 24:
        failures.append(f"invalid PNG: {path}")
        continue
    width, height = struct.unpack(">II", payload[16:24])
    if (width, height) != (1920, 1080):
        failures.append(f"unexpected dimensions {view}: {width}x{height}")
    evidence[view] = {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": len(payload), "width": width, "height": height,
        "sha256": hashlib.sha256(payload).hexdigest().upper(),
    }

report = {
    "$schema": "cairnwell/audit/press-train-a-visual-review-v032/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V032_CART_MECHANICAL_CORRECTION_RETAINED__PRO_SHEETS04_05_RELEASE_ART_HOLD__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V032_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"),
    "map": "/Game/LineBoss/Maps/LB_PressTrainACartPlateClearanceCandidate_v032",
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png",
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_05_PRESS_TRAIN_A_4K.png",
    ],
    "fresh_exact_map_evidence": evidence,
    "manual_original_resolution_inspection": {
        "passes": [
            "the five S02-S06 die carts now read as mobile equipment because their six-wheel envelope clears the service deck",
            "paired tooling loads remain transform-aligned with every corrected cart",
            "white physical identity plates carry restrained dark Cairnwell text without Line Boss working-title branding",
            "cart close and service views now prove the repeated changeover route and cart staging direction",
            "seven-stage order, overall 56 m flow axis and Cairnwell Automotive / Moorcross Works identity remain intact",
        ],
        "release_holds": [
            "hero, overview and service views remain substantially too dark for release-quality control-room CCTV play",
            "open skeletal frames and large blank crown panels read as a blockout rather than the Pro reference's heavy enclosed press architecture",
            "floating stage-name text crosses machinery and is not acceptable final diegetic identification",
            "S01 destack/load and S07 unload/inspect endpoints remain visually underdeveloped",
            "stage shells are excessively repetitive; exterior access doors, enclosed guarding, utility cabinets, roof services and fabricated mass are insufficient",
            "restored material hierarchy remains flat and overly clean; calibrated seams, fasteners, oils, wear, service labels and condition variants are incomplete",
            "validation hall, floor, ceiling and lighting are not final shared Press Shop context",
            "native HMI/state binding, process motion, sheet flow, audio, faults/save, collision, navigation and crane-clearance gates have not started for this visual candidate",
        ],
        "history": {
            "v028": "release evidence improved but carts read as fixed layered pedestals",
            "v029": "300 mm physically plausible cart/tooling lift exposed the wheel envelope; first plaque typography failed alignment",
            "v030": "plate alignment and lower/wider camera passed, but text was too small",
            "v031": "larger text passed identity direction but intersected the plate face",
            "v032": "face clearance and complete five-view evidence retain the cart correction; whole-train release art still fails",
        },
    },
    "decision": (
        "Retain v032 only as the current unpromoted cart-mechanical and exterior-detail parent. "
        "Author a reusable dimensioned enclosed exterior-shell source pass from Pro Sheets 04/05, replacing the skeletal/blockout reading while preserving verified transforms, carts, tooling, service interfaces and TBC world authority."
    ),
    "pro_redesign_required": False,
    "world_placement": "TBC_NOT_INVENTED", "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
