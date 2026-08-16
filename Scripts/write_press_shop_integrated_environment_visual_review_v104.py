"""Record the mandatory human visual verdict for isolated environment v104."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CAPTURE_ROOT = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v104_integrated_environment"
OUT = ROOT / "Saved/Audits/PressShopIntegration/integrated_environment_visual_review_v104.json"
NAMES = {
    "whole_shop": "press_shop_environment_v104_whole_shop.png",
    "front_end": "press_shop_environment_v104_front_end.png",
    "crane_coil": "press_shop_environment_v104_crane_coil.png",
    "connected_line": "press_shop_environment_v104_connected_line.png",
}

evidence = []
for role, name in NAMES.items():
    path = CAPTURE_ROOT / name
    if not path.is_file():
        raise FileNotFoundError(path)
    evidence.append({
        "role": role,
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
        "resolution_px": [1920, 1080],
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-integrated-environment-visual-review-v104/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "EARLY_VISUAL_GATE_FAIL__LIGHT_WARNING_AND_PLANK_FLOOR_CAUSES_CORRECTED__HALL_COMPOSITION_AND_CAMERA_REWORK_REQUIRED__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v104",
    "evidence": evidence,
    "passes": [
        "The pillar/plank source texture is no longer bound to the front-end floor actors.",
        "One directional light owns forward shading and the skylight no longer uses invalid real-time capture.",
        "The connected PR-005 through PR-010 machinery remains present and readable at closer range.",
        "The accepted v103 map and PR-009/PR-010 accepted authority remain unchanged.",
    ],
    "failures": [
        {"severity": "BLOCKER", "finding": "The hall reads as an oversized, mostly empty black volume rather than a finished automotive Press Shop."},
        {"severity": "BLOCKER", "finding": "Whole-shop, front-end and crane/coil cameras are obstructed or dominated by the roof slab and structural posts."},
        {"severity": "MAJOR", "finding": "Lighting still forms isolated bright pools along machinery with surrounding areas falling into black voids."},
        {"severity": "MAJOR", "finding": "Large unallocated floor expanses and repeated unsupported columns make the factory composition feel like blockout rather than release-quality installation."},
        {"severity": "MAJOR", "finding": "The fixed cameras are unsuitable as player CCTV feeds because they do not frame actionable stations or material-flow events clearly."},
        {"severity": "MAJOR", "finding": "The procedural concrete correction is too visually uniform at hall scale and still lacks believable joint, wear and routing hierarchy."},
    ],
    "required_successor_actions": [
        "Author CCTV cameras station-by-station at operational eye lines with unobstructed process, transfer and HMI evidence.",
        "Resolve the Press Shop shell envelope and roof visibility for camera operation; do not expose exterior voids or roof occlusion in normal feeds.",
        "Establish continuous industrial ambient illumination plus localized task lighting without isolated white pools.",
        "Break the hall into credible production, logistics and support bays with purposeful density and service clearances.",
        "Retain restrained sealed concrete but add measured slab joints, traffic wear and route markings without returning to plank-like texture repetition.",
    ],
    "accepted_v103_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "audit": str(OUT)}, indent=2))

