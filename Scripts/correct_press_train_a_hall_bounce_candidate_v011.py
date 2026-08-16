"""Create v011 with validation-only rear hall bounce lighting."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAInstalledHallCandidate_v010"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAHallBounceCandidate_v011"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_hall_bounce_v011.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v011 from preserved v010: {TARGET}")

lights = []
for index, y in enumerate((-200.0, 1400.0, 3000.0, 4600.0), start=1):
    actor = actors_api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(620.0, y, 720.0), unreal.Rotator())
    actor.set_actor_label(f"CA_MW_PTA_InstalledHallBounce_{index:02d}")
    actor.tags = [
        unreal.Name("LB.Validation.Environment"),
        unreal.Name("LB.Validation.Environment.InstalledHallBounce"),
        unreal.Name("LB.Asset.Candidate.v011"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    component = actor.get_editor_property("point_light_component")
    component.set_editor_property("intensity", 150.0)
    component.set_editor_property("attenuation_radius", 1050.0)
    component.set_editor_property("source_radius", 120.0)
    component.set_light_color(unreal.LinearColor(0.46, 0.52, 0.50, 1.0))
    lights.append(actor.get_actor_label())

failures = []
if len(lights) != 4:
    failures.append(f"expected four rear hall bounce lights, found {len(lights)}")
if not levels.save_current_level():
    failures.append("could not save v011 hall-bounce candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-hall-bounce-v011/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V011_FOUR_REAR_HALL_BOUNCE_LIGHTS_FOR_SILHOUETTE_SEPARATION__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V011_HALL_BOUNCE__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "hall_bounce_light_count": len(lights),
    "hall_bounce_light_intensity": 150.0,
    "validation_environment_only": True,
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
