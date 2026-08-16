"""Run the final broad-area roof-bounce calibration directly from retained v242."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_scaled_broad_roof_bounce_candidate_v248.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v248", "v249").replace("V248", "V249")
code = code.replace('"intensity": 300.0', '"intensity": 900.0')
code = code.replace('"intensity_preview_only": 300.0', '"intensity_preview_only": 900.0')
code = code.replace("SCALED_BROAD", "FINAL_BROAD")
code = code.replace("scaled broad", "final broad")
code = code.replace("SCALED_BROAD", "FINAL_BROAD")
exec(compile(code, str(source) + "::v249", "exec"), globals(), globals())
