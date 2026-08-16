"""Deterministic, dependency-free tonal gate for Body Shop player captures.

Only 1920x1080 high-resolution screenshots whose live receipt identifies them
as coming directly from the possessed management pawn are sampled.  Slate/UI
captures are deliberately excluded, so editor chrome and widget pixels cannot
affect the lighting result.  Regions are normalized gameplay-viewport regions.
"""
from __future__ import annotations

import argparse
import binascii
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_SIZE = (1920, 1080)
MINIMUM_FULL_GATE_PYTHON = (3, 13)
EXPECTED_LIVE_STATUS = "PASS__BODY_SHOP_RELEASE_CANDIDATE_ACTUAL_PLAYER_PIE"
EXPECTED_VISUAL_V004_VALIDATION_SHA256 = "956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E"
EXPECTED_MANAGEMENT_V005_PATCH_SHA256 = "8A305B26C838567FC3F26063B28F9D7FA65382F9A932F762A8CC3C4DD7F7ED50"
EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256 = "DCDBCBFA4D47FEBF21A22FD98F30ADC880D037519EBDBC6AE34BD7D4CE9F88D8"
EXPECTED_MANAGEMENT_V005_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"
OVERVIEW_NAME = "01_actual_management_pawn_hud_overview.png"
FIXTURE_NAME = "02_actual_management_pawn_fixture_view.png"
EXPECTED_SCENE_NAMES = {
    OVERVIEW_NAME,
    FIXTURE_NAME,
    "03_actual_management_pawn_welding_process_view.png",
}

# These inset, normalized regions sample only the high-res gameplay image.  The
# overview floor patch is an intentionally empty foreground aisle area, not a
# machine skin or the deliberately darker protected FLT/tow lane at lower left.
SCENE_ROI = (0.02, 0.02, 0.98, 0.98)
MIDDLE_LOWER_ROI = (0.04, 0.30, 0.96, 0.94)
OVERVIEW_FLOOR_ROI = (0.35, 0.70, 0.65, 0.90)

OVERVIEW_P90_MAX = 0.68
FIXTURE_P90_MAX = 0.70
MIDDLE_LOWER_OVER_075_FRACTION_MAX = 0.05
FLOOR_MEAN_MIN = 0.36
FLOOR_MEAN_MAX = 0.48


class GateFailure(RuntimeError):
    pass


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def assert_supported_full_gate_runtime() -> None:
    if sys.implementation.name != "cpython" or sys.version_info[:2] < MINIMUM_FULL_GATE_PYTHON:
        required = ".".join(str(part) for part in MINIMUM_FULL_GATE_PYTHON)
        actual = f"{sys.implementation.name} {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        raise GateFailure(
            "full tonal analysis requires CPython " + required
            + "+; refusing unsafe runtime " + actual
        )


def runtime_identity() -> dict:
    executable = Path(sys.executable).resolve()
    library = executable.with_name(
        f"python{sys.version_info.major}{sys.version_info.minor}.dll"
    )
    result = {
        "implementation": sys.implementation.name,
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        "executable": str(executable),
        "executable_sha256": digest(executable),
    }
    if library.is_file():
        result["runtime_library"] = str(library)
        result["runtime_library_sha256"] = digest(library)
    return result


def unfilter_scanline(filter_type: int, filtered: bytes, previous: bytes,
                      bytes_per_pixel: int) -> bytes:
    """Reconstruct one PNG row without mutating either source row.

    Filter dispatch happens once per row and source rows remain immutable.  The
    full gate separately refuses CPython 3.11 after both UE-bundled 3.11.8 and
    local 3.11.9 proved unsafe under sustained exact-capture decoding.
    """
    if filter_type not in range(5):
        raise GateFailure("unsupported PNG filter type")
    if bytes_per_pixel <= 0 or len(filtered) != len(previous):
        raise GateFailure("PNG scanline geometry is invalid")
    if filter_type == 0:
        return filtered

    reconstructed = bytearray(len(filtered))
    if filter_type == 1:
        for channel in range(bytes_per_pixel):
            left = 0
            for index in range(channel, len(filtered), bytes_per_pixel):
                decoded = (filtered[index] + left) & 0xFF
                reconstructed[index] = decoded
                left = decoded
    elif filter_type == 2:
        for index, encoded in enumerate(filtered):
            reconstructed[index] = (encoded + previous[index]) & 0xFF
    elif filter_type == 3:
        for channel in range(bytes_per_pixel):
            left = 0
            for index in range(channel, len(filtered), bytes_per_pixel):
                up = previous[index]
                decoded = (filtered[index] + ((left + up) // 2)) & 0xFF
                reconstructed[index] = decoded
                left = decoded
    else:
        for channel in range(bytes_per_pixel):
            left = 0
            upper_left = 0
            for index in range(channel, len(filtered), bytes_per_pixel):
                up = previous[index]
                estimate = left + up - upper_left
                distance_left = abs(estimate - left)
                distance_up = abs(estimate - up)
                distance_upper_left = abs(estimate - upper_left)
                if distance_left <= distance_up and distance_left <= distance_upper_left:
                    predictor = left
                elif distance_up <= distance_upper_left:
                    predictor = up
                else:
                    predictor = upper_left
                decoded = (filtered[index] + predictor) & 0xFF
                reconstructed[index] = decoded
                left = decoded
                upper_left = up
    return bytes(reconstructed)


def decode_png_bytes(data: bytes) -> tuple[int, int, list[bytes]]:
    if not data.startswith(PNG_SIGNATURE):
        raise GateFailure("image is not a PNG")
    cursor = len(PNG_SIGNATURE)
    ihdr = None
    compressed = bytearray()
    saw_iend = False
    while cursor + 12 <= len(data):
        length = struct.unpack(">I", data[cursor:cursor + 4])[0]
        kind = data[cursor + 4:cursor + 8]
        start = cursor + 8
        end = start + length
        if end + 4 > len(data):
            raise GateFailure("PNG chunk is truncated")
        payload = data[start:end]
        expected_crc = struct.unpack(">I", data[end:end + 4])[0]
        actual_crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise GateFailure("PNG chunk CRC mismatch")
        if kind == b"IHDR":
            if ihdr is not None or length != 13:
                raise GateFailure("PNG IHDR inventory is invalid")
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            saw_iend = True
            break
        cursor = end + 4
    if ihdr is None or not saw_iend or not compressed:
        raise GateFailure("PNG is missing IHDR, IDAT or IEND")
    width, height, bit_depth, colour_type, compression, filter_method, interlace = ihdr
    if (width <= 0 or height <= 0 or bit_depth != 8 or colour_type not in (2, 6)
            or compression != 0 or filter_method != 0 or interlace != 0):
        raise GateFailure("only non-interlaced 8-bit RGB/RGBA PNG captures are accepted")
    bytes_per_pixel = 3 if colour_type == 2 else 4
    stride = width * bytes_per_pixel
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as exc:
        raise GateFailure("PNG IDAT decompression failed: " + str(exc)) from exc
    if len(raw) != height * (stride + 1):
        raise GateFailure("PNG decompressed byte count is invalid")
    rows = []
    previous = bytes(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        filtered = raw[offset + 1:offset + 1 + stride]
        offset += stride + 1
        scanline = unfilter_scanline(filter_type, filtered, previous, bytes_per_pixel)
        rows.append(scanline)
        previous = scanline
    return width, height, rows


def decode_png(path: Path) -> tuple[int, int, list[bytes]]:
    if not path.is_file() or path.stat().st_size < 1024:
        raise GateFailure("capture is missing or too small: " + str(path))
    return decode_png_bytes(path.read_bytes())


def pixel_bounds(width: int, height: int, roi: tuple[float, float, float, float]) -> tuple[int, int, int, int]:
    x0 = max(0, min(width - 1, int(math.floor(roi[0] * width))))
    y0 = max(0, min(height - 1, int(math.floor(roi[1] * height))))
    x1 = max(x0 + 1, min(width, int(math.ceil(roi[2] * width))))
    y1 = max(y0 + 1, min(height, int(math.ceil(roi[3] * height))))
    return x0, y0, x1, y1


def histogram(rows: list[bytes], width: int, height: int,
              roi: tuple[float, float, float, float]) -> tuple[list[int], int, int]:
    x0, y0, x1, y1 = pixel_bounds(width, height, roi)
    channels = len(rows[0]) // width
    counts = [0] * 256
    total_luma = 0
    count = 0
    for y in range(y0, y1):
        row = rows[y]
        for x in range(x0, x1):
            index = x * channels
            # Integer Rec.709 approximation (coefficients sum to 256).  All
            # thresholds therefore operate deterministically on displayed sRGB.
            luma = (54 * row[index] + 183 * row[index + 1]
                    + 19 * row[index + 2] + 128) // 256
            counts[luma] += 1
            total_luma += luma
            count += 1
    if count == 0:
        raise GateFailure("tonal ROI is empty")
    return counts, total_luma, count


def percentile_from_histogram(counts: list[int], count: int, percentile: float) -> float:
    target = max(1, int(math.ceil(percentile * count)))
    running = 0
    for value, occurrences in enumerate(counts):
        running += occurrences
        if running >= target:
            return value / 255.0
    raise GateFailure("histogram percentile could not be resolved")


def roi_metrics(rows: list[bytes], width: int, height: int,
                roi: tuple[float, float, float, float]) -> dict:
    counts, total_luma, count = histogram(rows, width, height, roi)
    over_075 = sum(counts[192:])
    return {
        "normalized_roi": list(roi),
        "pixel_bounds": list(pixel_bounds(width, height, roi)),
        "sample_count": count,
        "mean_luminance_srgb": round(total_luma / (count * 255.0), 6),
        "p90_luminance_srgb": round(percentile_from_histogram(counts, count, 0.90), 6),
        "fraction_luminance_over_0_75": round(over_075 / count, 6),
    }


def bind_scene_capture(capture_dir: Path, live: dict, filename: str) -> tuple[Path, dict]:
    matches = [row for row in live.get("screenshots", [])
               if Path(str(row.get("path", ""))).name == filename]
    if len(matches) != 1:
        raise GateFailure("live receipt does not bind exactly one scene capture: " + filename)
    record = matches[0]
    path = Path(str(record.get("path", ""))).resolve()
    if (path.parent != capture_dir or record.get("source") != "possessed_management_pawn"
            or record.get("hud_required") is not False or record.get("exists") is not True
            or not isinstance(record.get("sha256"), str)):
        raise GateFailure("scene capture authority/path metadata drift: " + filename)
    if digest(path) != record["sha256"]:
        raise GateFailure("scene capture hash drift: " + filename)
    return path, record


def add_gate(gates: list[dict], name: str, actual: float, comparison: str,
             threshold, passed: bool, source: str, roi: tuple[float, float, float, float]) -> None:
    gates.append({
        "name": name,
        "source": source,
        "normalized_roi": list(roi),
        "actual": round(actual, 6),
        "comparison": comparison,
        "threshold": threshold,
        "passed": passed,
    })


def run_gate(capture_dir: Path, live_receipt: Path) -> dict:
    capture_dir = capture_dir.resolve()
    live_receipt = live_receipt.resolve()
    if not capture_dir.is_dir() or not live_receipt.is_file():
        raise GateFailure("capture directory or live receipt is missing")
    live = json.loads(live_receipt.read_text(encoding="utf-8-sig"))
    management_binding = live.get("prerequisites", {}).get(
        "management_cutaway_v005_validation", {})
    management_path = Path(str(management_binding.get("path", ""))).resolve()
    if (management_binding.get("sha256") != EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256
            or management_binding.get("schema")
                != "lineboss/audit/bodyshop/management-cutaway-v005-validation/v1"
            or management_binding.get("status")
                != "PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005"
            or management_binding.get("map_sha256") != EXPECTED_MANAGEMENT_V005_MAP_SHA256
            or not management_path.is_file()
            or digest(management_path) != EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256):
        raise GateFailure("live PIE receipt is not bound to the exact management-cutaway v005 validation")
    management_gate = json.loads(management_path.read_text(encoding="utf-8-sig"))
    management_prerequisites = management_gate.get("prerequisites", {})
    if (management_gate.get("$schema")
            != "lineboss/audit/bodyshop/management-cutaway-v005-validation/v1"
            or management_gate.get("status")
                != "PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005"
            or management_gate.get("failures")
            or management_prerequisites.get(
                "visual_readability_v004_validation", {}).get("sha256")
                != EXPECTED_VISUAL_V004_VALIDATION_SHA256
            or management_prerequisites.get(
                "management_cutaway_v005_patch", {}).get("sha256")
                != EXPECTED_MANAGEMENT_V005_PATCH_SHA256
            or management_gate.get("map", {}).get("sha256")
                != EXPECTED_MANAGEMENT_V005_MAP_SHA256
            or management_gate.get("map", {}).get(
                "read_only_fresh_load_hash_unchanged") is not True
            or live.get("map_sha256_before") != EXPECTED_MANAGEMENT_V005_MAP_SHA256
            or live.get("map_sha256_after") != EXPECTED_MANAGEMENT_V005_MAP_SHA256):
        raise GateFailure("management-cutaway v005 map authority drift")
    checks = live.get("checks", {})
    welding = checks.get("welding_process_mirrored_sample", {})
    presentation = checks.get("underbody_release_presentation_contract", {})
    underbody = presentation.get("underbody_fixture", {})
    conveyor = presentation.get("continuous_conveyor_chain", {})
    fixture_wip = presentation.get("fixture_capture_runtime_wip", {})
    joints = conveyor.get("joints", [])
    scene_names = {Path(str(row.get("path", ""))).name for row in live.get("screenshots", [])
                   if row.get("source") == "possessed_management_pawn"
                   and row.get("hud_required") is False}
    if (live.get("status") != EXPECTED_LIVE_STATUS or live.get("failures")
            or live.get("map_hash_unchanged") is not True
            or len(live.get("screenshots", [])) != 6
            or scene_names != EXPECTED_SCENE_NAMES
            or welding.get("passed") is not True
            or welding.get("both_captures_completed_in_held_process_stage") is not True
            or presentation.get("passed") is not True
            or underbody.get("no_underbody_main_presentation_mesh") is not True
            or underbody.get("main_presentation_asset_path") != ""
            or underbody.get("continuous_conveyor") is not True
            or underbody.get("conveyor_span_cm") != 1200.0
            or underbody.get("painted_work_zone") is not True
            or underbody.get("floor_working_zone_instances") != 2
            or underbody.get("floor_safety_marking_instances") != 6
            or underbody.get("neutral_conveyor_lane_width_cm") != 260.0
            or underbody.get("uses_open_rail_safety_presentation") is not True
            or underbody.get("auto_assembled_fence_segments") != 18
            or conveyor.get("passed") is not True
            or len(conveyor.get("cells", [])) != 4
            or len(joints) != 3
            or any(joint.get("passed") is not True or joint.get("gap_cm") != 0.0
                   for joint in joints)
            or fixture_wip.get("passed") is not True
            or fixture_wip.get("logical_wip_before_captures") != 1
            or fixture_wip.get("visible_runtime_wip_before_captures") != 1
            or fixture_wip.get("logical_wip_after_both_captures") != 1
            or fixture_wip.get("visible_runtime_wip_after_both_captures") != 1
            or fixture_wip.get("both_captures_completed_with_one_runtime_wip") is not True):
        raise GateFailure(
            "live PIE receipt is not the complete six-capture v005 release-presentation authority")

    overview_path, overview_record = bind_scene_capture(capture_dir, live, OVERVIEW_NAME)
    fixture_path, fixture_record = bind_scene_capture(capture_dir, live, FIXTURE_NAME)
    overview_width, overview_height, overview_rows = decode_png(overview_path)
    fixture_width, fixture_height, fixture_rows = decode_png(fixture_path)
    if (overview_width, overview_height) != EXPECTED_SIZE or (fixture_width, fixture_height) != EXPECTED_SIZE:
        raise GateFailure("tonal gate requires exact 1920x1080 high-resolution gameplay captures")

    overview_scene = roi_metrics(overview_rows, overview_width, overview_height, SCENE_ROI)
    fixture_scene = roi_metrics(fixture_rows, fixture_width, fixture_height, SCENE_ROI)
    overview_middle = roi_metrics(
        overview_rows, overview_width, overview_height, MIDDLE_LOWER_ROI)
    fixture_middle = roi_metrics(
        fixture_rows, fixture_width, fixture_height, MIDDLE_LOWER_ROI)
    floor = roi_metrics(overview_rows, overview_width, overview_height, OVERVIEW_FLOOR_ROI)

    gates = []
    add_gate(gates, "overview_p90", overview_scene["p90_luminance_srgb"], "<=",
             OVERVIEW_P90_MAX, overview_scene["p90_luminance_srgb"] <= OVERVIEW_P90_MAX,
             OVERVIEW_NAME, SCENE_ROI)
    add_gate(gates, "fixture_p90", fixture_scene["p90_luminance_srgb"], "<=",
             FIXTURE_P90_MAX, fixture_scene["p90_luminance_srgb"] <= FIXTURE_P90_MAX,
             FIXTURE_NAME, SCENE_ROI)
    add_gate(gates, "overview_middle_lower_fraction_over_0_75",
             overview_middle["fraction_luminance_over_0_75"], "<=",
             MIDDLE_LOWER_OVER_075_FRACTION_MAX,
             overview_middle["fraction_luminance_over_0_75"]
             <= MIDDLE_LOWER_OVER_075_FRACTION_MAX,
             OVERVIEW_NAME, MIDDLE_LOWER_ROI)
    add_gate(gates, "fixture_middle_lower_fraction_over_0_75",
             fixture_middle["fraction_luminance_over_0_75"], "<=",
             MIDDLE_LOWER_OVER_075_FRACTION_MAX,
             fixture_middle["fraction_luminance_over_0_75"]
             <= MIDDLE_LOWER_OVER_075_FRACTION_MAX,
             FIXTURE_NAME, MIDDLE_LOWER_ROI)
    floor_mean = floor["mean_luminance_srgb"]
    add_gate(gates, "overview_empty_aisle_floor_mean", floor_mean, "inclusive_range",
             [FLOOR_MEAN_MIN, FLOOR_MEAN_MAX], FLOOR_MEAN_MIN <= floor_mean <= FLOOR_MEAN_MAX,
             OVERVIEW_NAME, OVERVIEW_FLOOR_ROI)
    failures = [gate["name"] for gate in gates if not gate["passed"]]
    return {
        "$schema": "lineboss/audit/bodyshop/visual-readability-v004-tonal-analysis/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": ("PASS__BODYSHOP_VISUAL_READABILITY_V004_TONAL_GATES"
                   if not failures else "FAIL__BODYSHOP_VISUAL_READABILITY_V004_TONAL_GATES"),
        "method": {
            "decoder": "dependency-free PNG CRC/zlib/unfilter; 8-bit RGB/RGBA non-interlaced only",
            "luminance": "display-sRGB integer Rec.709 approximation (54R+183G+19B)/256",
            "editor_chrome_excluded": True,
            "capture_authority": "1920x1080 possessed-management-pawn high-res screenshots only",
            "slate_or_ui_captures_sampled": False,
        },
        "runtime": runtime_identity(),
        "management_cutaway_v005_validation_receipt": {
            "path": str(management_path),
            "sha256": digest(management_path),
        },
        "live_pie_receipt": {"path": str(live_receipt), "sha256": digest(live_receipt)},
        "captures": {
            "overview": {"path": str(overview_path), "sha256": overview_record["sha256"],
                         "size": [overview_width, overview_height], "scene": overview_scene,
                         "middle_lower": overview_middle, "empty_aisle_floor": floor},
            "fixture": {"path": str(fixture_path), "sha256": fixture_record["sha256"],
                        "size": [fixture_width, fixture_height], "scene": fixture_scene,
                        "middle_lower": fixture_middle},
        },
        "gates": gates,
        "failures": failures,
        "writes_to_content_source_config_or_saves": False,
    }


SELF_TEST_RGBA_ROWS = (
    bytes((0, 0, 0, 255, 64, 32, 16, 255, 255, 255, 255, 128)),
    bytes((12, 24, 48, 255, 90, 45, 20, 240, 220, 180, 140, 220)),
    bytes((20, 40, 60, 200, 100, 120, 140, 180, 240, 210, 170, 160)),
    bytes((5, 15, 25, 100, 55, 75, 95, 130, 205, 185, 165, 210)),
    bytes((30, 10, 50, 90, 80, 60, 120, 150, 230, 200, 180, 240)),
)


def make_test_png() -> bytes:
    width, height = 3, len(SELF_TEST_RGBA_ROWS)
    bytes_per_pixel = 4
    pixels = bytearray()
    previous = bytes(width * bytes_per_pixel)
    for filter_type, row in enumerate(SELF_TEST_RGBA_ROWS):
        pixels.append(filter_type)
        for index, value in enumerate(row):
            left = row[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = up
            elif filter_type == 3:
                predictor = (left + up) // 2
            else:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up),
                             abs(estimate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
            pixels.append((value - predictor) & 0xFF)
        previous = row

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


def self_test() -> int:
    width, height, rows = decode_png_bytes(make_test_png())
    metrics = roi_metrics(rows, width, height, (0.0, 0.0, 1.0, 1.0))
    if ((width, height) != (3, 5) or tuple(rows) != SELF_TEST_RGBA_ROWS
            or metrics["sample_count"] != 15):
        raise GateFailure("internal decoder/metric self-test failed")
    print(json.dumps({"status": "PASS__PNG_DECODER_AND_TONAL_METRIC_SELF_TEST",
                      "metrics": metrics}, indent=2))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-dir", type=Path)
    parser.add_argument("--live-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.self_test:
        return self_test()
    if args.capture_dir is None or args.live_receipt is None or args.output is None:
        raise GateFailure("--capture-dir, --live-receipt and --output are required")
    assert_supported_full_gate_runtime()
    output = args.output.resolve()
    if output.exists():
        raise GateFailure("refusing to overwrite tonal-analysis receipt: " + str(output))
    result = run_gate(args.capture_dir, args.live_receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"].startswith("PASS__") else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GateFailure as exc:
        print("BODYSHOP_VISUAL_READABILITY_V004_TONAL_ANALYSIS_ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
