"""Record the manually inspected PR-008 v076 fixed-camera visual decision."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v076_pr005_runtime"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v076.json"
FILES = [
    "press_shop_v076_pr008_layered_process.png",
    "press_shop_v076_pr008_layered_motion.png",
    "press_shop_v076_pr008_layered_hmi.png",
    "press_shop_v076_pr008_pr009_interface.png",
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
    raise RuntimeError("All v076 promotion-gate images must be 1920x1080")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v076/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "TECHNICAL_RUNTIME_AND_CAMERA_GATE_PASS__PROCEDURAL_MATERIAL_FREQUENCY_CONTRAST_IDENTITY_AND_NATIVE_STRIP_VISUAL_FAIL__REJECTED__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076",
    "comparison_authority": [
        "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0",
        "Saved/Audits/press_shop_pr008_visual_review_v075.json",
    ],
    "images": images,
    "passes": [
        "All four fixed cameras captured the intended PR-008 subjects without the removed engineering cage.",
        "Cairnwell green, foundry charcoal and safety-yellow hierarchy remains recognizable.",
        "The brighter steel direction improves some exposed strip surfaces.",
        "The compact local HMI remains readable and secondary to remote control-room authority.",
        "The genuine hall column and approved open-mesh guarding remain present.",
    ],
    "failures": [
        "Procedural colour and roughness breakup is far too high-frequency and high-contrast, producing a coarse sand-textured appearance across green, yellow, charcoal and light-grey surfaces.",
        "The finish reads less like coated industrial machinery than v075 and materially diverges from the Pro reference surfaces.",
        "The enlarged main identity plate is still not sufficiently legible at the clean process management camera.",
        "Not every native moving strip or representative blank surface receives the brighter worked-steel response; dark belt-like areas remain.",
        "The light-grey cabinet bank remains visually flat in form and overly bright despite the noisy surface treatment.",
        "PR-009 has no receiving actor, so the physical discharge handoff remains unproved.",
    ],
    "next_candidate_requirements": [
        "Branch from retained v075, not from rejected v076.",
        "Use broad, restrained material variation with much lower contrast and no visible grain at management-camera distance.",
        "Audit and override the native PR-008 station's moving strip and blank components as well as standalone detailed meshes.",
        "Increase operator-facing identity text size and contrast within a physically mounted plate.",
        "Repeat every inherited gate and inspect four fresh fixed-camera images before any promotion decision.",
    ],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
