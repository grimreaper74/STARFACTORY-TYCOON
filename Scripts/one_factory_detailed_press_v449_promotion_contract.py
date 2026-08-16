"""Offline contract for the isolated v449 -> OneFactory Native Press promotion.

The source aggregate and its thirteen accepted PBR materials are immutable.  A
write-enabled Unreal lane may only duplicate them into the dedicated allowlisted
OneFactory root, rebind all 306 slots to the duplicates, and emit one-shot receipts.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from one_factory_detailed_press_v001_contract import (
    ContractError,
    MATERIAL_HASHES,
    SOURCE_MAP_SHA256,
    V449_MATERIAL_SLOT_COUNT,
    V449_RECEIPT_RELATIVE,
    V449_RUNTIME_MESH,
    V449_RUNTIME_MESH_RELATIVE,
    V449_RUNTIME_MESH_SHA256,
    forbidden_reference_reason,
    package_to_file,
    sha256,
    validate_preserved_evidence,
)


DEST_ROOT = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
    "DetailedPresentation_v001"
)
DEST_MATERIAL_ROOT = DEST_ROOT + "/Materials"
DEST_MESH = DEST_ROOT + "/SM_OneFactoryDetailedPressPresentation_v001"

BUILD_RECEIPT_RELATIVE = Path(
    "Saved/Audits/OneFactory/DetailedPressPresentation_v001/"
    "v449_owned_promotion_build_v001.json"
)
VALIDATION_RECEIPT_RELATIVE = Path(
    "Saved/Audits/OneFactory/DetailedPressPresentation_v001/"
    "v449_owned_promotion_fresh_load_validation_v001.json"
)
BUILD_SCHEMA = "cairnwell/one-factory/detailed-press/v449-owned-promotion-build/v1"
VALIDATION_SCHEMA = (
    "cairnwell/one-factory/detailed-press/"
    "v449-owned-promotion-fresh-load-validation/v1"
)

PROTECTED_MAPS = {
    "source_v438": (
        Path("Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"),
        SOURCE_MAP_SHA256,
    ),
    "restored_v001": (
        Path("Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap"),
        "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
    ),
    "current_v913": (
        Path("Content/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913.umap"),
        "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
    ),
}


def package_leaf(package: str) -> str:
    return str(package).rsplit("/", 1)[-1]


def object_path(package: str) -> str:
    return package + "." + package_leaf(package)


def destination_material_package(source_package: str) -> str:
    if source_package not in MATERIAL_HASHES:
        raise ContractError(f"Unrecognised v449 source material: {source_package}")
    return DEST_MATERIAL_ROOT + "/" + package_leaf(source_package)


SOURCE_TO_DEST_MATERIAL = {
    source: destination_material_package(source) for source in MATERIAL_HASHES
}
DEST_MATERIAL_PACKAGES = tuple(sorted(SOURCE_TO_DEST_MATERIAL.values()))
DEST_ASSET_PACKAGES = (DEST_MESH, *DEST_MATERIAL_PACKAGES)


def package_file(root: Path, package: str) -> Path:
    if not package.startswith("/Game/"):
        raise ContractError(f"Not a project package: {package}")
    return root / "Content" / (package[len("/Game/") :] + ".uasset")


def protected_hashes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for label, (relative, expected) in PROTECTED_MAPS.items():
        path = root / relative
        if not path.is_file():
            raise ContractError(f"Protected map missing: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ContractError(f"Protected map hash drift [{label}]: {actual}")
        rows[label] = actual
    return rows


def source_asset_hashes(root: Path) -> dict[str, str]:
    """Re-prove the immutable aggregate and every accepted source material."""
    rows = {V449_RUNTIME_MESH: sha256(root / V449_RUNTIME_MESH_RELATIVE)}
    rows.update({
        package: sha256(package_to_file(root, package))
        for package in sorted(MATERIAL_HASHES)
    })
    expected = {V449_RUNTIME_MESH: V449_RUNTIME_MESH_SHA256, **MATERIAL_HASHES}
    if rows != expected:
        drifted = sorted(
            package for package, actual in rows.items()
            if actual != expected.get(package)
        )
        raise ContractError(
            "Immutable v449 source asset hash drift: " + json.dumps(drifted)
        )
    return rows


def source_slot_packages(root: Path) -> list[str]:
    receipt_path = root / V449_RECEIPT_RELATIVE
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    slots = [str(value).split(".", 1)[0] for value in receipt.get("materials", [])]
    if len(slots) != V449_MATERIAL_SLOT_COUNT:
        raise ContractError(f"v449 material-slot count drift: {len(slots)}")
    if set(slots) != set(MATERIAL_HASHES):
        raise ContractError("v449 material-slot family drift")
    return slots


def expected_destination_slot_objects(root: Path) -> list[str]:
    return [object_path(SOURCE_TO_DEST_MATERIAL[source]) for source in source_slot_packages(root)]


def validate_source(root: Path) -> dict[str, Any]:
    root = root.resolve()
    evidence = validate_preserved_evidence(root)
    protected = protected_hashes(root)
    immutable_sources = source_asset_hashes(root)
    slots = source_slot_packages(root)
    for package in DEST_ASSET_PACKAGES:
        reason = forbidden_reference_reason(package)
        if reason:
            raise ContractError(f"Owned destination is forbidden [{package}]: {reason}")
        if not package.startswith(DEST_ROOT + "/"):
            raise ContractError(f"Owned destination escapes exact root: {package}")
    return {
        "status": "PASS__EXACT_PRE_MESHY_V449_PROMOTION_SOURCE_PINNED",
        "source_mesh": V449_RUNTIME_MESH,
        "source_mesh_sha256": V449_RUNTIME_MESH_SHA256,
        "source_material_count": len(MATERIAL_HASHES),
        "immutable_source_asset_count": len(immutable_sources),
        "material_slot_count": len(slots),
        "material_slot_histogram": dict(sorted(Counter(slots).items())),
        "destination_root": DEST_ROOT,
        "destination_asset_count": len(DEST_ASSET_PACKAGES),
        "protected_map_hashes": protected,
        "v438_evidence_status": evidence["status"],
    }


def validate_destination_absent(root: Path) -> None:
    for package in DEST_ASSET_PACKAGES:
        path = package_file(root, package)
        if path.exists():
            raise ContractError(f"Owned destination already exists: {path}")


def validate_build_receipt(root: Path, payload: dict[str, Any]) -> None:
    root = root.resolve()
    failures: list[str] = []
    if payload.get("$schema") != BUILD_SCHEMA:
        failures.append("wrong build schema")
    if payload.get("source_mesh") != V449_RUNTIME_MESH:
        failures.append("wrong source mesh")
    if payload.get("source_mesh_sha256") != V449_RUNTIME_MESH_SHA256:
        failures.append("wrong source mesh hash")
    if payload.get("destination_mesh") != DEST_MESH:
        failures.append("wrong destination mesh")
    if payload.get("material_slot_count") != V449_MATERIAL_SLOT_COUNT:
        failures.append("wrong material-slot count")
    if payload.get("editor_bootstrap_world") != "/Engine/Maps/Entry.Entry":
        failures.append("promotion did not bootstrap the exact Engine Entry world")
    if payload.get("map_loaded") is not False or payload.get("map_saved") is not False:
        failures.append("promotion script claims a map load/save mutation")
    if payload.get("source_assets_modified") is not False:
        failures.append("promotion claims source asset mutation")
    if payload.get("destination_slot_objects") != expected_destination_slot_objects(root):
        failures.append("destination material-slot sequence drift")
    if payload.get("protected_map_hashes_before") != payload.get(
        "protected_map_hashes_after"
    ):
        failures.append("protected map hashes changed")
    if payload.get("protected_map_hashes_after") != protected_hashes(root):
        failures.append("protected map hashes do not match contract")
    if payload.get("source_asset_hashes_before") != payload.get(
        "source_asset_hashes_after"
    ):
        failures.append("immutable source asset hashes changed")
    if payload.get("source_asset_hashes_after") != source_asset_hashes(root):
        failures.append("immutable source asset hashes do not match contract")
    assets = payload.get("destination_assets", [])
    if not isinstance(assets, list) or {
        str(row.get("package", "")) for row in assets
    } != set(DEST_ASSET_PACKAGES):
        failures.append("destination asset inventory drift")
        assets = assets if isinstance(assets, list) else []
    for row in assets:
        package = str(row.get("package", ""))
        path = package_file(root, package)
        if (
            not path.is_file()
            or path.stat().st_size != row.get("size_bytes")
            or sha256(path) != row.get("sha256")
        ):
            failures.append(f"destination file hash/size drift: {package}")
    dependency_rows = payload.get("dependency_rows", {})
    if set(dependency_rows.get(DEST_MESH, [])) != set(DEST_MATERIAL_PACKAGES):
        failures.append("owned aggregate dependency closure drift")
    if any(dependency_rows.get(package, []) for package in DEST_MATERIAL_PACKAGES):
        failures.append("owned PBR material dependency closure drift")
    if payload.get("dependency_proof") != (
        "EXACT_LIVE_306_STATIC_MESH_MATERIAL_BINDINGS"
    ):
        failures.append("owned dependency proof is not the exact live binding seam")
    if payload.get(
        "persisted_asset_registry_dependency_closure_deferred_to_fresh_process"
    ) is not True:
        failures.append("persisted AssetRegistry closure was not deferred explicitly")
    observed_rows = payload.get(
        "same_process_asset_registry_dependency_rows", {}
    )
    observed_unexpected = {
        dependency
        for dependencies in observed_rows.values()
        for dependency in dependencies
        if dependency not in set(DEST_ASSET_PACKAGES)
    }
    if observed_unexpected:
        failures.append("same-process AssetRegistry observed external dependencies")
    if failures:
        raise ContractError("; ".join(failures))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--require-destination-absent", action="store_true")
    parser.add_argument("--build-receipt", type=Path)
    args = parser.parse_args()
    result = validate_source(args.project_root)
    if args.require_destination_absent:
        validate_destination_absent(args.project_root)
    if args.build_receipt:
        validate_build_receipt(
            args.project_root,
            json.loads(args.build_receipt.read_text(encoding="utf-8")),
        )
        result["build_receipt_status"] = "PASS"
    print(json.dumps(result, indent=2))
