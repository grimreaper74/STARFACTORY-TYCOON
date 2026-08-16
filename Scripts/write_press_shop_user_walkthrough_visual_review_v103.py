"""Record the user's free-camera v103 walkthrough as a whole-shop visual failure.

These images are supplementary exploratory evidence, not fixed-camera release
evidence and not a replacement for the mandatory Pro-reference camera suite.
"""

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCREENSHOTS = Path(r"C:\Users\greg_\Pictures\Screenshots")
OUT = ROOT / "Saved/Audits/PressShopIntegration/user_walkthrough_visual_review_v103_2026-08-05.json"

evidence = []
for number in range(11149, 11156):
    path = SCREENSHOTS / f"Screenshot ({number}).png"
    header = path.read_bytes()[:24]
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    evidence.append({
        "file": str(path),
        "bytes": path.stat().st_size,
        "width": width,
        "height": height,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper(),
    })

payload = {
    "$schema": "cairnwell/audit/press-shop-user-walkthrough-visual-review-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "WHOLE_SHOP_VISUAL_GATE_FAIL__ACCEPTED_PR009_PR010_TECHNICAL_BASELINE_PRESERVED__ISOLATED_ENVIRONMENT_SUCCESSOR_REQUIRED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103",
    "evidence_type": "user free-camera PIE walkthrough; supplementary defect discovery only",
    "evidence": evidence,
    "confirmed_release_blockers": [
        "real-time skylight configuration emits an on-screen missing-sky-component warning",
        "multiple directional lights compete for the forward-shading role",
        "large floor zones read as timber/plank or strongly repeated coloured tiles rather than sealed industrial concrete and installed machine foundations",
        "lighting alternates between clipped white pools and unresolved black voids",
        "large hall regions remain visibly sparse and structurally unfinished",
        "repeated columns, barriers, walkways and service routes need final spacing, termination and installed-context review",
        "coil receipt/store presentation remains repetitive and under-dressed at whole-shop distance",
        "machinery and service density is inconsistent between the accepted PR009/PR010 end and the earlier front-end areas",
        "crane rail, trolley, hook and operating-state presentation needs a dedicated integrated visual gate",
        "the accepted station-level v103 evidence did not prove release-quality whole-shop composition",
    ],
    "editor_only_obstruction": "Unreal source-content change prompt was visible; controlled source files must not be auto-reimported into the accepted map",
    "required_next_action": "read-only exact-actor audit, then an isolated v103-derived environment correction candidate; never overwrite accepted v103",
    "fixed_camera_pro_gate_satisfied": False,
    "accepted_map_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "evidence_count": len(evidence),
    "blocker_count": len(payload["confirmed_release_blockers"]),
    "audit": str(OUT),
}, indent=2))
