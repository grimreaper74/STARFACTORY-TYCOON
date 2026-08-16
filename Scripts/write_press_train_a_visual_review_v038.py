"""Record the manually inspected v038 five-camera Pro comparison."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v038"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_visual_review_v038.json"
files = {
    "hero": "press_train_a_v038_hero.png", "overview": "press_train_a_v038_overview.png",
    "draw": "press_train_a_v038_draw_stage.png",
    "service": "press_train_a_v038_die_change_service.png",
    "cart": "press_train_a_v038_die_cart_detail.png",
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
    "$schema": "cairnwell/audit/press-train-a-visual-review-v038/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V038_DISTINCT_ENCLOSED_PROCESS_CUE_DIRECTION_RETAINED__PRO_SHEETS04_05_RELEASE_ART_HOLD__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V038_VISUAL_EVIDENCE_INCOMPLETE__NOT_PROMOTED"),
    "map": "/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038",
    "references": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png",
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_05_PRESS_TRAIN_A_4K.png",
    ],
    "fresh_exact_map_evidence": evidence,
    "manual_original_resolution_inspection": {
        "passes": [
            "the overview now gives S03-S06 distinct, readable operator-side process silhouettes without exposing exhaustive internal mechanisms",
            "S03 reads as paired forming-pressure accumulators and servo manifold rather than another repeated cabinet",
            "S04 reads as a trim station through its guarded amber scrap chute and evacuation mouth",
            "S05 reads as a pierce station through four slug-collection drawers and amber witness points",
            "S06 reads as final restrike/quality confirmation through four load-cell towers and a cyan-green signal bank",
            "the cue modules remain compact within the enclosed facade language and preserve Cairnwell green, Train A blue and safety-yellow hierarchy",
            "hero, overview and draw-stage views show the improvement; service and cart evidence remain intact and unobstructed",
            "no Line Boss working-title branding appears in-world",
        ],
        "release_holds": [
            "the shared press crowns and broad inherited frame surfaces remain too pale and clean compared with the Pro heavy-industrial references",
            "physical stage identity and HMI content remain too small to read reliably from the fixed overview and hero cameras",
            "S01 destack/load and S07 unload/inspect still need stronger believable material-transfer interiors and visible limited motion",
            "the opposite die-change side remains visually unfinished and much darker than the operator-side presentation",
            "die carts need final tow-point, dock clamp, connector and cable-chain proof in a better service evidence composition",
            "the validation hall lacks final common Press Shop floor markings, structural context, atmospheric balance and condition variation",
            "native HMI/state binding, limited press animation, sheet transfer, audio, faults/save, collision, navigation and crane-clearance gates remain open",
        ],
        "history": {
            "v035": "retained enclosed CCTV-first architecture but repeated S03-S06 facades",
            "v036": "exact inherited material reassignment passed technically but produced no decisive management-camera improvement",
            "v037": "first cue integration was rejected because local facing exposed blank structural backplates",
            "v038": "corrected cue facing exposes process hardware to the operator/CCTV side and is retained",
        },
    },
    "decision": (
        "Retain v038 as the current unpromoted Train A visual parent. Do not promote v036-v038. "
        "Next improve crown/frame mass, fixed-camera physical identity/HMI legibility, S01/S07 material-flow presentation and die-change-side mechanical evidence before runtime gates."
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
