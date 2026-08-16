"""Independent fresh-process reload validation for the owned v449 Press pack."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True

import unreal


ROOT = Path(unreal.Paths.project_dir())
SCRIPT_DIR = ROOT / "Scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from one_factory_detailed_press_v001_contract import (  # noqa: E402
    ContractError,
    V449_MATERIAL_SLOT_COUNT,
    V449_RUNTIME_MESH,
    V449_RUNTIME_MESH_RELATIVE,
    V449_RUNTIME_MESH_SHA256,
    sha256,
)
from one_factory_detailed_press_v449_promotion_contract import (  # noqa: E402
    BUILD_RECEIPT_RELATIVE,
    DEST_ASSET_PACKAGES,
    DEST_MATERIAL_PACKAGES,
    DEST_MESH,
    VALIDATION_RECEIPT_RELATIVE,
    VALIDATION_SCHEMA,
    expected_destination_slot_objects,
    object_path,
    package_file,
    protected_hashes,
    source_asset_hashes,
    validate_build_receipt,
    validate_source,
)


BUILD = ROOT / BUILD_RECEIPT_RELATIVE
OUT = ROOT / VALIDATION_RECEIPT_RELATIVE
LIB = unreal.EditorAssetLibrary


def project_dependencies(package: str) -> set[str]:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    options = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True,
        include_searchable_names=False,
        include_soft_management_references=False,
        include_hard_management_references=False,
    )
    dependencies = registry.get_dependencies(package, options) or []
    return {
        str(value) for value in dependencies
        if str(value).startswith("/Game/")
    }


def require_engine_entry_bootstrap_world() -> str:
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = subsystem.get_editor_world() if subsystem else None
    path = world.get_path_name() if world else ""
    if not path.startswith("/Engine/Maps/Entry."):
        raise ContractError(
            "Fresh validator must bootstrap only /Engine/Maps/Entry; actual world: "
            + path
        )
    return path


def main() -> None:
    bootstrap_world = require_engine_entry_bootstrap_world()
    validate_source(ROOT)
    if not BUILD.is_file():
        raise ContractError(f"Owned v449 build receipt missing: {BUILD}")
    if OUT.exists():
        raise ContractError(f"Refusing to overwrite validation receipt: {OUT}")
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    validate_build_receipt(ROOT, build)
    maps_before = protected_hashes(ROOT)
    sources_before = source_asset_hashes(ROOT)

    destination_objects = {}
    for package in DEST_ASSET_PACKAGES:
        value = LIB.load_asset(package)
        if value is None or value.get_path_name() != object_path(package):
            raise ContractError(f"Fresh-load failed for owned asset: {package}")
        destination_objects[package] = value
    mesh = destination_objects[DEST_MESH]
    if not isinstance(mesh, unreal.StaticMesh):
        raise ContractError("Fresh-loaded owned Press asset is not a StaticMesh")
    for package in DEST_MATERIAL_PACKAGES:
        if not isinstance(destination_objects[package], unreal.MaterialInterface):
            raise ContractError(f"Fresh-loaded owned material has wrong class: {package}")
    static_materials = list(mesh.get_editor_property("static_materials"))
    if len(static_materials) != V449_MATERIAL_SLOT_COUNT:
        raise ContractError("Fresh-loaded owned Press mesh lost its 306 slots")
    actual_slots = []
    for index in range(V449_MATERIAL_SLOT_COUNT):
        material = mesh.get_material(index)
        actual_slots.append(material.get_path_name() if material else "")
    expected_slots = expected_destination_slot_objects(ROOT)
    if actual_slots != expected_slots:
        raise ContractError("Fresh-loaded owned Press slot sequence drift")

    allowed_dependencies = set(DEST_ASSET_PACKAGES)
    dependency_rows = {
        package: sorted(project_dependencies(package))
        for package in DEST_ASSET_PACKAGES
    }
    if set(dependency_rows[DEST_MESH]) != set(DEST_ASSET_PACKAGES[1:]):
        raise ContractError(
            "Fresh-loaded aggregate dependency closure is not its exact 13 materials: "
            + json.dumps(dependency_rows[DEST_MESH])
        )
    if any(dependency_rows[package] for package in DEST_ASSET_PACKAGES[1:]):
        raise ContractError("Fresh-loaded PBR materials gained project dependencies")
    unexpected_dependencies = sorted({
        dependency
        for dependencies in dependency_rows.values()
        for dependency in dependencies
        if dependency not in allowed_dependencies
    })
    if unexpected_dependencies:
        raise ContractError(
            "Fresh-loaded owned dependency closure escaped: "
            + json.dumps(unexpected_dependencies)
        )

    maps_after = protected_hashes(ROOT)
    if maps_after != maps_before:
        raise ContractError("Protected map hashes changed during fresh-load validation")
    if sha256(ROOT / V449_RUNTIME_MESH_RELATIVE) != V449_RUNTIME_MESH_SHA256:
        raise ContractError("Source v449 mesh changed during owned validation")
    sources_after = source_asset_hashes(ROOT)
    if sources_after != sources_before:
        raise ContractError("Immutable source assets changed during fresh-load validation")

    asset_rows = []
    for package in DEST_ASSET_PACKAGES:
        path = package_file(ROOT, package)
        asset_rows.append({
            "package": package,
            "object_path": object_path(package),
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
            "class_path": destination_objects[package].get_class().get_path_name(),
        })
    payload = {
        "$schema": VALIDATION_SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "PASS__FRESH_PROCESS_OWNED_V449_PRESS_PACK_EXACT_14_ASSETS_"
            "306_REBOUND_SLOTS__NO_EXTERNAL_PROJECT_DEPENDENCIES"
        ),
        "build_receipt_sha256": sha256(BUILD),
        "source_mesh": V449_RUNTIME_MESH,
        "source_mesh_sha256": V449_RUNTIME_MESH_SHA256,
        "destination_mesh": DEST_MESH,
        "destination_asset_count": len(asset_rows),
        "destination_assets": asset_rows,
        "material_slot_count": len(actual_slots),
        "destination_slot_objects": actual_slots,
        "dependency_rows": dependency_rows,
        "unexpected_project_dependencies": [],
        "protected_map_hashes_before": maps_before,
        "protected_map_hashes_after": maps_after,
        "source_asset_hashes_before": sources_before,
        "source_asset_hashes_after": sources_after,
        "map_loaded": False,
        "map_saved": False,
        "editor_bootstrap_world": bootstrap_world,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    unreal.log(payload["status"])


try:
    main()
finally:
    unreal.SystemLibrary.quit_editor()
