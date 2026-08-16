"""Fresh corrected-front-end cumulative successor after failed v214/v215."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_corrected_front_end_cumulative_candidate_v214.py")
code = source.read_text(encoding="utf-8").replace("v214", "v216").replace("V214", "V216")
exec(compile(code, str(source) + "::v216", "exec"), {
    "__name__": "__main__",
    "__file__": str(source),
})
