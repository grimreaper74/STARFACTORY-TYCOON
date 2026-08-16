"""v096 adapter for the established PR-009 navigation validator."""
from pathlib import Path

adapter = Path(__file__).with_name("validate_press_shop_pr009_navigation_pie_v089.py")
code = adapter.read_text(encoding="utf-8").replace(
    "press_shop_pr009_transfer_guide_collision_v089_config",
    "press_shop_pr009_flow_axis_correction_v096_config")
exec(compile(code, str(adapter) + "::v096-flow-axis", "exec"), globals(), globals())

