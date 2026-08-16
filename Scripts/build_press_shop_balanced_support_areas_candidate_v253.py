"""Build balanced structured support areas directly from retained v249."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_structured_support_areas_candidate_v251.py")
code = source.read_text(encoding="utf-8").replace("v251", "v253").replace("V251", "V253")
code = code.replace(
    'east_bay("PR040", "PR-040 QUARANTINE | TBC", 9900.0, -3200.0)',
    'east_bay("PR040", "PR-040 QUARANTINE | TBC", 9900.0, -3200.0, 1150.0, 780.0)'
)
code = code.replace('"intensity": 900.0, "attenuation_radius": 1200.0,',
                    '"intensity": 260.0, "attenuation_radius": 950.0,')
code = code.replace('"source_width": 340.0, "source_height": 180.0, "light_color": unreal.Color(205, 220, 225, 255), "cast_shadows": True',
                    '"source_width": 520.0, "source_height": 300.0, "light_color": unreal.Color(205, 220, 225, 255), "cast_shadows": False')
code = code.replace("structured_support_areas_build_v253", "balanced_support_areas_build_v253")
code = code.replace("structured-support-areas-build-v253", "balanced-support-areas-build-v253")
code = code.replace("PASS__STRUCTURED_SUPPORT_BAYS_ADDED_DIRECTLY_FROM_V249", "PASS__BALANCED_SUPPORT_BAYS_ADDED_DIRECTLY_FROM_V249")
exec(compile(code, str(source) + "::v253", "exec"), globals(), globals())
