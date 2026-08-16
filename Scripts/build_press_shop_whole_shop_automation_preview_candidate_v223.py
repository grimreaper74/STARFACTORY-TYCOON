"""Correct v219's Python Rotator positional-order defect in a fresh successor."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_whole_shop_automation_preview_candidate_v219.py")
code = source.read_text(encoding="utf-8").replace("v219", "v223").replace("V219", "V223")

needle = '''def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def transform_record(actor):'''
replacement = '''def rot(value):
    return [float(value.pitch), float(value.yaw), float(value.roll)]


def make_rotator(pitch=0.0, yaw=0.0, roll=0.0):
    value = unreal.Rotator()
    value.set_editor_properties({"pitch": pitch, "yaw": yaw, "roll": roll})
    return value


def transform_record(actor):'''
if needle not in code:
    raise RuntimeError("v219 rotation-helper insertion point changed")
code = code.replace(needle, replacement, 1)

bad_record = 'rotation=unreal.Rotator(*record["rotation"]),'
good_record = 'rotation=make_rotator(*record["rotation"]),'
if bad_record not in code:
    raise RuntimeError("v219 record Rotator source changed")
code = code.replace(bad_record, good_record, 1)

bad_install = 'rotation=unreal.Rotator(0.0, spec["yaw"], 0.0),'
good_install = 'rotation=make_rotator(0.0, spec["yaw"], 0.0),'
if bad_install not in code:
    raise RuntimeError("v219 install Rotator source changed")
code = code.replace(bad_install, good_install, 1)

exec(compile(code, str(source) + "::correct-rotator-v223", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})

