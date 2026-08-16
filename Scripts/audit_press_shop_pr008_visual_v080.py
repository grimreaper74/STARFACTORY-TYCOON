"""Record the early-camera rejection of PR-008 installed-hall candidate v080."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v080_pr005_runtime/press_shop_v080_pr008_installed_process.png"
AUDIT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v080.json"
data = IMAGE.read_bytes()
if data[:8] != b"\x89PNG\r\n\x1a\n":
    raise RuntimeError("v080 early-gate receipt is not a PNG")
width, height = struct.unpack(">II", data[16:24])
if (width, height) != (1920, 1080):
    raise RuntimeError("v080 early-gate receipt must be 1920x1080")

payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v080/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "EARLY_PROCESS_CAMERA_FAIL__CROPPED_FLOATING_WALL_SERVICE_SPINE_AND_IDENTITY_COMPOSITION_REGRESSION__REJECTED__FULL_GATES_NOT_RUN__NOT_PROMOTED",
    "candidate_map": "/Game/LineBoss/Maps/LB_PressShop_PR008InstalledHallCandidate_v080",
    "parent_map": "/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079",
    "image": {
        "path": str(IMAGE.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data),
        "width": width,
        "height": height,
    },
    "useful_elements": [
        "Foundation anchor plates are readable and improve installation grounding.",
        "Reference-backed service categories and diegetic cell-header intent remain valid ideas.",
    ],
    "failures": [
        "The rear wall is poorly composed for the angled management camera and appears as a cropped floating slab in the upper-right frame.",
        "Service headers and drops read as dangling graphic lines instead of installed factory utilities.",
        "The cell identity is clipped and less useful than the retained v079 machine-mounted identity.",
        "The added backdrop does not increase believable hall depth or Pro-level machine density.",
    ],
    "decision": "Reject v080 at the early camera gate; do not spend the full runtime/gate cycle.",
    "next_candidate_requirements": [
        "Branch from retained v079, not rejected v080.",
        "Retain the useful anchor-plate idea only after checking exact machine-base correspondence.",
        "Place architecture using camera frusta and real hall/service clearances before adding geometry.",
        "Use properly supported trays, brackets and connected drops; no floating service lines.",
        "Run a process-camera check before any inherited technical gates.",
    ],
    "retained_v079_unchanged": True,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(payload["status"])
