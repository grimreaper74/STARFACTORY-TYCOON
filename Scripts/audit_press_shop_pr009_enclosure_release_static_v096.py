"""Adapt the v095 enclosure audit to the isolated v096 flow-axis candidate."""
from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr009_enclosure_release_static_v095.py")
code = source.read_text(encoding="utf-8").replace(
    "press_shop_pr009_enclosure_release_v095_config",
    "press_shop_pr009_flow_axis_correction_v096_config").replace(
    "Saved/Audits/PR009_InMap_v095/", "Saved/Audits/PR009_InMap_v096/").replace(
    "LB_PR009_V095_", "LB_PR009_V096_")
exec(compile(code, str(source) + "::v096-flow-axis", "exec"), globals(), globals())

