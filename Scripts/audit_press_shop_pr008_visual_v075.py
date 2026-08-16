"""Record the manually inspected fixed-camera visual verdict for PR-008 v075."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v075_pr005_runtime"
OUT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v075.json"

CAPTURES = {
    "clean_process": "press_shop_v075_pr008_clean_process.png",
    "clean_motion": "press_shop_v075_pr008_clean_motion.png",
    "clean_hmi": "press_shop_v075_pr008_clean_hmi.png",
    "pr008_pr009_interface": "press_shop_v075_pr008_pr009_interface.png",
}


def inspect_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"Not a PNG: {path}")
    width, height = struct.unpack(">II", data[16:24])
    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(data).hexdigest().upper(),
        "bytes": len(data),
        "width_px": width,
        "height_px": height,
    }


payload = {
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v075/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": "PR008_v075",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075",
    "reference_authority": "CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0 plus accepted Press Shop Pro references",
    "review_result": "ENGINEERING_CLEANUP_FLOOR_ZONING_AND_CAMERA_DIRECTION_PASS__MATERIAL_IDENTITY_ENVIRONMENT_AND_PR009_HANDOFF_HOLD__NOT_PROMOTED",
    "captures": {name: inspect_png(CAPTURE_DIR / filename) for name, filename in CAPTURES.items()},
    "passes": [
        "The white engineering cage and floating engineering labels are absent from all fresh views.",
        "The duplicated v073 HMI pedestal captions are suppressed and the live v074 screen has one readable hierarchy.",
        "A dimensioned dark machine pad, remote service aisle and continuous safety boundary give PR-008 a coherent floor footprint.",
        "The process and moving assemblies read clearly as one connected servo-blanking line.",
        "The authentic hall column remains present but the interface camera no longer lets it conceal the discharge mechanism.",
        "Approved open-mesh guarding, outward E-stops and Cairnwell/Moorcross colour hierarchy remain intact.",
    ],
    "release_blockers": [
        "Machine and cabinet finishes remain too uniform, clean and plastic-like compared with the layered Pro reference.",
        "The replacement process strip reads too dark and belt-like; it needs a dedicated bright worked-steel material and controlled reflections.",
        "Identity plates remain small or washed out and are not consistently legible at management-camera distance.",
        "The HMI is physically crowded between the electrical cabinets and adjacent structure; a release camera/clearance proof and stronger screen framing remain required.",
        "The local floor treatment is coherent but still lacks authored joints, anchors, foundation interfaces, service symbols and restrained operational wear.",
        "Hall lighting and background architecture remain sparse and flat, so the cell does not yet match the depth and realism of the Pro presentation.",
        "PR-009 is not authored in the map, so the final physical blank handoff and receiving buffer remain unproved.",
    ],
    "required_next_candidate": "Create isolated v076 with dedicated strip steel, layered machine/cabinet material response, legible identity and authored floor/foundation detail; retain the clear v075 cameras and then connect the real PR-009 receiver.",
    "technical_gates_passed": [
        "PR008 native runtime/motion/HMI/safety/isolation",
        "primary crane runtime",
        "support crane runtime",
        "traceable PR004-to-PR005 handoff",
        "collision and runtime navigation",
    ],
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_remain_rejected": True,
    "promotion_authorized": False,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUT}")
