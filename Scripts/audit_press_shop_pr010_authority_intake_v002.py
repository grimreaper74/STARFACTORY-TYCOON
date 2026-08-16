"""Record PR-010 intake after yaw and accepted-parent resolution."""
from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr010_authority_intake_v001.py")
code = source.read_text(encoding="utf-8").replace(
    "pr010_authority_intake_v001.json", "pr010_authority_intake_v002.json").replace(
    "pr010-authority-intake-v001/v1", "pr010-authority-intake-v002/v1").replace(
    '"Confirm PR010 local-to-world rotation from accepted master-plan context.",',
    '"Resolved: accepted yaw -90 degrees maps local +Y flow to increasing world X.",')
exec(compile(code, str(source) + "::resolved-v002", "exec"), globals(), globals())
