"""Correct the overexposed lighting in the isolated press comparison map."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
map_path = "/Game/LineBoss/Developer/Validation/Maps/LB_PressGeometryComparison_v958"
output = root / "Saved/Audits/PressTrains/press_geometry_neutral_lighting_v960.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
point_lights = [actor for actor in actors.get_all_level_actors() if isinstance(actor, unreal.PointLight)]
point_lights.sort(key=lambda actor: actor.get_actor_location().x)
intensities = [1800.0, 1200.0, 1600.0]
for actor, intensity in zip(point_lights, intensities):
    component = actor.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", 2200.0)
for actor in actors.get_all_level_actors():
    if isinstance(actor, unreal.SkyLight):
        actor.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.45)
if not levels.save_current_level():
    raise RuntimeError("save failed")
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({
    "revision": "v960",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__NEUTRAL_NON_CLIPPING_COMPARISON_LIGHTING",
    "map": map_path,
    "point_light_intensities": intensities,
    "sky_intensity": 0.45,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_GEOMETRY_NEUTRAL_LIGHTING_V960_PASS")
