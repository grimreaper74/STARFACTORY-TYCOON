"""Correct PR-009 modular presentation flow direction while preserving its v095 shell."""

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009FlowAxisCorrectionCandidate_v096"
OUT = ROOT / "Saved/Audits/PR009_InMap_v096/flow_axis_correction_build.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
DATUM_X = 600.0
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

actors = actors_api.get_all_level_actors()
modular = []
renamed = 0
for actor in actors:
    label = actor.get_actor_label()
    if label.startswith("LB_PR009_V095_"):
        actor.set_actor_label(label.replace("LB_PR009_V095_", "LB_PR009_V096_", 1))
        renamed += 1
    tags = [str(tag).replace("v095", "v096").replace("V095", "V096") for tag in actor.tags]
    tags = [tag for tag in tags if tag not in ("LB.Asset.AcceptedBaseline", "LB.Asset.Accepted.PR009.v095")]
    if actor.get_actor_label().startswith("LB_PR009_V096_"):
        for tag in ("LB.Asset.Candidate.v096", "LB.Asset.CandidateNotPromoted"):
            if tag not in tags:
                tags.append(tag)
    actor.tags = [unreal.Name(tag) for tag in tags]
    if actor.get_actor_label().startswith("LB_PR009_V096_MOD_PR009_"):
        modular.append(actor)

before_rows = []
for actor in modular:
    loc = actor.get_actor_location()
    before_rows.append({"label": actor.get_actor_label(), "location_cm": [loc.x, loc.y, loc.z]})
    actor.set_actor_location(unreal.Vector(2.0 * DATUM_X - loc.x, loc.y, loc.z), False, False)

if not levels.save_current_level():
    raise RuntimeError("Could not save v096 flow-axis correction")

after_rows = []
negative_scale = []
for actor in modular:
    loc = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    after_rows.append({"label": actor.get_actor_label(), "location_cm": [loc.x, loc.y, loc.z]})
    if scale.x <= 0 or scale.y <= 0 or scale.z <= 0:
        negative_scale.append(actor.get_actor_label())

def select_x(rows, token):
    return [row["location_cm"][0] for row in rows if token in row["label"]]

infeed = select_x(after_rows, "_MOD_PR009_01_") + select_x(after_rows, "_MOD_PR009_M01_InfeedRoll_")
output = select_x(after_rows, "_MOD_PR009_08_")
stations = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
enclosure = [actor for actor in actors if actor.get_actor_label().startswith("LB_PR009_V096_ENC_SM_CA_MW_ENC_PR009_")]
failures = []
if len(modular) != 158: failures.append(f"expected 158 modular actors, found {len(modular)}")
if len(stations) != 1: failures.append(f"expected one native station, found {len(stations)}")
if len(flows) != 1: failures.append(f"expected one flow controller, found {len(flows)}")
if len(enclosure) != 7: failures.append(f"expected seven enclosure modules, found {len(enclosure)}")
if negative_scale: failures.append(f"negative/non-positive actor scale found on {len(negative_scale)} modular actors")
if not infeed or abs(statistics.mean(infeed) - 279.3) > 30: failures.append("corrected infeed centre is not near authoritative world X 275 cm")
if not output or abs(statistics.mean(output) - 925.7) > 80: failures.append("corrected output group is not on the authoritative east/output side")
if infeed and output and statistics.mean(infeed) >= statistics.mean(output): failures.append("corrected infeed is not upstream of output")

result = {
    "$schema": "cairnwell/audit/pr009-flow-axis-correction-build-v096/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PR009_MODULAR_FLOW_AXIS_CORRECTED__FULL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PR009_FLOW_AXIS_CORRECTION_BUILD",
    "parent_map": "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095",
    "target_map": MAP,
    "correction": "Reflect modular source-origin placements only across world X=600 cm; preserve Y service side, Z, actor rotations, identity scale, enclosure and fixed PR008/PR009 interface.",
    "renamed_actor_count": renamed,
    "modular_actor_count": len(modular),
    "enclosure_module_count": len(enclosure),
    "authority_count": len(stations),
    "flow_controller_count": len(flows),
    "infeed_mean_world_x_cm": statistics.mean(infeed) if infeed else None,
    "infeed_range_world_x_cm": [min(infeed), max(infeed)] if infeed else None,
    "output_mean_world_x_cm": statistics.mean(output) if output else None,
    "output_range_world_x_cm": [min(output), max(output)] if output else None,
    "expected_pr010_infeed_shuttle_world_x_cm": 1020.0,
    "negative_scale_actor_count": len(negative_scale),
    "failures": failures,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR009_V096_BUILD {result['status']} {OUT}")
if failures:
    raise RuntimeError("; ".join(failures))
