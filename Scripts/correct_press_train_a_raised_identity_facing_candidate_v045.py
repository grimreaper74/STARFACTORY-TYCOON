"""Create v045 by turning the seven raised identity plates to operator/CCTV."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainARaisedIdentityCandidate_v044"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainARaisedIdentityFacingCandidate_v045"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_raised_identity_facing_v045.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v045 from v044: {TARGET}")
corrected = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.Fixed.RaisedIdentityPlate" in tags:
        actor.set_actor_rotation(unreal.Rotator(yaw=180.0), False)
        corrected.append(actor.get_actor_label())
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v045" not in tags:
            tags.append("LB.Asset.Candidate.v045")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
failures = []
if len(corrected) != 7 or scope_count != 173:
    failures.append(f"cardinality mismatch corrected={len(corrected)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v045 raised-identity-facing candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-raised-identity-facing-v045/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V045_SEVEN_RAISED_IDENTITY_PLATES_FACED_OPERATOR_CCTV_SIDE__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V045_RAISED_IDENTITY_FACING__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "corrected_plates": corrected,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
