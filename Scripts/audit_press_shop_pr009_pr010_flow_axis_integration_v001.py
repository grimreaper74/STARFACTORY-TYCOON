"""Prove physical PR-008/PR-009/PR-010 flow-axis alignment from fixed numeric authority."""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CONTEXT = ROOT / "Saved/Audits/PR010_Intake/pr010_master_plan_context_v001.json"
OUT = ROOT / "Saved/Audits/PR010_Intake/pr009_pr010_flow_axis_integration_v001.json"
data = json.loads(CONTEXT.read_text(encoding="utf-8-sig"))
actors = data["nearest_actors"]


def xs(predicate):
    return [row["location_cm"][0] for row in actors if predicate(row["label"].upper())]


infeed_x = xs(lambda label: "LB_PR009_V095_MOD_PR009_01_" in label or "LB_PR009_V095_MOD_PR009_M01_INFEEDROLL" in label)
output_x = xs(lambda label: "LB_PR009_V095_MOD_PR009_08_" in label)
transfer_x = xs(lambda label: "LB_PR009_V095_SM_CA_MW_PR008_PR009_TRANSER" in label)
if not transfer_x:
    transfer_x = xs(lambda label: "LB_PR009_V095_SM_CA_MW_PR008_PR009_TRANSFER" in label)

datum_pr009_x = 600.0
datum_pr010_x = 1350.0
expected = {
    "pr009_infeed_centre_world_x_cm": datum_pr009_x + (-3250.0 / 10.0),
    "pr009_output_centre_world_x_cm": datum_pr009_x + (2950.0 / 10.0),
    "pr010_infeed_shuttle_centre_world_x_cm": datum_pr010_x + (-3300.0 / 10.0),
}
observed = {
    "pr009_infeed_actor_count": len(infeed_x),
    "pr009_infeed_mean_world_x_cm": statistics.mean(infeed_x) if infeed_x else None,
    "pr009_infeed_range_world_x_cm": [min(infeed_x), max(infeed_x)] if infeed_x else None,
    "pr009_output_actor_count": len(output_x),
    "pr009_output_mean_world_x_cm": statistics.mean(output_x) if output_x else None,
    "pr009_output_range_world_x_cm": [min(output_x), max(output_x)] if output_x else None,
    "pr008_pr009_transfer_range_world_x_cm": [min(transfer_x), max(transfer_x)] if transfer_x else None,
}

failures = []
if not infeed_x or not output_x or not transfer_x:
    failures.append("required physical interface actor sets were not found")
else:
    if statistics.mean(infeed_x) <= statistics.mean(output_x):
        failures.append("observed PR009 modular infeed is not upstream of observed output along increasing world X")
    if abs(statistics.mean(infeed_x) - expected["pr009_infeed_centre_world_x_cm"]) > 200:
        failures.append("observed PR009 modular infeed is on the opposite side of the authoritative infeed centre")
    if abs(statistics.mean(output_x) - expected["pr009_output_centre_world_x_cm"]) > 200:
        failures.append("observed PR009 modular output is on the opposite side of the authoritative output centre")

result = {
    "$schema": "cairnwell/audit/pr009-pr010-flow-axis-integration-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FAIL__PR009_MODULAR_PRESENTATION_FLOW_AXIS_REVERSED__V095_ACCEPTANCE_REVOKED" if failures else "PASS__PHYSICAL_FLOW_AXIS_ALIGNED",
    "authority": {
        "station_local_axes": "+X across lane, +Y material flow, +Z up",
        "station_yaw_degrees": -90,
        "world_flow_direction": "increasing world X",
        "fixed_datums_world_x_cm": {"PR008": -500, "PR009": 600, "PR010": 1350},
        "mapping": "At yaw -90 degrees, station local +Y maps to increasing world X.",
    },
    "expected": expected,
    "observed": observed,
    "failures": failures,
    "consequence": {
        "pr009_v095": "Retain as a technically gated enclosure candidate but revoke accepted-baseline status until modular presentation endpoints are corrected and all gates/images repeat.",
        "pr010": "Do not build its Unreal blockout on the reversed PR009 interface. Source authority intake may continue.",
        "pro_redesign_required": False,
    },
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
if failures:
    raise SystemExit(2)

