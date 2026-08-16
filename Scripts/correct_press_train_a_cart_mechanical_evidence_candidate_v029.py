"""Create isolated v029 with readable mobile die carts and flush Cairnwell plates."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAReleaseEvidenceCandidate_v028"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainACartMechanicalEvidenceCandidate_v029"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_cart_mechanical_evidence_v029.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v029 from v028: {TARGET}")


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


def append_tags(actor, *new_tags):
    values = [str(tag) for tag in actor.tags]
    for value in new_tags:
        if value not in values:
            values.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in values])


cart_records = []
identity_plates = []
for index in range(2, 7):
    stage = f"S{index:02d}"
    cart = one(f"CA_MW_PTA_{stage}_DieCart")
    tooling = one(f"CA_MW_PTA_{stage}_DieCartToolingLoad")
    cart_before = cart.get_actor_location()
    tooling_before = tooling.get_actor_location()
    if abs(cart_before.z - tooling_before.z) > 0.1:
        raise RuntimeError(f"{stage} cart/tooling z mismatch before correction")

    corrected_z = 120.0
    cart.set_actor_location(unreal.Vector(cart_before.x, cart_before.y, corrected_z), False, False)
    tooling.set_actor_location(unreal.Vector(tooling_before.x, tooling_before.y, corrected_z), False, False)
    append_tags(cart, "LB.PressTrain.ReleaseDetail.DieCartRideHeightCorrected.v029")
    append_tags(tooling, "LB.PressTrain.ReleaseDetail.DieCartRideHeightCorrected.v029")

    # The release cart mesh has its service-side identity plate at local X=-2330 mm
    # and local Z=-150 mm. Its 180-degree placement makes this world +X.
    plate_location = unreal.Vector(cart_before.x + 235.2, cart_before.y, corrected_z - 15.0)
    plate = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, plate_location, unreal.Rotator(yaw=-90.0))
    plate.set_actor_label(f"CA_MW_PTA_{stage}_DieCartIdentityPlate_v029")
    plate.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated",
        "LB.PressTrain.ReleaseDetail.CartIdentityPlate",
        f"LB.PressTrain.ReleaseDetail.{stage}.CartIdentityPlate",
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v029", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    plate.text_render.set_text(f"CAIRNWELL  |  A-{stage}")
    plate.text_render.set_world_size(10.5)
    plate.text_render.set_text_render_color(unreal.Color(226, 232, 229, 255))
    plate.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    plate.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    plate.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    plate.text_render.set_editor_property("cast_shadow", False)
    identity_plates.append(plate.get_actor_label())
    cart_records.append({
        "stage": stage,
        "previous_z_cm": round(cart_before.z, 3),
        "corrected_z_cm": corrected_z,
        "wheel_bottom_estimate_cm": 47.0,
        "wheel_top_estimate_cm": 107.0,
        "deck_bottom_estimate_cm": 94.0,
        "tooling_pair_preserved": True,
    })

cart_camera = one("CA_MW_PTA_CAM_DieCartDetail")
camera_location = unreal.Vector(1260.0, 1050.0, 300.0)
camera_target = unreal.Vector(500.0, 1500.0, 105.0)
cart_camera.set_actor_location(camera_location, False, False)
cart_camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target), False)
cart_camera.camera_component.set_editor_property("field_of_view", 60.0)

scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v029" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v029")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(cart_records) != 5 or len(identity_plates) != 5 or scope_count != 157:
    failures.append(
        f"cardinality mismatch carts={len(cart_records)} plates={len(identity_plates)} scope={scope_count}")
if any(abs(record["previous_z_cm"] - 90.0) > 0.1 for record in cart_records):
    failures.append(f"unexpected inherited cart ride height: {cart_records}")
if not levels.save_current_level():
    failures.append("could not save v029 cart-mechanical-evidence candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-cart-mechanical-evidence-v029/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V029_FIVE_CARTS_PHYSICALLY_LIFTED_WITH_PAIRED_TOOLING_READABLE_WHEEL_ENVELOPE_AND_FLUSH_CAIRNWELL_PLATES__FRESH_PRO_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V029_CART_MECHANICAL_EVIDENCE__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET,
    "cart_records": cart_records, "identity_plates": identity_plates,
    "cart_camera_location_cm": [1260.0, 1050.0, 300.0],
    "cart_camera_target_cm": [500.0, 1500.0, 105.0],
    "cart_camera_fov_deg": 60.0,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
