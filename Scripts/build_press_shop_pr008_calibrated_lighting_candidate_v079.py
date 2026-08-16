"""Build v079 from retained v077 using a calibrated low-intensity v078 lighting design."""
from pathlib import Path

base = Path(__file__).with_name("build_press_shop_pr008_reflection_environment_candidate_v078.py")
code = base.read_text(encoding="utf-8")
code = code.replace("ReflectionEnvironmentCandidate_v078", "CalibratedLightingCandidate_v079")
code = code.replace("Environment_v078", "CalibratedLighting_v079")
code = code.replace("reflection_environment_candidate_v078", "calibrated_lighting_candidate_v079")
code = code.replace("V078", "V079").replace("v078", "v079")
code = code.replace("(5.4, 5.9, 6.2)", "(0.55, 0.60, 0.64)")
code = code.replace('"intensity": 22000.0', '"intensity": 550.0')
code = code.replace("6200.0, (218, 232, 241)", "90.0, (218, 232, 241)")
code = code.replace("5200.0, (242, 226, 207)", "75.0, (242, 226, 207)")
code = code.replace('"brightness": 0.92', '"brightness": 0.78')
code = code.replace(
    'unreal.LinearColor(0.12, 0.15, 0.17, 1.0)',
    'unreal.LinearColor(0.06, 0.075, 0.085, 1.0)')
code = code.replace(
    "LOCAL_INDUSTRIAL_LIGHTING_REFLECTION_ENVIRONMENT_BUILT_FROM_RETAINED_V077",
    "CALIBRATED_LOW_INTENSITY_LIGHTING_BUILT_FROM_RETAINED_V077")
code = code.replace(
    "physical overhead luminaires, restrained camera fills and one local runtime reflection capture; v077 smooth materials unchanged",
    "physical overhead luminaires at 550 intensity, 90/75 camera fills and a restrained local reflection capture; v077 smooth materials unchanged")
exec(compile(code, str(base) + "::v079-calibrated-adapter", "exec"), globals(), globals())
