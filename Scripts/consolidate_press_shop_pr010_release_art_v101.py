"""Consolidate exact-map PR-010 v101 technical and Pro-reference visual evidence."""

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved/Audits/PR010_ReleaseArt_v101"
SHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v101_pr010_release_art"
FILES = {
    "source": AUDIT / "pr010_release_art_source_audit_v101.json",
    "build": AUDIT / "pr010_release_art_build_v101.json",
    "hmi_correction": AUDIT / "hmi_legibility_correction_v101.json",
    "static": AUDIT / "pr010_release_art_static_gate_v101.json",
    "runtime_collision_save_authority": AUDIT / "runtime_collision_pie_audit_v101.json",
    "navigation": AUDIT / "navigation_pie_audit_v101.json",
    "automation_regression": AUDIT / "automation_regression_v101.json",
}
evidence, failures = {}, []
for key, path in FILES.items():
    if not path.is_file(): failures.append(f"missing evidence: {path}"); continue
    row = json.loads(path.read_text(encoding="utf-8"))
    evidence[key] = {"path": str(path.relative_to(ROOT)), "status": row.get("status")}
    if not str(row.get("status", "")).startswith("PASS"): failures.append(f"{key} did not pass")

build_log = ROOT / "Saved/Logs/PR010_ReleaseArt_v101/native_build.log"
build_text = ""
if build_log.is_file():
    raw = build_log.read_bytes()
    for encoding in ("utf-8-sig", "utf-16", "utf-16-le"):
        try:
            build_text = raw.decode(encoding)
            if "Result:" in build_text: break
        except UnicodeError:
            continue
native_build_pass = "Result: Succeeded" in build_text
if not native_build_pass: failures.append("native UE 5.8 build proof missing/failed")
images = {}
for name in ("overview", "infeed", "handoff", "service_hmi"):
    disk_name = "service_hmi" if name == "service_hmi" else name
    path = SHOTS / f"press_shop_v101_pr010_{disk_name}.png"
    images[name] = {"path": str(path.relative_to(ROOT)), "exists": path.is_file(), "bytes": path.stat().st_size if path.is_file() else 0}
    if not path.is_file() or path.stat().st_size < 1024: failures.append(f"missing/empty fixed-camera image: {name}")

accepted = [
    "Eight carrier positions read as engineered roller pallets rather than solid yellow blocks.",
    "Nine stack presentations read as layered steel sheets with straps and identification plates.",
    "Open louver fascia and open-grid end guards preserve the four-lane material-flow sightline.",
    "Cairnwell Automotive, Moorcross Works, PR-010, remote state and capacity are legible on the authoritative HMI point.",
    "Correct 2.4 m moving cradle/fixed 13 m M01 envelope and four-lane arrangement remain visually intact.",
]
holds = [
    "The Pro Sheet 03 hero's dense upper service deck still needs rooftop drives, cable/hose routing, access handrails and service detail.",
    "The four lane ID pylons remain plain blockout columns and the white stack ID plates have no unique traceability text.",
    "Shared hall/floor presentation remains too clean and top-sheet highlights are still hot compared with the settled industrial hero reference.",
    "The local HMI rows are legible presentation text but are not yet bound to changing native PR-010 runtime values.",
]
visual = {"$schema": "cairnwell/audit/pr010-release-art-visual-v101/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V101_CARRIER_STACK_OPEN_FASCIA_HMI_DIRECTION_RETAINED__PRO_SHEET_03_SERVICE_DETAIL_AND_LIVE_HMI_HOLD__NOT_PROMOTED",
    "authority": "SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/visuals/SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png",
    "images": images, "accepted_visual_direction": accepted, "release_holds": holds,
    "next_candidate": "Isolated v102: authoritative-envelope service deck/rails/routing, detailed lane pylons and unique stack IDs, live HMI binding and final material/exposure pass.",
    "new_pro_design_required": False, "promotion_authorized": False}
(AUDIT / "pr010_visual_review_v101.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")

report = {"$schema": "cairnwell/audit/pr010-release-art-verification-v101/v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR010_V101_EXACT_MAP_COMPILE_AUTOMATION_STATIC_RUNTIME_SAVE_AUTHORITY_COLLISION_NAVIGATION__VISUAL_RELEASE_HOLD__NOT_PROMOTED" if not failures else "FAIL__PR010_V101_EVIDENCE_INCOMPLETE__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101", "parent": "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100",
    "native_build_pass": native_build_pass, "technical_evidence": evidence, "fixed_camera_images": images,
    "visual_status": visual["status"], "accepted_visual_direction": accepted, "visual_release_holds": holds,
    "new_pro_design_required": False, "failures": failures, "promotion_authorized": False}
(AUDIT / "PR010_V101_RELEASE_VERIFICATION.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2)); raise SystemExit(1 if failures else 0)
