"""Adapt the v095 shell/door/portal physical validator to v096."""
from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr009_enclosure_physical_pie_v095.py")
code = source.read_text(encoding="utf-8").replace(
    "press_shop_pr009_enclosure_release_v095_config",
    "press_shop_pr009_flow_axis_correction_v096_config").replace(
    "Saved/Audits/PR009_InMap_v095/", "Saved/Audits/PR009_InMap_v096/").replace(
    "V095", "V096")
exec(compile(code, str(source) + "::v096-flow-axis", "exec"), globals(), globals())
