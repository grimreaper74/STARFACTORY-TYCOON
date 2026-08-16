"""Create isolated Train A v002 with the FBX flow-axis and die-cart envelope corrected."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAIsolatedCandidate_v001"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAFlowAxisCandidate_v002"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_flow_axis_correction_v002.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v002 from preserved v001: {TARGET}")


def tags(actor):
    return {str(tag) for tag in actor.tags}


scope = [actor for actor in actors_api.get_all_level_actors() if "LB.PressTrain.TrainA.Isolated" in tags(actor)]
presentation = [actor for actor in scope if isinstance(actor, unreal.StaticMeshActor) and "LB.Validation.Environment" not in tags(actor)]
rotated = []
die_carts = []
for actor in presentation:
    actor.set_actor_rotation(unreal.Rotator(yaw=180.0), False)
    current_tags = [str(tag) for tag in actor.tags]
    if "LB.Asset.Candidate.v002" not in current_tags:
        current_tags.append("LB.Asset.Candidate.v002")
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in current_tags])
    rotated.append(actor.get_actor_label())
    if "DieCart" in actor.get_actor_label():
        location = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(500.0, location.y, location.z), False, False)
        die_carts.append(actor.get_actor_label())

# Keep all visible identity and cameras candidate-traceable without changing their authored evidence transforms.
for actor in scope:
    if actor in presentation:
        continue
    current_tags = [str(tag) for tag in actor.tags]
    if "LB.Asset.Candidate.v002" not in current_tags:
        current_tags.append("LB.Asset.Candidate.v002")
    actor.set_editor_property("tags", [unreal.Name(tag) for tag in current_tags])

failures = []
if len(rotated) != 37:
    failures.append(f"expected 37 corrected presentation actors, found {len(rotated)}")
if len(die_carts) != 5:
    failures.append(f"expected five corrected die carts, found {len(die_carts)}")
if not levels.save_current_level():
    failures.append("could not save v002 flow-axis correction")
report = {
    "$schema": "cairnwell/audit/press-train-a-flow-axis-correction-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V002_SOURCE_PLUS_Y_TO_UNREAL_PLUS_Y_DIE_CARTS_WITHIN_ENVELOPE__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V002_FLOW_AXIS__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "rotated_presentation_actor_count": len(rotated),
    "corrected_die_cart_count": len(die_carts),
    "assembly_yaw_deg": 180.0,
    "die_cart_local_x_cm": 500.0,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
