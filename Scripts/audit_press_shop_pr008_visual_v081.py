"""Record the early visual insufficiency of PR-008 measured anchors v081."""
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v081_pr005_runtime/press_shop_v081_pr008_anchored_motion.png"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v081.json"
data = IMAGE.read_bytes()
width, height = struct.unpack(">II", data[16:24])
if data[:8] != b"\x89PNG\r\n\x1a\n" or (width, height) != (1920, 1080):
    raise RuntimeError("Invalid v081 early-camera PNG receipt")
payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v081/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "MEASURED_BASE_ANCHOR_DIRECTION_TECHNICALLY_PLAUSIBLE__FIXED_CAMERA_VISUAL_EVIDENCE_INSUFFICIENT__NOT_RETAINED__FULL_GATES_NOT_RUN__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008AnchoredInstallationCandidate_v081",
    "image": {
        "path": str(IMAGE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data), "width": width, "height": height,
    },
    "decision": "Do not retain v081; anchors are mostly obscured beneath measured base footprints.",
    "next": "Branch from v079 and place physically plausible anchor tabs immediately outside measured base corners, then repeat the early motion-camera gate.",
    "retained_v079_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
