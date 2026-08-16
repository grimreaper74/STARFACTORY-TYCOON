"""Record the manually inspected v035 five-camera Pro comparison."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v035"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_visual_review_v035.json"
files = {
    "hero": "press_train_a_v035_hero.png", "overview": "press_train_a_v035_overview.png",
    "draw": "press_train_a_v035_draw_stage.png",
    "service": "press_train_a_v035_die_change_service.png",
    "cart": "press_train_a_v035_die_cart_detail.png",
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
    "$schema": "cairnwell/audit/press-train-a-visual-review-v035/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V035_ENCLOSED_CCTV_FIRST_ARCHITECTURE_AND_CART_DIRECTION_RETAINED__PRO_SHEETS04_05_RELEASE_ART_HOLD__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V035_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"),
    "map": "/Game/LineBoss/Maps/LB_PressTrainAFacadeMaterialCandidate_v035",
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png",
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_05_PRESS_TRAIN_A_4K.png",
    ],
    "fresh_exact_map_evidence": evidence,
    "manual_original_resolution_inspection": {
        "passes": [
            "seven physical facade modules convert the operator side from skeletal frames into intentionally enclosed CCTV-first machines",
            "draw press, shared middle presses, destack/load and unload/inspect endpoints now have distinct exterior mass and silhouettes",
            "fabricated service doors, guarded process apertures, inspection glazing, lower guards, roof services and HMI plates read in hero and draw views",
            "validation-era floating stage names are absent; all stage identity actors are flush to authored physical plates",
            "broad facade fills improve management-camera readability without erasing process-aperture depth",
            "facade-only dark grey/green layering restores more Cairnwell hierarchy while retaining blue Train A and yellow safety cues",
            "v032 six-wheel cart ride-height, paired tooling and die-change route remain intact and readable",
        ],
        "release_holds": [
            "inherited press-frame/crown materials remain too pale under the restored lighting and reduce heavy-machinery mass",
            "middle press facades are still overly repeated; stage-specific trim, pierce, lubrication, scrap and final-restrike exterior cues need stronger differentiation",
            "flush stage text does not yet read reliably at fixed-camera distance and needs final decal/HMI calibration",
            "S01/S07 retain a blockout-level interior process story despite improved exterior silhouettes",
            "service-side view remains dark and largely exposes inherited blank panels rather than finished die-change service architecture",
            "carts still need final tow-point/dock-interface/cable-chain evidence and fully readable identity decals",
            "validation hall, floor, ceiling and lighting are not the final common Press Shop environment",
            "native HMI/state binding, visible process motion, sheet transfer, audio, faults/save, collision, navigation and crane-clearance gates remain deferred until the visual gate closes",
        ],
        "history": {
            "v032": "cart-mechanical correction retained; whole train remained skeletal and too dark",
            "v033": "first enclosed source integration removed floating labels; hero exposed clipped crown highlights and dark lower facades",
            "v034": "five broad operator-side fills and safer exposure made enclosed architecture readable",
            "v035": "facade-only material calibration retained; inherited frame response and release details remain open",
        },
    },
    "decision": (
        "Retain v035 as the current unpromoted enclosed Train A parent. No new Pro design is required. "
        "Next calibrate inherited stage-frame/crown materials, strengthen S03-S06 process-specific exterior cues, finish physical IDs/HMI and service-side die-change evidence, then repeat all five visual gates before runtime work."
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
