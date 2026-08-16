"""Retain the v095 map but revoke acceptance after the cross-station flow-axis failure."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095"
AXIS_AUDIT = ROOT / "Saved/Audits/PR010_Intake/pr009_pr010_flow_axis_integration_v001.json"
OUT = ROOT / "Saved/Audits/PR009_Accepted_v095/acceptance_revocation_receipt.json"
axis = json.loads(AXIS_AUDIT.read_text(encoding="utf-8-sig"))
if not str(axis.get("status", "")).startswith("FAIL__PR009_MODULAR_PRESENTATION_FLOW_AXIS_REVERSED"):
    raise RuntimeError("Flow-axis audit does not authorize acceptance revocation")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
changed = 0
for actor in actors:
    tags = [str(tag) for tag in actor.tags]
    filtered = [tag for tag in tags if tag not in ("LB.Asset.AcceptedBaseline", "LB.Asset.Accepted.PR009.v095")]
    if actor.get_actor_label().startswith("LB_PR009_V095_"):
        for tag in ("LB.Asset.CandidateNotPromoted", "LB.Asset.AcceptanceRevoked.AxisIntegration"):
            if tag not in filtered:
                filtered.append(tag)
        changed += 1
    actor.tags = [unreal.Name(tag) for tag in filtered]
if not levels.save_current_level():
    raise RuntimeError("Could not save revoked-retained v095 map")

accepted_tags = sum(
    str(tag) in ("LB.Asset.AcceptedBaseline", "LB.Asset.Accepted.PR009.v095")
    for actor in actors for tag in actor.tags
)
receipt = {
    "$schema": "cairnwell/audit/pr009-v095-acceptance-revocation/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "retained_map": MAP,
    "status": "PASS__PR009_V095_ACCEPTANCE_REVOKED__MAP_RETAINED_NOT_PROMOTED" if not accepted_tags else "FAIL__ACCEPTED_TAGS_REMAIN",
    "retagged_actor_count": changed,
    "accepted_tag_count": accepted_tags,
    "reason_audit": str(AXIS_AUDIT.relative_to(ROOT)),
    "map_deleted": False,
    "promotion_authorized": False,
}
OUT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR009_REVOKE {receipt['status']} {OUT}")
if accepted_tags:
    raise RuntimeError("Accepted tags remain after revocation")
