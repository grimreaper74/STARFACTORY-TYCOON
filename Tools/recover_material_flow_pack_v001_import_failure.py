"""Remove only the proven-unapproved Material Flow v001 partial import.

The first guarded native import correctly stopped when UE 5.8 retained the
FBX stem in Combine-Meshes-off child asset names.  It had already created the
16 new textures and the four FeedCoilAssembly meshes, but no material
instances, actor references, approval receipt, or map changes.  This explicit
recovery lane records that exact partial state, proves it is isolated, then
deletes only that namespace so the corrected importer can make a fresh,
auditable one-shot attempt.

It must never be used as a generic cleanup tool.  Any drift in the partial
inventory, any approved import receipt, or any external referencer is a hard
failure and leaves native content untouched.
"""

from __future__ import annotations

import hashlib
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
AUDIT_DIR = (
    PROJECT_ROOT / "Saved/Audits/OneFactory/Press/MaterialFlowPackRuntimePrep_v001"
)
APPROVAL_RECEIPT = AUDIT_DIR / "import_receipt.json"
PREFLIGHT_RECEIPT = AUDIT_DIR / "import_recovery_v001_preflight.json"
RESULT_RECEIPT = AUDIT_DIR / "import_recovery_v001.json"
FAILURE_RECEIPT = AUDIT_DIR / "import_recovery_v001_failure.json"
IMPORTER = PROJECT_ROOT / "Tools/import_material_flow_pack_v001.py"
SOURCE_MANIFEST = (
    PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_v001/"
    "matflowpack_manifest.json"
)
SOURCE_STATS = (
    PROJECT_ROOT / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v001/"
    "runtime_prep_stats.json"
)

CHANNELS = ("BC", "N", "ORM", "MASK")
NEW_FAMILIES = ("GalvanizedCoil", "DarkRubber", "TaskLightGlass", "StampedPanel")
RAW_FBX_STEM = "CA_PTA_S01_FeedCoilAssembly_LOD0"
RAW_MESHES = (
    "SM_CA_MW_PT_S01CoilCart_v001",
    "SM_CA_MW_PT_S01CoilRack_v001",
    "SM_CA_MW_PT_S01DecoilerBase_v001",
    "SM_CA_MW_PT_S01DecoilerSpindle_v001",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().lower()


def object_path(folder: str, name: str) -> str:
    return "{}/{}.{}".format(folder, name, name)


def texture_name(family: str, channel: str) -> str:
    return "T_CA_MW_PT_{}_{}".format(family, channel)


def raw_mesh_name(semantic_name: str) -> str:
    return "{}_{}".format(RAW_FBX_STEM, semantic_name)


EXPECTED_TEXTURE_PATHS = {
    object_path(DESTINATION + "/Textures", texture_name(family, channel))
    for family in NEW_FAMILIES for channel in CHANNELS
}
EXPECTED_RAW_MESH_PATHS = {
    object_path(DESTINATION + "/Meshes", raw_mesh_name(semantic_name))
    for semantic_name in RAW_MESHES
}
EXPECTED_PARTIAL_ASSETS = EXPECTED_TEXTURE_PATHS | EXPECTED_RAW_MESH_PATHS


def fail(message: str) -> None:
    raise RuntimeError("Material Flow v001 partial-import recovery failed: {}".format(message))


def asset_path(asset) -> str:
    return str(asset.get_path_name()) if asset else "none"


def file_fingerprints() -> dict:
    if not CONTENT_DESTINATION.is_dir():
        fail("partial content directory is missing: {}".format(CONTENT_DESTINATION))
    fingerprints = {}
    for path in sorted(CONTENT_DESTINATION.rglob("*")):
        if path.is_file():
            fingerprints[str(path.relative_to(CONTENT_DESTINATION)).replace("\\", "/")] = {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
    return fingerprints


def write_json_once(path: Path, payload: dict) -> None:
    if path.exists():
        fail("recovery evidence already exists; refusing to overwrite {}".format(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def expected_classes_and_referencers() -> tuple[dict, dict]:
    classes = {}
    referencers = {}
    for path in sorted(EXPECTED_PARTIAL_ASSETS):
        asset = unreal.load_asset(path)
        if asset is None:
            fail("expected partial asset does not resolve: {}".format(path))
        if path in EXPECTED_TEXTURE_PATHS and not isinstance(asset, unreal.Texture):
            fail("partial texture is not a Texture: {}".format(path))
        if path in EXPECTED_RAW_MESH_PATHS and not isinstance(asset, unreal.StaticMesh):
            fail("partial raw mesh is not a StaticMesh: {}".format(path))
        if asset_path(asset) != path:
            fail("partial asset identity drifted: {} -> {}".format(path, asset_path(asset)))
        classes[path] = asset.get_class().get_name()
        external = sorted(
            str(reference) for reference in
            unreal.EditorAssetLibrary.find_package_referencers_for_asset(path, True)
            if not str(reference).startswith(DESTINATION)
        )
        if external:
            fail("partial asset has external referencers: {} -> {}".format(path, external))
        referencers[path] = external
    return classes, referencers


def preflight() -> dict:
    if APPROVAL_RECEIPT.exists():
        fail("approved import receipt exists; this recovery lane must never delete approved content")
    if PREFLIGHT_RECEIPT.exists() or RESULT_RECEIPT.exists() or FAILURE_RECEIPT.exists():
        fail("recovery evidence already exists; inspect it instead of rerunning this lane")
    if not unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
        fail("native partial destination does not exist")
    actual = set(unreal.EditorAssetLibrary.list_assets(
        DESTINATION, recursive=True, include_folder=False))
    if actual != EXPECTED_PARTIAL_ASSETS:
        fail("partial namespace differs from the exact 20-package failure signature; got {} assets".format(
            len(actual)))
    if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION + "/Materials"):
        material_assets = list(unreal.EditorAssetLibrary.list_assets(
            DESTINATION + "/Materials", recursive=True, include_folder=False))
        if material_assets:
            fail("partial namespace contains materials; recovery scope is no longer safe")
    classes, referencers = expected_classes_and_referencers()
    fingerprints = file_fingerprints()
    if len(fingerprints) != len(EXPECTED_PARTIAL_ASSETS):
        fail("partial on-disk package count differs from the exact 20-package signature")
    return {
        "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v001-recovery/v1",
        "status": "PASS__MATERIAL_FLOW_PARTIAL_IMPORT_ISOLATED_FOR_RECOVERY",
        "reason": (
            "UE 5.8 prefixed Combine-Meshes-off child meshes with the FBX stem; "
            "the first import gate rejected names before material creation or actor use"
        ),
        "destination": DESTINATION,
        "content_destination": str(CONTENT_DESTINATION),
        "approval_receipt_absent": True,
        "expected_partial_asset_count": len(EXPECTED_PARTIAL_ASSETS),
        "partial_assets": sorted(actual),
        "asset_classes": classes,
        "external_referencers": referencers,
        "on_disk_fingerprints": fingerprints,
        "source_provenance": {
            "importer": str(IMPORTER),
            "importer_sha256": sha256(IMPORTER),
            "source_manifest_sha256": sha256(SOURCE_MANIFEST),
            "source_runtime_stats_sha256": sha256(SOURCE_STATS),
        },
        "map_opened_by_script": False,
        "map_saved_by_script": False,
        "delete_scope": [DESTINATION],
    }


def main() -> None:
    evidence = preflight()
    write_json_once(PREFLIGHT_RECEIPT, evidence)
    if not unreal.EditorAssetLibrary.delete_directory(DESTINATION):
        fail("UE refused to delete the already-proven partial destination")
    if unreal.EditorAssetLibrary.does_directory_exist(DESTINATION):
        remaining = list(unreal.EditorAssetLibrary.list_assets(
            DESTINATION, recursive=True, include_folder=False))
        if remaining:
            fail("partial destination still contains assets after delete: {}".format(remaining))
    if CONTENT_DESTINATION.exists():
        remaining_files = [path for path in CONTENT_DESTINATION.rglob("*") if path.is_file()]
        if remaining_files:
            fail("partial content files remain after UE deletion: {}".format(remaining_files))
    result = {
        **evidence,
        "status": "PASS__MATERIAL_FLOW_PARTIAL_IMPORT_REMOVED_FOR_CLEAN_RETRY",
        "preflight_receipt": str(PREFLIGHT_RECEIPT),
        "native_destination_exists_after_delete": unreal.EditorAssetLibrary.does_directory_exist(
            DESTINATION),
        "content_destination_exists_after_delete": CONTENT_DESTINATION.exists(),
        "content_writes_removed": [DESTINATION],
        "source_content_writes": [],
    }
    write_json_once(RESULT_RECEIPT, result)
    unreal.log("LINE_BOSS_MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY_PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        failure = {
            "$schema": "lineboss/onefactory/press/material-flow-runtimeprep-v001-recovery/v1",
            "status": "FAIL__MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "delete_scope": [DESTINATION],
            "source_content_writes": [],
        }
        if not FAILURE_RECEIPT.exists():
            FAILURE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
            with io.open(FAILURE_RECEIPT, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(failure, indent=2, sort_keys=True) + "\n")
        unreal.log_error("LINE_BOSS_MATERIAL_FLOW_PARTIAL_IMPORT_RECOVERY_FAIL " + str(error))
        raise
    finally:
        unreal.SystemLibrary.quit_editor()
