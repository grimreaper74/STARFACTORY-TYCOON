"""Fresh-process, read-only and live-PIE validation of Body Shop HISM usage.

This validator is independent of the presentation implementation. It is pinned
to the exact v005 Body map, current compiled presentation source, Press v913,
14-package Materials_v002 namespace, the exact fresh-loaded eight-asset native
six-axis robot family, active procedural presentation meshes and repair receipt
hashes. It loads the saved Body Shop map, enters PIE long enough to
exercise all four skid-conveyor cells and the underbody floor-paint batches,
then proves that no protected package or source file changed.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

PROJECT = Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0, str(PROJECT / "Scripts"))
from body_shop_support_kit_native_v002_contract import (  # noqa: E402
    validate as validate_support_kit,
)
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
FUNCTIONAL = DEST + "/M_LB_BodyShop_Functional_Master_v002"
MAP_ASSET = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
RESTORED_PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"
DEFAULT_GAME_FILE = PROJECT / "Config/DefaultGame.ini"
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
REPAIR_RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_hism_usage_repair_v001.json"
AUDIT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_hism_usage_validation_v004.json"
USAGE_PROPERTY = "used_with_instanced_static_meshes"
BASIC_SHAPE_MATERIAL = "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"
BASIC_SHAPE_CUBE = "/Engine/BasicShapes/Cube.Cube"

EXPECTED_REPAIR_RECEIPT_SHA256 = "8EE7EF8DF2058525FE81ED328B5CA150FE643EBFBA30208795AF619B1A35E7CB"
EXPECTED_MAP_SHA256 = "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F"
EXPECTED_PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
EXPECTED_RESTORED_PRESS_SHA256 = "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5"
EXPECTED_DEFAULT_GAME_SHA256 = "4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B"

EXPECTED_PRESENTATION_SOURCE_HASHES = {
    "Source/LineBossCarFactory/LBBodyShopCellActor.h":
        "EF109269B19312936CCAD8F658D0DC473798C84C6F8D14B4C42CD33EF49DAA4A",
    "Source/LineBossCarFactory/LBBodyShopCellActor.cpp":
        "F325580675C4CC9A4E4C70A573EC52BFCCFA422E51994924CDC3BA6D4D84B103",
    "Source/LineBossCarFactory/LBBodyShopCellPresentationTests.cpp":
        "601C423BAAD0CD20FE3DBD39FB84CDC528ECA93CEBDD0BE51406F1488DEBDFDB",
    "Source/LineBossCarFactory/LBBodyShopRobotActor.h":
        "456B123DB39F9463E9E8524F82AB4883A0C9979DBB8D24969217031BEAC05BF8",
    "Source/LineBossCarFactory/LBBodyShopRobotActor.cpp":
        "6D0F6D2F8EFDD46642A748BC299690BC6B36860F53C5E0EB535D0A0BD3DBE600",
    "Source/LineBossCarFactory/LBBodyShopPrototypeGameMode.h":
        "158DBFFD439D38ADFA86FDA506D013F69A05101B9F5CB597E32FDA983274904A",
    "Source/LineBossCarFactory/LBBodyShopPrototypeGameMode.cpp":
        "ECCA312F31715B9A0DDEDDD29EE234B6CFEDDA6E5DA1467B4553BA9B57375D9E",
    "Source/LineBossCarFactory/LBBodyShopPrototypeRuntime.h":
        "E0C94B23FAB4BA2061895E633D1C47C2204AFC687603BF8955A28C82453D92BE",
    "Source/LineBossCarFactory/LBBodyShopPrototypeRuntime.cpp":
        "2FB99D2D5903441B05619DD65EA0E9F29CC3DE1EBD70DF088473E3BF005970D2",
    "Source/LineBossCarFactory/LBBodyShopPrototypeRuntimeTests.cpp":
        "D24670FBF780FDCF79A0F896A5A5E1DB81FC88D3FB9FB700BA1E566D664B0C04",
    "Source/LineBossCarFactory/LBBodyShopServiceDressingActor.h":
        "32F03835C8E87B25CB3743EEC434E2B8C2E6E2C6F80D5855FAEFF61F92FD7EEA",
    "Source/LineBossCarFactory/LBBodyShopServiceDressingActor.cpp":
        "5EE90E11BAE87DB2949F5D45A523FFEB899A3FDBE9D3C0EBAFC0305300F43AAC",
    "Source/LineBossCarFactory/LBBodyShopServiceDressingActorTests.cpp":
        "9EB7F1983CA58D847B5578F4D8B36A1C01F694436D3251CF5CD043184D41AD61",
    "Source/LineBossCarFactory/LBBodyShopServiceDressingIntegrationTests.cpp":
        "08C4DE3E2194097F40056768BCD9BD5349D3583E6F3D536B97ACDA44DEEC7CD7",
    "Source/LineBossCarFactory/LBBodyShopPackagedPerformanceBridgeTests.cpp":
        "12DB12B31F6165FC08D80F71955628DDBA8EAB0044A67783F93A31731DE71C2B",
}

EXPECTED_MATERIAL_HASHES = {
    DEST + "/M_LB_BodyShop_Functional_Master_v002": "F04868806F50DAEF5D1792649E7CCB0DFEC4D5333F340A8D6E6B8A65097EC82B",
    DEST + "/M_LB_BodyShop_LayeredPaint_Master_v002": "10380C5D9DD24072C90999EBF8573E5BB4A6668FC5588C8950A41FF1BD175911",
    DEST + "/MI_LB_BodyShop_BlackMotor_v002": "F0F5DB61EB363B2987992C4774F79C530CF7D0BBC72B4792EAC2067237DB8051",
    DEST + "/MI_LB_BodyShop_BrushedSteel_v002": "A0F6B3A8B9B6928484526968E0A59845571C51023091C75A98E1B6DCA80A1E44",
    DEST + "/MI_LB_BodyShop_CreamPaint_v002": "7FEAC6A1ED633AA6FB36D09BA74F144CD194FC5C60E11E189068E0C761509E25",
    DEST + "/MI_LB_BodyShop_EmeraldPanel_v002": "F139E15987AA6D8807895CA490F0DEECDA1B106AFB392DC8166046A09373DE18",
    DEST + "/MI_LB_BodyShop_GraphiteTooling_v002": "67B70AB8286E55A0CDD60D8B4F82C17355D66F5901AC9D6280BFC2CA0E0A91D3",
    DEST + "/MI_LB_BodyShop_SafetyYellow_v002": "62538D9449AC456387B94116692A927BE6CDF93494DC109A4B9213D2288393DD",
    DEST + "/MI_LB_BodyShop_ScannerLens_v002": "ABA56A12D79C0F7AD09FE1F668A2BD6BD6A5DAFEC085D69493B4C8DBB3DAEC40",
    DEST + "/MI_LB_BodyShop_StatusAmber_v002": "2108F30645A41544D7C467F8E0EA43CD74379894C5DB93084D942E8310BB24FF",
    DEST + "/MI_LB_BodyShop_StatusGreen_v002": "FD01422DD21BD311DBDA64E2145450DB86BABF56C4E3AFE2D6D0A5C97A6733D7",
    DEST + "/MI_LB_BodyShop_StatusRed_v002": "F94C3D563424BFE79E759CD982EA2901D36EFD40762EA7973A99BD042E4CBC01",
    DEST + "/MI_LB_BodyShop_StructuralLightGrey_v002": "B1609764D304E1B18E1C1131DFFF6BB03A33705AE81751720E4BBF5A7747847C",
    DEST + "/MI_LB_BodyShop_VacuumRubber_v002": "BB71CFA36236CF592155C2641BE3E853CDA01A419BA1A49C79FEE2060D32D4EF",
}

EXPECTED_EXISTING_PRESENTATION_MESH_HASHES = {
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001": "262AB2C8F5289465DB3547BEA11DFCB072721C4A931E6EC81E9723CE2483BDAE",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001": "61BF706DF4306873381566A56A0EDD9C1B1A0E7949A07C5928AE79A4F58657A2",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001": "53D7443AA524CCF655AFA82BCD9C3950D9C559EA2F41D93E10309B74B0563C71",
}

WARNING_ASSETS = sorted([
    DEST + "/MI_LB_BodyShop_StructuralLightGrey_v002",
    DEST + "/MI_LB_BodyShop_BrushedSteel_v002",
    DEST + "/MI_LB_BodyShop_SafetyYellow_v002",
])
WARNING_OBJECTS = {asset + "." + asset.rsplit("/", 1)[-1] for asset in WARNING_ASSETS}
EXPECTED_HISM_COMPONENTS = {
    "SkidConveyorStructure": WARNING_ASSETS[2],
    "SkidConveyorRollers": WARNING_ASSETS[0],
    "SkidConveyorSafety": WARNING_ASSETS[1],
}
EXPECTED_CONVEYOR_CELL_COUNT = 4
EXPECTED_CONVEYOR_HISM_ROW_COUNT = 12
EXPECTED_FLOOR_HISM_COUNTS = {
    "CellFloorWorkingZone": 2,
    "CellFloorSafetyMarking": 6,
}
EXPECTED_SERVICE_HISM = {
    "EmptyReturnCartNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_EmptyReturnCart_v002."
        "SM_LB_BodyShopSupport_EmptyReturnCart_v002",
        6,
    ),
    "ComponentServicePalletNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_ComponentServicePallet_v002."
        "SM_LB_BodyShopSupport_ComponentServicePallet_v002",
        3,
    ),
    "EmptySmallPartsCrateNativeV002Instances": (
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/"
        "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002."
        "SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002",
        3,
    ),
}
EXPECTED_SERVICE_ACTOR_NAME = "LB_BodyShop_ServiceDressing_v002"
EXPECTED_SERVICE_TAGS = {
    "LB.BodyShop.ServiceDressing.v002",
    "LB.Asset.CleanRoomNative.v002",
    "LB.NotProcessWIP",
}

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
started = time.monotonic()
phase_started = started
phase = "wait_world"
tick_handle = None
terminal_detail = ""
terminal_written = False

payload = {
    "$schema": "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-validation-v004/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "IN_PROGRESS",
    "fresh_process": True,
    "read_only_content_validation": True,
    "shutdown_strategy": "END_PIE_THEN_UNREGISTER_SLATE_CALLBACK_THEN_RELEASE_PYTHON_KEEP_ALIVE",
    "repair_receipt_sha256": None,
    "functional_master_usage": {},
    "live_pie": {},
    "protected_hashes_before": {},
    "protected_hashes_after": {},
    "failures": [],
}


def digest(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError("missing protected file: " + str(path))
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_file(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def asset_hashes(expected: dict[str, str], label: str) -> dict[str, str]:
    actual = {asset: digest(package_file(asset)) for asset in expected}
    drift = {asset: {"actual": actual[asset], "expected": sha}
             for asset, sha in expected.items() if actual[asset] != sha}
    if drift:
        raise RuntimeError(label + " hash drift: " + json.dumps(drift, sort_keys=True))
    return actual


def native_robot_validation_snapshot() -> dict:
    evidence = (
        (NATIVE_ROBOT_LANE_SUMMARY, NATIVE_ROBOT_LANE_SUMMARY_SHA256),
        (NATIVE_ROBOT_IMPORT_RECEIPT, NATIVE_ROBOT_IMPORT_RECEIPT_SHA256),
        (NATIVE_ROBOT_VALIDATION_RECEIPT, NATIVE_ROBOT_VALIDATION_RECEIPT_SHA256),
    )
    for path, expected_hash in evidence:
        if not path.is_file() or digest(path) != expected_hash:
            raise RuntimeError(
                "exact final native robot evidence missing or changed: " + str(path)
            )
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
        raise RuntimeError("final native robot lane summary contract drift")
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
        raise RuntimeError("final native robot import receipt contract drift")
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
            or record.get("press_v913_map_sha256_unchanged") != EXPECTED_PRESS_SHA256
            or record.get("body_shop_map_sha256_unchanged") != EXPECTED_MAP_SHA256
            or record.get("failures")):
        raise RuntimeError("native robot fresh-load receipt contract drift")
    rows = record.get("assets", {})
    if set(rows) != set(NATIVE_ROBOT_ASSETS):
        raise RuntimeError("native robot fresh-load asset-key inventory drift")
    packages = {}
    triangle_totals = [0, 0, 0]
    for key, expected_asset in NATIVE_ROBOT_ASSETS.items():
        row = rows[key]
        expected_object = expected_asset + "." + expected_asset.rsplit("/", 1)[-1]
        disk = PROJECT / Path(row.get("package_after_load", {}).get("path", ""))
        expected_hash = row.get("package_after_load", {}).get("sha256")
        lods = row.get("lods", [])
        if (row.get("package_path") != expected_asset
                or row.get("object_path") != expected_object
                or row.get("lod_count") != 3
                or len(lods) != 3
                or row.get("package_hash_unchanged_by_fresh_load") is not True
                or not isinstance(expected_hash, str)
                or expected_hash != NATIVE_ROBOT_PACKAGE_HASHES[key]
                or digest(disk) != expected_hash):
            raise RuntimeError("native robot package/receipt drift: " + key)
        for lod_index, lod in enumerate(lods):
            if (lod.get("uv_channels") != 1
                    or not isinstance(lod.get("triangles"), int)):
                raise RuntimeError("native robot per-LOD contract drift: " + key)
            triangle_totals[lod_index] += lod["triangles"]
        packages[expected_asset] = expected_hash
    if triangle_totals != NATIVE_ROBOT_TRIANGLE_TOTALS:
        raise RuntimeError("native robot aggregate triangle totals drift")
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


def presentation_source_hashes() -> dict[str, str]:
    actual = {relative: digest(PROJECT / Path(relative))
              for relative in EXPECTED_PRESENTATION_SOURCE_HASHES}
    drift = {relative: {"actual": actual[relative], "expected": expected}
             for relative, expected in EXPECTED_PRESENTATION_SOURCE_HASHES.items()
             if actual[relative] != expected}
    if drift:
        raise RuntimeError("Body Shop presentation source hash drift: "
                           + json.dumps(drift, sort_keys=True))
    return actual


def protected_snapshot() -> dict:
    body_map = digest(MAP_FILE)
    press = digest(PRESS_FILE)
    restored_press = digest(RESTORED_PRESS_FILE)
    default_game = digest(DEFAULT_GAME_FILE)
    if body_map != EXPECTED_MAP_SHA256:
        raise RuntimeError("Body Shop map hash drift: " + body_map)
    if press != EXPECTED_PRESS_SHA256:
        raise RuntimeError("protected Press v913 hash drift: " + press)
    if restored_press != EXPECTED_RESTORED_PRESS_SHA256:
        raise RuntimeError("protected full restored Press hash drift: " + restored_press)
    if default_game != EXPECTED_DEFAULT_GAME_SHA256:
        raise RuntimeError("DefaultGame.ini support cook-root authority drift: " + default_game)
    native_robot = native_robot_validation_snapshot()
    native_support_kit = validate_support_kit(PROJECT)
    return {
        "body_shop_map": body_map,
        "press_v913_map": press,
        "press_full_factory_restored_v001_map": restored_press,
        "default_game_with_native_cook_roots": default_game,
        "presentation_source": presentation_source_hashes(),
        "materials_v002": asset_hashes(EXPECTED_MATERIAL_HASHES, "Materials_v002"),
        "existing_active_presentation_meshes": asset_hashes(
            EXPECTED_EXISTING_PRESENTATION_MESH_HASHES,
            "existing active Body Shop presentation meshes",
        ),
        "native_six_axis_robot": native_robot,
        "native_support_kit_v002": native_support_kit,
    }


def static_contract() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        raise RuntimeError("project identity drift")
    if AUDIT.exists():
        raise RuntimeError("refusing to overwrite independent validation receipt")
    repair_hash = digest(REPAIR_RECEIPT)
    if repair_hash != EXPECTED_REPAIR_RECEIPT_SHA256:
        raise RuntimeError("repair receipt hash drift: " + repair_hash)
    payload["repair_receipt_sha256"] = repair_hash
    payload["protected_hashes_before"] = protected_snapshot()

    assets = sorted({path.split(".", 1)[0]
                     for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    if assets != sorted(EXPECTED_MATERIAL_HASHES):
        raise RuntimeError("exact 14-asset Materials_v002 inventory drift: " + str(assets))
    functional = lib.load_asset(FUNCTIONAL)
    if not isinstance(functional, unreal.Material):
        raise RuntimeError("functional master missing or wrong class")
    usage = bool(functional.get_editor_property(USAGE_PROPERTY))
    if not usage:
        raise RuntimeError("functional master lost MATUSAGE_InstancedStaticMeshes after fresh reload")
    payload["functional_master_usage"] = {
        "asset": FUNCTIONAL,
        "usage_property": USAGE_PROPERTY,
        "used_with_instanced_static_meshes": usage,
        "sha256": EXPECTED_MATERIAL_HASHES[FUNCTIONAL],
    }
    for target in WARNING_ASSETS:
        instance = lib.load_asset(target)
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            raise RuntimeError("warning target is not a MIC: " + target)
        if instance.get_editor_property("parent") != functional:
            raise RuntimeError("warning MIC parent drift: " + target)

    native_snapshot = payload["protected_hashes_before"]["native_six_axis_robot"]
    if len(native_snapshot.get("packages", {})) != 8:
        raise RuntimeError("native six-axis robot package protection is incomplete")


def exposed_bool(component, property_name: str) -> dict:
    """Read optional UPROPERTY state without making engine exposure a false failure."""
    try:
        return {"exposed": True, "value": bool(component.get_editor_property(property_name))}
    except Exception:
        return {"exposed": False, "value": None}


def floor_visual_only_contract(component) -> dict:
    collision = component.get_collision_enabled()
    state = {
        "collision_enabled": str(collision),
        "generate_overlap_events": exposed_bool(component, "generate_overlap_events"),
        "can_ever_affect_navigation": exposed_bool(component, "can_ever_affect_navigation"),
        "cast_shadow": exposed_bool(component, "cast_shadow"),
        "receives_decals": exposed_bool(component, "receives_decals"),
        "collision_responses": {},
    }
    if collision != unreal.CollisionEnabled.NO_COLLISION:
        raise RuntimeError(component.get_name() + " is not visual-only: collision is "
                           + str(collision))
    for key in ("generate_overlap_events", "can_ever_affect_navigation",
                "cast_shadow", "receives_decals"):
        if state[key]["exposed"] and state[key]["value"]:
            raise RuntimeError(component.get_name() + " is not visual-only: " + key)

    # Validate representative engine and gameplay channels when Python exposes
    # the inherited primitive-component query. NoCollision is still mandatory
    # above even if a future engine build omits one of these channel wrappers.
    for channel_name, channel in (
        ("world_static", unreal.CollisionChannel.ECC_WORLD_STATIC),
        ("world_dynamic", unreal.CollisionChannel.ECC_WORLD_DYNAMIC),
        ("pawn", unreal.CollisionChannel.ECC_PAWN),
        ("visibility", unreal.CollisionChannel.ECC_VISIBILITY),
        ("camera", unreal.CollisionChannel.ECC_CAMERA),
        ("physics_body", unreal.CollisionChannel.ECC_PHYSICS_BODY),
        ("vehicle", unreal.CollisionChannel.ECC_VEHICLE),
    ):
        try:
            response = component.get_collision_response_to_channel(channel)
            expected = unreal.CollisionResponseType.ECR_IGNORE
            response_numeric = getattr(response, "value", None)
            expected_numeric = getattr(expected, "value", None)
            if response_numeric is None:
                try:
                    response_numeric = int(response)
                except (TypeError, ValueError):
                    pass
            if expected_numeric is None:
                try:
                    expected_numeric = int(expected)
                except (TypeError, ValueError):
                    pass
            response_text = str(response)
            state["collision_responses"][channel_name] = {
                "exposed": True,
                "value": response_text,
                "numeric_value": response_numeric,
            }
            if not (response == expected
                    or (response_numeric is not None
                        and expected_numeric is not None
                        and response_numeric == expected_numeric)):
                raise RuntimeError(
                    f"{component.get_name()} {channel_name} collision response is "
                    f"{response_text} ({response_numeric})")
        except RuntimeError:
            raise
        except Exception:
            state["collision_responses"][channel_name] = {
                "exposed": False, "value": None}
    return state


def dynamic_floor_material_contract(component) -> dict:
    material = component.get_material(0)
    if material is None:
        raise RuntimeError(component.get_name() + " has no live floor material")
    material_class = material.get_class().get_name()
    if material_class != "MaterialInstanceDynamic":
        raise RuntimeError(component.get_name() + " floor material is not dynamic: "
                           + material_class)
    try:
        parent = material.get_editor_property("parent")
    except Exception as exc:
        raise RuntimeError(component.get_name()
                           + " dynamic floor material parent is not exposed: " + str(exc))
    parent_path = parent.get_path_name() if parent is not None else None
    if parent_path != BASIC_SHAPE_MATERIAL:
        raise RuntimeError(component.get_name() + " dynamic floor material parent drift: "
                           + str(parent_path))
    return {
        "class": material_class,
        "stable_parent": parent_path,
        "transient_object_path_recorded": False,
    }


def live_hism_contract(world) -> None:
    cells = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBBodyShopCellActor))
    if len(cells) != 6:
        raise RuntimeError("expected six live Body Shop cells, found " + str(len(cells)))
    conveyor_rows = []
    floor_rows = []
    for cell in cells:
        for component in cell.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
            name = component.get_name()
            count = int(component.get_instance_count())
            if name in EXPECTED_HISM_COMPONENTS and count > 0:
                material = component.get_material(0)
                material_path = material.get_path_name() if material is not None else None
                expected_asset = EXPECTED_HISM_COMPONENTS[name]
                expected_object = expected_asset + "." + expected_asset.rsplit("/", 1)[-1]
                if material_path != expected_object:
                    raise RuntimeError(
                        f"live {name} material drift: {material_path} != {expected_object}")
                conveyor_rows.append({"cell": cell.get_name(), "component": name,
                                      "instance_count": count, "material": material_path})
            elif name in EXPECTED_FLOOR_HISM_COUNTS and count > 0:
                expected_count = EXPECTED_FLOOR_HISM_COUNTS[name]
                if count != expected_count:
                    raise RuntimeError(
                        f"live {name} instance-count drift: {count} != {expected_count}")
                mesh = component.get_editor_property("static_mesh")
                mesh_path = mesh.get_path_name() if mesh is not None else None
                if mesh_path != BASIC_SHAPE_CUBE:
                    raise RuntimeError(f"live {name} primitive drift: {mesh_path}")
                floor_rows.append({
                    "cell": cell.get_name(),
                    "component": name,
                    "instance_count": count,
                    "static_mesh": mesh_path,
                    "dynamic_material": dynamic_floor_material_contract(component),
                    "visual_only": floor_visual_only_contract(component),
                })

    materials = {row["material"] for row in conveyor_rows}
    conveyor_cells = {row["cell"] for row in conveyor_rows}
    component_names_by_cell = {
        cell_name: {row["component"] for row in conveyor_rows if row["cell"] == cell_name}
        for cell_name in conveyor_cells}
    if (materials != WARNING_OBJECTS
            or len(conveyor_rows) != EXPECTED_CONVEYOR_HISM_ROW_COUNT
            or len(conveyor_cells) != EXPECTED_CONVEYOR_CELL_COUNT
            or any(names != set(EXPECTED_HISM_COMPONENTS)
                   for names in component_names_by_cell.values())):
        raise RuntimeError(
            "live conveyor HISM exercise drift: "
            f"rows={len(conveyor_rows)} cells={len(conveyor_cells)} "
            f"materials={sorted(materials)} components={component_names_by_cell}")

    floor_cells = {row["cell"] for row in floor_rows}
    floor_components = {row["component"] for row in floor_rows}
    if (len(floor_rows) != len(EXPECTED_FLOOR_HISM_COUNTS)
            or len(floor_cells) != 1
            or floor_components != set(EXPECTED_FLOOR_HISM_COUNTS)):
        raise RuntimeError(
            "live floor HISM exercise drift: "
            f"rows={len(floor_rows)} cells={len(floor_cells)} "
            f"components={sorted(floor_components)}")
    service_actors = list(unreal.GameplayStatics.get_all_actors_of_class(
        world, unreal.LBBodyShopServiceDressingActor))
    if len(service_actors) != 1:
        raise RuntimeError(
            "expected exactly one native-v002 service dressing actor, found "
            + str(len(service_actors)))
    service_actor = service_actors[0]
    actor_name = service_actor.get_name()
    actor_tags = {str(tag) for tag in service_actor.tags}
    if (actor_name != EXPECTED_SERVICE_ACTOR_NAME
            or not EXPECTED_SERVICE_TAGS.issubset(actor_tags)
            or not bool(service_actor.is_presentation_active())
            or not bool(service_actor.has_valid_presentation_contract())
            or bool(service_actor.represents_process_wip())
            or int(service_actor.get_visible_instance_count()) != 12):
        raise RuntimeError(
            "native-v002 service dressing actor contract drift: "
            f"name={actor_name} tags={sorted(actor_tags)} "
            f"active={service_actor.is_presentation_active()} "
            f"valid={service_actor.has_valid_presentation_contract()} "
            f"wip={service_actor.represents_process_wip()} "
            f"visible={service_actor.get_visible_instance_count()}")
    service_rows = []
    for component in service_actor.get_components_by_class(
            unreal.HierarchicalInstancedStaticMeshComponent):
        name = component.get_name()
        if name not in EXPECTED_SERVICE_HISM:
            continue
        expected_mesh, expected_count = EXPECTED_SERVICE_HISM[name]
        mesh = component.get_editor_property("static_mesh")
        mesh_path = mesh.get_path_name() if mesh is not None else None
        instance_count = int(component.get_instance_count())
        if mesh_path != expected_mesh or instance_count != expected_count:
            raise RuntimeError(
                f"native-v002 service HISM drift: {name} "
                f"mesh={mesh_path} count={instance_count}")
        service_rows.append({
            "component": name,
            "mesh": mesh_path,
            "instance_count": instance_count,
        })
    if ({row["component"] for row in service_rows} != set(EXPECTED_SERVICE_HISM)
            or sum(row["instance_count"] for row in service_rows) != 12):
        raise RuntimeError("native-v002 exact three-batch service HISM inventory drift")
    payload["live_pie"] = {
        "passed": True,
        "body_shop_cell_count": len(cells),
        "conveyor_cell_count": len(conveyor_cells),
        "exercised_conveyor_hism_component_count": len(conveyor_rows),
        "exercised_warning_materials": sorted(materials),
        "conveyor_components": conveyor_rows,
        "floor_cell_count": len(floor_cells),
        "exercised_floor_hism_component_count": len(floor_rows),
        "floor_components": floor_rows,
        "service_dressing_actor_count": len(service_actors),
        "service_dressing_actor": {
            "name": actor_name,
            "tags": sorted(actor_tags),
            "active": True,
            "valid_contract": True,
            "represents_process_wip": False,
        },
        "service_hism_batch_count": len(service_rows),
        "service_hism_instance_count": sum(
            row["instance_count"] for row in service_rows),
        "service_hism_components": sorted(
            service_rows, key=lambda row: row["component"]),
        "dynamic_floor_material_paths_are_not_persisted": True,
        "elapsed_seconds_before_inspection": round(time.monotonic() - started, 3),
    }


def complete_shutdown() -> None:
    global tick_handle
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    if payload["status"].startswith("PASS"):
        unreal.log("LINE_BOSS_BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004_PASS")
    else:
        unreal.log_error(
            "LINE_BOSS_BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004_FAIL "
            + terminal_detail)
    # UnrealEditor-Cmd's Python plugin owns the safe next-tick exit path. Releasing
    # keep-alive after unregistering lets this callback return before shutdown;
    # direct quit_editor/QUIT_EDITOR from Slate produced a post-LogExit C0000005.
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)


def finish(status: str, detail: str = "") -> None:
    global phase, phase_started, terminal_detail, terminal_written
    if terminal_written:
        return
    terminal_written = True
    terminal_detail = detail
    if detail:
        payload["failures"].append(detail)
    try:
        payload["protected_hashes_after"] = protected_snapshot()
        if payload["protected_hashes_after"] != payload["protected_hashes_before"]:
            payload["failures"].append("protected package snapshot changed during validation")
    except Exception as exc:
        payload["failures"].append("post-validation hash gate: " + str(exc))
    payload["status"] = status if not payload["failures"] else "FAIL__BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["writes_to_content_source_or_config"] = False
    payload["maps_meshes_materials_native_robot_press_changed"] = (
        False if not payload["failures"] else None
    )
    payload["maps_materials_meshes_native_robot_support_kit_press_changed"] = (
        False if not payload["failures"] else None
    )
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # A PIE failure can arrive inside the Slate tick. Request EndPlay, keep the
    # callback alive, and quit only after the game world has actually gone away.
    # This avoids tearing down the commandlet while PIE objects are unwinding.
    if tick_handle is not None:
        phase = "wait_terminal_end_play"
        phase_started = time.monotonic()
        levels.editor_request_end_play()
        return
    complete_shutdown()


def tick(_delta_seconds) -> None:
    global phase, phase_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if phase == "wait_terminal_end_play":
        if world is None:
            complete_shutdown()
        return
    if now - started > 35.0:
        finish("FAIL__BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004",
               "timed out in phase " + phase)
        return
    try:
        if phase == "wait_world":
            if world is None or now - phase_started < 5.0:
                return
            live_hism_contract(world)
            levels.editor_request_end_play()
            phase = "wait_end_play"
            phase_started = now
            return
        if phase == "wait_end_play" and world is None:
            finish("PASS__FRESH_PROCESS_LIVE_PIE_BODYSHOP_FUNCTIONAL_HISM_NATIVE_ROBOT_SUPPORT_KIT_PROTECTION_V004")
    except Exception as exc:
        finish("FAIL__BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004", str(exc))


try:
    static_contract()
    if not levels.load_level(MAP_ASSET):
        raise RuntimeError("could not load exact isolated Body Shop map")
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    levels.editor_request_begin_play()
except Exception as exc:
    finish("FAIL__BODYSHOP_FUNCTIONAL_HISM_USAGE_VALIDATION_V004", str(exc))
