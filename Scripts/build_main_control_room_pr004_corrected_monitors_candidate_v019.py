"""Build v019 from v018 with a fresh deterministic PR-004 control-room HMI."""

from pathlib import Path


SOURCE = Path(__file__).resolve().parent / "build_main_control_room_pr004_fresh_console_candidate_v016.py"
code = SOURCE.read_text(encoding="utf-8")
code = code.replace("v016", "v019")
code = code.replace("V016", "V019")
needle = 'code = code.replace("v009", "v019")'
replacement = needle + '\ncode = code.replace(\'BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008"\', \'BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCorrectedCandidate_v018"\')'
if needle not in code:
    raise RuntimeError("v016 version rewrite changed; refusing unverified v019 build")
code = code.replace(needle, replacement)
exec(compile(code, str(SOURCE) + "::v019", "exec"), globals(), globals())
