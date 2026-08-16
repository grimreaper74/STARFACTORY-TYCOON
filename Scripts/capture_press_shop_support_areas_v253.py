"""Capture closer operational fixed views of balanced v253 support areas."""

from pathlib import Path


source = Path(__file__).with_name("capture_press_shop_support_areas_v250.py")
code = source.read_text(encoding="utf-8").replace("v250", "v253").replace("V250", "V253")
old = '''VIEWS = {
    "north_west": ((-3000.0, 2600.0, 950.0), (-6100.0, 4500.0, 110.0), 53.0),
    "north_centre": ((5400.0, 2600.0, 950.0), (1100.0, 4500.0, 110.0), 58.0),
    "east_support": ((7200.0, 900.0, 1050.0), (9650.0, -1900.0, 110.0), 58.0),
}'''
new = '''VIEWS = {
    "north_west": ((-3600.0, 2900.0, 520.0), (-6500.0, 4550.0, 110.0), 47.0),
    "north_centre": ((2600.0, 2900.0, 520.0), (1100.0, 4550.0, 110.0), 48.0),
    "east_support": ((7600.0, -900.0, 650.0), (9700.0, -2000.0, 110.0), 49.0),
}'''
if old not in code:
    raise RuntimeError("v250 capture view block changed")
code = code.replace(old, new)
exec(compile(code, str(source) + "::v253", "exec"), globals(), globals())
