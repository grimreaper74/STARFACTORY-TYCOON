"""Run the retained PR005 physical sequence gate on exact whole-shop v273."""
from pathlib import Path
source = Path(__file__).with_name("validate_press_shop_pr005_runtime_sequence_pie_v213.py")
code = source.read_text(encoding="utf-8").replace("v213", "v273").replace("V213", "V273")
code = code.replace("CumulativeReleaseCandidate_v273", "PlayableManagementCandidate_v273")
exec(compile(code, str(source) + "::v273", "exec"), {"__name__": "__main__", "__file__": str(source)})
