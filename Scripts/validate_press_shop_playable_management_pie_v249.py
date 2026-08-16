"""Run the exact retained management gate against final broad-fill child v249."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v242.py")
code = source.read_text(encoding="utf-8").replace("v242", "v249").replace("V242", "V249")
exec(compile(code, str(source) + "::v249", "exec"), globals(), globals())
