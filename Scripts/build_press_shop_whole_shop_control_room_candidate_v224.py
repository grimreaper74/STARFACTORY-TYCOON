"""Add the walk-up console and concept task lighting to corrected v223."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_whole_shop_control_room_candidate_v220.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v219", "v223").replace("V219", "V223")
code = code.replace("v221", "v224").replace("V221", "V224")

needle = '''actors = actors_api.get_all_level_actors()
consoles = [a for a in actors if a.get_class().get_name() == "LBControlRoomOperationsConsole"]'''
replacement = '''# Localized neutral-white industrial task lighting makes the concept readable
# without altering the retained hall-light assets or claiming a final lux study.
task_lights = []
light_specs = [
    ("TRAIN_A", (3850.0, -4300.0, 1050.0), 18000.0, 1900.0),
    ("TRAIN_B", (3850.0, -2600.0, 1050.0), 18000.0, 1900.0),
    ("TRAIN_C", (3850.0, -900.0, 1050.0), 18000.0, 1900.0),
    ("TRAIN_D", (3850.0, 800.0, 1050.0), 18000.0, 1900.0),
    ("CONTROL", (2200.0, 4250.0, 475.0), 9000.0, 850.0),
]
for name, location, intensity, radius in light_specs:
    light = actors_api.spawn_actor_from_class(unreal.PointLight, unreal.Vector(*location), unreal.Rotator())
    if light is None:
        failures.append(f"could not spawn {name} concept task light")
        continue
    light.set_actor_label(f"LB_WHOLE_V224_LIGHT_{name}")
    light.point_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": radius,
        "light_color": unreal.Color(218, 232, 245, 255),
        "cast_shadows": False,
    })
    light.tags = [
        unreal.Name("LB.Lighting.IndustrialLED.Task"),
        unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
        unreal.Name("LB.Integration.WholeShopControlRoom.v224"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    task_lights.append(light.get_actor_label())

actors = actors_api.get_all_level_actors()
consoles = [a for a in actors if a.get_class().get_name() == "LBControlRoomOperationsConsole"]'''
if needle not in code:
    raise RuntimeError("control-room v221 light insertion point changed")
code = code.replace(needle, replacement, 1)

needle_payload = '''"press_train_authority_count": len(trains),
    "console_location_cm":'''
replacement_payload = '''"press_train_authority_count": len(trains),
    "preview_task_lights": task_lights,
    "console_location_cm":'''
if needle_payload not in code:
    raise RuntimeError("control-room v221 payload insertion point changed")
code = code.replace(needle_payload, replacement_payload, 1)

exec(compile(code, str(source) + "::v224", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})

