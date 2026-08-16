"""v088 adapter for the established PR-009 runtime navigation validator."""
from pathlib import Path
base = Path(__file__).with_name("validate_press_shop_pr009_navigation_pie.py")
code = base.read_text(encoding="utf-8").replace(
    "from press_shop_pr009_in_map_validation_config import TARGET_MAP",
    "from press_shop_pr009_trace_portal_clearance_v088_config import TARGET_MAP")
exec(compile(code, str(base) + "::v088-release-collision", "exec"), globals(), globals())
