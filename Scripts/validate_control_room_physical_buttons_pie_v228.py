"""Run the v228 management sequence through physical console button components."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v222.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v222", "physical-console-buttons-v228").replace("V222", "PHYSICAL_BUTTONS_V228")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_physical-console-buttons-v228",
    "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228")
code = code.replace(
    "Saved/Audits/PressShopIntegration/press_shop_playable_management_pie_physical-console-buttons-v228.json",
    "Saved/Audits/ControlRoom/control_room_physical_buttons_pie_v228.json")
needle = '''def enum_text(value):
    return str(value).split(".")[-1]
'''
replacement = '''def enum_text(value):
    return str(value).split(".")[-1]


def press(console, component_name):
    matches = [component for component in console.get_components_by_class(unreal.BoxComponent)
               if component.get_name() == component_name]
    if len(matches) != 1:
        raise RuntimeError(f"{component_name}: expected one physical hit target, found {len(matches)}")
    return bool(console.handle_component_interaction(matches[0]))
'''
if needle not in code:
    raise RuntimeError("button helper insertion point changed")
code = code.replace(needle, replacement, 1)
replacements = {
    "console.increase_quantity()": 'press(console, "BTN_QTY_UP")',
    "console.toggle_operating_mode()": 'press(console, "BTN_MODE")',
    "console.create_production_order()": 'press(console, "BTN_CREATE")',
    "console.start_or_resume_order()": 'press(console, "BTN_START")',
    "console.pause_order()": 'press(console, "BTN_PAUSE")',
    "console.stop_order()": 'press(console, "BTN_STOP")',
    "console.cycle_assigned_train()": 'press(console, "BTN_TRAIN")',
}
for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"physical button replacement missing: {old}")
    code = code.replace(old, new)
code = code.replace(
    "PASS__EXACT_MAP_RUNTIME_AUTHORITIES_CONSOLE_START_PAUSE_STOP_AND_TRAIN_ISOLATION__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "PASS__EXACT_MAP_PHYSICAL_CONSOLE_BUTTONS_CREATE_START_PAUSE_STOP_AND_TRAIN_SELECTION__NOT_PROMOTED")
exec(compile(code, str(source) + "::physical-buttons-v228", "exec"), globals(), globals())
