"""Run PR009 integrated navigation against retained-lighting v288."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr009_integrated_navigation_pie_v287.py")
code = source.read_text(encoding="utf-8").replace("v287", "v288").replace("V287", "V288")
exec(compile(code, str(source) + "::v288", "exec"), globals(), globals())
