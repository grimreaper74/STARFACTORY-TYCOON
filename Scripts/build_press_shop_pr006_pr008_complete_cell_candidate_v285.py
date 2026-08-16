"""Restore complete retained PR006-PR008 donor cells in a fresh v273 child."""
from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr006_pr008_motion_hmi_candidate_v284.py")
wrapper = source.read_text(encoding="utf-8").replace("v284", "v285").replace("V284", "V285")
needle = 'exec(compile(code, str(source) + "::v285", "exec"), globals(), globals())'
replacement = r"""
# The authority-only cumulative merge omitted stationary housings, beds, guards,
# supports and service cabinets as well as movers. Capture every station-scoped
# donor StaticMeshActor whose exact label is absent from protected v273.
base_capture = '''if not levels.load_level(BASE):
    raise RuntimeError(BASE)
base_labels = {actor.get_actor_label() for actor in actors_api.get_all_level_actors()}

text_records = {}'''
code = code.replace("text_records = {}", base_capture, 1)
old_filter = '''        if not is_attached_mover and not is_pr008_direct:
            continue'''
new_filter = '''        is_station_static = f"LB.Station.{family}" in tags
        if (not is_station_static and not is_attached_mover and not is_pr008_direct) or actor.get_actor_label() in base_labels:
            continue'''
if old_filter not in code:
    raise RuntimeError("v284 donor filter changed")
code = code.replace(old_filter, new_filter, 1)
code = code.replace(
    '"existing_release_art_removed": 0,',
    '"existing_release_art_removed": 0,\n    "repair_scope": "all absent donor station-scoped static actors plus retained HMI and commissioning",',
)
exec(compile(code, str(source) + "::v285", "exec"), globals(), globals())
"""
if needle not in wrapper:
    raise RuntimeError("v284 execution point changed")
wrapper = wrapper.replace(needle, replacement)
exec(compile(wrapper, str(source) + "::complete-cell-v285-wrapper", "exec"), globals(), globals())
