"""Create v038 by turning the four v037 cue modules operator-side."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAStageExteriorCuesCandidate_v037"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_stage_cue_facing_v038.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v038 from v037: {TARGET}")

corrected = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.Fixed.StageExteriorCue" in tags:
        actor.set_actor_rotation(unreal.Rotator(yaw=0.0), False)
        corrected.append({
            "actor": actor.get_actor_label(),
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
            "rotation": [actor.get_actor_rotation().roll, actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw],
        })
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v038" not in tags:
            tags.append("LB.Asset.Candidate.v038")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(corrected) != 4 or scope_count != 173:
    failures.append(f"cardinality mismatch corrected={len(corrected)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v038 cue-facing candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-stage-cue-facing-v038/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V038_FOUR_STAGE_CUE_MODULES_CORRECTED_TOWARD_OPERATOR_CCTV_SIDE__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V038_STAGE_CUE_FACING__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "corrected": corrected,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
