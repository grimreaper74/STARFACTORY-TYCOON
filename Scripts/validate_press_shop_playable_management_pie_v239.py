"""Run the exact retained management gate against restored-machine child v239."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v233.py")
code = source.read_text(encoding="utf-8").replace("v233", "v239").replace("V233", "V239")
exec(compile(code, str(source) + "::v239", "exec"), globals(), globals())
