"""Record the manually inspected fixed-camera visual verdict for PR-008 v074."""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v074_pr005_runtime"
OUT = ROOT / "Saved/Audits/press_shop_pr008_visual_review_v074.json"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074"

CAPTURES = {
    "native_process": "press_shop_v074_pr008_native_process.png",
    "native_motion": "press_shop_v074_pr008_native_motion.png",
    "native_hmi": "press_shop_v074_pr008_native_hmi.png",
    "pr008_pr009_interface": "press_shop_v074_pr008_pr009_interface.png",
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
    "$schema": "line-boss/audit/press-shop-pr008-visual-review-v074/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "candidate": "PR008_v074",
    "map": MAP,
    "reference_authority": "CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0 plus accepted Press Shop Pro references",
    "review_result": "TECHNICAL_RUNTIME_PASS__VISUAL_RELEASE_GATE_FAIL__NOT_PROMOTED",
    "captures": {name: inspect_png(CAPTURE_DIR / filename) for name, filename in CAPTURES.items()},
    "passes": [
        "PR-008 process sequence reads coherently from feed and loop control through pre-punch, shear and discharge.",
        "Detailed yellow and Cairnwell-green approved open-mesh guarding is present around authored machinery.",
        "The live HMI identifies Cairnwell Automotive, Moorcross Works and PR-008 without Line Boss in-world branding.",
        "Fixed-camera evidence covers the process, moving modules, HMI and PR-008 to PR-009 handoff direction.",
    ],
    "release_blockers": [
        "A giant white transparent planning cage remains visible around PR-008 and reads as unfinished placeholder geometry.",
        "Tall grey inherited structural slabs or columns obstruct the process and interface views.",
        "Materials are too flat and clean compared with the Pro machinery reference and lack release-quality layering.",
        "The floor lacks convincing routes, service zones, foundation interfaces and restrained operational wear.",
        "The HMI is crowded into inherited machine and column clutter, with obsolete v073 pedestal identity text overlapping behind it.",
        "The HMI screen hierarchy and remote alarm/action affordances remain too small and visually basic.",
        "The PR-008 to PR-009 interface camera is materially obstructed by a grey slab and the planning cage.",
        "Lighting is harsh and flat, with an over-bright floor and weak industrial depth.",
    ],
    "required_next_candidate": "Duplicate v074 to isolated v075; remove only confirmed PR-008 placeholders, fix HMI clearance and camera sightlines, then improve layered materials, floor zoning and lighting before fresh capture.",
    "accepted_pr004_v006_preserved": True,
    "rejected_pr004_v007_v010_remain_rejected": True,
    "promotion_authorized": False,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUT}")
