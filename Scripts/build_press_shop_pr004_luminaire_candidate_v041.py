"""Convert omnidirectional roof blooms into a directed factory light grid."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_pr004_luminaire_candidate_v041.json"
PREFIX = "LB_PR004_V041_"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors.destroy_actor(actor)

source_rows = []
downlights = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith("LB_INT_FRONT_FactoryFill_"):
        continue
    point = actor.get_component_by_class(unreal.PointLightComponent)
    if point is None:
        continue
    old_intensity = float(point.get_editor_property("intensity"))
    point.set_editor_properties({"intensity": 100.0, "attenuation_radius": 1450.0, "cast_shadows": False})
    location = actor.get_actor_location()
    number = int(label.rsplit("_", 1)[-1])
    downlight = actors.spawn_actor_from_class(
        unreal.SpotLight, unreal.Vector(location.x, location.y, location.z - 35.0), unreal.Rotator())
    downlight.set_actor_label(f"{PREFIX}Downlight_{number:02d}")
    downlight.tags = [unreal.Name("LB.Lighting.Candidate"), unreal.Name("LB.Lighting.FactoryDownlight"),
                      unreal.Name("LB.Asset.Candidate.v041"), unreal.Name("LB.Asset.CandidateNotPromoted")]
    downlight.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        downlight.get_actor_location(), unreal.Vector(location.x, location.y, 40.0)), False)
    intensity = 1300.0 if number in (8, 9, 10, 11, 12, 14, 15) else 950.0
    downlight.spot_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": 2250.0,
        "inner_cone_angle": 42.0,
        "outer_cone_angle": 72.0,
        "source_radius": 85.0,
        "soft_source_radius": 170.0,
        "cast_shadows": False,
        "light_color": unreal.Color(218, 230, 244, 255),
    })
    source_rows.append({"actor": label, "old_intensity": old_intensity, "new_ambient_intensity": 100.0})
    downlights.append(downlight.get_actor_label())

if len(source_rows) != 15 or len(downlights) != 15:
    raise RuntimeError(f"Unexpected factory grid sources={len(source_rows)} downlights={len(downlights)}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save {MAP}")

payload = {
    "$schema": "line-boss/audit/press-shop-pr004-luminaire-candidate-v041/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "DIRECTED_FACTORY_DOWNLIGHT_GRID_BUILT__FRESH_VISUAL_AND_TECHNICAL_REGATES_REQUIRED__NOT_PROMOTED",
    "base_map": "/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040",
    "map": MAP,
    "omnidirectional_sources_reduced": source_rows,
    "directed_downlight_count": len(downlights),
    "new_lights_cast_shadows": False,
    "geometry_or_authority_changed": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_LUMINAIRE_V041_BUILD_PASS downlights={len(downlights)}")
unreal.SystemLibrary.quit_editor()
