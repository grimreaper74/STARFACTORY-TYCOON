"""Record the manually inspected PR-008 v079 fixed-camera visual decision."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v079_pr005_runtime"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v079.json"
FILES = [
    "press_shop_v079_pr008_calibrated_process.png",
    "press_shop_v079_pr008_calibrated_motion.png",
    "press_shop_v079_pr008_calibrated_hmi.png",
    "press_shop_v079_pr008_pr009_interface.png",
]


def png_receipt(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Not a PNG: {path}")
    width, height = struct.unpack(">II", data[16:24])
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data),
        "width": width,
        "height": height,
    }


images = [png_receipt(SCREENSHOTS / name) for name in FILES]
if any(image["width"] != 1920 or image["height"] != 1080 for image in images):
    raise RuntimeError("All v079 visual-gate images must be 1920x1080")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v079/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "CALIBRATED_LIGHTING_AND_WORKED_STEEL_READABILITY_PASS__HALL_CONTEXT_MECHANICAL_DENSITY_IDENTITY_DISTANCE_AND_PR009_HOLD__RETAINED__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079",
    "comparison_authority": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_01_PR008_ENGINEERING_REFERENCE_4K.png",
        "Saved/Audits/press_shop_pr008_visual_review_v077.json",
        "Saved/Audits/press_shop_pr008_visual_review_v078.json",
    ],
    "images": images,
    "passes": [
        "All four fresh cameras retain readable Cairnwell green, foundry charcoal, safety yellow and worked-steel distinctions without v078 clipping.",
        "The process strip and discharged blank now read as reflective worked metal rather than black belt-like surfaces.",
        "The close motion view has clearer depth and edge response while preserving v077's smooth coated finish.",
        "The local HMI and E-stop remain legible and secondary to control-room authority.",
        "The real hall column, open-mesh guarding, measured discharge datum and inherited runtime authority remain intact.",
    ],
    "holds": [
        "The hall remains sparse and the floor/column highlights are slightly hot compared with the Pro reference's controlled industrial ambience.",
        "Machine enclosure, cabinet and mechanical/service density remain materially below the authoritative hero reference.",
        "The main identity plate remains too small at the long management-camera distance despite being readable in the close motion view.",
        "Some hard floor shadow/noise patterns still look like validation lighting rather than a finished factory installation.",
        "PR-009 has no receiving actor, so the physical downstream handoff remains unproved.",
    ],
    "technical_evidence": [
        "Saved/Audits/press_shop_pr008_native_runtime_v079.json",
        "Saved/Audits/press_shop_pr004_crane_runtime_v079.json",
        "Saved/Audits/press_shop_pr004_support_crane_runtime_v079.json",
        "Saved/Audits/press_shop_pr004_pr005_handoff_runtime_v079.json",
        "Saved/Audits/press_shop_pr004_navigation_runtime_v079.json",
        "Saved/Audits/press_shop_pr004_collision_navigation_v079.json",
        "Saved/Audits/press_shop_pr008_pr009_interface_v079.json",
    ],
    "next_candidate_requirements": [
        "Branch from retained v079 and keep its calibrated intensity range and v077 smooth material hierarchy.",
        "Replace validation-looking floor illumination with believable installed hall lighting and surrounding architectural depth.",
        "Increase Pro-guided enclosure, service, fastening and cabinet density without breaking native motion or measured envelopes.",
        "Improve long-camera identity through physically plausible sign placement/scale rather than oversized floating text.",
        "Stage and measure the real PR-009 receiver before approving the downstream interface.",
    ],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "rejected_pr008_v076_v078_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
