"""Consolidate exact-map PR-010 v100 technical evidence and honest visual decision."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved/Audits/PR010_ReleaseArt_v100"
SHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v100_pr010_release_art"
FILES = {
    "source": AUDIT / "pr010_release_art_source_audit_v100.json",
    "build": AUDIT / "pr010_release_art_build_v100.json",
    "static": AUDIT / "pr010_release_art_static_gate_v100.json",
    "runtime_collision_save_authority": AUDIT / "runtime_collision_pie_audit_v100.json",
    "navigation": AUDIT / "navigation_pie_audit_v100.json",
}

evidence, failures = {}, []
for key, path in FILES.items():
    if not path.is_file():
        failures.append(f"missing evidence: {path}")
        continue
    row = json.loads(path.read_text(encoding="utf-8"))
    evidence[key] = {"path": str(path.relative_to(ROOT)), "status": row.get("status")}
    if not str(row.get("status", "")).startswith("PASS"):
        failures.append(f"{key} did not pass")

images = {}
for name, file_name in {
    "overview": "press_shop_v100_pr010_overview.png",
    "infeed": "press_shop_v100_pr010_infeed.png",
    "handoff": "press_shop_v100_pr010_handoff.png",
    "service_hmi": "press_shop_v100_pr010_service_hmi.png",
}.items():
    path = SHOTS / file_name
    images[name] = {"path": str(path.relative_to(ROOT)), "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0}
    if not path.is_file() or path.stat().st_size < 1024:
        failures.append(f"missing/empty fixed-camera image: {name}")

visual_holds = [
    "Retained stack/carrier blocks remain too cubic and featureless for the Pro Sheet 03 release-art target.",
    "White and safety-yellow highlights clip under the current PR-010 task lighting while upper hall structure falls excessively dark.",
    "The fixed ServiceHMI view is occluded by a structural post; HMI identity and screen information are not legible.",
    "Large retained fascia/column primitives visually dominate and obscure the four-lane material-flow read.",
]

visual = {
    "$schema": "cairnwell/audit/pr010-release-art-visual-v100/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V100_OPEN_GUARD_CRADLE_LANE_HARDWARE_DIRECTION_RETAINED__PRO_SHEET_03_RELEASE_ART_HOLD__NOT_PROMOTED",
    "authority": "Cairnwell Press Shop remaining machinery pack, Sheet 03",
    "images": images,
    "accepted_visual_direction": [
        "Dimensioned 2.4 m moving transfer cradle inside the fixed 13 m M01 assembly envelope.",
        "Eight approved open-grid guard panels with retained invisible v099 collision proxies.",
        "Detailed four-lane safety scanners and recovery tow points.",
        "Remote coordination HMI moved to the authoritative local (6450, -3250) mm point.",
    ],
    "release_holds": visual_holds,
    "next_candidate": "Isolated v101: detailed carrier/stack modules, fascia simplification, exposure pass, unobstructed HMI evidence camera and legible Unreal-driven HMI/branding.",
    "promotion_authorized": False,
}
(AUDIT / "pr010_visual_review_v100.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")

report = {
    "$schema": "cairnwell/audit/pr010-release-art-verification-v100/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V100_EXACT_MAP_SOURCE_IMPORT_STATIC_RUNTIME_SAVE_AUTHORITY_COLLISION_NAVIGATION__VISUAL_RELEASE_HOLD__NOT_PROMOTED" if not failures else "FAIL__PR010_V100_EVIDENCE_INCOMPLETE__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100",
    "parent": "/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099",
    "technical_evidence": evidence, "fixed_camera_images": images,
    "visual_status": visual["status"], "visual_release_holds": visual_holds,
    "failures": failures, "promotion_authorized": False,
}
(AUDIT / "PR010_V100_RELEASE_VERIFICATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
raise SystemExit(1 if failures else 0)
