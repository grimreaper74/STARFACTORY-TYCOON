"""Create v031 with gameplay-distance legible Cairnwell die-cart plates."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACartIdentityCandidate_v030"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACartLegibilityCandidate_v031"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_cart_legibility_v031.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v031 from v030: {TARGET}")

actors = list(actors_api.get_all_level_actors())
plate_records = []
for index in range(2, 7):
    stage = f"S{index:02d}"
    matches = [actor for actor in actors if actor.get_actor_label() == f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v030"]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {stage} v030 cart plate, found {len(matches)}")
    plate = matches[0]
    plate.set_actor_label(f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v031")
    plate.text_render.set_text(f"CAIRNWELL  A-{stage}")
    plate.text_render.set_world_size(14.0)
    tags = [str(tag) for tag in plate.tags]
    tags.extend(("LB.Asset.Candidate.v031", "LB.PressTrain.ReleaseDetail.CartIdentityPlateLegible.v031"))
    plate.set_editor_property("tags", [unreal.Name(tag) for tag in dict.fromkeys(tags)])
    plate_records.append({"stage": stage, "world_size": 14.0, "text": f"CAIRNWELL  A-{stage}"})

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v031" not in tags:
            tags.append("LB.Asset.Candidate.v031")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(plate_records) != 5 or scope_count != 157:
    failures.append(f"cardinality mismatch plates={len(plate_records)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v031 cart-legibility candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-cart-legibility-v031/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V031_GAMEPLAY_DISTANCE_CAIRNWELL_CART_PLATE_LEGIBILITY__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V031_CART_LEGIBILITY__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "plate_records": plate_records,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
