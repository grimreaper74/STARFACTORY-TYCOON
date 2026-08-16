"""Run the v095 physical shell/door/portal audit on the accepted map."""
from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr009_enclosure_physical_pie_v095.py")
code = source.read_text(encoding="utf-8").replace(
    "press_shop_pr009_enclosure_release_v095_config",
    "press_shop_pr009_accepted_v095_config").replace(
    "Saved/Audits/PR009_InMap_v095/enclosure_physical_pie_audit.json",
    "Saved/Audits/PR009_Accepted_v095/enclosure_physical_pie_audit.json")
exec(compile(code, str(source) + "::accepted-v095", "exec"), globals(), globals())
