"""Capture the first live B_stylized Press Shop comparison set.

This preserves the proven v005 PIE camera lane, but changes only the evidence
identity and its required -0.50 exposure. The native photo helper now rejects
any other exposure while the B_stylized art-direction layer is active, so this
script cannot accidentally produce a misleading post-pass comparison.
"""

from pathlib import Path


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "Scripts/capture_native_press_shop_steam_photo_lane_v005.py"


if not SOURCE.is_file():
    raise RuntimeError("PRESS_B_STYLIZED_CAPTURE_FAIL: v005 capture lane is missing")


code = SOURCE.read_text(encoding="utf-8")
replacements = {
    "NativePressShopSteamPhotoLane_v005": "PressArtDirectionBStylized_v001",
    "press_shop_steam_photo_lane_v005": "press_art_direction_b_stylized_v001",
    "native-press-steam-photo-lane-v005": "press-art-direction-b-stylized-v001",
    "PASS__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "PASS__PRESS_B_STYLIZED_V001",
    "FAIL__NATIVE_PRESS_STEAM_PHOTO_CUTAWAY_PROBES": "FAIL__PRESS_B_STYLIZED_V001",
    "PRESS_STEAM_PHOTO_LANE": "PRESS_B_STYLIZED",
    "EXPOSURE_BIAS = -0.75": "EXPOSURE_BIAS = -0.50",
}
for before, after in replacements.items():
    if before not in code:
        raise RuntimeError(f"PRESS_B_STYLIZED_CAPTURE_FAIL: expected source token missing: {before}")
    code = code.replace(before, after)

exec(compile(code, str(SOURCE), "exec"), {"__name__": "__main__"})
