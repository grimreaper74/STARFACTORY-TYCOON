"""Record the fixed-camera visual decision for PR-008 external anchor tabs v082."""
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v082_pr005_runtime"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v082.json"
IMAGE_NAMES = (
    "press_shop_v082_pr008_anchor_tabs_process.png",
    "press_shop_v082_pr008_anchor_tabs_motion.png",
    "press_shop_v082_pr008_anchor_tabs_hmi.png",
    "press_shop_v082_pr008_pr009_interface.png",
)

images = []
for name in IMAGE_NAMES:
    path = IMAGE_ROOT / name
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Invalid PNG receipt: {path}")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1920, 1080):
        raise RuntimeError(f"Unexpected fixed-camera dimensions for {path}: {width}x{height}")
    images.append({
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data),
        "width": width,
        "height": height,
    })

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v082/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "MEASURED_EXTERNAL_ANCHOR_TAB_INSTALLATION_GROUNDING_PASS__HALL_CONTEXT_MECHANICAL_DENSITY_IDENTITY_DISTANCE_AND_PR009_HOLD__RETAINED__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008ExternalAnchorTabsCandidate_v082",
    "parent_map": "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079",
    "images": images,
    "inspection": {
        "passes": [
            "The external plates use measured v079 base footprints rather than arbitrary decoration.",
            "Tabs visibly overlap the selected machine-base corners and modestly improve floor installation grounding.",
            "The retained v079 lighting, worked-steel readability, material hierarchy, HMI and process composition survive.",
            "Process, motion, HMI and PR008-to-PR009-interface views are fresh 1920x1080 Unreal captures.",
            "All inherited native runtime, crane, handoff, collision and navigation gates pass.",
        ],
        "holds": [
            "The plates and studs remain generic candidate detail and should become authored base geometry before final release.",
            "They are intentionally NoCollision and navigation-neutral; the final physical collision strategy remains open.",
            "The change does not close the Pro-reference hall-context or mechanical/service-density gap.",
            "Cairnwell/Moorcross identity remains weak at management-camera distance.",
            "No real PR-009 receiver is present, so the downstream physical and live-transfer handoff remains unproved.",
        ],
    },
    "decision": "Retain v082 as a modest installation-grounding improvement over v079; do not promote it as release quality.",
    "next": "Integrate the real PR-009 receiver when staged, then author base-connected installation detail and repeat interface/runtime/fixed-camera gates.",
    "retained_v079_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
