"""Build v121 directly from v118; correct hall materials without wall hotspots."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr004_hall_finish_candidate_v119.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v119", "v121").replace("V119", "V121")
code = code.replace("(0.18, 0.19, 0.20), 0.86", "(0.21, 0.22, 0.23), 0.86")
code = code.replace("(0.075, 0.090, 0.105), 0.80", "(0.13, 0.15, 0.17), 0.80")
code = code.replace("(0.095, 0.115, 0.135), 0.54, 0.42", "(0.075, 0.095, 0.115), 0.54, 0.42")
code = code.replace("for index, x in enumerate((-10000.0, -8200.0, -6400.0, -4600.0), start=1):",
                    "for index, x in enumerate((), start=1):")
code = code.replace("if len(wall_wash) != 4:", "if len(wall_wash) != 0:")
code = code.replace("expected four wall-wash lights", "expected zero added wall-wash lights")
code = code.replace("NONREPEATING_HALL_FINISH_AND_WALL_WASH_BUILT", "NONREPEATING_HALL_FINISH_WITH_PROVEN_LIGHT_RIG_RETAINED")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
