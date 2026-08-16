"""Capture adapter for the isolated PR-009 v087 release-collision candidate."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr009_layered_presentation_v085.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085",
                    "/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087")
code = code.replace("LB_PR009_V085_", "LB_PR009_V087_")
code = code.replace("LB_PR009_V085_CAPTURE", "LB_PR009_V087_CAPTURE")
code = code.replace("v085_pr009_layered", "v087_pr009_release_collision")
code = code.replace("press_shop_v085_pr009_layered_", "press_shop_v087_pr009_release_collision_")
code = code.replace("layered v085", "release-collision v087")
code = code.replace("V085", "V087").replace("v085", "v087")
exec(compile(code, str(base) + "::v087-release-collision-capture", "exec"), globals(), globals())
