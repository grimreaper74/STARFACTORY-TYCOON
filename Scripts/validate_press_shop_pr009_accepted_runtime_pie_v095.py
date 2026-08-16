"""Run the proven v089/v095 runtime validator on the accepted v095 map."""
from pathlib import Path

adapter = Path(__file__).with_name("validate_press_shop_pr009_in_map_pie_v089.py")
code = adapter.read_text(encoding="utf-8").replace(
    "press_shop_pr009_transfer_guide_collision_v089_config",
    "press_shop_pr009_accepted_v095_config")
token = 'exec(compile(code, str(base) + "::v089-release-collision", "exec"), globals(), globals())'
replacement = 'code = code.replace(\'f"PR009_InMap_{VERSION}"\', \'"PR009_Accepted_v095"\')\n' + token
if token not in code:
    raise RuntimeError("accepted runtime audit-path injection token missing")
code = code.replace(token, replacement, 1)
exec(compile(code, str(adapter) + "::accepted-v095", "exec"), globals(), globals())

