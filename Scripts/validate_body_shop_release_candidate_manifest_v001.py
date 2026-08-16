"""Fail-closed manifest validation for one exact Body Shop Development package run.

The validator never searches Saved/ or historical logs for asset-name mentions.  Its
package proof is the IoStore listing generated from the archive passed on this command
line, tied to a fresh BuildCookRun receipt and staging directory from the same run.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from body_shop_support_kit_native_v002_contract import (
    ContractError as SupportKitContractError,
    validate as validate_support_kit,
)


MAP_PACKAGE = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MATERIAL_ROOT = "Content/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
MATERIAL_NAMES = (
    "M_LB_BodyShop_LayeredPaint_Master_v002.uasset",
    "M_LB_BodyShop_Functional_Master_v002.uasset",
    "MI_LB_BodyShop_BlackMotor_v002.uasset",
    "MI_LB_BodyShop_BrushedSteel_v002.uasset",
    "MI_LB_BodyShop_CreamPaint_v002.uasset",
    "MI_LB_BodyShop_EmeraldPanel_v002.uasset",
    "MI_LB_BodyShop_GraphiteTooling_v002.uasset",
    "MI_LB_BodyShop_SafetyYellow_v002.uasset",
    "MI_LB_BodyShop_ScannerLens_v002.uasset",
    "MI_LB_BodyShop_StatusAmber_v002.uasset",
    "MI_LB_BodyShop_StatusGreen_v002.uasset",
    "MI_LB_BodyShop_StatusRed_v002.uasset",
    "MI_LB_BodyShop_StructuralLightGrey_v002.uasset",
    "MI_LB_BodyShop_VacuumRubber_v002.uasset",
)

REQUIRED_SOURCE_ASSETS = {
    "prototype_map": "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap",
    "underbody_fixture": "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001.uasset",
    "vision_gate": "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.uasset",
    "handling_eight_cup": "Content/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.uasset",
    "body_skid": "Content/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/SM_LB_C2040_BIWBaseSkid_v001.uasset",
    "underbody_workpiece": "Content/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Workpiece/SM_LB_C2040_BIWBaseKit_Underbody_v001.uasset",
    "native_open_cgun": "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.uasset",
}
SUPPORT_SOURCE_ASSETS = {
    "support_electrical_cabinet": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Controls/SM_LB_BodyShopSupport_ElectricalCabinet_v002.uasset",
    "support_hmi_pedestal": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Controls/SM_LB_BodyShopSupport_HMIPedestal_v002.uasset",
    "support_component_service_pallet": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002.uasset",
    "support_empty_return_cart": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002.uasset",
    "support_panel_stillage_empty": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Empty_v002.uasset",
    "active_body_stillage_native_v002": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.uasset",
    "support_small_parts_bin_open": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsBin_Open_v002.uasset",
    "support_small_parts_crate_open": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002.uasset",
    "support_guard_gate_2m": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Safety/SM_LB_BodyShopSupport_GuardGate_2m_v002.uasset",
    "support_guard_panel_2m": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Safety/SM_LB_BodyShopSupport_GuardPanel_2m_v002.uasset",
    "support_extraction_pedestal": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Services/SM_LB_BodyShopSupport_ExtractionPedestal_v002.uasset",
    "support_utility_pedestal": "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Services/SM_LB_BodyShopSupport_UtilityPedestal_v002.uasset",
}
REQUIRED_SOURCE_ASSETS.update(SUPPORT_SOURCE_ASSETS)
for robot_part in ("Base", "J1", "J2", "J3", "J4", "J5", "J6"):
    REQUIRED_SOURCE_ASSETS[f"robot_{robot_part.lower()}"] = (
        "Content/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/"
        f"SM_LB_BodyShopRobotNative_{robot_part}_v001.uasset"
    )
for material_name in MATERIAL_NAMES:
    REQUIRED_SOURCE_ASSETS[f"material_{Path(material_name).stem.lower()}"] = (
        f"{MATERIAL_ROOT}/{material_name}"
    )

FINAL_NATIVE_ROBOT_RUN_RELATIVE = Path(
    "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T204134Z-19e41ca7"
)
FINAL_NATIVE_ROBOT_LANE_SUMMARY_SHA256 = "B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73"
FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256 = "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF"
FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256 = "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA"
FINAL_NATIVE_ROBOT_BASELINE_SHA256 = "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256 = "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
FINAL_NATIVE_ROBOT_TRIANGLE_TOTALS = [2628, 1964, 1356]
FULL_RESTORED_PRESS_RELATIVE = Path(
    "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
)
FULL_RESTORED_PRESS_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
FINAL_NATIVE_ROBOT_PACKAGES = {
    "Base": ("robot_base", "EB7975C71866AD9531FE8EBA93CAA14EDE06CC4333CCFBF88F965DF5E52E7000"),
    "CGun": ("native_open_cgun", "7473FA6260B17333ABC5D2833736A657D093458CFA004DD862876096F407EFE1"),
    "J1": ("robot_j1", "50C2A7065808D59C6666D52CC44F4BDB045E0B929350D9F821E5DEF027AE54C7"),
    "J2": ("robot_j2", "E6D5FA37E12B14279FE23042C940B3EF2FB33F3D6EE9D7E0D659526F5A471230"),
    "J3": ("robot_j3", "02D873DD7E6688AC60DD2E4D367A78742D6524CEDF80CABA876E20FD5B2D44C5"),
    "J4": ("robot_j4", "A9F887F6B8FF3955CD48FA3BF132F6F24A00DAED1765194442AD7999048E997C"),
    "J5": ("robot_j5", "EE26BCDD02B6F43132B5C2CCDB8F216B01CEDFA163748E8AC05A0CF5397D116F"),
    "J6": ("robot_j6", "832AC4BAD232E5BDBC1675A1E46B64BDFA4A833C5CAF1B4478A8E9492BBA0D10"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normal(path_or_text: str | Path) -> str:
    return str(path_or_text).replace("\\", "/").rstrip("/").lower()


def read_buildcookrun_log(path: Path) -> str:
    """Decode current-run UAT output without silently corrupting its command line."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    return raw.decode("utf-8")


def has_exact_buildcookrun_map_invocation(log_text: str) -> bool:
    """Require BuildCookRun and the exact Body Shop -map token on one log line."""
    normalized = log_text.replace("\\", "/")
    buildcookrun_token = re.compile(
        r"(?<!\S)[\"']?buildcookrun[\"']?(?=\s|$)", re.IGNORECASE
    )
    map_token = re.compile(
        rf"(?<!\S)[\"']?-map=[\"']?{re.escape(MAP_PACKAGE)}[\"']?(?=\s|$)",
        re.IGNORECASE,
    )
    return any(
        buildcookrun_token.search(line) and map_token.search(line)
        for line in normalized.splitlines()
    )


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def expected_package(relative: str) -> str:
    content_relative = relative.replace("\\", "/")[len("Content/") :]
    return "/game/" + content_relative.rsplit(".", 1)[0].lower()


def filename_matches(relative: str, candidate: str) -> bool:
    wanted = normal(relative)
    candidate_normal = normal(candidate).strip('"')
    return candidate_normal == wanted or candidate_normal.endswith("/" + wanted)


def read_listing_entries(listing_root: Path, failures: list[str]) -> tuple[list[dict], list[dict]]:
    listing_files = sorted(path for path in listing_root.rglob("*") if path.is_file())
    if not listing_files:
        failures.append("Current-run container listing directory is empty")
        return [], []

    entries: list[dict] = []
    file_records: list[dict] = []
    scopes_seen: set[str] = set()
    for listing in listing_files:
        if listing.suffix.lower() != ".csv":
            failures.append(f"Unexpected file in container-listing evidence: {listing.name}")
            continue
        relative_parts = listing.relative_to(listing_root).parts
        scope = relative_parts[0].lower() if len(relative_parts) > 1 else ""
        if scope not in {"archive", "stage"}:
            failures.append(f"IoStore listing is not scoped as archive/stage evidence: {listing}")
            continue
        scopes_seen.add(scope)
        raw = listing.read_text(encoding="utf-8-sig", errors="replace")
        file_records.append(
            {"path": str(listing), "scope": scope, "bytes": listing.stat().st_size,
             "sha256": sha256(listing)}
        )
        if "__legacylodstaging" in raw.lower():
            failures.append(f"Container listing includes forbidden __LegacyLODStaging: {listing.name}")

        reader = csv.DictReader(raw.splitlines())
        headers = {str(field).strip().lower() for field in (reader.fieldnames or [])}
        if not {"packagename", "filename"}.issubset(headers):
            failures.append(f"IoStore listing has no PackageName/Filename columns: {listing.name}")
            continue
        for row in reader:
            cleaned = {str(key).strip().lower(): str(value or "").strip() for key, value in row.items()}
            entries.append(
                {
                    "scope": scope,
                    "source": str(listing),
                    "package": normal(cleaned.get("packagename", "")),
                    "filename": normal(cleaned.get("filename", "")),
                    "container": cleaned.get("containername", ""),
                }
            )
    for required_scope in ("archive", "stage"):
        if required_scope not in scopes_seen:
            failures.append(f"Current-run IoStore evidence has no {required_scope} listing")
    return entries, file_records


def find_required_entry(relative: str, entries: list[dict], scope: str) -> dict | None:
    package = expected_package(relative)
    for entry in entries:
        if entry["scope"] == scope and (
            entry["package"] == package or filename_matches(relative, entry["filename"])
        ):
            return entry
    return None


def container_records(root: Path, failures: list[str], label: str) -> list[dict]:
    utocs = sorted(path for path in root.rglob("*.utoc") if path.name.lower() != "global.utoc")
    records = []
    if not utocs:
        failures.append(f"{label} contains no project IoStore .utoc container")
    for utoc in utocs:
        ucas = utoc.with_suffix(".ucas")
        if not ucas.is_file():
            failures.append(f"{label} IoStore toc has no matching .ucas: {utoc}")
            continue
        records.append(
            {
                "utoc": str(utoc),
                "utoc_bytes": utoc.stat().st_size,
                "utoc_sha256": sha256(utoc),
                "ucas": str(ucas),
                "ucas_bytes": ucas.stat().st_size,
                "ucas_sha256": sha256(ucas),
            }
        )
    return records


def executable_records(root: Path, failures: list[str], label: str) -> list[dict]:
    executables = sorted(root.rglob("LineBossCarFactory.exe"))
    if not executables:
        failures.append(f"{label} contains no LineBossCarFactory.exe")
    if not any("/linebosscarfactory/binaries/win64/" in normal(path) for path in executables):
        failures.append(f"{label} contains no packaged Win64 game binary")
    return [
        {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in executables
    ]


def validate_final_native_robot_authority(
    root: Path, validation_receipt: Path, failures: list[str]
) -> dict:
    run_root = root / FINAL_NATIVE_ROBOT_RUN_RELATIVE
    restored_press = root / FULL_RESTORED_PRESS_RELATIVE
    expected_validation = run_root / "fresh_load_validation_receipt_v001.json"
    lane_summary = run_root / "lane_summary_v001.json"
    import_receipt = run_root / "import_receipt_v001.json"
    expected = (
        (lane_summary, FINAL_NATIVE_ROBOT_LANE_SUMMARY_SHA256, "lane summary"),
        (import_receipt, FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256, "import receipt"),
        (expected_validation, FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256,
         "fresh-load validation receipt"),
    )
    if validation_receipt.resolve() != expected_validation.resolve():
        failures.append("Native robot validation argument is not the exact final 204134 receipt")
    if (not restored_press.is_file()
            or sha256(restored_press) != FULL_RESTORED_PRESS_SHA256):
        failures.append("Full restored Press map is missing or changed")
    for path, expected_hash, label in expected:
        if not path.is_file():
            failures.append(f"Final native robot {label} is missing: {path}")
        elif sha256(path) != expected_hash:
            failures.append(f"Final native robot {label} hash drifted: {path}")
    if any(not path.is_file() for path, _, _ in expected):
        return {}
    try:
        lane = json.loads(lane_summary.read_text(encoding="utf-8-sig"))
        imported = json.loads(import_receipt.read_text(encoding="utf-8-sig"))
        validated = json.loads(expected_validation.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"Final native robot evidence is malformed: {exc}")
        return {}
    if (lane.get("status")
            != "PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001"
            or lane.get("import_receipt", {}).get("sha256")
                != FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
            or lane.get("validation_receipt", {}).get("sha256")
                != FINAL_NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256
            or lane.get("no_ubt_invoked") is not True
            or lane.get("error") is not None):
        failures.append("Final native robot lane-summary contract drifted")
    if (imported.get("status")
            != "PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT"
            or imported.get("baseline_sha256") != FINAL_NATIVE_ROBOT_BASELINE_SHA256
            or imported.get("clean_disposition_contract_sha256")
                != FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256):
        failures.append("Final native robot import-receipt contract drifted")
    if (validated.get("status")
            != "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
            or validated.get("baseline_sha256") != FINAL_NATIVE_ROBOT_BASELINE_SHA256
            or validated.get("clean_disposition_contract_sha256")
                != FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256
            or validated.get("import_receipt_sha256")
                != FINAL_NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
            or validated.get("asset_count") != 8
            or validated.get("lod_count_per_asset") != 3
            or validated.get("source_fbx_count") != 24
            or validated.get("strict_per_asset_triangle_monotonicity") is not True
            or validated.get("exactly_one_uv_channel_on_all_24_lods") is not True
            or validated.get("manual_lod_screen_sizes_persisted_after_fresh_process_load") is not True
            or validated.get("failures")):
        failures.append("Final native robot validation-receipt contract drifted")
    assets = validated.get("assets", {})
    if set(assets) != set(FINAL_NATIVE_ROBOT_PACKAGES):
        failures.append("Final native robot asset-key inventory drifted")
        return {}
    triangle_totals = [0, 0, 0]
    package_records = {}
    for key, (source_label, expected_hash) in FINAL_NATIVE_ROBOT_PACKAGES.items():
        row = assets[key]
        expected_relative = REQUIRED_SOURCE_ASSETS[source_label]
        expected_package = "/Game/" + expected_relative[len("Content/"):-len(".uasset")]
        lods = row.get("lods", [])
        disk = root / expected_relative
        if (row.get("package_path") != expected_package
                or row.get("lod_count") != 3
                or len(lods) != 3
                or row.get("package_hash_unchanged_by_fresh_load") is not True
                or row.get("package_after_load", {}).get("sha256") != expected_hash
                or not disk.is_file()
                or (disk.is_file() and sha256(disk) != expected_hash)):
            failures.append(f"Final native robot package contract drifted: {key}")
        for lod_index, lod in enumerate(lods[:3]):
            if lod.get("uv_channels") != 1 or not isinstance(lod.get("triangles"), int):
                failures.append(f"Final native robot per-LOD contract drifted: {key}:LOD{lod_index}")
            else:
                triangle_totals[lod_index] += lod["triangles"]
        package_records[key] = {
            "source_label": source_label,
            "path": expected_relative,
            "sha256": expected_hash,
        }
    if triangle_totals != FINAL_NATIVE_ROBOT_TRIANGLE_TOTALS:
        failures.append("Final native robot aggregate triangle totals drifted")
    return {
        "lane_summary": {"path": str(lane_summary), "sha256": sha256(lane_summary)},
        "import_receipt": {"path": str(import_receipt), "sha256": sha256(import_receipt)},
        "validation_receipt": {
            "path": str(expected_validation), "sha256": sha256(expected_validation)
        },
        "baseline_sha256": FINAL_NATIVE_ROBOT_BASELINE_SHA256,
        "clean_disposition_contract_sha256":
            FINAL_NATIVE_ROBOT_CLEAN_DISPOSITION_SHA256,
        "lod_triangle_totals": triangle_totals,
        "asset_count": len(package_records),
        "lod_count_per_asset": 3,
        "packages": package_records,
        "protected_full_restored_press": {
            "path": str(restored_press),
            "sha256": sha256(restored_press) if restored_press.is_file() else None,
        },
    }


def validate_listing_receipt(
    receipt_path: Path,
    archive: Path,
    stage: Path,
    listing_root: Path,
    archive_containers: list[dict],
    stage_containers: list[dict],
    listing_records: list[dict],
    build_started: datetime,
    failures: list[str],
) -> dict | None:
    if not receipt_path.is_file():
        failures.append(f"Missing exact IoStore listing invocation receipt: {receipt_path}")
        return None
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"IoStore listing invocation receipt is malformed: {exc}")
        return None
    if receipt.get("schema") != (
        "cairnwell/body-shop/experimental-v001/iostore-listing-invocations/v1"
    ):
        failures.append("IoStore listing invocation receipt schema is not the v1 contract")
    if normal(receipt.get("archive_root", "")) != normal(archive):
        failures.append("IoStore listing receipt archive root does not match this run")
    if normal(receipt.get("stage_root", "")) != normal(stage):
        failures.append("IoStore listing receipt stage root does not match this run")

    records = receipt.get("records", [])
    if not isinstance(records, list) or not records:
        failures.append("IoStore listing invocation receipt has no records")
        return receipt
    expected_containers = {
        "archive": {normal(record["utoc"]): record for record in archive_containers},
        "stage": {normal(record["utoc"]): record for record in stage_containers},
    }
    expected_listings = {normal(record["path"]): record for record in listing_records}
    seen_containers: dict[str, set[str]] = {"archive": set(), "stage": set()}
    seen_listings: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.append(f"IoStore listing receipt record {index} is not an object")
            continue
        scope = str(record.get("scope", "")).lower()
        if scope not in {"archive", "stage"}:
            failures.append(f"IoStore listing receipt record {index} has invalid scope")
            continue
        package_root = archive if scope == "archive" else stage
        try:
            container = Path(str(record["container"])).resolve()
            ucas = Path(str(record["ucas"])).resolve()
            listing = Path(str(record["csv"])).resolve()
            started = parse_utc(str(record["started_utc"]))
            finished = parse_utc(str(record["finished_utc"]))
        except (KeyError, OSError, ValueError) as exc:
            failures.append(f"IoStore listing receipt record {index} is malformed: {exc}")
            continue
        container_key = normal(container)
        listing_key = normal(listing)
        expected_container = expected_containers[scope].get(container_key)
        expected_listing = expected_listings.get(listing_key)
        if not is_within(container, package_root):
            failures.append(f"IoStore listing receipt container escapes exact {scope} root: {container}")
        if expected_container is None:
            failures.append(f"IoStore listing receipt names an unexpected {scope} container: {container}")
        if normal(ucas) != normal(container.with_suffix(".ucas")):
            failures.append(f"IoStore listing receipt has mismatched .ucas path: {ucas}")
        if not is_within(listing, listing_root / scope):
            failures.append(f"IoStore listing receipt CSV escapes exact {scope} evidence: {listing}")
        if expected_listing is None or expected_listing.get("scope") != scope:
            failures.append(f"IoStore listing receipt names an unexpected {scope} CSV: {listing}")
        if record.get("exit_code") != 0:
            failures.append(f"IoStore listing receipt record {index} has nonzero exit code")
        if (finished < started or started.timestamp() < build_started.timestamp() - 2.0
                or finished > datetime.now(timezone.utc)):
            failures.append(f"IoStore listing receipt record {index} is not current to this build")
        if expected_container:
            if record.get("container_sha256") != expected_container["utoc_sha256"]:
                failures.append(f"IoStore .utoc hash differs from listing receipt: {container}")
            if record.get("ucas_sha256") != expected_container["ucas_sha256"]:
                failures.append(f"IoStore .ucas hash differs from listing receipt: {ucas}")
        if expected_listing and record.get("csv_sha256") != expected_listing["sha256"]:
            failures.append(f"IoStore CSV hash differs from listing receipt: {listing}")
        if expected_listing and not (
            started.timestamp() - 2.0 <= listing.stat().st_mtime <= finished.timestamp() + 120.0
        ):
            failures.append(f"IoStore CSV timestamp differs from its invocation receipt: {listing}")
        if container_key in seen_containers[scope]:
            failures.append(f"IoStore listing receipt repeats a {scope} container: {container}")
        if listing_key in seen_listings:
            failures.append(f"IoStore listing receipt repeats a CSV: {listing}")
        seen_containers[scope].add(container_key)
        seen_listings.add(listing_key)

    for scope in ("archive", "stage"):
        if seen_containers[scope] != set(expected_containers[scope]):
            failures.append(f"IoStore listing receipt does not cover the exact {scope} container set")
    if seen_listings != set(expected_listings):
        failures.append("IoStore listing receipt does not cover the exact CSV evidence set")
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--archive-root", required=True, type=Path)
    parser.add_argument("--stage-root", required=True, type=Path)
    parser.add_argument("--build-receipt", required=True, type=Path)
    parser.add_argument("--buildcookrun-log", required=True, type=Path)
    parser.add_argument("--container-listing-root", required=True, type=Path)
    parser.add_argument("--container-listing-receipt", required=True, type=Path)
    parser.add_argument("--native-robot-validation-receipt", required=True, type=Path)
    parser.add_argument("--native-support-validation-receipt", required=True, type=Path)
    parser.add_argument("--development-asset-registry", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    root = args.project_root.resolve()
    archive = args.archive_root.resolve()
    stage = args.stage_root.resolve()
    build_receipt_path = args.build_receipt.resolve()
    build_log = args.buildcookrun_log.resolve()
    listing_root = args.container_listing_root.resolve()
    listing_receipt_path = args.container_listing_receipt.resolve()
    native_robot_validation_receipt = args.native_robot_validation_receipt.resolve()
    native_support_validation_receipt = args.native_support_validation_receipt.resolve()
    output = args.output.resolve()
    run_root = output.parent
    failures: list[str] = []

    for path, label in ((root, "project"), (archive, "archive"), (stage, "stage"),
                        (listing_root, "container listing")):
        if not path.is_dir():
            failures.append(f"Missing {label} directory: {path}")
    for path, label in ((build_receipt_path, "BuildCookRun receipt"),
                        (build_log, "BuildCookRun log"),
                        (listing_receipt_path, "IoStore listing receipt"),
                        (native_robot_validation_receipt,
                         "final native robot validation receipt"),
                        (native_support_validation_receipt,
                         "final native support-kit validation receipt")):
        if not path.is_file():
            failures.append(f"Missing {label}: {path}")
    for evidence in (build_receipt_path, build_log, listing_root, listing_receipt_path, output):
        if not is_within(evidence, run_root):
            failures.append(f"Current-run evidence escapes receipt directory: {evidence}")

    build_receipt: dict = {}
    build_started = datetime.min.replace(tzinfo=timezone.utc)
    build_finished = datetime.max.replace(tzinfo=timezone.utc)
    if build_receipt_path.is_file():
        try:
            build_receipt = json.loads(build_receipt_path.read_text(encoding="utf-8-sig"))
            build_started = parse_utc(str(build_receipt["started_utc"]))
            build_finished = parse_utc(str(build_receipt["finished_utc"]))
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            failures.append(f"BuildCookRun receipt is malformed: {exc}")
        if build_receipt.get("schema") != "cairnwell/body-shop/experimental-v001/buildcookrun-invocation/v1":
            failures.append("BuildCookRun receipt schema is not the Body Shop v1 contract")
        if build_finished < build_started:
            failures.append("BuildCookRun receipt finishes before it starts")
        if build_receipt.get("exit_code") != 0:
            failures.append(f"BuildCookRun receipt exit code is not zero: {build_receipt.get('exit_code')}")
        if build_receipt.get("configuration") != "Development":
            failures.append("BuildCookRun receipt is not Development configuration")
        if build_receipt.get("map_package") != MAP_PACKAGE:
            failures.append("BuildCookRun receipt does not target the exact Body Shop map")
        if normal(build_receipt.get("archive_root", "")) != normal(archive):
            failures.append("BuildCookRun receipt archive path does not match this validation run")
        if normal(build_receipt.get("stage_root", "")) != normal(stage):
            failures.append("BuildCookRun receipt stage path does not match this validation run")
        if normal(build_receipt.get("log", "")) != normal(build_log):
            failures.append("BuildCookRun receipt log path does not match this validation run")
        if build_log.is_file() and build_receipt.get("log_sha256") != sha256(build_log):
            failures.append("BuildCookRun log hash differs from its current-run invocation receipt")
        command = [normal(value) for value in build_receipt.get("command_args", [])]
        required_args = {
            "buildcookrun",
            "-build",
            "-cook",
            "-platform=win64",
            "-clientconfig=development",
            f"-map={MAP_PACKAGE.lower()}",
            "-stage",
            "-pak",
            "-iostore",
            "-archive",
        }
        missing_args = sorted(required_args.difference(command))
        if missing_args:
            failures.append("BuildCookRun receipt is missing exact arguments: " + ", ".join(missing_args))
        if any("shipping" in value for value in command):
            failures.append("BuildCookRun receipt contains a Shipping argument")
        expected_support_cookdir = normal(
            "-cookdir=" + str(
                root / "Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002"
            )
        )
        if expected_support_cookdir not in command:
            failures.append("BuildCookRun receipt omits the exact native support-kit cook directory")

    build_log_record = None
    if build_log.is_file():
        build_log_record = {"path": str(build_log), "bytes": build_log.stat().st_size,
                            "sha256": sha256(build_log)}
        try:
            log_text = read_buildcookrun_log(build_log)
        except UnicodeDecodeError as exc:
            failures.append(f"Exact current BuildCookRun log encoding is unsupported/corrupt: {exc}")
        else:
            if not has_exact_buildcookrun_map_invocation(log_text):
                failures.append(
                    "Exact current BuildCookRun log does not identify the Body Shop map invocation"
                )
            if re.search(r"automationtool exiting with exitcode=(?!0\b)\d+|build failed|fatal error:",
                         log_text, re.IGNORECASE):
                failures.append("Exact current BuildCookRun log records a failed/fatal run")

    native_robot_authority = validate_final_native_robot_authority(
        root, native_robot_validation_receipt, failures
    )
    try:
        native_support_authority = validate_support_kit(
            root, native_support_validation_receipt
        )
    except (SupportKitContractError, OSError, json.JSONDecodeError) as exc:
        failures.append("Native support-kit v002 authority failed: " + str(exc))
        native_support_authority = {}
    source_records = []
    material_dir = root / MATERIAL_ROOT
    actual_material_names = sorted(path.name for path in material_dir.glob("*.uasset")) if material_dir.is_dir() else []
    if actual_material_names != sorted(MATERIAL_NAMES):
        failures.append(
            "Materials_v002 source family is not the exact 2-master/12-instance contract: "
            + json.dumps(actual_material_names)
        )
    for label, relative in REQUIRED_SOURCE_ASSETS.items():
        source = root / relative
        if not source.is_file():
            failures.append(f"Missing required source asset [{label}]: {relative}")
            continue
        source_records.append(
            {"label": label, "path": relative, "bytes": source.stat().st_size, "sha256": sha256(source)}
        )

    archive_containers = container_records(archive, failures, "Archive") if archive.is_dir() else []
    stage_containers = container_records(stage, failures, "Stage") if stage.is_dir() else []
    archive_executables = executable_records(archive, failures, "Archive") if archive.is_dir() else []
    stage_executables = executable_records(stage, failures, "Stage") if stage.is_dir() else []

    loose_forbidden = []
    for package_root in (archive, stage):
        if package_root.is_dir():
            loose_forbidden.extend(path for path in package_root.rglob("*") if "__legacylodstaging" in normal(path))
    if loose_forbidden:
        failures.append("Stage/archive contains loose forbidden __LegacyLODStaging path(s)")

    archive_container_hashes = {
        Path(record["utoc"]).name.lower(): (record["utoc_sha256"], record["ucas_sha256"])
        for record in archive_containers
    }
    stage_container_hashes = {
        Path(record["utoc"]).name.lower(): (record["utoc_sha256"], record["ucas_sha256"])
        for record in stage_containers
    }
    if archive_container_hashes != stage_container_hashes:
        failures.append("Archive and stage project IoStore container hashes differ")

    entries, listing_records = read_listing_entries(listing_root, failures) if listing_root.is_dir() else ([], [])
    listing_invocation_receipt = validate_listing_receipt(
        listing_receipt_path, archive, stage, listing_root,
        archive_containers, stage_containers, listing_records, build_started, failures
    )
    inclusion = {}
    for label, relative in REQUIRED_SOURCE_ASSETS.items():
        archive_match = find_required_entry(relative, entries, "archive")
        stage_match = find_required_entry(relative, entries, "stage")
        inclusion[label] = {
            "required_source_path": relative,
            "expected_package": expected_package(relative),
            "archive_present": archive_match is not None,
            "archive_evidence": archive_match,
            "stage_present": stage_match is not None,
            "stage_evidence": stage_match,
        }
        if archive_match is None:
            failures.append(f"Exact current archive listing omits required asset [{label}]: {relative}")
        if stage_match is None:
            failures.append(f"Exact current stage listing omits required asset [{label}]: {relative}")

    freshness_floor = build_started.timestamp() - 2.0
    listing_freshness_ceiling = datetime.now(timezone.utc).timestamp() + 5.0
    for record in listing_records:
        listing = Path(record["path"])
        if not (freshness_floor <= listing.stat().st_mtime <= listing_freshness_ceiling):
            failures.append(f"Container listing is not timestamped to the exact BuildCookRun: {listing}")

    development_registry_record = None
    if args.development_asset_registry:
        registry = args.development_asset_registry.resolve()
        if not registry.is_file():
            failures.append(f"Current-run DevelopmentAssetRegistry is missing: {registry}")
        elif not is_within(registry, run_root):
            failures.append("DevelopmentAssetRegistry evidence escapes the current run directory")
        else:
            development_registry_record = {
                "path": str(registry), "bytes": registry.stat().st_size, "sha256": sha256(registry)
            }
            if not (freshness_floor <= registry.stat().st_mtime
                    <= build_finished.timestamp() + 120.0):
                failures.append("DevelopmentAssetRegistry copy is not timestamped to this BuildCookRun")

    payload = {
        "$schema": "cairnwell/body-shop/experimental-v001/package-manifest-validation/v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_MANIFEST_EXACT_CONTAINER_V002"
        if not failures else "FAIL__BODY_SHOP_DEVELOPMENT_PACKAGE_MANIFEST_EXACT_CONTAINER_V002",
        "evidence_policy": "exact current BuildCookRun receipt + fresh stage/archive + hashed direct IoStore listing invocations; no historical-log search",
        "project_root": str(root),
        "archive_root": str(archive),
        "stage_root": str(stage),
        "build_receipt": build_receipt,
        "build_log": build_log_record,
        "development_asset_registry": development_registry_record,
        "native_six_axis_robot": native_robot_authority,
        "native_support_kit_v002": native_support_authority,
        "source_required_assets": source_records,
        "archive_containers": archive_containers,
        "stage_containers": stage_containers,
        "archive_executables": archive_executables,
        "stage_executables": stage_executables,
        "container_listing_files": listing_records,
        "container_listing_invocation_receipt": listing_invocation_receipt,
        "container_required_asset_inclusion": inclusion,
        "forbidden_legacy_lod_staging": [str(path) for path in loose_forbidden],
        "failures": failures,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(payload["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
