"""Build collision-corrected structured support areas directly from v249."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_structured_support_areas_candidate_v251.py")
code = source.read_text(encoding="utf-8").replace("v251", "v252").replace("V251", "V252")
code = code.replace(
    'east_bay("PR040", "PR-040 QUARANTINE | TBC", 9900.0, -3200.0)',
    'east_bay("PR040", "PR-040 QUARANTINE | TBC", 9900.0, -3200.0, 1150.0, 780.0)'
)
exec(compile(code, str(source) + "::v252", "exec"), globals(), globals())
