"""Create v041 with seven explicit physical identity plate/text assemblies."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAPhysicalIdentityCandidate_v041"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_physical_identity_v041.json"
MAT25 = "/Game/LineBoss/Candidates/PressTrains/Shared/Materials_v025"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
plate_material = library.load_asset(f"{MAT25}/M_CA_MW_PT_TrainAAccentLayered_v025")
if cube is None or plate_material is None:
    raise RuntimeError("physical identity plate dependencies are missing")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v041 from v038: {TARGET}")

removed = []
for actor in list(actors_api.get_all_level_actors()):
    if "LB.PressTrain.EnclosedFacade.IntegratedIdentity" in {str(tag) for tag in actor.tags}:
        removed.append(actor.get_actor_label())
        actors_api.destroy_actor(actor)

specs = [
    ("S01", "LOAD", 0.0, 520.0), ("S02", "DRAW", 750.0, 825.0),
    ("S03", "FORM", 1500.0, 665.0), ("S04", "TRIM", 2250.0, 665.0),
    ("S05", "PIERCE", 3000.0, 665.0), ("S06", "RESTRIKE", 3750.0, 665.0),
    ("S07", "INSPECT", 4500.0, 565.0),
]
plates = []
texts = []
for stage, title, y_cm, z_cm in specs:
    plate = actors_api.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(-435.0, y_cm, z_cm), unreal.Rotator())
    plate.set_actor_label(f"CA_MW_PTA_{stage}_PhysicalIdentityPlate_v041")
    plate.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.Fixed.IntegratedIdentityPlate",
        f"LB.PressTrain.EnclosedFacade.{stage}.PhysicalIdentityPlate",
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v041", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    plate.static_mesh_component.set_static_mesh(cube)
    plate.static_mesh_component.set_material(0, plate_material)
    plate.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    plate.static_mesh_component.set_collision_profile_name(unreal.Name("NoCollision"))
    plate.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    plate.set_actor_scale3d(unreal.Vector(0.04, 1.05 if stage not in {"S06", "S07"} else 1.25, 0.36))
    plates.append(plate.get_actor_label())

    text = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(-439.0, y_cm, z_cm), unreal.Rotator(yaw=90.0))
    text.set_actor_label(f"CA_MW_PTA_{stage}_PhysicalIdentityText_v041")
    text.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.PressTrain.EnclosedFacade.IntegratedIdentity",
        f"LB.PressTrain.EnclosedFacade.{stage}.IntegratedIdentity",
        "LB.Brand.CairnwellAutomotive", "LB.Site.MoorcrossWorks",
        "LB.Asset.Candidate.v041", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    text.text_render.set_text(f"{stage}  {title}")
    text.text_render.set_world_size(20.0 if stage not in {"S06", "S07"} else 18.0)
    text.text_render.set_text_render_color(unreal.Color(232, 244, 240, 255))
    text.text_render.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    text.text_render.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    text.text_render.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    text.text_render.set_editor_property("cast_shadow", False)
    texts.append(text.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v041" not in tags:
            tags.append("LB.Asset.Candidate.v041")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(removed) != 7 or len(plates) != 7 or len(texts) != 7 or scope_count != 180:
    failures.append(
        f"cardinality mismatch removed={len(removed)} plates={len(plates)} texts={len(texts)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v041 physical-identity candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-physical-identity-v041/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V041_SEVEN_OPERATOR_SIDE_PHYSICAL_IDENTITY_PLATE_TEXT_ASSEMBLIES__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V041_PHYSICAL_IDENTITY__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "removed_inherited_text": removed,
    "physical_plates": plates, "integrated_texts": texts, "scope_actor_count": scope_count,
    "floating_validation_labels_added": False, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
