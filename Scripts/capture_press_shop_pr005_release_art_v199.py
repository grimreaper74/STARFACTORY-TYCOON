"""Capture one inherited fixed PR005 camera on release-art candidate v199."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr005_runtime_cage_infill_v196.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v196",
    "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v199",
)
code = code.replace("LB_PR005_V196_CAPTURE", "LB_PR005_V199_CAPTURE")
code = code.replace("LB_PR005_V196_CAM_", "LB_PR005_V197_CAM_")
code = code.replace(
    "ValidationScreenshots/PressShopIntegration/pr005_runtime_cage_infill_v196/pr005_v196_",
    "ValidationScreenshots/PressShopIntegration/pr005_release_art_v199/pr005_v199_",
)
code = code.replace("PR005 v196 capture timeout", "PR005 v199 capture timeout")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
