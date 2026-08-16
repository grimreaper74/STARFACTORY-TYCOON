"""Repair the first Materials_v002 pass without rebuilding or rebinding meshes.

The first guarded pass exposed two UE 5.8 Python edge cases after its receipt:
the duplicated layered master was not explicitly saved, and Sine's input pin is
unnamed rather than ``Input``.  This script requires that exact failed state,
backs up the functional master, creates only the missing master, repairs only
the one graph connection, and records a separate superseding receipt.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
EXPECTED_PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8").resolve()
DEST = "/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002"
LAYERED_SOURCE = "/Game/LineBoss/Robots/Shared/Materials/Candidate_v002/M_LB_SupportRobot_LayeredPaint_v002"
LAYERED = DEST + "/M_LB_BodyShop_LayeredPaint_Master_v002"
FUNCTIONAL = DEST + "/M_LB_BodyShop_Functional_Master_v002"
BUILD = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_build.json"
REPAIR = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/presentation_materials_v002_functional_sm6_repair.json"
REJECTED = PROJECT / "Saved/Audits/BodyShop/Experimental_v001/RejectedArtifacts/presentation_materials_v002_initial_false_pass.json"
BACKUP = PROJECT / "Saved/Quarantine/BodyShop/PresentationMaterials_v002_FunctionalSM6Repair"
MAP_FILE = PROJECT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
CGUN_FILE = PROJECT / "Content/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/SM_LB_WeldTool_SpotGun_v001.uasset"

PAINT_MIS = ("MI_LB_BodyShop_CreamPaint_v002", "MI_LB_BodyShop_BlackMotor_v002")
FUNCTIONAL_MIS = (
    "MI_LB_BodyShop_StructuralLightGrey_v002", "MI_LB_BodyShop_BrushedSteel_v002",
    "MI_LB_BodyShop_GraphiteTooling_v002", "MI_LB_BodyShop_EmeraldPanel_v002",
    "MI_LB_BodyShop_SafetyYellow_v002", "MI_LB_BodyShop_VacuumRubber_v002",
    "MI_LB_BodyShop_ScannerLens_v002", "MI_LB_BodyShop_StatusGreen_v002",
    "MI_LB_BodyShop_StatusAmber_v002", "MI_LB_BodyShop_StatusRed_v002")

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def fail(message: str) -> None:
    raise RuntimeError("BODYSHOP_PRESENTATION_MATERIALS_V002_REPAIR_FAIL: " + message)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


def package_file(asset: str) -> Path:
    return PROJECT / "Content" / Path(asset.removeprefix("/Game/")).with_suffix(".uasset")


def main() -> None:
    if PROJECT != EXPECTED_PROJECT or str(unreal.SystemLibrary.get_game_name()) != "LineBossCarFactory":
        fail("project identity drift")
    if REPAIR.exists() or REJECTED.exists() or BACKUP.exists():
        fail("repair/rejected/backup output already exists")
    if not BUILD.is_file():
        fail("initial build receipt missing")
    build_bytes = BUILD.read_bytes()
    build = json.loads(build_bytes.decode("utf-8"))
    if (build.get("$schema") != "lineboss/audit/bodyshop/presentation-materials-v002-build/v1"
            or build.get("status") != "PASS__ISOLATED_BODYSHOP_PRESENTATION_MATERIALS_V002_BUILT_AND_BOUND"
            or build.get("functional_compile_contract")):
        fail("initial false-pass receipt is not the exact repairable revision")
    if digest(MAP_FILE) != build.get("map_sha256_before_and_after"):
        fail("protected Body Shop map changed")
    if digest(CGUN_FILE) != build.get("protected_cgun", {}).get("sha256_before_and_after"):
        fail("protected C-gun changed")
    if lib.does_asset_exist(LAYERED) or package_file(LAYERED).exists():
        fail("layered master is not in the exact missing-package state")
    functional = lib.load_asset(FUNCTIONAL)
    if not isinstance(functional, unreal.Material):
        fail("functional master is missing")
    functional_file = package_file(FUNCTIONAL)
    before_functional = digest(functional_file)

    expected_existing = sorted([FUNCTIONAL] + [DEST + "/" + name for name in PAINT_MIS + FUNCTIONAL_MIS])
    actual_existing = sorted({path.split(".", 1)[0]
                              for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    if actual_existing != expected_existing:
        fail("repairable 13-asset inventory drift: " + str(actual_existing))
    for row in build.get("mesh_packages", {}).values():
        disk = package_file(row["asset"])
        if not disk.is_file() or digest(disk) != row.get("sha256_after"):
            fail("bound mesh changed after initial pass: " + row.get("asset", "<missing>"))

    BACKUP.mkdir(parents=True, exist_ok=False)
    backup_file = BACKUP / functional_file.name
    shutil.copy2(functional_file, backup_file)
    if digest(backup_file) != before_functional:
        fail("functional-master backup hash mismatch")
    REJECTED.parent.mkdir(parents=True, exist_ok=True)
    REJECTED.write_bytes(build_bytes)
    if digest(REJECTED) != digest(BUILD):
        fail("initial receipt preservation hash mismatch")

    layered = lib.duplicate_asset(LAYERED_SOURCE, LAYERED)
    if not isinstance(layered, unreal.Material):
        fail("could not recreate local layered master")
    if not lib.save_loaded_asset(layered, only_if_is_dirty=False) or not package_file(LAYERED).is_file():
        fail("local layered master did not persist")

    expressions = mel.get_material_expressions(functional)
    dots = [node for node in expressions if isinstance(node, unreal.MaterialExpressionDotProduct)]
    sines = [node for node in expressions if isinstance(node, unreal.MaterialExpressionSine)]
    if len(dots) != 1 or len(sines) != 1:
        fail(f"expected one DotProduct and one Sine, found {len(dots)} and {len(sines)}")
    if not mel.connect_material_expressions(dots[0], "", sines[0], ""):
        fail("could not connect DotProduct to Sine's unnamed input")
    mel.recompile_material(functional)
    if not lib.save_loaded_asset(functional, only_if_is_dirty=False):
        fail("functional master save failed")

    for name in PAINT_MIS:
        instance = lib.load_asset(DEST + "/" + name)
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            fail("paint MIC missing: " + name)
        instance.set_editor_property("parent", layered)
        mel.update_material_instance(instance)
        if not lib.save_loaded_asset(instance, only_if_is_dirty=False):
            fail("paint MIC save failed: " + name)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    expected_final = sorted([LAYERED, FUNCTIONAL]
                            + [DEST + "/" + name for name in PAINT_MIS + FUNCTIONAL_MIS])
    actual_final = sorted({path.split(".", 1)[0]
                           for path in lib.list_assets(DEST, recursive=True, include_folder=False)})
    if actual_final != expected_final:
        fail("repaired 14-asset inventory drift: " + str(actual_final))
    if digest(MAP_FILE) != build.get("map_sha256_before_and_after") or digest(CGUN_FILE) != build.get("protected_cgun", {}).get("sha256_before_and_after"):
        fail("protected map or C-gun changed during repair")
    for row in build.get("mesh_packages", {}).values():
        if digest(package_file(row["asset"])) != row.get("sha256_after"):
            fail("mesh changed during material-master repair: " + row["asset"])

    payload = {
        "$schema": "lineboss/audit/bodyshop/presentation-materials-v002-functional-sm6-repair/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__BODYSHOP_PRESENTATION_MATERIALS_V002_PERSISTENCE_AND_FUNCTIONAL_SM6_REPAIRED",
        "initial_build_receipt_sha256": digest(BUILD),
        "preserved_initial_receipt": str(REJECTED),
        "preserved_initial_receipt_sha256": digest(REJECTED),
        "functional_master": {"asset": FUNCTIONAL, "sha256_before": before_functional,
                              "sha256_after": digest(functional_file),
                              "sine_input_pin": "unnamed", "connection_returned_true": True},
        "layered_master": {"asset": LAYERED, "sha256_after": digest(package_file(LAYERED)),
                           "explicitly_saved": True},
        "paint_instances_reparented_and_saved": list(PAINT_MIS),
        "asset_count": len(actual_final), "assets": actual_final,
        "map_sha256_unchanged": digest(MAP_FILE),
        "cgun_sha256_unchanged": digest(CGUN_FILE),
        "mesh_packages_unchanged": {name: row["sha256_after"]
                                     for name, row in build["mesh_packages"].items()},
        "recoverable_functional_backup": {"path": str(backup_file),
                                           "sha256": digest(backup_file)},
        "content_scope": [LAYERED, FUNCTIONAL] + [DEST + "/" + name for name in PAINT_MIS],
        "failures": []}
    REPAIR.parent.mkdir(parents=True, exist_ok=True)
    REPAIR.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log("LINE_BOSS_BODYSHOP_PRESENTATION_MATERIALS_V002_FUNCTIONAL_SM6_REPAIR_PASS")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

