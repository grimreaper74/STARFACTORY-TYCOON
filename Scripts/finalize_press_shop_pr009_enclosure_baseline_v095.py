"""Finalize and sanity-check the accepted PR-009 v095 map in a fresh editor process."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095"
OUT = ROOT / "Saved/Audits/PR009_Accepted_v095/promotion_receipt.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST):
    raise RuntimeError(DEST)

actors = actors_api.get_all_level_actors()
changed = 0
for actor in actors:
    tags = [str(tag) for tag in actor.tags if str(tag) != "LB.Asset.CandidateNotPromoted"]
    if actor.get_actor_label().startswith("LB_PR009_V095_"):
        for tag in ("LB.Asset.AcceptedBaseline", "LB.Asset.Accepted.PR009.v095"):
            if tag not in tags:
                tags.append(tag)
        changed += 1
    actor.tags = [unreal.Name(tag) for tag in tags]

if not levels.save_current_level():
    raise RuntimeError("Could not save accepted PR-009 v095 map")

stations = [actor for actor in actors if isinstance(actor, unreal.LBPR009Station)]
flows = [actor for actor in actors if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
modules = [actor for actor in actors if actor.get_actor_label().startswith("LB_PR009_V095_ENC_SM_CA_MW_ENC_PR009_")]
candidate_tags = sum(
    str(tag) == "LB.Asset.CandidateNotPromoted" for actor in actors for tag in actor.tags
)
failures = []
if len(stations) != 1: failures.append(f"expected one PR-009 authority, found {len(stations)}")
if len(flows) != 1: failures.append(f"expected one material-flow controller, found {len(flows)}")
if len(modules) != 7: failures.append(f"expected seven enclosure modules, found {len(modules)}")
if candidate_tags: failures.append(f"candidate-not-promoted tags remain: {candidate_tags}")
if any("LINE BOSS" in actor.get_actor_label().upper() for actor in actors):
    failures.append("Line Boss actor label found in accepted map")

receipt = {
    "$schema": "cairnwell/audit/pr009-accepted-baseline-v095/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "accepted_map": DEST,
    "status": "PASS__PR009_V095_ACCEPTED_BASELINE_CREATED" if not failures else "FAIL__ACCEPTED_MAP_SANITY",
    "actor_count": len(actors),
    "accepted_tagged_actor_count": changed,
    "enclosure_module_count": len(modules),
    "authority_count": len(stations),
    "flow_controller_count": len(flows),
    "candidate_not_promoted_tag_count": candidate_tags,
    "failures": failures,
    "press_shop_complete": False,
}
OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR009_ACCEPTED_FINAL {receipt['status']} {OUT}")
if failures:
    raise RuntimeError("; ".join(failures))
