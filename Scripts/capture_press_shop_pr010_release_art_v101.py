"""v101 exact-map adapter for the fixed PR-010 release-art camera suite."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr010_detailed_runtime_v098.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098", "/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101")
code = code.replace("LB_PR010_V098_CAPTURE", "LB_PR010_V101_CAPTURE")
code = code.replace("v098_pr010_detailed_runtime", "v101_pr010_release_art")
code = code.replace("press_shop_v098_pr010_", "press_shop_v101_pr010_")
code = code.replace("Cairnwell PR-010 v098 detailed remote buffer", "Cairnwell PR-010 v101 release-art candidate")
code = code.replace("PR010_V098_CAPTURE_", "PR010_V101_CAPTURE_")
exec(compile(code, str(base) + "::v101", "exec"), globals(), globals())
