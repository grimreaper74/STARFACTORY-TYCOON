"""Run the exact native PR-006 runtime/save gate on v208."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr006_runtime_pie_v061.py")
code = source.read_text(encoding="utf-8")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",
    "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
)
code = code.replace("press_shop_pr006_runtime_v061.json", "press_shop_pr006_runtime_v208.json")
code = code.replace("press-shop-pr006-runtime-v061", "press-shop-pr006-runtime-v208")
code = code.replace("PR006_V061", "PR006_V208")
exec(compile(code, str(source) + "::v208", "exec"), globals(), globals())
