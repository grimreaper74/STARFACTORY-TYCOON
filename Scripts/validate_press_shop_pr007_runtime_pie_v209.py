"""Run the retained PR-007 runtime sequence on exact release-art v209."""

from pathlib import Path

source = Path(__file__).with_name("validate_press_shop_pr007_runtime_pie_v057.py")
code = source.read_text(encoding="utf-8")
code = code.replace("LB_PressShop_PR007RuntimeCandidate_v057", "LB_PressShop_PR007ReleaseArtCandidate_v209")
code = code.replace("v057", "v209").replace("V057", "V209")
code = code.replace("now - started > 35.0", "now - started > 60.0")
# The release-detail map has heavier rendering work, so do not sample the two
# slowly changing fluid levels on the first Running tick.  Preserve the exact
# checks and allow up to twenty seconds for both very low consumption values
# to move beyond reflected-float precision on this exact map.
needle = '''        if not all(checks):
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", f"running checks={checks}")
            return
'''
replacement = '''        if not all(checks):
            if now - phase_started < 20.0:
                return
            finish("RUNTIME_PR007_NATIVE_FAIL__NOT_PROMOTED", f"running checks={checks}")
            return
'''
if needle not in code:
    raise RuntimeError("PR007 v209 timing replacement source missing")
code = code.replace(needle, replacement)
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
