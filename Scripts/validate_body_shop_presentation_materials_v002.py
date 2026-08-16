"""Fresh-process, read-only validation of Body Shop Presentation Materials_v002."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0, str(PROJECT / "Scripts"))
from body_shop_support_kit_native_v002_contract import (  # noqa: E402
    ContractError as SupportKitContractError,
    validate as validate_support_kit,
)
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
LAYERED = DEST + "/M_LB_BodyShop_LayeredPaint_Master_v002"
FUNCTIONAL = DEST + "/M_LB_BodyShop_Functional_Master_v002"
BUILD = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_build.json"
REPAIR = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_sm6_repair.json"
HISM_REPAIR = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_hism_usage_repair_v001.json"
VISUAL_V003_VALIDATION = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v003_validation.json"
VISUAL_V004_VALIDATION = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/visual_readability_v004_validation.json"
MANAGEMENT_V005_PATCH = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/management_cutaway_v005_patch.json"
MANAGEMENT_V005_VALIDATION = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/management_cutaway_v005_validation.json"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_native_robot_support_kit_validation_v004.json"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
RESTORED_PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
EXPECTED_RESTORED_PRESS_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
TARGET_SCREENS = [1.0, 0.55, 0.25]
NATIVE_ROBOT_RUN_ROOT = (
    PROJECT
    / "Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T204134Z-19e41ca7"
)
NATIVE_ROBOT_LANE_SUMMARY = NATIVE_ROBOT_RUN_ROOT / "lane_summary_v001.json"
NATIVE_ROBOT_IMPORT_RECEIPT = NATIVE_ROBOT_RUN_ROOT / "import_receipt_v001.json"
NATIVE_ROBOT_VALIDATION_RECEIPT = (
    NATIVE_ROBOT_RUN_ROOT / "fresh_load_validation_receipt_v001.json"
)
NATIVE_ROBOT_LANE_SUMMARY_SHA256 = "B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73"
NATIVE_ROBOT_IMPORT_RECEIPT_SHA256 = "B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF"
NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256 = "9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA"
NATIVE_ROBOT_BASELINE_SHA256 = "D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31"
NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256 = "E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3"
NATIVE_ROBOT_IMPORT_STATUS = "PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT"
NATIVE_ROBOT_STATUS = "PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001"
NATIVE_ROBOT_LANE_STATUS = "PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001"
NATIVE_ROBOT_TRIANGLE_TOTALS = [2628, 1964, 1356]
NATIVE_ROBOT_ASSETS = {
    "Base": "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001",
    **{
        f"J{joint}": (
            "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/"
            f"SM_LB_BodyShopRobotNative_J{joint}_v001"
        )
        for joint in range(1, 7)
    },
    "CGun": "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001",
}
NATIVE_ROBOT_PACKAGE_HASHES = {
    "Base": "EB7975C71866AD9531FE8EBA93CAA14EDE06CC4333CCFBF88F965DF5E52E7000",
    "CGun": "7473FA6260B17333ABC5D2833736A657D093458CFA004DD862876096F407EFE1",
    "J1": "50C2A7065808D59C6666D52CC44F4BDB045E0B929350D9F821E5DEF027AE54C7",
    "J2": "E6D5FA37E12B14279FE23042C940B3EF2FB33F3D6EE9D7E0D659526F5A471230",
    "J3": "02D873DD7E6688AC60DD2E4D367A78742D6524CEDF80CABA876E20FD5B2D44C5",
    "J4": "A9F887F6B8FF3955CD48FA3BF132F6F24A00DAED1765194442AD7999048E997C",
    "J5": "EE26BCDD02B6F43132B5C2CCDB8F216B01CEDFA163748E8AC05A0CF5397D116F",
    "J6": "832AC4BAD232E5BDBC1675A1E46B64BDFA4A833C5CAF1B4478A8E9492BBA0D10",
}
ACTIVE_PROCEDURAL_MATERIAL_BUILD_MESHES = {
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001",
}
EXPECTED_BUILD_SHA256 = "507F5E5EB486B76FF154AD673D4F94B4102BAD35ADF9635EF91EFC4FA30DA013"
EXPECTED_SM6_REPAIR_SHA256 = "DD360164A76D8A3D8B42E951CFC7E3EDE3BF093C06C95B95D440F84EC4397F1D"
EXPECTED_HISM_REPAIR_SHA256 = "8EE7EF8DF2058525FE81ED328B5CA150FE643EBFBA30208795AF619B1A35E7CB"
EXPECTED_VISUAL_V003_VALIDATION_SHA256 = "522705A431FE12C94EA19ECD53F15CA53FE4863CA342265434076094E9679A0F"
EXPECTED_VISUAL_V004_VALIDATION_SHA256 = "956E08511F2AA840D71B94E07217DBA357EA955B701BA3A8C9F744AAAC11757E"
EXPECTED_MANAGEMENT_V005_PATCH_SHA256 = "8A305B26C838567FC3F26063B28F9D7FA65382F9A932F762A8CC3C4DD7F7ED50"
EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256 = "DCDBCBFA4D47FEBF21A22FD98F30ADC880D037519EBDBC6AE34BD7D4CE9F88D8"
EXPECTED_MANAGEMENT_V005_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"

PALETTE = {
    "M_LB_BS_CreamPaint": ("MI_LB_BodyShop_CreamPaint_v002", "layered", (0.637596874, 0.571124829, 0.381326011), 0.18, 0.54, 0.28, (0, 0, 0), 0.0),
    "M_LB_BS_BlackMotor": ("MI_LB_BodyShop_BlackMotor_v002", "layered", (0.014443844, 0.017641954, 0.021219010), 0.25, 0.56, 0.28, (0, 0, 0), 0.0),
    "M_LB_BS_StructuralLightGrey": ("MI_LB_BodyShop_StructuralLightGrey_v002", "functional", (0.318546778, 0.391572478, 0.450785783), 0.65, 0.32, 0.035, (0, 0, 0), 0.0),
    "M_LB_BS_BrushedSteel": ("MI_LB_BodyShop_BrushedSteel_v002", "functional", (0.147027266, 0.194617830, 0.234550582), 0.82, 0.27, 0.045, (0, 0, 0), 0.0),
    "M_LB_BS_GraphiteTooling": ("MI_LB_BodyShop_GraphiteTooling_v002", "functional", (0.010960094, 0.018500220, 0.024157632), 0.62, 0.34, 0.030, (0, 0, 0), 0.0),
    "M_LB_BS_EmeraldPanel": ("MI_LB_BodyShop_EmeraldPanel_v002", "functional", (0.003035270, 0.194617830, 0.086500462), 0.28, 0.34, 0.025, (0, 0, 0), 0.0),
    "M_LB_BS_SafetyYellow": ("MI_LB_BodyShop_SafetyYellow_v002", "functional", (0.887923118, 0.396755231, 0.0), 0.22, 0.36, 0.025, (0, 0, 0), 0.0),
    "M_LB_BS_VacuumRubber": ("MI_LB_BodyShop_VacuumRubber_v002", "functional", (0.003346536, 0.004776953, 0.006048833), 0.02, 0.74, 0.018, (0, 0, 0), 0.0),
    "M_LB_BS_ScannerLens": ("MI_LB_BodyShop_ScannerLens_v002", "functional", (0.002731743, 0.144128471, 0.262250658), 0.15, 0.22, 0.015, (0.0, 0.35, 0.65), 0.22),
    "M_LB_BS_StatusGreen": ("MI_LB_BodyShop_StatusGreen_v002", "functional", (0.015996293, 0.644479682, 0.212230757), 0.05, 0.24, 0.010, (0.015996293, 0.644479682, 0.212230757), 3.0),
    "M_LB_BS_StatusAmber": ("MI_LB_BodyShop_StatusAmber_v002", "functional", (1.0, 0.337163615, 0.009721217), 0.05, 0.24, 0.010, (1.0, 0.337163615, 0.009721217), 3.0),
    "M_LB_BS_StatusRed": ("MI_LB_BodyShop_StatusRed_v002", "functional", (0.745404210, 0.026241222, 0.048171824), 0.05, 0.24, 0.010, (0.745404210, 0.026241222, 0.048171824), 3.0),
}

lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
USAGE_PROPERTY = "used_with_instanced_static_meshes"
# Frozen v001 repair provenance only. Current release validation reads this key
# for the three procedural support meshes and never activates the six retired
# robot rows that made up the rest of the historical nine-mesh snapshot.
HISTORICAL_HISM_MESH_HASH_KEY = "all_9_final_meshes"


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_PRESENTATION_MATERIALS_V002_VALIDATION_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_file(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def native_robot_validation_snapshot() -> dict:
    evidence = (
        (NATIVE_ROBOT_LANE_SUMMARY, NATIVE_ROBOT_LANE_SUMMARY_SHA256),
        (NATIVE_ROBOT_IMPORT_RECEIPT, NATIVE_ROBOT_IMPORT_RECEIPT_SHA256),
        (NATIVE_ROBOT_VALIDATION_RECEIPT, NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256),
    )
    for path, expected_hash in evidence:
        if not path.is_file() or digest(path) != expected_hash:
            fail("exact final native robot evidence missing or changed: " + str(path))
    lane = json.loads(NATIVE_ROBOT_LANE_SUMMARY.read_text(encoding="utf-8-sig"))
    imported = json.loads(NATIVE_ROBOT_IMPORT_RECEIPT.read_text(encoding="utf-8-sig"))
    record = json.loads(
        NATIVE_ROBOT_VALIDATION_RECEIPT.read_text(encoding="utf-8-sig")
    )
    if (lane.get("status") != NATIVE_ROBOT_LANE_STATUS
            or lane.get("import_receipt", {}).get("sha256")
                != NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
            or lane.get("validation_receipt", {}).get("sha256")
                != NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256
            or lane.get("no_ubt_invoked") is not True
            or lane.get("error") is not None):
        fail("final native robot lane summary contract drift")
    if (imported.get("$schema")
            != "lineboss/audit/bodyshop-robot-native-v001-unreal-import/v1"
            or imported.get("status") != NATIVE_ROBOT_IMPORT_STATUS
            or imported.get("baseline_sha256") != NATIVE_ROBOT_BASELINE_SHA256
            or imported.get("clean_disposition_contract_sha256")
                != NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256
            or imported.get("asset_count") != 8
            or imported.get("lod_count_per_asset") != 3
            or imported.get("source_fbx_count") != 24
            or imported.get("failures")):
        fail("final native robot import receipt contract drift")
    if (record.get("baseline_sha256") != NATIVE_ROBOT_BASELINE_SHA256
            or record.get("clean_disposition_contract_sha256")
                != NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256
            or record.get("import_receipt_sha256")
                != NATIVE_ROBOT_IMPORT_RECEIPT_SHA256
            or record.get("status") != NATIVE_ROBOT_STATUS
            or record.get("asset_count") != 8
            or record.get("lod_count_per_asset") != 3
            or record.get("source_fbx_count") != 24
            or record.get("fresh_process_proof", {}).get("distinct") is not True
            or record.get("target_package_hashes_unchanged_by_fresh_load") is not True
            or record.get("config_and_existing_promoted_asset_hashes_unchanged") is not True
            or record.get("strict_per_asset_triangle_monotonicity") is not True
            or record.get("exactly_one_uv_channel_on_all_24_lods") is not True
            or record.get("manual_lod_screen_sizes_persisted_after_fresh_process_load") is not True
            or record.get("press_v913_map_sha256_unchanged")
                != "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
            or record.get("body_shop_map_sha256_unchanged")
                != EXPECTED_MANAGEMENT_V005_MAP_SHA256
            or record.get("failures")
            or set(record.get("assets", {})) != set(NATIVE_ROBOT_ASSETS)):
        fail("native robot fresh-load receipt contract drift")
    packages = {}
    triangle_totals = [0, 0, 0]
    for key, asset in NATIVE_ROBOT_ASSETS.items():
        row = record["assets"][key]
        expected_object = asset + "." + asset.rsplit("/", 1)[-1]
        expected_hash = row.get("package_after_load", {}).get("sha256")
        disk = PROJECT / Path(row.get("package_after_load", {}).get("path", ""))
        lods = row.get("lods", [])
        if (row.get("package_path") != asset
                or row.get("object_path") != expected_object
                or row.get("lod_count") != 3
                or len(lods) != 3
                or row.get("package_hash_unchanged_by_fresh_load") is not True
                or not isinstance(expected_hash, str)
                or expected_hash != NATIVE_ROBOT_PACKAGE_HASHES[key]
                or digest(disk) != expected_hash):
            fail("native robot package/receipt drift: " + key)
        for lod_index, lod in enumerate(lods):
            if (lod.get("uv_channels") != 1
                    or not isinstance(lod.get("triangles"), int)):
                fail("native robot per-LOD contract drift: " + key)
            triangle_totals[lod_index] += lod["triangles"]
        packages[asset] = expected_hash
    if triangle_totals != NATIVE_ROBOT_TRIANGLE_TOTALS:
        fail("native robot aggregate triangle totals drift")
    return {
        "lane_summary": str(NATIVE_ROBOT_LANE_SUMMARY),
        "lane_summary_sha256": NATIVE_ROBOT_LANE_SUMMARY_SHA256,
        "import_receipt": str(NATIVE_ROBOT_IMPORT_RECEIPT),
        "import_receipt_sha256": NATIVE_ROBOT_IMPORT_RECEIPT_SHA256,
        "receipt": str(NATIVE_ROBOT_VALIDATION_RECEIPT),
        "receipt_sha256": NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256,
        "baseline_sha256": NATIVE_ROBOT_BASELINE_SHA256,
        "clean_disposition_contract_sha256":
            NATIVE_ROBOT_CLEAN_DISPOSITION_CONTRACT_SHA256,
        "lod_triangle_totals": triangle_totals,
        "packages": packages,
    }


def close(actual, expected, tolerance=0.0002):
    return abs(float(actual) - float(expected)) <= tolerance


def colour_close(actual, expected):
    return all(close(value, target) for value, target in
               zip((actual.r, actual.g, actual.b), expected))


def main():
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if AUDIT.exists():
        fail("refusing to overwrite independent native-robot material validation receipt")
    if not BUILD.is_file():
        fail("build receipt missing")
    if digest(BUILD) != EXPECTED_BUILD_SHA256:
        fail("exact build receipt hash drift")
    build = json.loads(BUILD.read_text(encoding="utf-8-sig"))
    if build.get("$schema") != "lineboss/audit/bodyshop/presentation-materials-v002-build/v1" or build.get("status") != "PASS__ISOLATED_BODYSHOP_PRESENTATION_MATERIALS_V002_BUILT_AND_BOUND":
        fail("build gate has not passed")
    repair = None
    if not build.get("functional_compile_contract"):
        if not REPAIR.is_file():
            fail("functional-master persistence/SM6 repair gate is missing")
        if digest(REPAIR) != EXPECTED_SM6_REPAIR_SHA256:
            fail("exact functional-master persistence/SM6 repair receipt hash drift")
        repair = json.loads(REPAIR.read_text(encoding="utf-8-sig"))
        if (repair.get("$schema") != "lineboss/audit/bodyshop/presentation-materials-v002-functional-sm6-repair/v1"
                or repair.get("status") != "PASS__BODYSHOP_PRESENTATION_MATERIALS_V002_PERSISTENCE_AND_FUNCTIONAL_SM6_REPAIRED"
                or repair.get("initial_build_receipt_sha256") != digest(BUILD)):
            fail("functional-master persistence/SM6 repair gate has not passed")

    if not HISM_REPAIR.is_file() or digest(HISM_REPAIR) != EXPECTED_HISM_REPAIR_SHA256:
        fail("exact functional-master HISM usage repair receipt is missing or changed")
    hism_repair = json.loads(HISM_REPAIR.read_text(encoding="utf-8-sig"))
    if (hism_repair.get("$schema") != "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-repair-v001/v1"
            or hism_repair.get("status") != "PASS__BODYSHOP_FUNCTIONAL_MASTER_INSTANCED_STATIC_MESH_USAGE_REPAIRED"
            or hism_repair.get("functional_master", {}).get("usage_before") is not False
            or hism_repair.get("functional_master", {}).get("usage_after") is not True):
        fail("functional-master HISM usage repair gate has not passed")
    expected_pre_hism = (repair.get("functional_master", {}).get("sha256_after") if repair
                         else build.get("functional_master_sha256_after"))
    if (expected_pre_hism is None
            or hism_repair.get("functional_master", {}).get("sha256_before") != expected_pre_hism):
        fail("functional-master SM6 -> HISM receipt chain drift")

    if (not VISUAL_V003_VALIDATION.is_file()
            or digest(VISUAL_V003_VALIDATION) != EXPECTED_VISUAL_V003_VALIDATION_SHA256):
        fail("exact visual-readability v003 validation receipt is missing or changed")
    visual = json.loads(VISUAL_V003_VALIDATION.read_text(encoding="utf-8-sig"))
    if (visual.get("$schema") != "lineboss/audit/bodyshop/visual-readability-v003-validation/v1"
            or visual.get("status") != "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V003"):
        fail("visual-readability v003 validation gate has not passed")
    if (not VISUAL_V004_VALIDATION.is_file()
            or digest(VISUAL_V004_VALIDATION) != EXPECTED_VISUAL_V004_VALIDATION_SHA256):
        fail("exact visual-readability v004 validation receipt is missing or changed")
    visual_v004 = json.loads(VISUAL_V004_VALIDATION.read_text(encoding="utf-8-sig"))
    if (visual_v004.get("$schema") != "lineboss/audit/bodyshop/visual-readability-v004-validation/v1"
            or visual_v004.get("status") != "PASS__FRESH_RELOAD_BODYSHOP_VISUAL_READABILITY_V004"
            or visual_v004.get("failures")):
        fail("visual-readability v004 validation gate has not passed")
    if (visual_v004.get("prerequisites", {}).get("visual_v003", {}).get("sha256")
            != digest(VISUAL_V003_VALIDATION)):
        fail("visual-readability v003 -> v004 receipt chain drift")

    if (not MANAGEMENT_V005_PATCH.is_file()
            or digest(MANAGEMENT_V005_PATCH) != EXPECTED_MANAGEMENT_V005_PATCH_SHA256):
        fail("exact management-cutaway v005 patch receipt is missing or changed")
    management_patch = json.loads(MANAGEMENT_V005_PATCH.read_text(encoding="utf-8-sig"))
    if (management_patch.get("$schema") != "lineboss/audit/bodyshop/management-cutaway-v005-patch/v1"
            or management_patch.get("status") != "PASS__BODYSHOP_MANAGEMENT_CUTAWAY_V005_MAP_PATCHED"
            or management_patch.get("failures")
            or management_patch.get("changed_actor_count") != 18
            or management_patch.get("prerequisite", {}).get(
                "visual_readability_v004_validation", {}).get("sha256")
                != digest(VISUAL_V004_VALIDATION)
            or management_patch.get("map", {}).get("sha256_before")
                != visual_v004.get("map", {}).get("sha256")
            or management_patch.get("map", {}).get("sha256_after")
                != EXPECTED_MANAGEMENT_V005_MAP_SHA256):
        fail("visual-readability v004 -> management-cutaway v005 patch chain drift")

    if (not MANAGEMENT_V005_VALIDATION.is_file()
            or digest(MANAGEMENT_V005_VALIDATION) != EXPECTED_MANAGEMENT_V005_VALIDATION_SHA256):
        fail("exact management-cutaway v005 validation receipt is missing or changed")
    management_v005 = json.loads(MANAGEMENT_V005_VALIDATION.read_text(encoding="utf-8-sig"))
    management_prerequisites = management_v005.get("prerequisites", {})
    if (management_v005.get("$schema")
            != "lineboss/audit/bodyshop/management-cutaway-v005-validation/v1"
            or management_v005.get("status")
            != "PASS__FRESH_RELOAD_BODYSHOP_MANAGEMENT_CUTAWAY_V005"
            or management_v005.get("failures")
            or management_prerequisites.get(
                "visual_readability_v004_validation", {}).get("sha256")
                != digest(VISUAL_V004_VALIDATION)
            or management_prerequisites.get(
                "management_cutaway_v005_patch", {}).get("sha256")
                != digest(MANAGEMENT_V005_PATCH)
            or management_v005.get("map", {}).get("sha256")
                != management_patch.get("map", {}).get("sha256_after")
            or management_v005.get("map", {}).get("read_only_fresh_load_hash_unchanged") is not True):
        fail("management-cutaway v005 fresh validation chain drift")

    current_map_hash = digest(MAP_FILE)
    if (current_map_hash != EXPECTED_MANAGEMENT_V005_MAP_SHA256
            or current_map_hash != management_v005.get("map", {}).get("sha256")
            or visual.get("map", {}).get("sha256")
            != hism_repair.get("protected_hashes", {}).get("body_shop_map")):
        fail("protected current Body Shop map changed")
    if (visual_v004.get("cream_material", {}).get("unchanged_by_v004") is not True
            or visual_v004.get("cream_material", {}).get("sha256")
            != visual.get("cream_material", {}).get("sha256")):
        fail("visual-readability v004 did not preserve the v003 cream material")
    if digest(PRESS_FILE) != hism_repair.get("protected_hashes", {}).get("press_v913_map"):
        fail("protected Press v913 map changed")
    if digest(RESTORED_PRESS_FILE) != EXPECTED_RESTORED_PRESS_SHA256:
        fail("protected full restored Press map changed")
    native_robot = native_robot_validation_snapshot()
    try:
        native_support_kit = validate_support_kit(PROJECT)
    except SupportKitContractError as exc:
        fail("native support-kit v002 contract drift: " + str(exc))
    for path, expected in build.get("source_hashes_before_and_after", {}).items():
        disk = Path(path)
        if not disk.is_file() or digest(disk) != expected:
            fail("shared source provenance changed: " + path)

    layered = lib.load_asset(LAYERED)
    functional = lib.load_asset(FUNCTIONAL)
    if not isinstance(layered, unreal.Material) or not isinstance(functional, unreal.Material):
        fail("local master material missing")
    if not bool(functional.get_editor_property(USAGE_PROPERTY)):
        fail("functional master is missing MATUSAGE_InstancedStaticMeshes")
    if repair:
        if digest(package_file(LAYERED)) != repair.get("layered_master", {}).get("sha256_after"):
            fail("repaired layered-master package hash drift")
    if digest(package_file(FUNCTIONAL)) != hism_repair.get("functional_master", {}).get("sha256_after"):
        fail("HISM-repaired functional-master package hash drift")

    current_material_hashes = dict(
        hism_repair.get("protected_hashes", {}).get("other_13_material_assets", {}))
    current_material_hashes[FUNCTIONAL] = hism_repair.get("functional_master", {}).get("sha256_after")
    if len(current_material_hashes) != 14 or set(current_material_hashes) != set(
            [LAYERED, FUNCTIONAL] + [DEST + "/" + row[0] for row in PALETTE.values()]):
        fail("HISM receipt does not bind the exact 14-asset Materials_v002 namespace")
    for asset, expected_hash in current_material_hashes.items():
        if digest(package_file(asset)) != expected_hash:
            fail("current Materials_v002 package hash drift: " + asset)
    expressions = mel.get_material_expressions(functional)
    if (len([node for node in expressions if isinstance(node, unreal.MaterialExpressionDotProduct)]) != 1
            or len([node for node in expressions if isinstance(node, unreal.MaterialExpressionSine)]) != 1):
        fail("functional master DotProduct/Sine graph shape drift")
    mel.recompile_material(layered)
    mel.recompile_material(functional)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    assets = sorted({path.split(".", 1)[0] for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    expected_assets = sorted([LAYERED, FUNCTIONAL] + [DEST + "/" + row[0] for row in PALETTE.values()])
    if assets != expected_assets or any("Candidate_v004" in path for path in assets):
        fail("isolated exact asset inventory drift")
    instance_rows = {}
    for slot, (name, family, base, metallic, roughness, variation, emissive, strength) in PALETTE.items():
        path = DEST + "/" + name
        instance = lib.load_asset(path)
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail("missing semantic MIC: " + slot)
        parent = instance.get_editor_property("parent")
        expected_parent = layered if family == "layered" else functional
        if parent != expected_parent:
            fail("semantic MIC parent drift: " + slot)
        if family == "layered":
            if slot == "M_LB_BS_CreamPaint":
                visual_cream = visual.get("cream_material", {})
                visual_scalars = visual_cream.get("scalars", {})
                if (visual_cream.get("asset") != path
                        or visual_cream.get("sha256") != digest(package_file(path))):
                    fail("visual-readability v003 cream package gate drift")
                expected_layered = {
                    "BaseRoughness": visual_scalars.get("BaseRoughness"),
                    "RoughnessVariation": visual_scalars.get("RoughnessVariation"),
                    "TextureScale": visual_scalars.get("TextureScale"),
                    "NormalStrength": visual_scalars.get("NormalStrength"),
                    "DustAmount": visual_scalars.get("DustAmount"),
                    "WearContrast": visual_scalars.get("WearContrast"),
                    "PaintCoverageBias": visual_scalars.get("PaintCoverageBias"),
                }
            else:
                expected_layered = {
                    "BaseRoughness": roughness, "RoughnessVariation": variation,
                    "TextureScale": 18.0, "NormalStrength": 0.05,
                    "DustAmount": 0.035, "WearContrast": 2.45,
                    "PaintCoverageBias": 0.93,
                }
            if (not colour_close(mel.get_material_instance_vector_parameter_value(instance, "PaintColour"), base)
                    or any(not close(mel.get_material_instance_scalar_parameter_value(instance, parameter), value)
                           for parameter, value in expected_layered.items())):
                fail("layered restored parameter drift: " + slot)
        else:
            if (not colour_close(mel.get_material_instance_vector_parameter_value(instance, "BaseColour"), base)
                    or not close(mel.get_material_instance_scalar_parameter_value(instance, "Metallic"), metallic)
                    or not close(mel.get_material_instance_scalar_parameter_value(instance, "Roughness"), roughness)
                    or not close(mel.get_material_instance_scalar_parameter_value(instance, "RoughnessVariation"), variation)
                    or not colour_close(mel.get_material_instance_vector_parameter_value(instance, "EmissiveColour"), emissive)
                    or not close(mel.get_material_instance_scalar_parameter_value(instance, "EmissiveStrength"), strength)):
                fail("functional parameter drift: " + slot)
        instance_rows[slot] = {"asset": path, "parent": parent.get_path_name(),
                               "sha256": digest(package_file(path))}

    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    active_material_build_mesh_rows = {}
    historical_robot_material_build_row_count = 0
    for name, expected in build.get("mesh_packages", {}).items():
        if expected["asset"] not in ACTIVE_PROCEDURAL_MATERIAL_BUILD_MESHES:
            historical_robot_material_build_row_count += 1
            continue
        mesh = lib.load_asset(expected["asset"])
        if not isinstance(mesh, unreal.StaticMesh):
            fail("bound final mesh missing: " + name)
        slots = [str(row.get_editor_property("material_slot_name")) for row in mesh.get_editor_property("static_materials")]
        materials = [mesh.get_material(i).get_path_name() if mesh.get_material(i) else None for i in range(len(slots))]
        expected_materials = [DEST + "/" + PALETTE[slot][0] + "." + PALETTE[slot][0] for slot in slots]
        if (slots != expected["slots"] or materials != expected_materials
                or any("WorldGrid" in value for value in materials)
                or [int(mesh.get_num_triangles(i)) for i in range(mesh.get_num_lods())] != expected["triangles"]
                or [round(float(v), 4) for v in subsystem.get_lod_screen_sizes(mesh)] != TARGET_SCREENS
                or int(subsystem.get_simple_collision_count(mesh)) != 0
                or int(subsystem.get_convex_collision_count(mesh)) != 0
                or bool(subsystem.get_nanite_settings(mesh).get_editor_property("enabled"))):
            fail("final mesh material/geometry/LOD/collision contract drift: " + name)
        current_hash = digest(package_file(expected["asset"]))
        if current_hash != expected["sha256_after"]:
            fail("final mesh package hash drift: " + name)
        if current_hash != hism_repair.get("protected_hashes", {}).get(
                HISTORICAL_HISM_MESH_HASH_KEY, {}).get(expected["asset"]):
            fail("final mesh is not tied to the exact HISM repair pre/post snapshot: " + name)
        active_material_build_mesh_rows[name] = {
            "asset": expected["asset"], "slots": slots,
            "materials": materials, "sha256": current_hash,
            "release_role": "active_procedural_support",
        }
    if (set(row["asset"] for row in active_material_build_mesh_rows.values())
            != ACTIVE_PROCEDURAL_MATERIAL_BUILD_MESHES
            or historical_robot_material_build_row_count != 6):
        fail("historical material-build receipt did not resolve to 3 active procedural meshes and 6 retired robot rows")

    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True,
        include_hard_package_references=True, include_searchable_names=False,
        include_soft_management_references=False, include_hard_management_references=False)
    dependencies = sorted({str(dep) for asset in assets for dep in registry.get_dependencies(asset, options)})
    if any("Candidate_v004" in dep for dep in dependencies):
        fail("Candidate_v004 dependency entered the isolated material pack")
    required_textures = {
        "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Base_Color_Metal_Paint_Chips",
        "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_Normal_Metal_Paint_Chips",
        "/Game/Surface_Forge/Textures/Metal_Paint_Chips/T_ORD_Metal_Paint_Chips"}
    layered_dependencies = {str(dep) for dep in registry.get_dependencies(LAYERED, options)}
    if not required_textures.issubset(layered_dependencies):
        fail("local layered master is missing required Surface Forge dependencies")

    payload = {"$schema": "lineboss/audit/bodyshop/presentation-materials-v002-native-robot-support-kit-validation-v004/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__FRESH_RELOAD_BODYSHOP_PRESENTATION_MATERIALS_NATIVE_ROBOT_SUPPORT_KIT_V004",
        "build_receipt_sha256": digest(BUILD),
        "functional_sm6_repair_receipt_sha256": digest(REPAIR) if repair else None,
        "functional_hism_usage_repair_receipt_sha256": digest(HISM_REPAIR),
        "visual_readability_v003_validation_receipt_sha256": digest(VISUAL_V003_VALIDATION),
        "visual_readability_v004_validation_receipt_sha256": digest(VISUAL_V004_VALIDATION),
        "management_cutaway_v005_patch_receipt_sha256": digest(MANAGEMENT_V005_PATCH),
        "management_cutaway_v005_validation_receipt_sha256": digest(MANAGEMENT_V005_VALIDATION),
        "namespace": DEST,
        "assets": assets, "instances": instance_rows,
        "active_procedural_material_build_meshes": active_material_build_mesh_rows,
        "historical_robot_material_build_rows_excluded_from_current_release":
            historical_robot_material_build_row_count,
        "native_six_axis_robot": native_robot,
        "native_support_kit_v002": native_support_kit,
        "exact_material_namespace_hashes": current_material_hashes,
        "dependencies": dependencies, "required_surface_forge_textures": sorted(required_textures),
        "map_sha256_unchanged": digest(MAP_FILE),
        "protected_press_v913_sha256_unchanged": digest(PRESS_FILE),
        "protected_full_restored_press_sha256_unchanged": digest(RESTORED_PRESS_FILE),
        "functional_master_usage": {"property": USAGE_PROPERTY,
                                      "used_with_instanced_static_meshes": True},
        "world_grid_on_final_meshes": False, "candidate_v004_dependency": False,
        "writes_to_content_or_config": False, "failures": [], "promotion_authorized": False}
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_PRESENTATION_MATERIALS_NATIVE_ROBOT_SUPPORT_KIT_V004_VALIDATION_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
