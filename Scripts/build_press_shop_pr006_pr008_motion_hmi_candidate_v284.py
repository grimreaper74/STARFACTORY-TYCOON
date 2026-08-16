"""Restore retained PR006-PR008 movers, commissioning and live HMI rows."""
from pathlib import Path

source = Path(__file__).with_name("build_press_shop_pr006_pr008_motion_restore_candidate_v282.py")
code = source.read_text(encoding="utf-8").replace("v282", "v284").replace("V282", "V284")
code = code.replace("records = {}\nfor family, donor in DONORS.items():", "text_records = {}\nrecords = {}\nfor family, donor in DONORS.items():")
capture_needle = "    records[family] = rows\n\nif library.does_asset_exist(MAP):"
capture_replacement = r'''    text_rows = []
    for actor in actors_api.get_all_level_actors():
        label = actor.get_actor_label()
        if not isinstance(actor, unreal.TextRenderActor):
            continue
        if family not in label.upper() or "HMI_TEXT" not in label.upper():
            continue
        component = actor.text_render
        colour = component.get_editor_property("text_render_color")
        text_rows.append({
            "label": label, "location": vec(actor.get_actor_location()),
            "rotation": rot(actor.get_actor_rotation()), "scale": vec(actor.get_actor_scale3d()),
            "tags": [str(tag) for tag in actor.tags],
            "text": str(component.get_editor_property("text")),
            "world_size": float(component.get_editor_property("world_size")),
            "colour": [int(colour.r), int(colour.g), int(colour.b), int(colour.a)],
        })
    text_records[family] = text_rows
    records[family] = rows

if library.does_asset_exist(MAP):'''
if capture_needle not in code:
    raise RuntimeError("v282 donor-text capture point changed")
code = code.replace(capture_needle, capture_replacement)

save_needle = 'if not levels.save_current_level():\n    raise RuntimeError("could not save v284")'
restore_and_commission = r'''
# Restore the exact retained live HMI text actors omitted by the cumulative merge.
restored_hmi = {}
for family, rows in text_records.items():
    restored_hmi[family] = []
    for row in rows:
        actor = actors_api.spawn_actor_from_class(
            unreal.TextRenderActor, unreal.Vector(*row["location"]),
            unreal.Rotator(row["rotation"][2], row["rotation"][0], row["rotation"][1]))
        if actor is None:
            raise RuntimeError(f"could not restore HMI row {family}:{row['label']}")
        actor.set_actor_label(row["label"])
        actor.set_actor_scale3d(unreal.Vector(*row["scale"]))
        actor.tags = [unreal.Name(tag) for tag in row["tags"]] + [
            unreal.Name("LB.Integration.MotionRestore.v284"), unreal.Name("LB.Asset.Candidate.v284"),
            unreal.Name("LB.Asset.CandidateNotPromoted")]
        component = actor.text_render
        component.set_text(row["text"])
        component.set_world_size(row["world_size"])
        component.set_text_render_color(unreal.Color(*row["colour"]))
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("can_ever_affect_navigation", False)
        restored_hmi[family].append(row["label"])

# Reapply exact retained donor commissioning values; no new process data.
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
if save_needle not in code:
    raise RuntimeError("v282 save point changed")
code = code.replace(save_needle, restore_and_commission + "\n" + save_needle)
code = code.replace('"spawned_counts": {family: len(rows) for family, rows in spawned.items()},',
                    '"spawned_counts": {family: len(rows) for family, rows in spawned.items()},\n    "restored_hmi": restored_hmi,')
exec(compile(code, str(source) + "::v284", "exec"), globals(), globals())
