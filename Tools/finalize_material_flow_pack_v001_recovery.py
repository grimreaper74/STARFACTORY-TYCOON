"""Finalize the single-file tail of the proven Material Flow import recovery.

UE's bulk directory delete removed nineteen of the twenty preflight-approved
assets, then returned false because one Texture2D package remained.  This is
not a generic delete utility: it accepts only that one recorded asset, proves
there are no external referencers, deletes it through Unreal, and removes
only the resulting empty filesystem folders.  The original preflight and
failure receipts remain immutable evidence of the first recovery pass.
"""

from __future__ import annotations

import io
import json
import traceback
from pathlib import Path

import unreal


PROJECT_ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
DESTINATION = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "MaterialFlowPack_v001"
)
CONTENT_DESTINATION = (
    PROJECT_ROOT / "Content/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "MaterialFlowPack_v001"
)
REMAINING_ASSET = (
    DESTINATION + "/Textures/T_CA_MW_PT_TaskLightGlass_ORM."
    "T_CA_MW_PT_TaskLightGlass_ORM"
)
AUDIT_DIR = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001"
)
PREFLIGHT_RECEIPT = AUDIT_DIR / "import_recovery_v001_preflight.json"
PRIOR_FAILURE_RECEIPT = AUDIT_DIR / "import_recovery_v001_failure.json"
APPROVAL_RECEIPT = AUDIT_DIR / "import_receipt.json"
RESULT_RECEIPT = AUDIT_DIR / "import_recovery_v001_finalize.json"
FAILURE_RECEIPT = AUDIT_DIR / "import_recovery_v001_finalize_failure.json"


def fail(message: str) -> None:
    raise RuntimeError("Material Flow v001 recovery finalization failed: {}".format(message))


def write_once(path: Path, payload: dict) -> None:
    if path.exists():
        fail("evidence already exists; refusing to overwrite {}".format(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def remove_empty_tree(path: Path) -> list[str]:
    """Remove only empty directories beneath this exact already-empty root."""
    removed = []
    if not path.exists():
        return removed
    for candidate in sorted(
            (directory for directory in path.rglob("*") if directory.is_dir()),
            key=lambda directory: len(directory.parts), reverse=True):
        if any(candidate.iterdir()):
            fail("filesystem cleanup found unexpected content in {}".format(candidate))
        candidate.rmdir()
        removed.append(str(candidate))
    if path.exists():
        if any(path.iterdir()):
            fail("filesystem cleanup found unexpected content in {}".format(path))
        path.rmdir()
        removed.append(str(path))
    return removed


def main() -> None:
    if APPROVAL_RECEIPT.exists():
        fail("approved import receipt exists; never clean approved content")
    if not PREFLIGHT_RECEIPT.exists() or not PRIOR_FAILURE_RECEIPT.exists():
        fail("the exact first-recovery evidence is missing")
    if RESULT_RECEIPT.exists() or FAILURE_RECEIPT.exists():
        fail("finalization evidence already exists")

    assets = set(unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False))
    if assets != {REMAINING_ASSET}:
        fail("remaining namespace differs from the exact one-file recovery tail: {}".format(
            sorted(assets)))
    asset = unreal.load_asset(REMAINING_ASSET)
    if asset is None or not isinstance(asset, unreal.Texture):
        fail("the exact remaining asset is not a Texture")
    references = sorted(
        str(reference) for reference in
        unreal.EditorAssetLibrary.find_package_referencers_for_asset(
            REMAINING_ASSET, True)
        if not str(reference).startswith(DESTINATION)
    )
    if references:
        fail("remaining asset has external referencers: {}".format(references))
    if not unreal.EditorAssetLibrary.delete_asset(REMAINING_ASSET):
        fail("UE refused to delete the exact unreferenced remaining asset")
    assets_after_delete = list(unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False))
    if assets_after_delete:
        fail("native destination still has assets after tail deletion: {}".format(
            assets_after_delete))
    removed_directories = remove_empty_tree(CONTENT_DESTINATION)
    if CONTENT_DESTINATION.exists():
        fail("empty filesystem content root remains after exact cleanup")
    result = {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v001-recovery-finalize/v1",
        "status": "PASS__MATERIAL_FLOW_PARTIAL_IMPORT_FULLY_REMOVED_FOR_CLEAN_RETRY",
        "destination": DESTINATION,
        "preflight_receipt": str(PREFLIGHT_RECEIPT),
        "prior_recovery_failure_receipt": str(PRIOR_FAILURE_RECEIPT),
        "only_remaining_asset_deleted": REMAINING_ASSET,
        "external_referencers": references,
        "native_assets_after_delete": assets_after_delete,
        "empty_directories_removed": removed_directories,
        "approval_receipt_absent": True,
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "source_content_writes": [],
    }
    write_once(RESULT_RECEIPT, result)
    unreal.log("LINE_BOSS_MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY_FINALIZE_PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        payload = {
            "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v001-recovery-finalize/v1",
            "status": "FAIL__MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY_FINALIZE",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "delete_scope": [REMAINING_ASSET],
            "source_content_writes": [],
        }
        if not FAILURE_RECEIPT.exists():
            FAILURE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
            with io.open(FAILURE_RECEIPT, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        unreal.log_error("LINE_BOSS_MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY_FINALIZE_FAIL " +
                         str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()
