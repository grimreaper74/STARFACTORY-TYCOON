"""Run the retained management authority gate unchanged against lighting child v227."""

from pathlib import Path


source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v226.py")
code = source.read_text(encoding="utf-8").replace("v226", "v227").replace("V226", "V227")
exec(compile(code, str(source) + "::v227", "exec"), globals(), globals())
