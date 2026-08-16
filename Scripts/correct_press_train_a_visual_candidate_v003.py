"""Create the isolated Train A v003 early visual correction from verified v002.

This pass deliberately preserves every v002 presentation-mesh transform and changes
only the evidence environment, identity facing and fixed-camera composition.  It is
an early visual-direction gate, not a promotion or production placement.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAFlowAxisCandidate_v002"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAVisualCandidate_v003"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_visual_correction_v003.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v003 from verified v002: {TARGET}")


def actor_by_label(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one actor labelled {label}, found {len(matches)}")
    return matches[0]


def add_tag(actor, value):
    values = [str(tag) for tag in actor.tags]
    if value not in values:
        values.append(value)
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in values])


# Lock the verified presentation transforms before touching evidence-only actors.
presentation = []
before = {}
for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    if isinstance(actor, unreal.StaticMeshActor) and "LB.PressTrain.TrainA.Isolated" in actor_tags and "LB.Validation.Environment" not in actor_tags:
        presentation.append(actor)
        transform = actor.get_actor_transform()
        before[actor.get_actor_label()] = {
            "location": [transform.translation.x, transform.translation.y, transform.translation.z],
            "rotation": [transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w],
            "scale": [transform.scale3d.x, transform.scale3d.y, transform.scale3d.z],
        }
        add_tag(actor, "LB.Asset.Candidate.v003")

# The v001 evidence rig was orders of magnitude too bright for the inherited layered
# Press Shop materials.  Keep local authored light positions but recalibrate their
# output to recover charcoal/green/steel hierarchy and remove white/cyan clipping.
sky = actor_by_label("CA_MW_PTA_IsolatedSky")
sky.get_editor_property("light_component").set_editor_property("intensity", 0.16)
directional = actor_by_label("CA_MW_PTA_IsolatedKey")
directional.get_editor_property("directional_light_component").set_editor_property("intensity", 0.42)
rect_lights = []
for index in range(1, 8):
    light = actor_by_label(f"CA_MW_PTA_IsolatedFill_{index:02d}")
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 140.0)
    component.set_light_color(unreal.LinearColor(0.50, 0.58, 0.56, 1.0))
    rect_lights.append(light.get_actor_label())

# The unmaterialled evidence floor dominated the frame.  Give it the established
# foundry-charcoal response without changing its verified evidence-only transform.
floor = actor_by_label("CA_MW_PTA_IsolatedEvidenceFloor")
floor_material_path = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085"
floor_material = library.load_asset(floor_material_path)
if floor_material is None:
    raise RuntimeError(f"Missing floor material: {floor_material_path}")
floor.static_mesh_component.set_material(0, floor_material)

# Text had been authored edge-on to the negative-X CCTV evidence side.  Face all
# Train A identity panels toward that side and preserve their content/positions.
identity_actors = []
for actor in actors_api.get_all_level_actors():
    actor_tags = {str(tag) for tag in actor.tags}
    if isinstance(actor, unreal.TextRenderActor) and "LB.PressTrain.TrainA.Isolated" in actor_tags:
        actor.set_actor_rotation(unreal.Rotator(yaw=180.0), False)
        add_tag(actor, "LB.Asset.Candidate.v003")
        identity_actors.append(actor.get_actor_label())


def set_camera(label, location, target, fov):
    actor = actor_by_label(label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_property("field_of_view", fov)
    add_tag(actor, "LB.Asset.Candidate.v003")


# Wider, lower three-quarter views make the seven-stage rhythm and lower process
# openings readable without the draw-stage clipping present in v002.
set_camera(
    "CA_MW_PTA_CAM_Hero",
    unreal.Vector(-2850.0, -1900.0, 1450.0),
    unreal.Vector(0.0, 2200.0, 430.0),
    54.0,
)
set_camera(
    "CA_MW_PTA_CAM_Overview",
    unreal.Vector(-4550.0, 2250.0, 4700.0),
    unreal.Vector(0.0, 2250.0, 350.0),
    56.0,
)
set_camera(
    "CA_MW_PTA_CAM_DrawStage",
    unreal.Vector(-2300.0, 250.0, 1150.0),
    unreal.Vector(0.0, 750.0, 390.0),
    52.0,
)

failures = []
if len(presentation) != 37:
    failures.append(f"expected 37 preserved presentation actors, found {len(presentation)}")
if len(rect_lights) != 7:
    failures.append(f"expected seven recalibrated fill lights, found {len(rect_lights)}")
if len(identity_actors) != 8:
    failures.append(f"expected eight corrected identity actors, found {len(identity_actors)}")

# Prove no presentation transform drift occurred in this evidence-only correction.
drift = []
for actor in presentation:
    transform = actor.get_actor_transform()
    after = {
        "location": [transform.translation.x, transform.translation.y, transform.translation.z],
        "rotation": [transform.rotation.x, transform.rotation.y, transform.rotation.z, transform.rotation.w],
        "scale": [transform.scale3d.x, transform.scale3d.y, transform.scale3d.z],
    }
    if after != before[actor.get_actor_label()]:
        drift.append(actor.get_actor_label())
if drift:
    failures.append(f"verified presentation transforms drifted: {drift}")

if not levels.save_current_level():
    failures.append("could not save v003 early visual candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-visual-correction-v003/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V003_EXPOSURE_IDENTITY_CAMERA_CORRECTION__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V003_EARLY_VISUAL_CORRECTION__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "preserved_presentation_actor_count": len(presentation),
    "presentation_transform_drift": drift,
    "recalibrated_rect_light_count": len(rect_lights),
    "corrected_identity_actor_count": len(identity_actors),
    "sky_intensity": 0.16,
    "directional_intensity": 0.42,
    "rect_light_intensity": 140.0,
    "floor_material": floor_material_path,
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
