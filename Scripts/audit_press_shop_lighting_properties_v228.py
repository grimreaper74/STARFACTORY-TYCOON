"""Read-only lighting property snapshot for v228 visual tuning."""

import json
from pathlib import Path

import unreal


MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_lighting_properties_v228.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

records = []
for actor in actors_api.get_all_level_actors():
    class_name = actor.get_class().get_name()
    component = None
    properties = {}
    if class_name == "RectLight":
        component = actor.rect_light_component
        names = ["intensity", "attenuation_radius", "source_width", "source_height", "light_color", "cast_shadows"]
    elif class_name == "SpotLight":
        component = actor.spot_light_component
        names = ["intensity", "attenuation_radius", "inner_cone_angle", "outer_cone_angle", "light_color", "cast_shadows"]
    elif class_name == "PointLight":
        component = actor.point_light_component
        names = ["intensity", "attenuation_radius", "light_color", "cast_shadows"]
    elif class_name == "SkyLight":
        component = actor.light_component
        names = ["intensity", "light_color", "cast_shadows", "real_time_capture"]
    elif class_name == "DirectionalLight":
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        names = ["intensity", "light_color", "cast_shadows"]
    else:
        continue
    for name in names:
        try:
            properties[name] = str(component.get_editor_property(name))
        except Exception as exc:
            properties[name] = f"UNREADABLE:{exc}"
    location = actor.get_actor_location()
    records.append({
        "label": actor.get_actor_label(), "class": class_name,
        "location_cm": [location.x, location.y, location.z], "properties": properties,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.SystemLibrary.quit_editor()
