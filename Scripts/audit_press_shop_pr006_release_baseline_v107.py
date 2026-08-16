"""Record the exact PR-006 baseline in retained full-line environment v107."""

from pathlib import Path

source = Path(__file__).with_name("audit_press_shop_pr006_release_baseline_v205.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v205", "v107").replace("V205", "V107")
code = code.replace(
    "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v107",
    "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107",
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
