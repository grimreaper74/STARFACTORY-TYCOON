"""Create v047 by clearing the wider S07 facade with its segmented identity plate."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainASegmentedIdentityCandidate_v046"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAS07IdentityClearanceCandidate_v047"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_s07_identity_clearance_v047.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v047 from v046: {TARGET}")
target_actor = None
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.SegmentedIdentityPlate.S07" in tags:
        target_actor = actor
        location = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(-485.0, location.y, location.z), False, False)
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v047" not in tags:
            tags.append("LB.Asset.Candidate.v047")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
failures = []
if target_actor is None or scope_count != 173:
    failures.append(f"S07 plate/scope mismatch target={target_actor is not None} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v047 S07 identity-clearance candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-s07-identity-clearance-v047/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V047_S07_SEGMENTED_IDENTITY_CLEARS_WIDE_INSPECTION_FACADE__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V047_S07_IDENTITY_CLEARANCE__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET,
    "corrected_actor": target_actor.get_actor_label() if target_actor else None,
    "corrected_x_cm": -485.0, "scope_actor_count": scope_count,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
