"""Create v039 with readable short identities on the seven authored facade plates."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAIntegratedIdentityCandidate_v039"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_integrated_identity_v039.json"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
plate_material = library.load_asset(f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025")
if plate_material is None:
    raise RuntimeError("Train A identity plate material is missing")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v039 from v038: {TARGET}")

short_names = {
    "S01": "S01  LOAD", "S02": "S02  DRAW", "S03": "S03  FORM",
    "S04": "S04  TRIM", "S05": "S05  PIERCE", "S06": "S06  RESTRIKE",
    "S07": "S07  INSPECT",
}
plate_overrides = []
identity_updates = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    tag_set = set(tags)
    if "LB.PressTrain.Fixed.EnclosedFacade" in tag_set:
        component = actor.static_mesh_component
        for index, slot_name in enumerate(component.get_material_slot_names()):
            if str(slot_name) == "CA_MW_LabelWhite":
                component.set_material(index, plate_material)
                plate_overrides.append({"actor": actor.get_actor_label(), "slot_index": index})
    if "LB.PressTrain.EnclosedFacade.IntegratedIdentity" in tag_set:
        stage = next((value for value in short_names if f".{value}.IntegratedIdentity" in tag_set), None)
        if stage is None:
            raise RuntimeError(f"could not resolve stage identity for {actor.get_actor_label()}")
        component = actor.text_render
        component.set_text(short_names[stage])
        component.set_world_size(18.0 if stage not in {"S06", "S07"} else 16.0)
        component.set_text_render_color(unreal.Color(230, 242, 238, 255))
        component.set_editor_property("cast_shadow", False)
        identity_updates.append({
            "actor": actor.get_actor_label(), "stage": stage,
            "text": short_names[stage], "world_size_cm": 18.0 if stage not in {"S06", "S07"} else 16.0,
            "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        })
    if "LB.PressTrain.TrainA.Isolated" in tag_set:
        scope_count += 1
        if "LB.Asset.Candidate.v039" not in tags:
            tags.append("LB.Asset.Candidate.v039")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(plate_overrides) != 7 or len(identity_updates) != 7 or scope_count != 173:
    failures.append(
        f"cardinality mismatch plates={len(plate_overrides)} identities={len(identity_updates)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v039 integrated-identity candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-integrated-identity-v039/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V039_SEVEN_AUTHORED_PLATES_DARKENED_AND_SHORT_HIGH_CONTRAST_IDENTITIES_CALIBRATED__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V039_INTEGRATED_IDENTITY__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "plate_overrides": plate_overrides,
    "identity_updates": identity_updates, "scope_actor_count": scope_count,
    "floating_validation_labels_added": False, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
