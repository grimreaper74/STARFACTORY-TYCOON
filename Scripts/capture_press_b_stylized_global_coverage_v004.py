"""Real-RHI coverage-footprint probe for the large OneFactory Press department.

The six-fixture B master is an isolated Paint-hall calibration.  Press tests
at 12,000 and 120,000 lm per fixture proved that changing only local intensity
leaves the large department black or clips local pools.  This reversible probe
keeps B's sun, sky, 5000 K response and fixed exposure, then temporarily
reactivates the pre-existing native OneFactory 5000 K RectLight authority at
its authored 800,000 lm.  It measures broad coverage footprint only; it does
not promote the authority as the final Press lighting solution.
"""

from pathlib import Path


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "Scripts/capture_native_press_shop_steam_photo_lane_v005.py"
AUTHORITY_TAGS = {
    "LB.OneFactory.Lighting.Authority.5000K.v001",
    "LB.OneFactory.Shell.v001",
    "LB.Provenance.NativeOnly",
    "LB.OneFactory.Environment",
}
AUTHORITY_LUMENS = 800_000.0


if not SOURCE.is_file():
    raise RuntimeError("PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: capture lane is missing")


code = SOURCE.read_text(encoding="utf-8")
replacements = {
    "NativePressShopSteamPhotoLane_v005": "PressBStylizedGlobalCoverage_v004",
    "press_shop_steam_photo_lane_v005": "press_b_stylized_global_coverage_v004",
    "native-press-steam-photo-lane-v005": "press-b-stylized-global-coverage-v004",
    "PASS__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "PASS__PRESS_B_GLOBAL_COVERAGE_V004",
    "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "FAIL__PRESS_B_GLOBAL_COVERAGE_V004",
    "PRESS_STEAM_PHOTO_LANE": "PRESS_B_GLOBAL_COVERAGE",
    "EXPOSURE_BIAS = -0.75": "EXPOSURE_BIAS = -0.50",
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(
            f"PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: source token missing: {before}"
        )
    code = code.replace(before, after)

injection = f'''
AUTHORITY_TAGS = {sorted(AUTHORITY_TAGS)!r}
AUTHORITY_LUMENS = {AUTHORITY_LUMENS!r}

SHOTS = ({{**SHOTS[0], "filename": "01_press_full_operator_global_coverage.png"}},)


def apply_global_coverage(world):
    candidates = []
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RectLight):
        tags = {{str(tag) for tag in actor.tags}}
        if all(tag in tags for tag in AUTHORITY_TAGS):
            candidates.append(actor)
    if len(candidates) != 1:
        raise RuntimeError(
            "PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: expected one exact map authority, found {{}}".format(
                len(candidates)
            )
        )
    component = candidates[0].get_component_by_class(unreal.RectLightComponent)
    if component is None:
        raise RuntimeError("PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: authority has no RectLightComponent")
    component.set_editor_property("intensity", AUTHORITY_LUMENS)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5000.0)
    component.set_visibility(True)
    return "map 5000 K authority temporarily active at {{:.0f}} lm for broad-coverage proof".format(
        AUTHORITY_LUMENS
    )

'''
marker = "try:\n    if RECEIPT.exists():"
if marker not in code:
    raise RuntimeError("PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: source start marker missing")
code = code.replace(marker, injection + marker, 1)

original = '''            lighting_reason = unreal.LBOneFactoryDevFactory.ensure_dev_lighting(world, 5.0)
            if lighting_reason is None:
                raise RuntimeError("Native runtime lighting setup was rejected")
            configure_photo_camera(world)'''
replacement = '''            lighting_reason = unreal.LBOneFactoryDevFactory.ensure_dev_lighting(world, 5.0)
            if lighting_reason is None:
                raise RuntimeError("Native runtime lighting setup was rejected")
            lighting_reason = str(lighting_reason) + "; " + apply_global_coverage(world)
            configure_photo_camera(world)'''
if original not in code:
    raise RuntimeError("PRESS_B_GLOBAL_COVERAGE_PROBE_FAIL: lighting hook marker missing")
code = code.replace(original, replacement, 1)

exec(compile(code, str(SOURCE), "exec"), {"__name__": "__main__"})
