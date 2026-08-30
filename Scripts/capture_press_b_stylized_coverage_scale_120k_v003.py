"""One-shot real-RHI high-range coverage-scale probe for the Press hall.

The 12,000 lm v002 probe remained visually under-lit at the management
camera.  This retains v002 as evidence and tests the next rational bracket:
six fixtures at 120,000 lm, totalling 720,000 lm, close to the original
factory authority's 800,000 lm but retaining B_stylized's fixture locations,
sun, sky, exposure and 5000 K response.  It is a reversible evidence probe,
not a promoted lighting preset.
"""

from pathlib import Path


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "Scripts/capture_native_press_shop_steam_photo_lane_v005.py"
FIXTURE_LUMENS = 120_000.0
PRESS_B_TAG = "LB.OneFactory.PressBStylizedLighting"


if not SOURCE.is_file():
    raise RuntimeError("PRESS_B_SCALE_PROBE_FAIL: v005 capture lane is missing")


code = SOURCE.read_text(encoding="utf-8")
replacements = {
    "NativePressShopSteamPhotoLane_v005": "PressBStylizedCoverageScale120k_v003",
    "press_shop_steam_photo_lane_v005": "press_b_stylized_coverage_scale_120k_v003",
    "native-press-steam-photo-lane-v005": "press-b-stylized-coverage-scale-120k-v003",
    "PASS__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "PASS__PRESS_B_COVERAGE_SCALE_120K_V003",
    "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "FAIL__PRESS_B_COVERAGE_SCALE_120K_V003",
    "PRESS_STEAM_PHOTO_LANE": "PRESS_B_COVERAGE_SCALE_120K",
    "EXPOSURE_BIAS = -0.75": "EXPOSURE_BIAS = -0.50",
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(
            f"PRESS_B_SCALE_PROBE_FAIL: expected source token missing: {before}"
        )
    code = code.replace(before, after)

injection = f'''
# The B master is intentionally constructed first.  This probe then applies
# the next ceiling-height/covered-area bracket only in PIE.
FIXTURE_LUMENS = {FIXTURE_LUMENS!r}
PRESS_B_TAG = {PRESS_B_TAG!r}

SHOTS = ({{**SHOTS[0], "filename": "01_press_full_operator_scale_120k.png"}},)


def apply_coverage_scale(world):
    fixtures = [
        actor
        for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RectLight)
        if PRESS_B_TAG in [str(tag) for tag in actor.tags]
    ]
    if len(fixtures) != 6:
        raise RuntimeError(
            "PRESS_B_SCALE_PROBE_FAIL: expected six B fixtures, found {{}}".format(
                len(fixtures)
            )
        )
    for actor in fixtures:
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            raise RuntimeError("PRESS_B_SCALE_PROBE_FAIL: B fixture lacks RectLightComponent")
        component.set_editor_property("intensity", FIXTURE_LUMENS)
    return "B base 1200 lm scaled to {{:.0f}} lm per fixture for hall coverage".format(
        FIXTURE_LUMENS
    )

'''
marker = "try:\n    if RECEIPT.exists():"
if marker not in code:
    raise RuntimeError("PRESS_B_SCALE_PROBE_FAIL: source start marker missing")
code = code.replace(marker, injection + marker, 1)

original = '''            lighting_reason = unreal.LBOneFactoryDevFactory.ensure_dev_lighting(world, 5.0)
            if lighting_reason is None:
                raise RuntimeError("Native runtime lighting setup was rejected")
            configure_photo_camera(world)'''
replacement = '''            lighting_reason = unreal.LBOneFactoryDevFactory.ensure_dev_lighting(world, 5.0)
            if lighting_reason is None:
                raise RuntimeError("Native runtime lighting setup was rejected")
            lighting_reason = str(lighting_reason) + "; " + apply_coverage_scale(world)
            configure_photo_camera(world)'''
if original not in code:
    raise RuntimeError("PRESS_B_SCALE_PROBE_FAIL: lighting hook marker missing")
code = code.replace(original, replacement, 1)

exec(compile(code, str(SOURCE), "exec"), {"__name__": "__main__"})
