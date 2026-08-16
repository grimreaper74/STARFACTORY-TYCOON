"""Fresh successor after incomplete v214; never overwrites the failed package."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_corrected_front_end_cumulative_candidate_v214.py")
code = source.read_text(encoding="utf-8").replace("v214", "v215").replace("V214", "V215")
exec(compile(code, str(source) + "::v215", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})
