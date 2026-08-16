"""Install retained native PR-006..PR-010 authorities into corrected v224."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_playable_management_candidate_v222.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v221", "v224").replace("V221", "V224")
code = code.replace("v222", "v225").replace("V222", "V225")
exec(compile(code, str(source) + "::v225", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})

