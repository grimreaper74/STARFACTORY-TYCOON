"""Restore retained movers and exact donor commissioning in a fresh v273 child."""
from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr006_pr008_motion_restore_candidate_v282.py")
code = source.read_text(encoding="utf-8").replace("v282", "v283").replace("V282", "V283")
commissioning = r'''
# Reapply the exact retained donor commissioning values omitted by the v222
# authority-only merge. These are copied from the preserved v061/v057/v074
# builders; no recipe, process value or safety authority is invented here.
station006 = stations["PR006"]
station006.set_control_power(True)
station006.set_guards_closed(True)
station006.set_strip_available(True)
station006.set_cassette_locked(True)
station006.set_drives_healthy(True)
station006.set_leveller_recipe(unreal.Name("L-1500-A"), 1.20, 1.15, 16.0)
if not station006.start_line():
    raise RuntimeError("retained PR006 commissioning refused")

station007 = stations["PR007"]
station007.set_control_power(True)
station007.set_guards_closed(True)
station007.set_strip_threaded(True)
station007.set_mist_extraction_healthy(True)
station007.set_fluid_levels(82.0, 76.0)
station007.set_filter_differential(0.34)
if not station007.start_line():
    raise RuntimeError("retained PR007 commissioning refused")

station008 = stations["PR008"]
station008.set_control_power(True)
station008.set_guards_closed(True)
station008.set_strip_available(True)
station008.set_strip_loop_percent(50.0)
station008.set_edge_tracking_deviation(0.0)
station008.set_feed_position_error(0.0)
station008.set_feed_servo_healthy(True)
station008.set_pre_punch_tool_healthy(True)
station008.set_press_shear_load(45.0)
station008.set_hydraulic_pressure(215.0)
station008.set_slug_chute_fill(12.0)
station008.set_scrap_bin_fill(18.0)
station008.set_blank_outfeed_clear(True)
station008.set_safety_circuit_healthy(True)
station008.set_blank_recipe(1450.0, 18.0)
station008.set_measured_cut_length(1450.0)
if not station008.execute_remote_command(
        unreal.LBPR008Command.START, unreal.Name("MW.MCR.PR008.CONSOLE"),
        unreal.Name("CW.MW.CONTROL_ROOM")):
    raise RuntimeError("retained PR008 commissioning refused")
'''
needle = 'if not levels.save_current_level():\n    raise RuntimeError("could not save v283")'
replacement = commissioning + '\n' + needle
if needle not in code:
    raise RuntimeError("v282 builder injection point changed")
code = code.replace(needle, replacement)
exec(compile(code, str(source) + "::v283", "exec"), globals(), globals())
