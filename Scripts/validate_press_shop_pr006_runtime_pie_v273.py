"""Run the retained PR006 runtime/save gate on exact whole-shop v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr006_runtime_pie_v213.py")
code = source.read_text(encoding="utf-8").replace("v213", "v273").replace("V213", "V273")
code = code.replace("CumulativeReleaseCandidate_v273", "PlayableManagementCandidate_v273")
exec(compile(code, str(source) + "::v273", "exec"), globals(), globals())
