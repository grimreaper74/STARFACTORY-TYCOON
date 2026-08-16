"""Run v273 fleet cycle through the operations console's physical hit targets."""
from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_control_room_support_fleet_pie_v269.py")
code = source.read_text(encoding="utf-8").replace("v269", "v273").replace("V269", "V273")
code = code.replace(
    "Audits/ControlRoom/control_room_support_fleet_pie_v273.json",
    "Audits/ControlRoom/control_room_support_fleet_physical_buttons_pie_v273.json")
code = code.replace(
    "cairnwell/audit/control-room-support-fleet-pie-v273/v1",
    "cairnwell/audit/control-room-support-fleet-physical-buttons-pie-v273/v1")
needle = 'phase = "wait_ready"\nselected = ""\nhandle = None\n'
replacement = '''phase = "wait_ready"
selected = ""
handle = None


def press(console, component_name):
    matches = [component for component in console.get_components_by_class(unreal.BoxComponent)
               if component.get_name() == component_name]
    if len(matches) != 1:
        raise RuntimeError(f"{component_name}: expected one physical hit target, found {len(matches)}")
    return bool(console.handle_component_interaction(matches[0]))
'''
if needle not in code:
    raise RuntimeError("physical helper insertion point changed")
code = code.replace(needle, replacement, 1)
for direct, physical in {
    "console.dispatch_selected_support_unit()": 'press(console, "BTN_SUPPORT_DISPATCH")',
    "console.recall_selected_support_unit()": 'press(console, "BTN_SUPPORT_RECALL")',
    "console.cycle_support_unit()": 'press(console, "BTN_SUPPORT_UNIT")',
}.items():
    if direct not in code:
        raise RuntimeError(f"missing call replacement: {direct}")
    code = code.replace(direct, physical)
code = code.replace(
    "CONTROL_ROOM_SUPPORT_FLEET_V273_DISPATCH_RECALL_AND_SELECTION_PASS__NOT_PROMOTED",
    "CONTROL_ROOM_SUPPORT_FLEET_V273_PHYSICAL_BUTTON_DISPATCH_RECALL_AND_SELECTION_PASS__NOT_PROMOTED")
code = code.replace("LINE_BOSS_CONTROL_ROOM_SUPPORT_FLEET_V273", "LINE_BOSS_CONTROL_ROOM_SUPPORT_FLEET_PHYSICAL_V273")
exec(compile(code, str(source) + "::physical-buttons-v273", "exec"), globals(), globals())
