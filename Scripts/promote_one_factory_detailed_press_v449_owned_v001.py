"""Isolated write lane for the exact pre-Meshy v449 OneFactory Press visual.

Only fourteen new assets under the dedicated OneFactory Native Press root may be
created.  Sources and protected maps are hash guarded; partial new assets are
deleted on failure.  No map is loaded or saved by this script.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

sys.dont_write_bytecode = True

import unreal


ROOT = Path(unreal.Paths.project_dir())
SCRIPT_DIR = ROOT / "Scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from one_factory_detailed_press_v001_contract import (  # noqa: E402
    ContractError,
    MATERIAL_HASHES,
    V449_MATERIAL_SLOT_COUNT,
    V449_RUNTIME_MESH,
    V449_RUNTIME_MESH_SHA256,
    sha256,
)
from one_factory_detailed_press_v449_promotion_contract import (  # noqa: E402
    BUILD_RECEIPT_RELATIVE,
    BUILD_SCHEMA,
    DEST_ASSET_PACKAGES,
    DEST_MATERIAL_ROOT,
    DEST_MESH,
    SOURCE_TO_DEST_MATERIAL,
    expected_destination_slot_objects,
    object_path,
    package_file,
    protected_hashes,
    source_asset_hashes,
    source_slot_packages,
    validate_build_receipt,
    validate_destination_absent,
    validate_source,
)


OUT = ROOT / BUILD_RECEIPT_RELATIVE
LIB = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def asset(package: str) -> Any:
    value = LIB.load_asset(package)
    if value is None:
        raise ContractError(f"Asset failed to load: {package}")
    return value


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
            "Promotion must bootstrap only /Engine/Maps/Entry; actual world: " + path
        )
    return path


def duplicate(source_package: str, destination_package: str) -> Any:
    source = asset(source_package)
    destination_name = destination_package.rsplit("/", 1)[-1]
    destination_dir = destination_package.rsplit("/", 1)[0]
    value = TOOLS.duplicate_asset(destination_name, destination_dir, source)
    if value is None or value.get_path_name().split(".", 1)[0] != destination_package:
        raise ContractError(
            f"Asset duplication failed: {source_package} -> {destination_package}"
        )
    return value


def save_new_asset(value: Any, package: str) -> None:
    if not LIB.save_loaded_asset(value, only_if_is_dirty=False):
        raise ContractError(f"Failed to save new owned asset: {package}")
    if not package_file(ROOT, package).is_file():
        raise ContractError(f"Saved owned package has no file: {package}")


def rollback(created: list[str]) -> list[str]:
    failures: list[str] = []
    # The aggregate owns hard references to all thirteen materials, so it must
    # be retired first.  Destination packages were proven absent at preflight.
    ordered = ([DEST_MESH] if DEST_MESH in created else []) + sorted(
        package for package in created if package != DEST_MESH
    )
    for package in ordered:
        if LIB.does_asset_exist(package) and not LIB.delete_asset(package):
            failures.append(package)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.SystemLibrary.collect_garbage()
    for package in ordered:
        if LIB.does_asset_exist(package) or package_file(ROOT, package).exists():
            failures.append(package)
    failures = sorted(set(failures))
    return failures


def main() -> None:
    bootstrap_world = require_engine_entry_bootstrap_world()
    validate_source(ROOT)
    validate_destination_absent(ROOT)
    if OUT.exists():
        raise ContractError(f"Refusing to overwrite one-shot build receipt: {OUT}")
    maps_before = protected_hashes(ROOT)
    sources_before = source_asset_hashes(ROOT)
    source_slots = source_slot_packages(ROOT)
    source_slot_objects = [object_path(package) for package in source_slots]

    source_mesh = asset(V449_RUNTIME_MESH)
    if not isinstance(source_mesh, unreal.StaticMesh):
        raise ContractError("Pinned v449 source is not a StaticMesh")
    source_static_materials = list(source_mesh.get_editor_property("static_materials"))
    if len(source_static_materials) != V449_MATERIAL_SLOT_COUNT:
        raise ContractError("Pinned v449 source mesh lost its exact 306 slots")
    actual_source_slots = []
    for index in range(V449_MATERIAL_SLOT_COUNT):
        material = source_mesh.get_material(index)
        actual_source_slots.append(material.get_path_name() if material else "")
    if actual_source_slots != source_slot_objects:
        raise ContractError("Pinned v449 source mesh material-slot sequence drift")
    source_dependencies = project_dependencies(V449_RUNTIME_MESH)
    if source_dependencies != set(MATERIAL_HASHES):
        raise ContractError(
            "Pinned v449 mesh dependency closure differs from its exact 13 materials: "
            + json.dumps(sorted(source_dependencies))
        )

    created: list[str] = []
    try:
        owned_materials: dict[str, Any] = {}
        for source_package in sorted(MATERIAL_HASHES):
            destination = SOURCE_TO_DEST_MATERIAL[source_package]
            owned = duplicate(source_package, destination)
            if not isinstance(owned, unreal.MaterialInterface):
                raise ContractError(f"Owned material has wrong class: {destination}")
            created.append(destination)
            owned_materials[source_package] = owned

        owned_mesh = duplicate(V449_RUNTIME_MESH, DEST_MESH)
        if not isinstance(owned_mesh, unreal.StaticMesh):
            raise ContractError("Owned v449 duplicate is not a StaticMesh")
        created.append(DEST_MESH)
        for index, source_package in enumerate(source_slots):
            owned_mesh.set_material(index, owned_materials[source_package])
        for source_package in sorted(MATERIAL_HASHES):
            save_new_asset(
                owned_materials[source_package],
                SOURCE_TO_DEST_MATERIAL[source_package],
            )
        save_new_asset(owned_mesh, DEST_MESH)
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

        destination_slots = []
        for index in range(V449_MATERIAL_SLOT_COUNT):
            material = owned_mesh.get_material(index)
            destination_slots.append(material.get_path_name() if material else "")
        expected_slots = expected_destination_slot_objects(ROOT)
        if destination_slots != expected_slots:
            raise ContractError("Owned mesh material-slot rebind failed")
        live_binding_material_packages = sorted({
            value.split(".", 1)[0] for value in destination_slots
        })
        if set(live_binding_material_packages) != set(DEST_ASSET_PACKAGES[1:]):
            raise ContractError("Owned live material binding closure is not exact")
        allowed_dependencies = set(DEST_ASSET_PACKAGES)
        same_process_registry_rows = {
            package: sorted(project_dependencies(package))
            for package in DEST_ASSET_PACKAGES
        }
        unexpected_owned_dependencies = sorted({
            dependency
            for dependencies in same_process_registry_rows.values()
            for dependency in dependencies
            if dependency not in allowed_dependencies
        })
        if unexpected_owned_dependencies:
            raise ContractError(
                "Owned closure escaped the dedicated OneFactory root: "
                + json.dumps(unexpected_owned_dependencies)
            )
        # UE does not index a newly saved package's dependency graph until an
        # AssetRegistry restart.  This receipt therefore proves the exact live
        # 306-slot binding closure; the independent process below is solely
        # responsible for proving the persisted registry closure.
        dependency_rows = {
            DEST_MESH: live_binding_material_packages,
            **{package: [] for package in DEST_ASSET_PACKAGES[1:]},
        }

        maps_after = protected_hashes(ROOT)
        if maps_after != maps_before:
            raise ContractError("Protected map hashes changed during promotion")
        sources_after = source_asset_hashes(ROOT)
        if sources_after != sources_before:
            raise ContractError("Immutable v449 source assets changed during promotion")
        destination_assets = []
        for package in DEST_ASSET_PACKAGES:
            path = package_file(ROOT, package)
            destination_assets.append({
                "package": package,
                "object_path": object_path(package),
                "file_relative": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
        payload = {
            "$schema": BUILD_SCHEMA,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "status": (
                "PASS__EXACT_PRE_MESHY_V449_DUPLICATED_AND_REBOUND_IN_"
                "ONEFACTORY_NATIVE_PRESS_ROOT__NO_MAP_SAVED"
            ),
            "source_mesh": V449_RUNTIME_MESH,
            "source_mesh_sha256": V449_RUNTIME_MESH_SHA256,
            "source_material_hashes": MATERIAL_HASHES,
            "source_material_slot_objects": source_slot_objects,
            "destination_mesh": DEST_MESH,
            "destination_asset_count": len(destination_assets),
            "destination_assets": destination_assets,
            "material_slot_count": len(destination_slots),
            "destination_slot_objects": destination_slots,
            "dependency_rows": dependency_rows,
            "dependency_proof": "EXACT_LIVE_306_STATIC_MESH_MATERIAL_BINDINGS",
            "same_process_asset_registry_dependency_rows": (
                same_process_registry_rows
            ),
            "persisted_asset_registry_dependency_closure_deferred_to_fresh_process": True,
            "protected_map_hashes_before": maps_before,
            "protected_map_hashes_after": maps_after,
            "source_asset_hashes_before": sources_before,
            "source_asset_hashes_after": sources_after,
            "source_assets_modified": False,
            "map_loaded": False,
            "map_saved": False,
            "editor_bootstrap_world": bootstrap_world,
        }
        validate_build_receipt(ROOT, payload)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        unreal.log(payload["status"])
    except Exception:
        # Destination packages were proven absent before mutation, so an exact
        # inventory scan is safer than trusting that duplication returned before
        # every newly-created package was appended to ``created``.
        rollback_candidates = [
            package for package in DEST_ASSET_PACKAGES
            if LIB.does_asset_exist(package)
        ]
        rollback_failures = rollback(rollback_candidates)
        if rollback_failures:
            unreal.log_error(
                "OWNED V449 PROMOTION ROLLBACK FAILED: "
                + json.dumps(rollback_failures)
            )
        raise


try:
    main()
finally:
    unreal.SystemLibrary.quit_editor()
