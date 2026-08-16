"""Build v123 directly from v118 with one coherent broad-area hall light rig."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr004_hall_finish_candidate_v119.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v119", "v123").replace("V119", "V123")
code = code.replace("(0.18, 0.19, 0.20), 0.86", "(0.19, 0.20, 0.21), 0.86")
code = code.replace("(0.075, 0.090, 0.105), 0.80", "(0.11, 0.13, 0.15), 0.80")
code = code.replace("(0.095, 0.115, 0.135), 0.54, 0.42", "(0.075, 0.095, 0.115), 0.54, 0.42")
code = code.replace("for index, x in enumerate((-10000.0, -8200.0, -6400.0, -4600.0), start=1):",
                    "for index, x in enumerate((), start=1):")
code = code.replace("if len(wall_wash) != 4:", "if len(wall_wash) != 0:")
code = code.replace("expected four wall-wash lights", "expected zero wall-wash lights")
code = code.replace("# Broad, low-intensity wall wash reveals installed structure without bleaching",
'''disabled_legacy_lights = []
for legacy_actor in actors_api.get_all_level_actors():
    legacy_label = legacy_actor.get_actor_label()
    legacy_component = None
    if legacy_label.startswith("LB_INT_FRONT_FactoryFill_"):
        legacy_component = legacy_actor.get_component_by_class(unreal.PointLightComponent)
    elif legacy_label.startswith("LB_PR004_V041_Downlight_"):
        legacy_component = legacy_actor.get_component_by_class(unreal.SpotLightComponent)
    if legacy_component is None:
        continue
    disabled_legacy_lights.append({"actor": legacy_label,
                                   "old_intensity": float(legacy_component.get_editor_property("intensity"))})
    legacy_component.set_editor_property("affects_world", False)
    legacy_component.set_editor_property("intensity", 0.0)
    legacy_actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in legacy_actor.tags] +
        ["LB.Asset.Candidate.v123", "LB.Lighting.SupersededGridDisabled"])]

broad_hall_lights = []
for row_y in (-4300.0, -1200.0):
    for x in (-10000.0, -8200.0, -6400.0, -4600.0, -3000.0):
        index = len(broad_hall_lights) + 1
        broad = actors_api.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(x, row_y, 1640.0), unreal.Rotator(-90.0, 0.0, 0.0))
        broad.set_actor_label(f"LB_PR004_V123_BroadHallRect_{index:02d}")
        broad_component = broad.get_component_by_class(unreal.RectLightComponent)
        broad_component.set_editor_properties({
            "intensity": 7.0,
            "source_width": 1250.0,
            "source_height": 120.0,
            "attenuation_radius": 2100.0,
            "cast_shadows": False,
            "light_color": unreal.Color(210, 222, 228, 255),
        })
        broad.tags = [unreal.Name(value) for value in (
            "LB.Asset.Candidate.v123", "LB.Asset.CandidateNotPromoted",
            "LB.Lighting.HallContinuousAmbient", "LB.Environment.HallFinish.v123")]
        broad_hall_lights.append(broad.get_actor_label())

# Broad, low-intensity wall wash reveals installed structure without bleaching''')
code = code.replace('"wall_wash_lights": wall_wash,',
                    '"wall_wash_lights": wall_wash,\n    "disabled_legacy_light_grid": disabled_legacy_lights,\n    "broad_hall_rect_lights": broad_hall_lights,')
code = code.replace("NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT",
                    "NONREPEATING_HALL_FINISH_AND_COHERENT_RECT_LIGHT_RIG_BUILT")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
