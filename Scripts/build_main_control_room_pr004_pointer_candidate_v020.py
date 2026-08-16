"""Build v020 from v018 with the compiled pointer-hit PR-004 console."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_corrected_monitors_candidate_v019.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v019", "v020")
code = code.replace("V019", "V020")
exec(compile(code, str(SOURCE) + "::v020", "exec"), globals(), globals())
