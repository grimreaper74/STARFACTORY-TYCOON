"""Capture live PR-006 fixed views on the retained full-line v107 parent."""

from pathlib import Path

source = Path(__file__).with_name("capture_press_shop_pr005_live_hmi_runtime_v043.py")
code = source.read_text(encoding="utf-8")
needle = '    "v061": "/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061",'
code = code.replace(
    needle,
    needle + '\n    "v107": "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107",',
)
code = code.replace(
    '("v057", "v058", "v059", "v060", "v061")',
    '("v057", "v058", "v059", "v060", "v061", "v107")',
)
code = code.replace(
    '("v060", "v061")',
    '("v060", "v061", "v107")',
)
code = code.replace(
    'CANDIDATE == "v061"',
    'CANDIDATE in ("v061", "v107")',
)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
