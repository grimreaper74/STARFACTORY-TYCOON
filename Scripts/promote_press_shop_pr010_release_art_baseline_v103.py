"""Promote the fully gated PR-010 v103 station into an immutable accepted map."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103"
DEST = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
VERIFICATION = ROOT / "Saved/Audits/PR010_ReleaseArt_v103/PR010_V103_RELEASE_VERIFICATION.json"
OUT = ROOT / "Saved/Audits/PR010_Accepted_v103/promotion_receipt.json"
REQUIRED = "PASS__PR010_V103_SOURCE_IMPORT_STATIC_COMPILE_AUTOMATION_RUNTIME_SAVE_AUTHORITY_COLLISION_NAV_LIVE_HMI_FRESH_VISUAL__PROMOTION_AUTHORIZED__PRESS_SHOP_NOT_COMPLETE"
ACCEPTED_TAG = "LB.Asset.Accepted.PR010.v103"

verification = json.loads(VERIFICATION.read_text(encoding="utf-8"))
if verification.get("status") != REQUIRED or not verification.get("promotion_authorized"):
    raise RuntimeError("The consolidated PR-010 v103 gate does not authorize promotion")
destination_preexisted = unreal.EditorAssetLibrary.does_asset_exist(DEST)
if destination_preexisted and OUT.exists():
    raise RuntimeError(f"Accepted map and promotion receipt already exist; refusing to overwrite: {DEST}")
if not destination_preexisted:
    if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE, DEST):
        raise RuntimeError(f"Could not duplicate {SOURCE} to {DEST}")
    if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated accepted map: {DEST}")
    # duplicate_asset leaves a world reference resident in this commandlet. End this
    # pass cleanly; a second invocation finalizes the already-saved exact duplicate.
    report = {
        "$schema": "cairnwell/audit/pr010-accepted-baseline-promotion-v103/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_map": SOURCE,
        "accepted_map": DEST,
        "status": "PASS__PR010_V103_ACCEPTED_DUPLICATE_CREATED__FINALIZATION_REQUIRES_SECOND_PASS",
        "press_shop_complete": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (OUT.parent / "duplication_receipt.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"CAIRNWELL_PR010_V103_ACCEPTED {report['status']}")
    raise SystemExit(0)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(DEST):
    raise RuntimeError(f"Could not load duplicated accepted map: {DEST}")

scope = []
retagged = 0
removed_candidate_tags = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.Station.PR010" not in actor_tags:
        continue
    scope.append(actor)
    retained = []
    for tag in actor_tags:
        if tag.startswith("LB.Asset.Candidate"):
            removed_candidate_tags += 1
        elif tag != ACCEPTED_TAG:
            retained.append(tag)
    retained.append(ACCEPTED_TAG)
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in retained])
    retagged += 1

if not scope:
    raise RuntimeError("No PR-010 station actors found in duplicated map")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save accepted map after finalization: {DEST}")

candidate_tags_remaining = sum(
    str(tag).startswith("LB.Asset.Candidate")
    for actor in scope
    for tag in actor.tags
)
accepted_tag_count = sum(ACCEPTED_TAG in {str(tag) for tag in actor.tags} for actor in scope)
failures = []
if candidate_tags_remaining:
    failures.append(f"{candidate_tags_remaining} candidate tags remain in PR-010 scope")
if accepted_tag_count != len(scope):
    failures.append(f"accepted tag count {accepted_tag_count} does not match PR-010 scope {len(scope)}")

report = {
    "$schema": "cairnwell/audit/pr010-accepted-baseline-promotion-v103/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source_map": SOURCE,
    "accepted_map": DEST,
    "resumed_existing_unfinalized_duplicate": destination_preexisted,
    "status": "PASS__PR010_V103_ACCEPTED_BASELINE_PROMOTED__POST_PROMOTION_GATES_REQUIRED" if not failures else "FAIL__PR010_V103_PROMOTION_FINALIZATION",
    "pr010_scope_actor_count": len(scope),
    "retagged_actor_count": retagged,
    "removed_candidate_tag_count": removed_candidate_tags,
    "candidate_tags_remaining": candidate_tags_remaining,
    "accepted_tag_count": accepted_tag_count,
    "failures": failures,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"CAIRNWELL_PR010_V103_ACCEPTED {report['status']} {OUT}")
if failures:
    raise RuntimeError("; ".join(failures))
