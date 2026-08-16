"""Create v043 with camera-readable stage codes; process meaning stays in physical cues/HMI."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAIdentityTextFacingCandidate_v042"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAIdentityCodeCandidate_v043"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_identity_code_v043.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v043 from v042: {TARGET}")

updated = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.EnclosedFacade.IntegratedIdentity" in tags:
        stage_tag = next(tag for tag in tags if tag.startswith("LB.PressTrain.EnclosedFacade.S") and tag.endswith(".IntegratedIdentity"))
        stage = stage_tag.split(".")[3]
        actor.text_render.set_text(stage)
        actor.text_render.set_world_size(32.0)
        actor.text_render.set_text_render_color(unreal.Color(242, 250, 246, 255))
        updated.append({"actor": actor.get_actor_label(), "stage_code": stage})
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v043" not in tags:
            tags.append("LB.Asset.Candidate.v043")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(updated) != 7 or scope_count != 180:
    failures.append(f"cardinality mismatch updated={len(updated)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v043 identity-code candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-identity-code-v043/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V043_SEVEN_CAMERA_READABLE_PHYSICAL_STAGE_CODES__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V043_IDENTITY_CODE__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "updated": updated,
    "scope_actor_count": scope_count, "process_name_authority": "physical cues plus HMI detail view",
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
