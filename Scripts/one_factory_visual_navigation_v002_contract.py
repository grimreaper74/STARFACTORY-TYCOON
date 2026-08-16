"""Frozen, Unreal-independent contract for OneFactory visual/navigation v002.

This module contains only deterministic data, hashing and PNG inspection.  It
is intentionally importable by normal CPython so the offline tests can verify
the exact same visual gates used by the later Unreal real-RHI validator.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import struct
from typing import Any, Iterator
import zlib


SOURCE_MAP = (
    "/Game/LineBoss/Factory/OneFactory/v001/Maps/"
    "LB_MoorcrossWorks_OneFactory_v001"
)
SOURCE_MAP_OBJECT = f"{SOURCE_MAP}.{SOURCE_MAP.rsplit('/', 1)[-1]}"
SOURCE_MAP_RELATIVE = (
    "Content/LineBoss/Factory/OneFactory/v001/Maps/"
    "LB_MoorcrossWorks_OneFactory_v001.umap"
)
SOURCE_MAP_SHA256 = (
    "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682"
)

TARGET_MAP = (
    "/Game/LineBoss/Factory/OneFactory/v002/Maps/"
    "LB_MoorcrossWorks_OneFactory_v002"
)
TARGET_MAP_OBJECT = f"{TARGET_MAP}.{TARGET_MAP.rsplit('/', 1)[-1]}"
TARGET_MAP_RELATIVE = (
    "Content/LineBoss/Factory/OneFactory/v002/Maps/"
    "LB_MoorcrossWorks_OneFactory_v002.umap"
)

V001_VALIDATOR_RELATIVE = "Scripts/validate_one_factory_shell_v001.py"
V001_VALIDATOR_SHA256 = (
    "2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61"
)
VISUAL_STANDARD_RELATIVE = "Docs/LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md"
VISUAL_STANDARD_SHA256 = (
    "0E61306C437BCB587C82D6BF5609CAFDA1211E004CCFC86C6C4608CBA42A2971"
)

# These maps remain fixed authorities.  Body/Paint, Config, Source, all other
# Content and every .sav are snapshotted at runner start and compared again at
# every checkpoint, because the shared Paint lane may legitimately settle
# before this deferred successor is run.
STATIC_PROTECTED_HASHES = {
    SOURCE_MAP_RELATIVE: SOURCE_MAP_SHA256,
    "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap":
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap":
        "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    VISUAL_STANDARD_RELATIVE: VISUAL_STANDARD_SHA256,
    V001_VALIDATOR_RELATIVE: V001_VALIDATOR_SHA256,
}

OLD_LIGHT_LABEL = "LB_OF_ENV_LightingAuthority_5000K_v001"
OLD_EXPOSURE_LABEL = "LB_OF_ENV_FixedExposureAuthority_v001"
EXPOSURE_LABEL = "LB_OF_ENV_FixedExposureAuthority_v002"
SUN_LABEL = "LB_OF_ENV_CommonSunAuthority_v002"
SKY_LABEL = "LB_OF_ENV_CommonSkyAuthority_v002"
RECAST_LABEL = "RecastNavMesh-Default"
FLOOR_HISM_LABEL = "LB_OF_ENV_HISM_FloorSlabs_v001"

MAP_TAG = "LB.OneFactory.VisualNavigation.v002"
NATIVE_TAG = "LB.Provenance.NativeOnly"
ENVIRONMENT_TAG = "LB.OneFactory.Environment"
HIGH_BAY_GRID_TAG = "LB.OneFactory.Lighting.HighBayGrid.v002"
LIGHT_AUTHORITY_TAG = "LB.OneFactory.Lighting.Authority.5000K.v002"
FIXED_EXPOSURE_TAG = "LB.OneFactory.Lighting.FixedExposure.v002"
COMMON_SUN_TAG = "LB.OneFactory.Lighting.CommonSun.v002"
COMMON_SKY_TAG = "LB.OneFactory.Lighting.CommonSky.v002"
PERFORMANCE_TAG = "LB.OneFactory.Lighting.NoShadowPerformance.v002"
NAVIGATION_TAG = "LB.OneFactory.Navigation.Built.v002"

# Eight columns x four rows cover the 620 m x 310 m hall.  The 75 m x 70 m
# pitch deliberately keeps the no-shadow movable light overlap bounded while
# the 42 m x 7 m emitting faces retain a readable high-bay rhythm.
HIGH_BAY_X_CM = (
    -26_250.0, -18_750.0, -11_250.0, -3_750.0,
    3_750.0, 11_250.0, 18_750.0, 26_250.0,
)
HIGH_BAY_Y_CM = (-10_500.0, -3_500.0, 3_500.0, 10_500.0)
HIGH_BAY_Z_CM = 2_700.0
HIGH_BAY_INTENSITY_LM = 48_000.0
HIGH_BAY_ATTENUATION_CM = 6_000.0
HIGH_BAY_SOURCE_WIDTH_CM = 4_200.0
HIGH_BAY_SOURCE_HEIGHT_CM = 700.0
HIGH_BAY_TEMPERATURE_K = 5_000.0
HIGH_BAY_COUNT = len(HIGH_BAY_X_CM) * len(HIGH_BAY_Y_CM)

SUN_INTENSITY = 0.30
SKY_INTENSITY = 0.20
FIXED_EXPOSURE_MIN = 1.0
FIXED_EXPOSURE_MAX = 1.0
FIXED_EXPOSURE_BIAS = -0.50

# These are management/player routes across the unchanged canonical datums.
NAVIGATION_PROBES = (
    ("logistics_spine_west_east", (-28_000.0, 0.0, 80.0),
     (28_000.0, 0.0, 80.0)),
    ("service_spine_west_east", (-28_000.0, -14_000.0, 80.0),
     (28_000.0, -14_000.0, 80.0)),
    ("press_to_body", (-14_500.0, 8_000.0, 80.0),
     (-11_000.0, -8_500.0, 80.0)),
    ("body_to_paint", (-11_000.0, -8_500.0, 80.0),
     (10_000.0, -8_500.0, 80.0)),
    ("paint_to_assembly", (10_000.0, -8_500.0, 80.0),
     (16_500.0, 8_500.0, 80.0)),
)
NAVIGATION_PROJECT_EXTENT_CM = (500.0, 500.0, 500.0)

SCREENSHOT_SIZE = (1_920, 1_080)
MINIMUM_SCREENSHOT_BYTES = 500_000
SCREENSHOT_NAMES = (
    "01_empty_factory_overview.png",
    "02_populated_press_bay.png",
    "03_body_bay.png",
    "04_paint_bay.png",
    "05_assembly_bay.png",
    "06_populated_press_with_umg_nav_clean.png",
)

# Paint calibration B is the common factory master reference.
VISUAL_GATES = {
    "mean_luma_min": 0.35,
    "mean_luma_max": 0.48,
    "black_clip_luma": 0.01,
    "black_clip_fraction_max": 0.01,
    "white_clip_luma": 0.99,
    "white_clip_fraction_max": 0.005,
    "maximum_scene_mean_spread": 0.08,
    "maximum_top_left_warning_red_pixels": 25,
}

V001_ACTUAL_PLAYER_EVIDENCE = (
    {
        "name": "01_empty_factory_management_overview.png",
        "sha256": "C7CC1C28095CC83279D7F764999E18B58B3DAC60B9010E98BDF1567C4A8E5637",
    },
    {
        "name": "02_populated_press_starter_wide_overview.png",
        "sha256": "7645637C24E077BF6B0F61BAEC1C70A15467913EA0882ACE27D7C23532AEC1FA",
    },
    {
        "name": "03_press_train_dispatch_agv_close.png",
        "sha256": "943BCE49E04D3F1B56E6727C8F43210197FBFA5E563E87B96CDDD6818C487D65",
    },
    {
        "name": "04_populated_press_starter_with_umg.png",
        "sha256": "430182F1D00D1D2E882BC76BC61CA0B3A39DA665F8A31B9506BDE7B190207580",
    },
)
V001_ACTUAL_PLAYER_SCREENSHOT_RELATIVE_ROOT = (
    "Saved/ValidationScreenshots/OneFactory/v001/ActualPlayerPIE/"
    "20260815T035404438Z"
)
V001_ACTUAL_PLAYER_LOG_RELATIVE = (
    "Saved/Audits/OneFactory/v001/ActualPlayerPIE/Runs/20260815T035404438Z/"
    "Logs/actual_player_pie.stdout.log"
)

BUILD_RECEIPT_RELATIVE = (
    "Saved/Audits/OneFactory/v002/VisualNavigation/"
    "one_factory_visual_navigation_build_v002.json"
)
VALIDATION_RECEIPT_RELATIVE = (
    "Saved/Audits/OneFactory/v002/VisualNavigation/"
    "one_factory_visual_navigation_validation_v002.json"
)
SCREENSHOT_RELATIVE_ROOT = (
    "Saved/ValidationScreenshots/OneFactory/v002/VisualNavigation"
)

BUILD_STATUS = (
    "PASS__ONE_FACTORY_V002_FACTORY_WIDE_CAIRNWELL_LIGHTING_AND_NAVIGATION_BUILT__"
    "SOURCE_V001_UNCHANGED"
)
VALIDATION_STATUS = (
    "PASS__ONE_FACTORY_V002_FRESH_RELOAD_REAL_RHI_PIE_EVEN_LIGHTING_AND_NAV_VALID__"
    "ZERO_SAVED_PRODUCTION_OR_WIP"
)


def high_bay_label(row: int, column: int) -> str:
    """Return the deterministic one-based actor label for one grid fixture."""
    return f"LB_OF_ENV_HighBay_R{row:02d}_C{column:02d}_v002"


def high_bay_specs() -> tuple[dict[str, Any], ...]:
    rows = []
    for row, y in enumerate(HIGH_BAY_Y_CM, 1):
        for column, x in enumerate(HIGH_BAY_X_CM, 1):
            rows.append({
                "label": high_bay_label(row, column),
                "row": row,
                "column": column,
                "location_cm": (x, y, HIGH_BAY_Z_CM),
            })
    return tuple(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _paeth(a: int, b: int, c: int) -> int:
    prediction = a + b - c
    pa = abs(prediction - a)
    pb = abs(prediction - b)
    pc = abs(prediction - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _png_rows(path: Path) -> tuple[int, int, int, Iterator[bytes]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    offset = 8
    width = height = colour_type = bit_depth = interlace = None
    compressed = bytearray()
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, colour_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if compression != 0 or filtering != 0:
                raise ValueError("Unsupported PNG compression/filter method")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if width is None or height is None:
        raise ValueError("PNG has no IHDR")
    if bit_depth != 8 or colour_type not in (2, 6) or interlace != 0:
        raise ValueError(
            f"Only non-interlaced 8-bit RGB/RGBA PNG is supported: "
            f"depth={bit_depth} colour={colour_type} interlace={interlace}"
        )
    channels = 3 if colour_type == 2 else 4
    scanline_bytes = width * channels
    raw = zlib.decompress(bytes(compressed))
    expected_size = (scanline_bytes + 1) * height
    if len(raw) != expected_size:
        raise ValueError(f"PNG scanline length {len(raw)} != {expected_size}")

    def decoded_rows() -> Iterator[bytes]:
        previous = bytearray(scanline_bytes)
        cursor = 0
        for _ in range(height):
            filter_type = raw[cursor]
            cursor += 1
            encoded = raw[cursor:cursor + scanline_bytes]
            cursor += scanline_bytes
            current = bytearray(scanline_bytes)
            for index, value in enumerate(encoded):
                left = current[index - channels] if index >= channels else 0
                above = previous[index]
                upper_left = previous[index - channels] if index >= channels else 0
                if filter_type == 0:
                    predictor = 0
                elif filter_type == 1:
                    predictor = left
                elif filter_type == 2:
                    predictor = above
                elif filter_type == 3:
                    predictor = (left + above) // 2
                elif filter_type == 4:
                    predictor = _paeth(left, above, upper_left)
                else:
                    raise ValueError(f"Unsupported PNG filter {filter_type}")
                current[index] = (value + predictor) & 0xFF
            previous = current
            yield bytes(current)

    return width, height, channels, decoded_rows()


def png_metrics(path: Path, sample_stride: int = 2) -> dict[str, Any]:
    """Measure the frozen Rec.709 and warning-red gates without Pillow."""
    width, height, channels, rows = _png_rows(path)
    luma_total = 0.0
    sample_count = black_count = white_count = red_count = 0
    for y, row in enumerate(rows):
        if y < 160:
            for x in range(0, min(640, width)):
                offset = x * channels
                red, green, blue = row[offset], row[offset + 1], row[offset + 2]
                if (
                    red >= 160 and red >= green * 1.5 and red >= blue * 1.5
                ):
                    red_count += 1
        for x in range(0, width, max(1, sample_stride)):
            offset = x * channels
            red, green, blue = row[offset], row[offset + 1], row[offset + 2]
            if y % max(1, sample_stride) == 0:
                luma = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0
                luma_total += luma
                sample_count += 1
                black_count += int(luma <= VISUAL_GATES["black_clip_luma"])
                white_count += int(luma >= VISUAL_GATES["white_clip_luma"])
    if sample_count == 0:
        raise ValueError(f"PNG has no sampled pixels: {path}")
    return {
        "dimensions": [width, height],
        "sample_stride": max(1, sample_stride),
        "sample_count": sample_count,
        "mean_luma": round(luma_total / sample_count, 6),
        "black_clip_fraction": round(black_count / sample_count, 6),
        "white_clip_fraction": round(white_count / sample_count, 6),
        "top_left_warning_red_pixels": red_count,
    }


def scene_metrics_pass(metrics: dict[str, Any]) -> bool:
    return (
        metrics.get("dimensions") == list(SCREENSHOT_SIZE)
        and VISUAL_GATES["mean_luma_min"]
        <= float(metrics.get("mean_luma", -1.0))
        <= VISUAL_GATES["mean_luma_max"]
        and float(metrics.get("black_clip_fraction", 1.0))
        <= VISUAL_GATES["black_clip_fraction_max"]
        and float(metrics.get("white_clip_fraction", 1.0))
        <= VISUAL_GATES["white_clip_fraction_max"]
    )
