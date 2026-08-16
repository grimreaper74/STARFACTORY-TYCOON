"""Record the manually inspected PR-008 v078 fixed-camera visual rejection."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v078_pr005_runtime"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v078.json"
FILES = [
    "press_shop_v078_pr008_environment_process.png",
    "press_shop_v078_pr008_environment_motion.png",
    "press_shop_v078_pr008_environment_hmi.png",
    "press_shop_v078_pr008_pr009_interface.png",
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
    raise RuntimeError("All v078 visual-gate images must be 1920x1080")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v078/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "TECHNICAL_GATE_PASS__SEVERE_OVEREXPOSURE_COLOUR_IDENTITY_HMI_AND_MATERIAL_READABILITY_FAIL__REJECTED__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008ReflectionEnvironmentCandidate_v078",
    "comparison_authority": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_01_PR008_ENGINEERING_REFERENCE_4K.png",
        "Saved/Audits/press_shop_pr008_visual_review_v077.json",
    ],
    "images": images,
    "technical_passes": [
        "UE 5.8 editor build succeeds.",
        "Native PR-008 process, HMI, safety and isolation runtime gate passes.",
        "Primary and support crane runtime gates pass.",
        "Traceable PR-004-to-PR-005 handoff, navigation and combined collision/navigation gates pass.",
        "PR-008 discharge datum remains measured; PR-009 remains absent.",
    ],
    "visual_failures": [
        "The overhead and camera-fill photometric values grossly exceed the inherited exposure range and clip most machine and floor values to white.",
        "Cairnwell green, foundry charcoal, safety yellow and worked-steel material distinctions are largely destroyed.",
        "The identity plate and local HMI lose legibility instead of improving control-room and drone inspection readability.",
        "Fixture glare and the lit hall column dominate the process composition.",
        "The PR-009 interface view cannot reliably communicate blank, rollers, guarding or downstream datum under the clipped exposure.",
    ],
    "decision": "Reject v078. Retain v077 as the only parent for the next candidate.",
    "next_candidate_requirements": [
        "Branch from v077, not v078.",
        "Use an order-of-magnitude lower local-light intensity calibrated to the inherited exposure before adding multiple fixtures.",
        "Capture one process view first and reject immediately if green, charcoal, yellow, HMI text or blank detail clips.",
        "Keep reflection support local and restrained; preserve v077 smooth materials unchanged.",
        "Repeat every inherited gate and all four cameras before promotion discussion.",
    ],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "retained_pr008_v077_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
