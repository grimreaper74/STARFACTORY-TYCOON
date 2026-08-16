"""Capture adapter for the isolated PR-009 v089 release-collision candidate."""
from pathlib import Path

base = Path(__file__).with_name("capture_press_shop_pr009_layered_presentation_v085.py")
code = base.read_text(encoding="utf-8")
code = code.replace("/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085",
                    "/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089")
code = code.replace("LB_PR009_V085_", "LB_PR009_V089_")
code = code.replace("LB_PR009_V085_CAPTURE", "LB_PR009_V089_CAPTURE")
code = code.replace("v085_pr009_layered", "v089_pr009_transfer_guide_collision")
code = code.replace("press_shop_v085_pr009_layered_", "press_shop_v089_pr009_transfer_guide_collision_")
code = code.replace("layered v085", "transfer-guide-collision v089")
code = code.replace("V085", "V089").replace("v085", "v089")
exec(compile(code, str(base) + "::v089-release-collision-capture", "exec"), globals(), globals())
