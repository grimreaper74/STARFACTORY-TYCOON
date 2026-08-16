"""Record the manually inspected PR-008 v077 fixed-camera visual decision."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v077_pr005_runtime"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v077.json"
FILES = [
    "press_shop_v077_pr008_smooth_process.png",
    "press_shop_v077_pr008_smooth_motion.png",
    "press_shop_v077_pr008_smooth_hmi.png",
    "press_shop_v077_pr008_pr009_interface.png",
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
    raise RuntimeError("All v077 promotion-gate images must be 1920x1080")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v077/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SMOOTH_MATERIAL_IDENTITY_AND_CAMERA_DIRECTION_PASS__REFLECTION_ENVIRONMENT_MECHANICAL_DENSITY_AND_PR009_HANDOFF_HOLD__RETAINED__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077",
    "comparison_authority": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_01_PR008_ENGINEERING_REFERENCE_4K.png",
        "Saved/Audits/press_shop_pr008_visual_review_v075.json",
        "Saved/Audits/press_shop_pr008_visual_review_v076.json",
    ],
    "images": images,
    "passes": [
        "All four fresh fixed cameras show the intended PR-008 process, motion, local HMI and downstream interface subjects.",
        "Smooth Cairnwell green, foundry charcoal and safety-yellow finishes remove v076's coarse procedural grain and restore a more credible coated-machine hierarchy.",
        "The mounted Cairnwell Automotive, Moorcross Works and PR-008 identity is legible in the motion inspection view without using Line Boss in-world branding.",
        "The local HMI remains readable at inspection distance and appropriately secondary to control-room authority.",
        "Approved open-mesh guarding, E-stops, genuine hall structure and the measured PR-008 discharge datum remain present.",
    ],
    "holds": [
        "The discharged blank reads nearly black at some angles because the local reflection and lighting environment is too sparse.",
        "Machine enclosure, cabinet-bank form and mechanical density remain materially simpler than the authoritative Pro hero reference.",
        "The surrounding hall is sparse and flat, reducing depth and camera-view production credibility.",
        "The main identity remains small at the long management-camera distance even though it is legible in the close inspection view.",
        "PR-009 has no receiving actor, so the physical PR-008 to PR-009 handoff remains unproved.",
    ],
    "next_candidate_requirements": [
        "Branch from retained v077 and preserve its smooth material hierarchy; do not reintroduce visible procedural grain.",
        "Improve local reflection capture, industrial lighting and surrounding hall context so worked steel and blanks remain readable from every fixed camera.",
        "Add physically plausible enclosure, cabinet and mechanism depth guided by the Pro reference while preserving runtime motion and measured datums.",
        "Optimize identity for control-room cameras while retaining a believable mounted service plate for drone inspection.",
        "Stage and validate the real PR-009 receiver before claiming a physical downstream handoff.",
    ],
    "control_room_viewing_policy": {
        "primary": "CCTV management-view silhouette, motion, state and identity legibility",
        "secondary": "drone inspection geometry, service access, safety and fault evidence",
        "local_hmi": "service/status panel only; control-room authority remains primary",
        "removed_requirement": "pedestrian/player walk-up interaction and navigation",
        "retained_requirements": [
            "machine and material collision",
            "robot service access",
            "crane clearances",
            "safety exclusions",
            "maintenance access",
            "close inspection quality",
        ],
    },
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "rejected_pr008_v076_not_used_as_parent": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
