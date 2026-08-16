"""Create v032 with cart identity text clear of the physical plaque face."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACartLegibilityCandidate_v031"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACartPlateClearanceCandidate_v032"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_cart_plate_clearance_v032.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v032 from v031: {TARGET}")

actors = list(actors_api.get_all_level_actors())
records = []
for index in range(2, 7):
    stage = f"S{index:02d}"
    label = f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v031"
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    plate = matches[0]
    previous = plate.get_actor_location()
    plate.set_actor_location(unreal.Vector(previous.x + 3.5, previous.y, previous.z), False, False)
    plate.set_actor_label(f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v032")
    tags = [str(tag) for tag in plate.tags]
    tags.extend(("LB.Asset.Candidate.v032", "LB.PressTrain.ReleaseDetail.CartIdentityPlateFaceClearance.v032"))
    plate.set_editor_property("tags", [unreal.Name(tag) for tag in dict.fromkeys(tags)])
    records.append({"stage": stage, "outward_face_clearance_added_cm": 3.5})

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v032" not in tags:
            tags.append("LB.Asset.Candidate.v032")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(records) != 5 or scope_count != 157:
    failures.append(f"cardinality mismatch plates={len(records)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v032 cart-plate-clearance candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-cart-plate-clearance-v032/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V032_CART_IDENTITY_TEXT_CLEARS_PHYSICAL_PLAQUE_FACE__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V032_CART_PLATE_CLEARANCE__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "plate_records": records,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
