"""Exact, read-only authority contract for BodyShopSupportKitNative_v002.

The support kit is a clean-room native family imported once through the guarded
v003 lane.  Downstream material, PIE, package and performance gates import this
module so a single byte-exact contract protects all 12 packages and their three
explicit LODs.  This module never writes project state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


RUN_RELATIVE = Path(
    "Saved/Audits/BodyShop/SupportKitNative_v002/UnrealImportLane_v003/"
    "20260814T223952Z-fa3434b0"
)
RECOVERY_RECEIPT_NAME = "failed_v002_archive_quarantine_receipt_v003.json"
IMPORT_RECEIPT_NAME = "import_receipt_v003.json"
VALIDATION_RECEIPT_NAME = "fresh_load_validation_receipt_v003.json"
LANE_SUMMARY_NAME = "lane_summary_v003.json"

BASELINE_SHA256 = "A124CE80D77717C062CFFE5AFDD5058905957D29B8A8BB01979A4567149653A6"
RECOVERY_RECEIPT_SHA256 = "BBE9F02910027B111B07CBABE163CDE3A139DE065FF8E24FE99BB497470090F6"
IMPORT_RECEIPT_SHA256 = "F5E1735BE76AD9F2086AE1B533CA92DD240D740129A9BBC147A872D818B2F286"
VALIDATION_RECEIPT_SHA256 = "CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82"
LANE_SUMMARY_SHA256 = "6797C6C7E295C00D1921DFB378100C26C9905848E8EF63DB0501BBA0FC583C22"

LANE_SCHEMA = (
    "lineboss/audit/bodyshop-support-kit-native-v002-unreal-import-lane-summary/v3"
)
LANE_STATUS = (
    "PASS__HASH_GUARDED_IMPORT_AND_INDEPENDENT_FRESH_LOAD_"
    "BODYSHOP_SUPPORT_KIT_NATIVE_V002_LANE_V003"
)
RECOVERY_STATUS = (
    "PASS__FAILED_V002_PACKAGES_EXACT_HASH_ARCHIVED_AND_RECOVERABLY_QUARANTINED"
)
IMPORT_SCHEMA = "lineboss/audit/bodyshop-support-kit-native-v002-unreal-import/v3"
IMPORT_STATUS = (
    "PASS__HASH_GUARDED_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V002_"
    "BASELINE_V003_UNREAL_INTAKE"
)
VALIDATION_SCHEMA = (
    "lineboss/audit/bodyshop-support-kit-native-v002-fresh-load-validation/v3"
)
VALIDATION_STATUS = (
    "PASS__INDEPENDENT_FRESH_PROCESS_LOAD_12_ASSETS_3_LODS_"
    "BODYSHOP_SUPPORT_KIT_NATIVE_V002_LANE_V003"
)
DESTINATION_NAMESPACE = (
    "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002"
)
EXPECTED_TRIANGLE_TOTALS = [20408, 7580, 1780]
EXPECTED_LOD_SCREEN_SIZES = [1.0, 0.45, 0.18]

ASSETS = {
    "PanelStillageEmpty": (
        "Logistics/SM_LB_BodyShopSupport_PanelStillage_Empty_v002",
        [3252, 1188, 264],
        "0C4428A51DF5D9965B1393D5FBFFC6353227BDE1B050D193100E44156F5845DD",
    ),
    "PanelStillageFull": (
        "Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002",
        [3908, 1392, 304],
        "0A2539DCB13C166282849C219F56BC6856C6A89189B67D347BB0E4EA32F49DB9",
    ),
    "EmptyReturnCart": (
        "Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002",
        [2424, 936, 304],
        "2F5B39D82FEAB87E2D3948CE81ECFCA2537B76D5EAC03A9F1E479C62AEA22339",
    ),
    "ComponentServicePallet": (
        "Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002",
        [1944, 704, 120],
        "05161D75CEB5ACFB8A62216E6F4E7BB850C4A117D17E70D8CF54A103C7485076",
    ),
    "SmallPartsCrate": (
        "Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
        [1404, 572, 120],
        "400DC20D140C6DDE0B775892D4B7B07A79FC6F59B6C8FDAEE2C1A5F70AF129CF",
    ),
    "SmallPartsBin": (
        "Logistics/SM_LB_BodyShopSupport_SmallPartsBin_Open_v002",
        [1080, 440, 120],
        "13BC93E724CBD367F4CF572C8D04A0D0138EC338C129B50CFEDD8FB0191E2B36",
    ),
    "ElectricalCabinet": (
        "Controls/SM_LB_BodyShopSupport_ElectricalCabinet_v002",
        [888, 300, 88],
        "6492920421B619F2F219773329055636D594E376CA2481CEDD1446EF1CF3512B",
    ),
    "HMIPedestal": (
        "Controls/SM_LB_BodyShopSupport_HMIPedestal_v002",
        [672, 320, 76],
        "17FAA935651B644F1008802D52FD9A95DCF951782822BDE67423FD92DD912E0D",
    ),
    "GuardPanel2m": (
        "Safety/SM_LB_BodyShopSupport_GuardPanel_2m_v002",
        [1620, 528, 84],
        "0C627C244438C79DE6F0EFBCAF082FCDBD8EE9095E5A90C1BA69135099AAF2EE",
    ),
    "GuardGate2m": (
        "Safety/SM_LB_BodyShopSupport_GuardGate_2m_v002",
        [2052, 704, 132],
        "B1B6AB520F0A3F4A0932F69B410BB1AC7D28C6AFF4AB6459FB656A8B38508A4B",
    ),
    "UtilityPedestal": (
        "Services/SM_LB_BodyShopSupport_UtilityPedestal_v002",
        [612, 248, 76],
        "F3DF5CF02E5C3FEAC90FF04A4A3C41C09C6184E33B8C3EDDB0AAE7E57FCAFA00",
    ),
    "ExtractionPedestal": (
        "Services/SM_LB_BodyShopSupport_ExtractionPedestal_v002",
        [552, 248, 92],
        "5A535F95849EB73383D7347C6C5C77785170DE099898B4B3E6D83C89CE989560",
    ),
}

MATERIAL_BINDINGS = {
    "M_LB_Support_FoundryCharcoal": "MI_LB_BodyShop_GraphiteTooling_v002",
    "M_LB_Support_SafetyYellow": "MI_LB_BodyShop_SafetyYellow_v002",
    "M_LB_Support_CairnwellGreen": "MI_LB_BodyShop_EmeraldPanel_v002",
    "M_LB_Support_RubberBlack": "MI_LB_BodyShop_VacuumRubber_v002",
    "M_LB_Support_BrushedSteel": "MI_LB_BodyShop_BrushedSteel_v002",
    "M_LB_Support_WarmWhite": "MI_LB_BodyShop_CreamPaint_v002",
    "M_LB_Support_SteelGrey": "MI_LB_BodyShop_StructuralLightGrey_v002",
    "M_LB_Support_ReadyAqua": "MI_LB_BodyShop_ScannerLens_v002",
    "M_LB_Support_SignalRed": "MI_LB_BodyShop_StatusRed_v002",
    "M_LB_Support_IndicatorGreen": "MI_LB_BodyShop_StatusGreen_v002",
    "M_LB_Support_IndicatorAmber": "MI_LB_BodyShop_StatusAmber_v002",
    "M_LB_Support_IndicatorRed": "MI_LB_BodyShop_StatusRed_v002",
    "M_LB_Support_LensBlue": "MI_LB_BodyShop_ScannerLens_v002",
}
MATERIAL_NAMESPACE = (
    "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
)


class ContractError(RuntimeError):
    """Raised when any frozen support-kit authority field drifts."""


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def require_hash(path: Path, expected: str, label: str) -> Path:
    if not path.is_file():
        raise ContractError(f"missing {label}: {path}")
    actual = sha256(path)
    if actual != expected:
        raise ContractError(f"{label} hash drifted: {actual} != {expected}")
    return path


def package_path(relative: str) -> str:
    return f"{DESTINATION_NAMESPACE}/{relative}"


def object_path(relative: str) -> str:
    package = package_path(relative)
    return f"{package}.{relative.rsplit('/', 1)[-1]}"


def disk_relative(relative: str) -> Path:
    return Path("Content") / Path(package_path(relative).removeprefix("/Game/")).with_suffix(
        ".uasset"
    )


def _material_object(slot: str) -> str:
    leaf = MATERIAL_BINDINGS[slot]
    return f"{MATERIAL_NAMESPACE}/{leaf}.{leaf}"


def validate(project_root: Path, validation_receipt: Path | None = None) -> dict:
    """Validate the exact lane, receipts, 12 packages, LODs and material bindings."""
    root = project_root.resolve()
    run_root = root / RUN_RELATIVE
    lane_path = require_hash(
        run_root / LANE_SUMMARY_NAME, LANE_SUMMARY_SHA256, "support-kit lane summary"
    )
    recovery_path = require_hash(
        run_root / RECOVERY_RECEIPT_NAME,
        RECOVERY_RECEIPT_SHA256,
        "support-kit failed-v002 recovery receipt",
    )
    import_path = require_hash(
        run_root / IMPORT_RECEIPT_NAME, IMPORT_RECEIPT_SHA256, "support-kit import receipt"
    )
    fresh_path = require_hash(
        run_root / VALIDATION_RECEIPT_NAME,
        VALIDATION_RECEIPT_SHA256,
        "support-kit fresh-load receipt",
    )
    if validation_receipt is not None and validation_receipt.resolve() != fresh_path.resolve():
        raise ContractError("support-kit receipt argument is not the exact frozen v003 receipt")

    lane = json.loads(lane_path.read_text(encoding="utf-8-sig"))
    recovery = json.loads(recovery_path.read_text(encoding="utf-8-sig"))
    imported = json.loads(import_path.read_text(encoding="utf-8-sig"))
    fresh = json.loads(fresh_path.read_text(encoding="utf-8-sig"))
    if (
        lane.get("$schema") != LANE_SCHEMA
        or lane.get("status") != LANE_STATUS
        or lane.get("import_receipt", {}).get("sha256") != IMPORT_RECEIPT_SHA256
        or lane.get("validation_receipt", {}).get("sha256") != VALIDATION_RECEIPT_SHA256
        or lane.get("failed_v002_recovery", {}).get("status") != RECOVERY_STATUS
        or lane.get("failed_v002_recovery", {}).get("receipt", {}).get("sha256")
        != RECOVERY_RECEIPT_SHA256
        or lane.get("no_ubt_invoked") is not True
        or lane.get("error") is not None
    ):
        raise ContractError("support-kit lane-summary contract drifted")
    if recovery.get("status") != RECOVERY_STATUS:
        raise ContractError("support-kit failed-v001 recovery contract drifted")
    if (
        imported.get("$schema") != IMPORT_SCHEMA
        or imported.get("status") != IMPORT_STATUS
        or imported.get("baseline_sha256") != BASELINE_SHA256
        or imported.get("destination_namespace") != DESTINATION_NAMESPACE
        or imported.get("asset_count") != 12
        or imported.get("lod_count_per_asset") != 3
        or imported.get("source_fbx_count") != 36
        or imported.get("strict_per_asset_monotonic_triangles_verified") is not True
        or imported.get("exact_one_uv_channel_per_lod_verified") is not True
        or imported.get("new_material_or_texture_assets") != 0
        or imported.get("failures")
    ):
        raise ContractError("support-kit import-receipt contract drifted")
    if (
        fresh.get("$schema") != VALIDATION_SCHEMA
        or fresh.get("status") != VALIDATION_STATUS
        or fresh.get("baseline_sha256") != BASELINE_SHA256
        or fresh.get("destination_namespace") != DESTINATION_NAMESPACE
        or fresh.get("import_receipt", {}).get("sha256") != IMPORT_RECEIPT_SHA256
        or fresh.get("asset_count") != 12
        or fresh.get("lod_count_per_asset") != 3
        or fresh.get("fresh_process_proof", {}).get("distinct") is not True
        or fresh.get("target_package_hashes_unchanged_by_fresh_load") is not True
        or fresh.get(
            "source_config_saves_maps_and_existing_content_hashes_unchanged"
        )
        is not True
        or fresh.get("manual_lod_screen_sizes_persisted_after_fresh_process_load")
        is not True
        or fresh.get("auto_compute_lod_screen_size_disabled_on_all_assets") is not True
        or fresh.get("deterministic_material_bindings_persisted") is not True
        or fresh.get("deterministic_box_collision_persisted") is not True
        or fresh.get("floor_centred_pivots_and_dimensions_persisted") is not True
        or fresh.get("strict_per_asset_monotonic_triangles_persisted") is not True
        or fresh.get("exact_one_uv_channel_per_lod_persisted") is not True
        or fresh.get("new_material_or_texture_assets") != 0
        or fresh.get("failures")
    ):
        raise ContractError("support-kit fresh-load receipt contract drifted")

    rows = fresh.get("assets", {})
    target_after = fresh.get("target_packages_after", {})
    if set(rows) != set(ASSETS) or len(target_after) != len(ASSETS):
        raise ContractError("support-kit exact 12-asset inventory drifted")

    totals = [0, 0, 0]
    packages: dict[str, str] = {}
    material_bindings: dict[str, list[str]] = {}
    for key, (relative, expected_triangles, expected_hash) in ASSETS.items():
        row = rows[key]
        expected_object = object_path(relative)
        expected_package = package_path(relative)
        expected_disk_relative = disk_relative(relative)
        disk = root / expected_disk_relative
        target_key = expected_disk_relative.as_posix()
        target_record = target_after.get(target_key, {})
        lods = row.get("lods", [])
        if (
            row.get("asset_key") != key
            or row.get("object_path") != expected_object
            or row.get("lod_count") != 3
            or row.get("lod_screen_sizes") != EXPECTED_LOD_SCREEN_SIZES
            or row.get("lod_screen_size_auto_computed") is not False
            or len(lods) != 3
            or row.get("triangle_chain") != expected_triangles
            or row.get("strict_monotonic_triangles") is not True
            or row.get("simple_collision_count") != 1
            or row.get("convex_collision_count") != 0
            or row.get("nanite_enabled") is not False
            or target_record.get("sha256") != expected_hash
            or not disk.is_file()
            or sha256(disk) != expected_hash
        ):
            raise ContractError(f"support-kit package/asset contract drifted: {key}")
        for lod_index, lod in enumerate(lods):
            if (
                lod.get("lod") != lod_index
                or lod.get("triangles") != expected_triangles[lod_index]
                or lod.get("uv_channels") != 1
                or lod.get("bounds", {}).get("pivot_cm") != [0.0, 0.0, 0.0]
            ):
                raise ContractError(f"support-kit LOD contract drifted: {key}:LOD{lod_index}")
            totals[lod_index] += int(lod["triangles"])
        slots = row.get("global_material_slots", [])
        bindings = row.get("bound_materials", [])
        expected_bindings = [_material_object(slot) for slot in slots]
        if (
            not slots
            or any(slot not in MATERIAL_BINDINGS for slot in slots)
            or bindings != expected_bindings
            or any("WorldGrid" in value for value in bindings)
        ):
            raise ContractError(f"support-kit material binding drifted: {key}")
        packages[expected_package] = expected_hash
        material_bindings[expected_package] = bindings

    if totals != EXPECTED_TRIANGLE_TOTALS:
        raise ContractError(
            f"support-kit aggregate triangle totals drifted: {totals}"
        )
    if not all(re.fullmatch(r"[0-9A-F]{64}", value) for value in packages.values()):
        raise ContractError("support-kit package hash format drifted")
    return {
        "run_root": str(run_root),
        "lane_summary": {"path": str(lane_path), "sha256": LANE_SUMMARY_SHA256},
        "recovery_receipt": {
            "path": str(recovery_path),
            "sha256": RECOVERY_RECEIPT_SHA256,
        },
        "import_receipt": {"path": str(import_path), "sha256": IMPORT_RECEIPT_SHA256},
        "validation_receipt": {
            "path": str(fresh_path),
            "sha256": VALIDATION_RECEIPT_SHA256,
        },
        "baseline_sha256": BASELINE_SHA256,
        "destination_namespace": DESTINATION_NAMESPACE,
        "asset_count": len(packages),
        "lod_count_per_asset": 3,
        "lod_triangle_totals": totals,
        "packages": packages,
        "material_bindings": material_bindings,
        "writes_to_project": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--validation-receipt", type=Path)
    args = parser.parse_args()
    try:
        snapshot = validate(args.project_root, args.validation_receipt)
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"BODYSHOP_SUPPORT_KIT_NATIVE_V002_CONTRACT_FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(snapshot, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
