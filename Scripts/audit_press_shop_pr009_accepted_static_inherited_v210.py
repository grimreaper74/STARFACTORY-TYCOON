"""Run accepted PR-009 static authority audit on exact v210."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr009_enclosure_release_static_v095.py")
code = source.read_text(encoding="utf-8").replace(
    "press_shop_pr009_enclosure_release_v095_config",
    "press_shop_pr009_inherited_v210_config").replace(
    "Saved/Audits/PR009_InMap_v095/enclosure_release_static_audit.json",
    "Saved/Audits/PressShopIntegration/pr009_accepted_static_inherited_v210.json").replace(
    "LB_PR009_V095_", "LB_PR009_V096_")
exec(compile(code, str(source) + "::inherited-v210", "exec"), globals(), globals())
