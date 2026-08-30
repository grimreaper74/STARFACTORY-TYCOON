"""Fresh real-RHI baseline captures before the Press art-direction pass.

The proven v005 lane is executed verbatim with an isolated evidence root and
receipt identity.  It remains a runtime-only PIE capture: no map or Content
packages are saved.  Keeping the capture implementation identical makes the
before/after comparison about art direction rather than camera-tool drift.
"""

from pathlib import Path


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "Scripts/capture_native_press_shop_steam_photo_lane_v005.py"


if not SOURCE.is_file():
    raise RuntimeError("PRESS_ART_DIRECTION_BASELINE_FAIL: v005 capture lane is missing")


code = SOURCE.read_text(encoding="utf-8")
replacements = {
    "NativePressShopSteamPhotoLane_v005": "PressArtDirectionBaseline_v001",
    "press_shop_steam_photo_lane_v005": "press_art_direction_baseline_v001",
    "native-press-steam-photo-lane-v005": "press-art-direction-baseline-v001",
    "PASS__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "PASS__PRESS_ART_DIRECTION_BASELINE_V001",
    "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "FAIL__PRESS_ART_DIRECTION_BASELINE_V001",
    "PRESS_STEAM_PHOTO_LANE": "PRESS_ART_DIRECTION_BASELINE",
}
for before, after in replacements.items():
    code = code.replace(before, after)

exec(compile(code, str(SOURCE), "exec"), {"__name__": "__main__"})
