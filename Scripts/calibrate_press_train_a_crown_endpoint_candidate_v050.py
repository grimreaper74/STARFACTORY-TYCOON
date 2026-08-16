"""Create v050 with flush, darker crown mass and restrained endpoint clearance."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointClearanceCandidate_v049"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointCalibrationCandidate_v050"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_crown_endpoint_calibration_v050.json"
FOUNDRY = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025/M_CA_MW_PT_FoundryCharcoalLayered_v025"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
foundry = library.load_asset(FOUNDRY)
if foundry is None:
    raise RuntimeError(f"missing crown calibration material: {FOUNDRY}")
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v050 from v049: {TARGET}")

calibrated = []
scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.Fixed.CrownEndpointPresentation" in tags:
        location = actor.get_actor_location()
        if any(".HeavyCrown" in tag for tag in tags):
            x_cm = -70.0
            actor.static_mesh_component.set_material(1, foundry)
            material_override = "slot_1_service_grey_to_layered_foundry_charcoal"
        elif "LB.PressTrain.CrownEndpoint.S01.VisibleBlankFeed" in tags:
            x_cm = -110.0
            material_override = None
        elif "LB.PressTrain.CrownEndpoint.S07.VisiblePanelDischarge" in tags:
            x_cm = -220.0
            material_override = None
        else:
            raise RuntimeError(f"unrecognized crown/endpoint semantic: {actor.get_actor_label()} {tags}")
        actor.set_actor_location(unreal.Vector(x_cm, location.y, location.z), False, False)
        calibrated.append({
            "actor": actor.get_actor_label(),
            "x_cm": x_cm,
            "material_override": material_override,
        })
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v050" not in tags:
            tags.append("LB.Asset.Candidate.v050")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(calibrated) != 7:
    failures.append(f"expected seven calibrated actors, found {len(calibrated)}")
if scope_count != 180:
    failures.append(f"expected 180 scoped actors, found {scope_count}")
if not levels.save_current_level():
    failures.append("could not save v050 crown/endpoint calibration candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-crown-endpoint-calibration-v050/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V050_FLUSH_DARKER_CROWNS_AND_RESTRAINED_ENDPOINT_CLEARANCE__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V050_CROWN_ENDPOINT_CALIBRATION__NOT_PROMOTED"
    ),
    "source_map": SOURCE,
    "map": TARGET,
    "calibrated": calibrated,
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
