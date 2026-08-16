"""Record the manually inspected v025 four-camera Pro comparison."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v025"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_visual_review_v025.json"
files = {
    "hero": "press_train_a_v025_hero.png",
    "overview": "press_train_a_v025_overview.png",
    "draw": "press_train_a_v025_draw_stage.png",
    "service": "press_train_a_v025_die_change_service.png",
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
    "$schema": "cairnwell/audit/press-train-a-visual-review-v025/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V025_RELEASE_DETAIL_AND_SUBTLE_LAYERED_MATERIAL_DIRECTION_RETAINED__PRO_SHEETS04_05_RELEASE_ART_HOLD__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V025_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"),
    "map": "/Game/LineBoss/Maps/LB_PressTrainAMaterialCalibrationCandidate_v025",
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png",
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_05_PRESS_TRAIN_A_4K.png",
    ],
    "fresh_exact_map_evidence": evidence,
    "manual_original_resolution_inspection": {
        "passes": [
            "seven-stage Train A silhouette, stage order and Cairnwell Automotive / Moorcross Works identity remain readable",
            "transform-compatible six-wheel cart source, separate tooling loads and enhanced docks are present across S02-S06",
            "supported utility, frame seam/fastener and distinct running/standby/maintenance modules are integrated as reusable geometry",
            "v025 fine low-contrast material variation corrects the rejected coarse marble/smoke appearance in v024",
            "die-change camera proves five cart/tooling positions without temporary floating labels",
        ],
        "release_holds": [
            "operator hero and overview remain too dark for release-quality control-room CCTV readability",
            "broad crown and enclosure panels remain too plain; crown drives, access platforms, service doors, vents and fabricated depth are below the Pro hero target",
            "current service camera does not clearly prove wheel bogies, tow points, docking cones, clamps, cable chain or dock interlocks",
            "seams, fasteners and supported utility drops do not yet read strongly enough at management-camera distance",
            "S01/S07 endpoint machinery, shared hall/floor context, calibrated decals and restored-versus-mothballed condition treatment remain incomplete",
            "HMI/state binding, animation, audio, material flow, faults/save, collision, navigation and crane-clearance gates have not been run for this visual candidate",
        ],
        "history": {
            "v023": "release geometry and identity integrated; technical pass, visual hold for darkness and label clutter",
            "v024": "first layered-material calibration rejected because large high-contrast noise read as marble/smoke",
            "v025": "subtle layered-material and clean-label direction retained; release art still held",
        },
    },
    "decision": "Retain v025 only as the current unpromoted release-detail/material direction. Author a second reusable exterior-detail pass for crowns, access/platform/door/vent hierarchy and a three-quarter die-change evidence camera before runtime gates.",
    "world_placement": "TBC_NOT_INVENTED", "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise SystemExit(1)
