"""Run whole playable-management PIE against visible complete-cell v287."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v273.py")
code = source.read_text(encoding="utf-8").replace("v273", "v287").replace("V273", "V287")
exec(compile(code, str(source) + "::v287", "exec"), globals(), globals())
