"""Run the exact static gate on isolated Train A v062."""

import json
from pathlib import Path

import unreal


base = Path(__file__).with_name("audit_press_train_a_dock_coupling_static_v056.py")
code = base.read_text(encoding="utf-8")
code = code.replace("Candidate_v056", "Candidate_v062")
code = code.replace("static_v056", "industrial_readability_static_v062")
code = code.replace("static-v056", "industrial-readability-static-v062")
code = code.replace("LB.Asset.Candidate.v056", "LB.Asset.Candidate.v062")
code = code.replace("PRESS_TRAIN_A_V056", "PRESS_TRAIN_A_V062")
code = code.replace("DockCouplingEvidence_v001", "DockCouplingEvidence_v003")
code = code.replace("DockCouplingEngaged_v001", "DockCouplingEngaged_v003")
code = code.replace('"presentation": (len(presentation), 140)', '"presentation": (len(presentation), 142)')
code = code.replace('"exterior": (len(exterior), 14)', '"exterior": (len(exterior), 16)')
code = code.replace(
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 185:")',
    'code = code.replace("if len(scope) != 164:", "if len(scope) != 187:")',
)
code = code.replace(
    'code = code.replace("expected 164 scoped actors", "expected 185 scoped actors")',
    'code = code.replace("expected 164 scoped actors", "expected 187 scoped actors")',
)
code = code.replace("V056", "V062").replace("v056", "v062")
exec(compile(code, str(base) + "::v062", "exec"), globals(), globals())

actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = {actor.get_actor_label(): actor for actor in actors_api.get_all_level_actors()}
access_labels = [
    "CA_MW_PTA_S02_MaintenanceAccess",
    "CA_MW_PTA_S03_MaintenanceAccess_v062",
    "CA_MW_PTA_S05_MaintenanceAccess_v062",
    "CA_MW_PTA_S06_MaintenanceAccess",
]
access = []
for label in access_labels:
    actor = actors.get(label)
    if actor is None:
        failures.append(f"maintenance access missing: {label}")
        continue
    location = actor.get_actor_location()
    access.append({"actor": label, "location_cm": [location.x, location.y, location.z]})
    if abs(location.x - (-130.0)) > 0.1:
        failures.append(f"maintenance access facade clearance mismatch: {label} x={location.x}")

endpoint_expected = {
    "CA_MW_PTA_S01_VisibleBlankFeed_v048": -190.0,
    "CA_MW_PTA_S07_VisiblePanelDischarge_v048": -300.0,
}
endpoint_clearance = []
for label, expected_x in endpoint_expected.items():
    actor = actors.get(label)
    if actor is None:
        failures.append(f"endpoint missing: {label}")
        continue
    location = actor.get_actor_location()
    endpoint_clearance.append({"actor": label, "x_cm": location.x})
    if abs(location.x - expected_x) > 0.1:
        failures.append(f"endpoint camera-clearance mismatch: {label} x={location.x}")

report["maintenance_access"] = access
report["endpoint_camera_clearance"] = endpoint_clearance
report["failures"] = failures
report["status"] = (
    "PASS__PRESS_TRAIN_A_V062_EXACT_MAP_INDUSTRIAL_READABILITY_AND_WARNING_CLEAN_COUPLINGS__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
    if not failures else "FAIL__PRESS_TRAIN_A_V062_INDUSTRIAL_READABILITY_STATIC_GATE__NOT_PROMOTED"
)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"maintenance_access": len(access), "endpoint_clearance": len(endpoint_clearance), "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
