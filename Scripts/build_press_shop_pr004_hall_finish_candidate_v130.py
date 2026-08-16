"""Build v130 directly from retained v124 with the proven v031 cross-hall fill disabled."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr004_hall_finish_candidate_v119.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118"',
    'BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124"')
code = code.replace("v119", "v130").replace("V119", "V130")
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
for legacy_actor in actors_api.get_all_level_actors():
    if legacy_actor.get_actor_label() != "LB_PR004_V031_CHookCameraFill":
        continue
    legacy_component = legacy_actor.get_component_by_class(unreal.SpotLightComponent)
    if legacy_component is None:
        continue
    disabled_v031_camera_fill.append({
        "actor": legacy_actor.get_actor_label(),
        "old_intensity": float(legacy_component.get_editor_property("intensity"))})
    legacy_component.set_editor_property("affects_world", False)
    legacy_component.set_editor_property("intensity", 0.0)
    legacy_actor.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in legacy_actor.tags] +
        ["LB.Asset.Candidate.v130", "LB.Lighting.SupersededCrossHallCameraFillDisabled"])]

# Broad, low-intensity wall wash reveals installed structure without bleaching''')
code = code.replace(
    'if len(wall_wash) != 0:',
    'if len(disabled_v031_camera_fill) != 1:\n    failures.append(f"expected one v031 camera fill, found {len(disabled_v031_camera_fill)}")\nif len(wall_wash) != 0:')
code = code.replace(
    '"wall_wash_lights": wall_wash,',
    '"wall_wash_lights": wall_wash,\n    "disabled_v031_cross_hall_camera_fill": disabled_v031_camera_fill,')
code = code.replace(
    "NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT",
    "NONREPEATING_HALL_FINISH_AND_PROVEN_V031_CROSS_HALL_FILL_REMOVED")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
