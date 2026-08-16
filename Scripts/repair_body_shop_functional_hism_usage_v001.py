"""One-shot repair for the isolated Body Shop functional material HISM usage.

The two accepted release-validation runs exposed exactly three
InstancedStaticMeshes warnings.  All three MICs inherit the same project-owned
functional master, so this script mutates and saves only that master.  It is
fail-closed on the exact warning logs and current Body map, Press v913,
Materials_v002, final mesh and C-gun package hashes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
FUNCTIONAL = DEST + "/M_LB_BodyShop_Functional_Master_v002"
USAGE_PROPERTY = "used_with_instanced_static_meshes"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
PRESS_FILE = PROJECT / "Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"
RECEIPT = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_hism_usage_repair_v001.json"
BACKUP_ROOT = PROJECT / "Saved/Quarantine/BodyShop/PresentationMaterials_v002_FunctionalHISMUsageRepair_v001"

EXPECTED_MAP_SHA256 = "9766E686B5AA2B0F006C54CA4E578C37944A1CE4CE99C41F4EC3DFC009894D0A"
EXPECTED_PRESS_SHA256 = "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6"
EXPECTED_CGUN_SHA256 = "79DAA22563EE54BC1F3C04C98B9CAEC7E22A1F01F7E65E9E76B147B4ABBC27BC"

SOURCE_LOGS = {
    PROJECT / "Saved/Audits/BodyShop/Experimental_v001/ReleaseValidation/20260814T064521Z/Logs/live_pie_release_validation.log":
        "AE6879DD0A3011A6CA944467B4A53D78CBE7D30E01D87B45F42B93C29A84DBD4",
    PROJECT / "Saved/Audits/BodyShop/Experimental_v001/ReleaseValidation/20260814T064847Z/Logs/live_pie_release_validation.log":
        "622CBCA5C33E35CD46F239D9BAF0F0D61458DDA715E37202EC50D161B4FBF3B6",
}
WARNING_PATTERN = re.compile(
    r"Material (?P<asset>/Game/[^\s]+?)\.[^\s]+ missing usage flag InstancedStaticMeshes!"
)
WARNING_ASSETS = sorted([
    DEST + "/MI_LB_BodyShop_StructuralLightGrey_v002",
    DEST + "/MI_LB_BodyShop_BrushedSteel_v002",
    DEST + "/MI_LB_BodyShop_SafetyYellow_v002",
])

EXPECTED_MATERIAL_HASHES = {
    DEST + "/M_LB_BodyShop_Functional_Master_v002": "DCC55743B2292200943113DB32E1B31867DD1372ED66C733814B455A73D5F287",
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

EXPECTED_MESH_HASHES = {
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001": "262AB2C8F5289465DB3547BEA11DFCB072721C4A931E6EC81E9723CE2483BDAE",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_Base_v001": "9CBE6D27268C7B942F7271546B5EC678C063C7CFEE35BE6B7DE0F017FFC3FBB0",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J1_v001": "4B81E41A999BCA1081EBDBE5FAAB76D4D5B19ECBC820FAD0D1B8B0C36D31E2E4",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J2_v001": "D4607CB5481E2CC8B7FF23921DE202CCE80676057213653DF8BF2C4730CFB15F",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J3_v001": "CE96B0591EFB8ABE3944658AA3A2ECF97E844B30C66C3ED49FE36B844AD6EE8A",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J4_v001": "EC6CBF9447DB73AFF82B4ACB184BF9F663480DD48DF4F461B85C4E258070826D",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Robot/SM_LB_BodyShopRobot_J5_v001": "1C5A3E3F3411F066B4AB5A4B63738A63A2CC7D30916F246C193496DA5E40C534",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001": "61BF706DF4306873381566A56A0EDD9C1B1A0E7949A07C5928AE79A4F58657A2",
    "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001": "53D7443AA524CCF655AFA82BCD9C3950D9C559EA2F41D93E10309B74B0563C71",
}

lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_FUNCTIONAL_HISM_USAGE_REPAIR_V001_FAIL: " + message)


def digest(path: Path) -> str:
    if not path.is_file():
        fail("missing protected file: " + str(path))
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_file(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def require_hash(path: Path, expected: str, label: str) -> str:
    actual = digest(path)
    if actual != expected:
        fail(f"{label} hash drift: {actual} != {expected}")
    return actual


def read_log(path: Path) -> str:
    raw = path.read_bytes()
    # PowerShell's redirected Unreal stdout is UTF-16 LE, while -abslog output
    # is UTF-8.  Preserve exact byte hashing above and decode only for the
    # warning allowlist comparison.
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    return raw.decode("utf-8", errors="replace")


def require_asset_hashes(expected: dict[str, str], label: str) -> dict[str, str]:
    actual = {asset: digest(package_file(asset)) for asset in expected}
    drift = {asset: {"actual": actual[asset], "expected": sha}
             for asset, sha in expected.items() if actual[asset] != sha}
    if drift:
        fail(label + " hash drift: " + json.dumps(drift, sort_keys=True))
    return actual


def instanced_static_mesh_usage():
    preferred = "MATUSAGE_INSTANCED_STATIC_MESHES"
    if hasattr(unreal.MaterialUsage, preferred):
        return getattr(unreal.MaterialUsage, preferred)
    candidates = [name for name in dir(unreal.MaterialUsage)
                  if "INSTANCED" in name.upper()
                  and "STATIC" in name.upper()
                  and "MESH" in name.upper()
                  and "SKINNED" not in name.upper()]
    if len(candidates) != 1:
        fail("could not resolve MATUSAGE_InstancedStaticMeshes: " + str(candidates))
    return getattr(unreal.MaterialUsage, candidates[0])


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if RECEIPT.exists() or BACKUP_ROOT.exists():
        fail("one-shot receipt or backup already exists")

    log_rows = {}
    for path, expected_hash in SOURCE_LOGS.items():
        actual_hash = require_hash(path, expected_hash, "source live PIE log")
        warnings = WARNING_PATTERN.findall(read_log(path))
        if len(warnings) != 3 or sorted(warnings) != WARNING_ASSETS:
            fail("source-log warning allowlist drift: " + str(path) + " -> " + str(warnings))
        log_rows[str(path)] = {"sha256": actual_hash, "warning_count": len(warnings),
                               "warning_assets": warnings}

    require_hash(MAP_FILE, EXPECTED_MAP_SHA256, "Body Shop map")
    require_hash(PRESS_FILE, EXPECTED_PRESS_SHA256, "protected Press v913 map")
    require_hash(CGUN_FILE, EXPECTED_CGUN_SHA256, "protected C-gun")
    materials_before = require_asset_hashes(EXPECTED_MATERIAL_HASHES, "Materials_v002 pre-repair")
    meshes_before = require_asset_hashes(EXPECTED_MESH_HASHES, "final Body Shop meshes pre-repair")
    actual_assets = sorted({path.split(".", 1)[0]
                            for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    if actual_assets != sorted(EXPECTED_MATERIAL_HASHES):
        fail("exact 14-asset Materials_v002 inventory drift: " + str(actual_assets))

    functional = lib.load_asset(FUNCTIONAL)
    if not isinstance(functional, unreal.Material):
        fail("functional master missing or wrong class")
    if bool(functional.get_editor_property(USAGE_PROPERTY)):
        fail("functional master is not in the exact false usage precondition")
    for target in WARNING_ASSETS:
        instance = lib.load_asset(target)
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail("warning target is not a MIC: " + target)
        parent = instance.get_editor_property("parent")
        if parent != functional:
            fail("warning MIC parent drift: " + target)

    functional_file = package_file(FUNCTIONAL)
    BACKUP_ROOT.mkdir(parents=True, exist_ok=False)
    backup_file = BACKUP_ROOT / functional_file.relative_to(PROJECT)
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(functional_file, backup_file)
    if digest(backup_file) != EXPECTED_MATERIAL_HASHES[FUNCTIONAL]:
        fail("functional-master backup hash mismatch")

    usage = instanced_static_mesh_usage()
    mel.set_base_material_usage(functional, usage, True)
    if not bool(functional.get_editor_property(USAGE_PROPERTY)):
        fail("UE 5.8 rejected MATUSAGE_InstancedStaticMeshes")
    mel.recompile_material(functional)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    if not lib.save_loaded_asset(functional, only_if_is_dirty=False):
        fail("functional master save failed")
    if not bool(functional.get_editor_property(USAGE_PROPERTY)):
        fail("usage property did not persist after save")

    functional_after = digest(functional_file)
    if functional_after == EXPECTED_MATERIAL_HASHES[FUNCTIONAL]:
        fail("functional master package hash did not change")
    other_materials = {asset: sha for asset, sha in EXPECTED_MATERIAL_HASHES.items()
                       if asset != FUNCTIONAL}
    materials_unchanged = require_asset_hashes(other_materials, "other 13 Materials_v002 assets")
    meshes_unchanged = require_asset_hashes(EXPECTED_MESH_HASHES, "final Body Shop meshes")
    require_hash(MAP_FILE, EXPECTED_MAP_SHA256, "Body Shop map after repair")
    require_hash(PRESS_FILE, EXPECTED_PRESS_SHA256, "protected Press v913 map after repair")
    require_hash(CGUN_FILE, EXPECTED_CGUN_SHA256, "protected C-gun after repair")

    payload = {
        "$schema": "lineboss/audit/bodyshop/presentation-materials-v002-functional-hism-usage-repair-v001/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__BODYSHOP_FUNCTIONAL_MASTER_INSTANCED_STATIC_MESH_USAGE_REPAIRED",
        "diagnosis_logs": log_rows,
        "warning_assets": WARNING_ASSETS,
        "functional_master": {
            "asset": FUNCTIONAL,
            "usage_enum": str(usage),
            "usage_property": USAGE_PROPERTY,
            "usage_before": False,
            "usage_after": True,
            "sha256_before": materials_before[FUNCTIONAL],
            "sha256_after": functional_after,
            "saved": True,
        },
        "recoverable_backup": {"path": str(backup_file), "sha256": digest(backup_file)},
        "protected_hashes": {
            "body_shop_map": EXPECTED_MAP_SHA256,
            "press_v913_map": EXPECTED_PRESS_SHA256,
            "cgun": EXPECTED_CGUN_SHA256,
            "other_13_material_assets": materials_unchanged,
            "all_9_final_meshes": meshes_unchanged,
        },
        "materials_v002_asset_count": len(actual_assets),
        "materials_v002_assets": actual_assets,
        "content_packages_changed": [FUNCTIONAL],
        "material_instances_resaved": [],
        "maps_meshes_cgun_press_changed": False,
        "source_or_config_changed": False,
        "visual_parameters_changed": False,
        "failures": [],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_FUNCTIONAL_HISM_USAGE_REPAIR_V001_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
