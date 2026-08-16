"""Texture-preserving isolated Unreal intake for the supplied PR005 detailed HMI.

This creates a new candidate asset only.  It does not edit maps, runtime bindings,
engineering sources, gameplay, saves, collision contracts, or v913.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir())
SOURCE = PROJECT / (
    "SourceAssets/Shared/FactoryAssetLibrary/MeshyCabinetHMI_v632/"
    "SM_CA_Factory_OperatorHMI_MeshyMaster_v632.glb"
)
DESTINATION = "/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001"
ASSET_NAME = "SM_CA_MW_PR005_DetailedHMI_Meshy_v001"
EXPECTED_PATH = f"{DESTINATION}/{ASSET_NAME}"
AUDIT = PROJECT / "Saved/Audits/PR005/HMI_v001/pr005_detailed_hmi_texture_intake_v001.json"


def material_record(slot: unreal.StaticMaterial) -> dict[str, str]:
    material = slot.get_editor_property("material_interface")
    return {
        "slot_name": str(
            slot.get_editor_property("imported_material_slot_name")
            or slot.get_editor_property("material_slot_name")
        ),
        "material": material.get_path_name() if material else "",
        "material_class": material.get_class().get_name() if material else "",
    }


def main() -> None:
    library = unreal.EditorAssetLibrary
    if not SOURCE.is_file():
        raise RuntimeError(f"Missing immutable HMI source: {SOURCE}")
    if library.does_asset_exist(EXPECTED_PATH):
        raise RuntimeError(f"Fresh-candidate invariant failed: {EXPECTED_PATH} already exists")

    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE),
        "destination_path": DESTINATION,
        "destination_name": ASSET_NAME,
        "automated": True,
        "replace_existing": False,
        "replace_existing_settings": False,
        "save": True,
    })
    # GLB uses the UE 5.8 Interchange route.  No generic material override is applied:
    # the source PBR atlas must remain intact for this first candidate validation.
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

    imported_paths = list(task.get_editor_property("imported_object_paths"))
    candidates = [
        library.load_asset(path)
        for path in imported_paths
        if library.load_asset(path) is not None
    ]
    mesh = library.load_asset(EXPECTED_PATH)
    if not isinstance(mesh, unreal.StaticMesh):
        mesh = next((asset for asset in candidates if isinstance(asset, unreal.StaticMesh)), None)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"No static mesh imported from {SOURCE}; imported={imported_paths}")

    bounds = mesh.get_bounds()
    static_materials = mesh.get_editor_property("static_materials")
    records = [material_record(slot) for slot in static_materials]
    if not records or any(not record["material"] for record in records):
        raise RuntimeError(f"Texture retention gate failed: missing material slot(s): {records}")

    # Intentionally do not enable collision, nav, or Nanite by assumption.  The asset
    # remains a visual-only candidate until rendered/material/bounds QA establishes policy.
    library.save_loaded_asset(mesh, only_if_is_dirty=False)
    library.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "status": "CANDIDATE_ONLY__TEXTURE_PRESERVATION_PASS__NO_RUNTIME_BINDING",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "immutable_source": str(SOURCE),
        "source_unchanged": True,
        "destination": DESTINATION,
        "static_mesh": mesh.get_path_name(),
        "imported_paths": imported_paths,
        "bounds_cm": {
            "origin": [round(bounds.origin.x, 4), round(bounds.origin.y, 4), round(bounds.origin.z, 4)],
            "box_extent": [round(bounds.box_extent.x, 4), round(bounds.box_extent.y, 4), round(bounds.box_extent.z, 4)],
            "size": [round(bounds.box_extent.x * 2, 4), round(bounds.box_extent.y * 2, 4), round(bounds.box_extent.z * 2, 4)],
        },
        "material_slots": records,
        "texture_policy": "KEEP_IMPORTED_PBR_ATLAS_INTACT__NO_GLOBAL_LIVERY_TINT",
        "collision_policy": "NOT_USED_FOR_GAMEPLAY__COMPONENT_MUST_BE_NO_COLLISION_NO_NAV_NO_OVERLAPS",
        "nanite_policy": "PENDING_RENDERED_VALIDATION",
        "runtime_binding": "NOT_STARTED",
        "map_change": "NONE",
        "v913_change": "NONE",
    }
    AUDIT.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_TEXTURE_INTAKE_PASS mesh={mesh.get_path_name()} audit={AUDIT}")


main()
