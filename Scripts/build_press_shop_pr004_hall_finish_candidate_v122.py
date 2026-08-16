"""Build v122 directly from v118 with obsolete point-fill hotspots removed."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr004_hall_finish_candidate_v119.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v119", "v122").replace("V119", "V122")
code = code.replace("(0.18, 0.19, 0.20), 0.86", "(0.21, 0.22, 0.23), 0.86")
code = code.replace("(0.075, 0.090, 0.105), 0.80", "(0.13, 0.15, 0.17), 0.80")
code = code.replace("(0.095, 0.115, 0.135), 0.54, 0.42", "(0.075, 0.095, 0.115), 0.54, 0.42")
code = code.replace("for index, x in enumerate((-10000.0, -8200.0, -6400.0, -4600.0), start=1):",
                    "for index, x in enumerate((), start=1):")
code = code.replace("if len(wall_wash) != 4:", "if len(wall_wash) != 0:")
code = code.replace("expected four wall-wash lights", "expected zero added wall-wash lights")
code = code.replace("# Broad, low-intensity wall wash reveals installed structure without bleaching",
'''legacy_fill_changes = []
for legacy_actor in actors_api.get_all_level_actors():
    legacy_label = legacy_actor.get_actor_label()
    if not legacy_label.startswith("LB_INT_FRONT_FactoryFill_"):
        continue
    legacy_component = legacy_actor.get_component_by_class(unreal.PointLightComponent)
    if legacy_component is None:
        continue
    legacy_fill_changes.append({"actor": legacy_label,
                                "old_intensity": float(legacy_component.get_editor_property("intensity"))})
    legacy_component.set_editor_property("affects_world", False)
    legacy_component.set_editor_property("intensity", 0.0)
    legacy_actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in legacy_actor.tags] +
        ["LB.Asset.Candidate.v122", "LB.Lighting.SupersededPointFillDisabled"])]

# Broad, low-intensity wall wash reveals installed structure without bleaching''')
code = code.replace('"wall_wash_lights": wall_wash,',
                    '"wall_wash_lights": wall_wash,\n    "disabled_legacy_factory_point_fills": legacy_fill_changes,')
code = code.replace("NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT",
                    "NONREPEATING_HALL_FINISH_AND_LEGACY_POINT_HOTSPOTS_REMOVED")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
