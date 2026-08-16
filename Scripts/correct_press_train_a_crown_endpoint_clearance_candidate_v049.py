"""Create v049 by clearing the operator facade with v048 crown/endpoint presentation."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointCandidate_v048"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointClearanceCandidate_v049"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_crown_endpoint_clearance_v049.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v049 from v048: {TARGET}")

corrected = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" in tags:
        location = actor.get_actor_location()
        if any(".HeavyCrown" in tag for tag in tags):
            x_cm = -120.0
        elif "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed" in tags:
            x_cm = -150.0
        elif "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge" in tags:
            x_cm = -250.0
        else:
            raise RuntimeError(f"unrecognized crown/endpoint semantic: {actor.get_actor_label()} {tags}")
        actor.set_actor_location(unreal.Vector(x_cm, location.y, location.z), False, False)
        corrected.append({"actor": actor.get_actor_label(), "x_cm": x_cm})
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v049" not in tags:
            tags.append("LB.Asset.Candidate.v049")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(corrected) != 7:
    failures.append(f"expected seven corrected presentation actors, found {len(corrected)}")
if scope_count != 180:
    failures.append(f"expected 180 scoped actors, found {scope_count}")
if not levels.save_current_level():
    failures.append("could not save v049 crown/endpoint-clearance candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-crown-endpoint-clearance-v049/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V049_CROWN_AND_ENDPOINT_PRESENTATION_CLEARS_OPERATOR_FACADES__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V049_CROWN_ENDPOINT_CLEARANCE__NOT_PROMOTED"
    ),
    "source_map": SOURCE,
    "map": TARGET,
    "corrected": corrected,
    "scope_actor_count": scope_count,
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
