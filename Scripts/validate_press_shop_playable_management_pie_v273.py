"""Run whole playable-management PIE against retained native-dock candidate v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_playable_management_pie_v260.py")
code = source.read_text(encoding="utf-8").replace("v260", "v273").replace("V260", "V273")
exec(compile(code, str(source) + "::v273", "exec"), globals(), globals())
