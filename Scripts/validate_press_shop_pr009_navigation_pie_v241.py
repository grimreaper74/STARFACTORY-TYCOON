"""v241 whole-shop adapter for the established PR009 navigation validator."""

from pathlib import Path


base = Path(__file__).with_name("validate_press_shop_pr009_navigation_pie.py")
code = base.read_text(encoding="utf-8").replace(
    "from press_shop_pr009_in_map_validation_config import TARGET_MAP",
    "from press_shop_pr009_whole_shop_v241_config import TARGET_MAP")
exec(compile(code, str(base) + "::whole-shop-v241", "exec"), globals(), globals())

