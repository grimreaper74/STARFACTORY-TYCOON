"""Build v132 from retained v124 with floor-focused high-bay cones and v031 removed."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr004_hall_finish_candidate_v119.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"')
code = code.replace("v119", "v132").replace("V119", "V132")
code = code.replace('"v118_changed": False', '"v124_changed": False')
code = code.replace("(0.18, 0.19, 0.20), 0.86", "(0.21, 0.22, 0.23), 0.86")
code = code.replace("(0.075, 0.090, 0.105), 0.80", "(0.13, 0.15, 0.17), 0.80")
code = code.replace("(0.095, 0.115, 0.135), 0.54, 0.42", "(0.075, 0.095, 0.115), 0.54, 0.42")
code = code.replace(
    "for index, x in enumerate((-10000.0, -8200.0, -6400.0, -4600.0), start=1):",
    "for index, x in enumerate((), start=1):")
code = code.replace("if len(wall_wash) != 4:", "if len(wall_wash) != 0:")
code = code.replace("expected four wall-wash lights", "expected zero added wall-wash lights")
code = code.replace(
    "# Broad, low-intensity wall wash reveals installed structure without bleaching",
    '''disabled_v031_camera_fill = []
focused_high_bays = []
for legacy_actor in actors_api.get_all_level_actors():
    legacy_label = legacy_actor.get_actor_label()
    if legacy_label == "LB_PR004_V031_CHookCameraFill":
        legacy_component = legacy_actor.get_component_by_class(unreal.SpotLightComponent)
        if legacy_component is None:
            continue
        disabled_v031_camera_fill.append({
            "actor": legacy_label,
            "old_intensity": float(legacy_component.get_editor_property("intensity"))})
        legacy_component.set_editor_property("affects_world", False)
        legacy_component.set_editor_property("intensity", 0.0)
        legacy_actor.tags = [unreal.Name(value) for value in dict.fromkeys(
            [str(value) for value in legacy_actor.tags] +
            ["LB.Asset.Candidate.v132", "LB.Lighting.SupersededCrossHallCameraFillDisabled"])]
    elif legacy_label.startswith("LB_PR004_V041_Downlight_"):
        legacy_component = legacy_actor.get_component_by_class(unreal.SpotLightComponent)
        if legacy_component is None:
            continue
        old_intensity = float(legacy_component.get_editor_property("intensity"))
        old_inner = float(legacy_component.get_editor_property("inner_cone_angle"))
        old_outer = float(legacy_component.get_editor_property("outer_cone_angle"))
        old_radius = float(legacy_component.get_editor_property("attenuation_radius"))
        new_intensity = 800.0 if old_intensity <= 1000.0 else 1100.0
        legacy_component.set_editor_properties({
            "intensity": new_intensity,
            "attenuation_radius": 1900.0,
            "inner_cone_angle": 32.0,
            "outer_cone_angle": 50.0,
        })
        focused_high_bays.append({
            "actor": legacy_label,
            "old_intensity": old_intensity,
            "new_intensity": new_intensity,
            "old_inner_cone_deg": old_inner,
            "new_inner_cone_deg": 32.0,
            "old_outer_cone_deg": old_outer,
            "new_outer_cone_deg": 50.0,
            "old_attenuation_cm": old_radius,
            "new_attenuation_cm": 1900.0,
        })
        legacy_actor.tags = [unreal.Name(value) for value in dict.fromkeys(
            [str(value) for value in legacy_actor.tags] +
            ["LB.Asset.Candidate.v132", "LB.Lighting.FactoryHighBayFloorFocused"])]

# Broad, low-intensity wall wash reveals installed structure without bleaching''')
code = code.replace(
    'if len(wall_wash) != 0:',
    'if len(disabled_v031_camera_fill) != 1:\n    failures.append(f"expected one v031 camera fill, found {len(disabled_v031_camera_fill)}")\nif len(focused_high_bays) != 15:\n    failures.append(f"expected 15 v041 downlights, found {len(focused_high_bays)}")\nif len(wall_wash) != 0:')
code = code.replace(
    '"wall_wash_lights": wall_wash,',
    '"wall_wash_lights": wall_wash,\n    "disabled_v031_cross_hall_camera_fill": disabled_v031_camera_fill,\n    "floor_focused_v041_high_bays": focused_high_bays,')
code = code.replace(
    "NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT",
    "NONREPEATING_HALL_FINISH_WITH_V031_REMOVED_AND_FLOOR_FOCUSED_HIGH_BAYS")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
