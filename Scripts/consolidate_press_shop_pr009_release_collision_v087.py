"""Consolidate reproducible PR-009 v087 release-collision evidence without promoting it."""
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved/Audits/PR009_InMap_v087"
LOGS = ROOT / "Saved/Logs/PR009_InMap_v087"
SHOTS = ROOT / "Saved/ValidationScreenshots/PressShopIntegration/v087_pr009_release_collision"
AUTOMATION = ROOT / "Saved/Automation/PR009_InMap_v087"

def read(name):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def png_row(path):
    with path.open("rb") as stream:
        head = stream.read(24)
    width, height = struct.unpack(">II", head[16:24])
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
            "width": width, "height": height, "sha256": sha256(path)}

def table(rows):
    return {row["path"]: (row["bytes"], row["sha256"]) for row in rows}

def automation_row(name):
    path = AUTOMATION / name / "index.json"
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return {"path": path.relative_to(ROOT).as_posix(), "succeeded": payload["succeeded"],
            "failed": payload["failed"], "not_run": payload["notRun"],
            "tests": [{"path": row["fullTestPath"], "state": row["state"],
                       "warnings": row["warnings"], "errors": row["errors"]} for row in payload["tests"]],
            "pass": payload["succeeded"] == 1 and payload["failed"] == 0 and payload["notRun"] == 0}

build = read("release_collision_build.json")
static = read("release_collision_static_audit.json")
runtime = read("runtime_pie_audit.json")
physical = read("physical_collision_pie_audit.json")
sweeps = read("collision_contract_sweep_audit.json")
navigation = read("navigation_pie_audit.json")
source = read("source_collision_evidence.json")
parent_visual = read("visual_invariants_parent.json")
target_visual = read("visual_invariants_target.json")
parent_before = read("integrity_parent_before_build.json")
validation_before = read("integrity_validation_before.json")
validation_after = read("integrity_validation_after.json")
auto_runtime = automation_row("RuntimeAndSave")
auto_handoff = automation_row("TraceableBlankHandoff")

shot_rows = [png_row(path) for path in sorted(SHOTS.glob("*.png"))]
visual_equal = parent_visual["actor_count"] == target_visual["actor_count"] and parent_visual["actors"] == target_visual["actors"]
visual = {
    "$schema": "cairnwell/audit/pr009-v087-visual-review/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "parent_map": build["parent_map"], "target_map": build["target_map"],
    "fresh_fixed_camera_captures": shot_rows,
    "capture_count": len(shot_rows),
    "parent_target_normalized_actor_count": [parent_visual["actor_count"], target_visual["actor_count"]],
    "parent_target_visual_actor_payloads_exactly_equal": visual_equal,
    "review": {
        "strengths": [
            "Cairnwell Automotive / Moorcross Works identity is present with no working-title branding.",
            "Guarding, rollers, gantry, cabinets, safety controls and layered industrial colours remain readable.",
            "Collision authoring is visually non-invasive; v086 and v087 actor visual fingerprints are identical."
        ],
        "retained_holds": [
            "Identity typography remains small and soft at CCTV distance.",
            "Service hardware, hoses, sensors and installed mechanical density remain sparse relative to the Pro reference.",
            "The hall/floor presentation remains bright and clean, and the elevated view still reads as a modular technical assembly.",
            "The interface view remains technical rather than release-cinematic."
        ],
        "collision_findings_not_visible_in_beauty_renders": [
            "The 1800 x 2600 mm maximum blank box sweep is blocked by the trace portal.",
            "The source-authoritative full gantry bridge range overlaps the trace portal beam and both posts."
        ]
    },
    "status": "PRESERVED_V086_VISUALS__KNOWN_VISUAL_AND_RELEASE_COLLISION_HOLDS__NOT_PROMOTED",
    "visual_approval": False,
    "promotion_authorized": False
}
(AUDIT / "visual_review_v087.json").write_text(json.dumps(visual, indent=2), encoding="utf-8")

validation_window = {
    key: table(validation_before[key]) == table(validation_after[key])
    for key in ("protected_files", "source_staging_files", "robot_files", "pr010_files")
}
parent_path = "Content/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086.umap"
protected_map_paths = [row["path"] for row in parent_before["protected_files"] if row["path"].endswith(".umap")]
before_protected = table(parent_before["protected_files"])
after_protected = table(validation_after["protected_files"])
protected_maps_unchanged = all(before_protected.get(path) == after_protected.get(path) for path in protected_map_paths)
handoff_paths = ["Docs/NEW_CHAT_HANDOVER_2026-08-03.md", "Docs/PROJECT_HANDOFF.md"]
handoff_baseline_changes = [path for path in handoff_paths if before_protected.get(path) != after_protected.get(path)]
target_unchanged_during_validation = validation_before["target_map_file"] == validation_after["target_map_file"]

native_log = LOGS / "native_build.log"
native_compile_pass = native_log.exists() and "Result: Succeeded" in native_log.read_text(encoding="utf-16", errors="ignore")
if not native_compile_pass:
    native_compile_pass = native_log.exists() and "Result: Succeeded" in native_log.read_text(encoding="utf-8", errors="ignore")

gates = {
    "G01_native_compile": {"pass": native_compile_pass, "evidence": "Saved/Logs/PR009_InMap_v087/native_build.log"},
    "G02_RuntimeAndSave_automation": {"pass": auto_runtime["pass"], "evidence": auto_runtime},
    "G03_TraceableBlankHandoff_automation": {"pass": auto_handoff["pass"], "evidence": auto_handoff},
    "G04_native_PIE_motion_save_authority": {"pass": runtime["status"].startswith("PASS") and not runtime["failures"],
        "evidence": "Saved/Audits/PR009_InMap_v087/runtime_pie_audit.json"},
    "G05_static_release_collision_inventory": {"pass": static["asset_collision_ready"] and static["complex_as_simple_count"] == 0,
        "evidence": "Saved/Audits/PR009_InMap_v087/release_collision_static_audit.json"},
    "G06_physical_perimeter_chassis_and_blank_path": {"pass": physical["status"].startswith("PASS"),
        "failures": physical["failures"], "evidence": "Saved/Audits/PR009_InMap_v087/physical_collision_pie_audit.json"},
    "G07_full_motion_contract_vs_blockers": {"pass": sweeps["status"].startswith("PASS"),
        "failures": sweeps["failures"], "unexpected_overlaps": sweeps["unexpected_blocking_overlaps"],
        "evidence": "Saved/Audits/PR009_InMap_v087/collision_contract_sweep_audit.json"},
    "G08_runtime_navigation": {"pass": navigation["status"].startswith("PASS") and navigation["protected_space_traversal_count"] == 0,
        "evidence": "Saved/Audits/PR009_InMap_v087/navigation_pie_audit.json"},
    "G09_visual_preservation": {"pass": visual_equal and len(shot_rows) == 4,
        "visual_approval": False, "evidence": "Saved/Audits/PR009_InMap_v087/visual_review_v087.json"},
    "G10_integrity": {"pass": all(validation_window.values()) and target_unchanged_during_validation and protected_maps_unchanged,
        "validation_window_unchanged": validation_window,
        "target_map_unchanged_during_validation": target_unchanged_during_validation,
        "parent_and_protected_maps_unchanged_from_prebuild": protected_maps_unchanged,
        "handoff_documents_changed_between_prebuild_and_validation": handoff_baseline_changes,
        "handoff_change_note": "Both handoff files changed before the validation_before snapshot; they remained byte-identical throughout this task's final validation window. Hash evidence cannot attribute the concurrent changes, and this task did not write them.",
        "evidence": ["Saved/Audits/PR009_InMap_v087/integrity_parent_before_build.json",
                     "Saved/Audits/PR009_InMap_v087/integrity_validation_before.json",
                     "Saved/Audits/PR009_InMap_v087/integrity_validation_after.json"]},
    "G11_zero_PR010": {"pass": not static["pr010_actors"] and validation_window["pr010_files"],
        "pr010_actor_count": len(static["pr010_actors"]), "pr010_files_unchanged": validation_window["pr010_files"]}
}

consolidated = {
    "$schema": "cairnwell/audit/pr009-release-collision-verification-v087/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FAIL_RELEASE_COLLISION_BLOCKED_BY_MAX_BLANK_TRACE_PORTAL_AND_FULL_GANTRY_PORTAL_OVERLAPS__NOT_PROMOTED",
    "parent_map": build["parent_map"], "target_map": build["target_map"],
    "source_ucx_evidence": {
        "evidence": "Saved/Audits/PR009_InMap_v087/source_collision_evidence.json",
        "supplied_proxy_count": source.get("supplied_ucx_proxy_count"),
        "assessment": build["supplied_ucx_assessment"]
    },
    "collision_inventory": {
        "ten_combined_static_groups": static["static_groups"],
        "fixed_blocking_chassis": static["fixed_chassis"],
        "query_only_movers": static["selective_query_movers"],
        "simple_primitive_total": static["simple_primitive_total"],
        "convex_primitive_total": static["convex_primitive_total"],
        "complex_as_simple_count": static["complex_as_simple_count"],
        "intentionally_no_collision_visual_count": len(static["intentionally_no_collision_modular_visuals"]),
        "intentional_no_collision_policy": build["intentionally_non_colliding_visual_policy"],
        "query_only_movers_are_physical_blockers": physical["query_only_movers_are_physical_blockers"]
    },
    "maximum_blank_evidence": physical["transferred_blank_envelope_authority"],
    "maximum_blank_sweep": physical["transferred_blank_box_sweep"],
    "engineered_allowed_contacts": sweeps["allowed_engineered_contacts"],
    "unapproved_full_range_overlaps": sweeps["unexpected_blocking_overlaps"],
    "gates": gates,
    "blocking_findings": [
        "The Pro maximum 1800 x 2600 mm blank envelope physically hits the trace portal at its zero-clearance 2600 mm opening.",
        "The source-authoritative 2800 mm gantry bridge range overlaps the trace portal beam and both posts.",
        "These are geometry/motion-contract conflicts; collision settings alone cannot resolve them defensibly."
    ],
    "release_collision_ready": False,
    "visual_approval": False,
    "promotion_authorized": False,
    "pr010_started": False
}
(AUDIT / "PR009_RELEASE_COLLISION_VERIFICATION_v087.json").write_text(json.dumps(consolidated, indent=2), encoding="utf-8")

report = f"""# PR-009 v087 release-collision verification

**Outcome:** FAIL / REWORK / NOT PROMOTED. `release_collision_ready=false`; `promotion_authorized=false`.

The isolated v087 map was created from immutable v086 and now uses authored simple box collision instead of complex-as-simple on all ten combined static station groups. Static authoring, native compile, both focused automations, native PIE behavior, navigation, visual preservation and validation-window integrity pass. Release acceptance fails on real geometry/clearance conflicts.

## Collision inventory

- 98 simple box primitives total: 58 on the ten combined static groups, 14 on substantial fixed chassis actors, and 26 query-only sensing envelopes on selected movers.
- 0 convex primitives and 0 complex-as-simple assets.
- Fixed chassis and substantial station envelopes use `BlockAll`, `QueryAndPhysics`, and are navigation relevant where appropriate.
- Selected movers use `OverlapAllDynamic`, `QueryOnly`, and are not physical blockers or navigation relevant.
- 118 minor modular visuals remain intentionally `NoCollision` (bolts, cables, sensors, energy-chain links and comparable detail).

## Release blockers

1. The physical 1800 x 2600 mm maximum blank sweep (tested half extents 90 x 130 cm) hits `LB_PR009_V087_SM_CA_MW_PR009_TracePortal_01` at approximately `(426, -1870, 105.5)` cm. The portal opening is effectively zero-clearance at the Pro maximum width.
2. The full source-authoritative 2800 mm gantry bridge contract intersects the trace portal beam and both posts. Eight engineered support/drive contacts are documented separately; these three portal overlaps are not approved contacts.

The material centerline and intended infeed/outfeed apertures are open. All 20 guard primitives respond when probed from their authored centers/normals. Per-asset isolated traces prove the fixed chassis and BaseFrame primitives respond physically. Query-only mover sensing is explicitly distinguished from physical blocking.

## Passed gates

- Native UE 5.8 editor compile: succeeded.
- `LineBoss.PressShop.PR009.RuntimeAndSave`: 1/1 success, zero warnings/errors.
- `LineBoss.PressShop.MaterialFlow.PR008ToPR009TraceableBlankHandoff`: 1/1 success, zero warnings/errors.
- PIE: exact singleton PR-008/PR-009/controller binding, transactional rollback/no phantom blanks, native mover presentation, safe stopped restore, trusted authority and isolation/zero-energy behavior all pass.
- Navigation: two 1040 cm non-partial perimeter routes; zero protected-space path points.
- Visual preservation: all 207 normalized v086/v087 visual actor payloads match exactly; four fresh 1920 x 1080 v087 captures were generated.
- Validation-window integrity: parent/protected maps, handoffs, source staging, robots, PR-010 and the target map remained unchanged. The two handoff hashes had changed before the final validation window and are recorded as an unattributed concurrent change, not overwritten here.

## Required rework

Resolve the trace-portal/maximum-blank clearance and reconcile the trace portal with the source-authoritative full gantry bridge range in a later isolated candidate. Do not solve this by disabling required physical collision or shrinking the authoritative blank envelope. Repeat all gates and visual review afterward.

Primary audit: `Saved/Audits/PR009_InMap_v087/PR009_RELEASE_COLLISION_VERIFICATION_v087.json`.
"""
(AUDIT / "PR009_RELEASE_COLLISION_VERIFICATION_REPORT.md").write_text(report, encoding="utf-8")

readme = """# PR-009 v087 reproducible validation handoff

This directory is an unpromoted collision-candidate evidence package. The candidate map is `/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087`; parent v086 is immutable.

Run order from the repository root:

1. `python Scripts/snapshot_press_shop_pr009_release_collision_v087_integrity.py validation_before`
2. Run the UE 5.8 native editor build and the two focused automation tests.
3. Run the v087 Unreal Python validators: static collision, runtime PIE, physical collision PIE, navigation PIE and visual invariants.
4. Run `python Scripts/audit_press_shop_pr009_collision_contract_sweeps_v087.py`.
5. Generate the four fixed-camera captures with `Scripts/capture_press_shop_pr009_release_collision_v087.py`, setting `LB_PR009_V087_CAPTURE` to `process`, `interface`, `cell`, then `elevated`.
6. `python Scripts/snapshot_press_shop_pr009_release_collision_v087_integrity.py validation_after`
7. `python Scripts/consolidate_press_shop_pr009_release_collision_v087.py`

On a clean first build, `Scripts/build_press_shop_pr009_release_collision_candidate_v087.py` is intentionally run twice: first to duplicate/save v086 as v087, then to author collision into the isolated target. Do not run it against v086. The supplied source UCX evidence is dimensionally reused only where proven; oversized proxies that close required process paths are rejected.

Current result is REWORK / NOT PROMOTED. See `PR009_RELEASE_COLLISION_VERIFICATION_v087.json` and the Markdown report.
"""
(AUDIT / "README.md").write_text(readme, encoding="utf-8")

print(json.dumps({"status": consolidated["status"], "release_collision_ready": False,
                  "promotion_authorized": False, "visual_captures": len(shot_rows),
                  "output": str(AUDIT / "PR009_RELEASE_COLLISION_VERIFICATION_v087.json")}, indent=2))
