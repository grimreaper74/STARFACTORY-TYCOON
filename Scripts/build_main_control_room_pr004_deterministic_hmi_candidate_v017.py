"""Build v017 from clean v008 with a fresh deterministic PR-004 HMI console."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_fresh_console_candidate_v016.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v016", "v017")
code = code.replace("V016", "V017")
exec(compile(code, str(SOURCE) + "::v017", "exec"), globals(), globals())
