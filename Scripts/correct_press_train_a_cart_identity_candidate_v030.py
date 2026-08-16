"""Create v030 with corrected die-cart plate typography and evidence framing."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACartMechanicalEvidenceCandidate_v029"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACartIdentityCandidate_v030"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_cart_identity_v030.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v030 from v029: {TARGET}")


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


plate_records = []
for index in range(2, 7):
    stage = f"S{index:02d}"
    plate = one(f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v029")
    plate.set_actor_label(f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v030")
    previous = plate.get_actor_location()
    corrected = unreal.Vector(previous.x, previous.y, 117.5)
    plate.set_actor_location(corrected, False, False)
    plate.text_render.set_text(f"CAIRNWELL  A-{stage}")
    plate.text_render.set_world_size(9.0)
    plate.text_render.set_text_render_color(unreal.Color(24, 36, 34, 255))
    plate.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    plate.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    values = [str(tag) for tag in plate.tags]
    if "LB.Asset.Candidate.v030" not in values:
        values.append("LB.Asset.Candidate.v030")
    values.append("LB.PressTrain.ReleaseDetail.CartIdentityPlateTypographyCorrected.v030")
    plate.set_editor_property("tags", [unreal.Name(value) for value in dict.fromkeys(values)])
    plate_records.append({
        "stage": stage, "previous_z_cm": round(previous.z, 3),
        "corrected_z_cm": 117.5, "text": f"CAIRNWELL  A-{stage}",
        "world_size": 9.0, "dark_text_on_light_plate": True,
    })

camera = one("CA_MW_PTA_CAM_DieCartDetail")
location = unreal.Vector(1400.0, 900.0, 260.0)
target = unreal.Vector(500.0, 1500.0, 108.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
camera.camera_component.set_editor_property("field_of_view", 66.0)

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v030" not in tags:
            tags.append("LB.Asset.Candidate.v030")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(plate_records) != 5 or scope_count != 157:
    failures.append(f"cardinality mismatch plates={len(plate_records)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v030 cart-identity candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-cart-identity-v030/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V030_DARK_CENTERED_CAIRNWELL_CART_PLATES_AND_LOWER_WIDER_MECHANICAL_EVIDENCE_CAMERA__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V030_CART_IDENTITY__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "plate_records": plate_records,
    "cart_camera_location_cm": [1400.0, 900.0, 260.0],
    "cart_camera_target_cm": [500.0, 1500.0, 108.0], "cart_camera_fov_deg": 66.0,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
