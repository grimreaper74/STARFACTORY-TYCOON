"""Restore only visible retained PR006-PR008 donor cells in a fresh v273 child."""
from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr006_pr008_complete_cell_candidate_v285.py")
wrapper = source.read_text(encoding="utf-8").replace("v285", "v286").replace("V285", "V286")
old = '''        is_station_static = f"LB.Station.{family}" in tags
        if (not is_station_static and not is_attached_mover and not is_pr008_direct) or actor.get_actor_label() in base_labels:
            continue'''
new = '''        is_station_static = f"LB.Station.{family}" in tags
        component_visible = bool(actor.static_mesh_component.get_editor_property("visible"))
        component_hidden_in_game = bool(actor.static_mesh_component.get_editor_property("hidden_in_game"))
        donor_visible = not actor.is_hidden_ed() and component_visible and not component_hidden_in_game
        if ((not is_station_static and not is_attached_mover and not is_pr008_direct)
                or actor.get_actor_label() in base_labels or not donor_visible):
            continue'''
if old not in wrapper:
    raise RuntimeError("v285 visible donor filter point changed")
wrapper = wrapper.replace(old, new, 1)
wrapper = wrapper.replace(
    '"repair_scope": "all absent donor station-scoped static actors plus retained HMI and commissioning"',
    '"repair_scope": "all visible absent donor station-scoped static actors plus retained HMI and commissioning"',
)
exec(compile(wrapper, str(source) + "::visible-complete-cell-v286", "exec"), globals(), globals())
