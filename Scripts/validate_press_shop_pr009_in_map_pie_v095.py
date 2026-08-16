"""v095 adapter for the established PR-009 process/motion/save/authority PIE validator."""
from pathlib import Path

adapter = Path(__file__).with_name("validate_press_shop_pr009_in_map_pie_v089.py")
code = adapter.read_text(encoding="utf-8").replace(
    "press_shop_pr009_transfer_guide_collision_v089_config",
    "press_shop_pr009_enclosure_release_v095_config")
exec(compile(code, str(adapter) + "::v095-enclosure-release", "exec"), globals(), globals())

