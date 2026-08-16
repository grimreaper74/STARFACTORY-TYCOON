"""Run the exact static/material/endpoint-clearance gate on isolated Train A v068."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_endpoint_evidence_static_v064.py")
code = base.read_text(encoding="utf-8")
code = code.replace('"scope": (len(scope), 189)', '"scope": (len(scope), 187)')
code = code.replace('"presentation": (len(presentation), 142)', '"presentation": (len(presentation), 140)')
code = code.replace("CA_MW_PTA_CAM_S01FeedEvidence_v064", "CA_MW_PTA_CAM_S01FeedClear_v068")
code = code.replace("CA_MW_PTA_CAM_S07DischargeEvidence_v064", "CA_MW_PTA_CAM_S07DischargeClear_v068")
code = code.replace("LB.PressTrain.EndpointEvidence.v064", "LB.PressTrain.EndpointClearance.v068")
code = code.replace("endpoint_evidence_static_v064", "endpoint_clearance_static_v068")
code = code.replace("endpoint-evidence-static-v064", "endpoint-clearance-static-v068")
code = code.replace("Candidate_v064", "Candidate_v068")
code = code.replace("LB.Asset.Candidate.v064", "LB.Asset.Candidate.v068")
code = code.replace("PRESS_TRAIN_A_V064", "PRESS_TRAIN_A_V068")
code = code.replace("V064", "V068").replace("v064", "v068")
exec(compile(code, str(base) + "::v068", "exec"), globals(), globals())

by_label = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
flow_checks = []
for label, expected_y, stage_tag, expected_min, expected_max in (
    ("CA_MW_PTA_S01_VisibleBlankFeed_v048", -150.0, "LB.PressTrain.Stage.S01", -470.1, -59.9),
    ("CA_MW_PTA_S07_VisiblePanelDischarge_v048", 4550.0, "LB.PressTrain.Stage.S07", 4569.9, 5140.1),
):
    actor = by_label.get(label)
    if actor is None:
        failures.append(f"corrected endpoint missing: {label}")
        continue
    location = actor.get_actor_location()
    rotation = actor.get_actor_rotation()
    origin, extent = actor.get_actor_bounds(False)
    y_min = origin.y - extent.y
    y_max = origin.y + extent.y
    actor_tags = {str(tag) for tag in actor.tags}
    flow_checks.append({
        "actor": label,
        "y_cm": location.y,
        "yaw_deg": rotation.yaw,
        "bounds_y_cm": [y_min, y_max],
        "stage_tag": stage_tag,
    })
    if abs(location.y - expected_y) > 0.1 or abs(rotation.yaw) > 0.1:
        failures.append(f"endpoint flow transform mismatch: {label}")
    if y_min < expected_min or y_max > expected_max:
        failures.append(f"endpoint flow bounds mismatch: {label} [{y_min}, {y_max}]")
    if stage_tag not in actor_tags or "LB.PressTrain.EndpointClearance.v068" not in actor_tags:
        failures.append(f"endpoint stage/clearance tag missing: {label}")

removed_checks = []
for label in ("CA_MW_PTA_S01_DESTACK__LOAD", "CA_MW_PTA_S07_UNLOAD__INSPECT"):
    absent = label not in by_label
    removed_checks.append({"actor": label, "absent": absent})
    if not absent:
        failures.append(f"obsolete endpoint occluder retained: {label}")

report["endpoint_flow_checks"] = flow_checks
report["removed_obsolete_occluders"] = removed_checks
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V068_EXACT_MAP_CORRECT_ENDPOINT_FLOW_CLEARANCE_ACCESS_MATERIALS_AND_WARNING_CLEAN_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V068_ENDPOINT_CLEARANCE_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"flow_checks": flow_checks, "removed_checks": removed_checks, "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
