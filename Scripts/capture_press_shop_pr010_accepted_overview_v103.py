"""Fresh accepted-map fixed overview adapter for PR-010 v103."""

from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr010_release_art_v103.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v103", "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103")
code = code.replace("LB_PR010_V103_CAPTURE", "LB_PR010_ACCEPTED_V103_CAPTURE")
code = code.replace("v103_pr010_release_art", "v103_pr010_accepted")
code = code.replace("press_shop_v103_pr010_", "press_shop_accepted_v103_pr010_")
code = code.replace("Cairnwell PR-010 v103 release-art candidate", "Cairnwell PR-010 accepted v103 baseline")
exec(compile(code, str(base) + "::accepted-v103", "exec"), globals(), globals())
