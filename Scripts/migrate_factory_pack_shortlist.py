"""Migrate only the approved Factory Environment shortlist and dependencies.

Run against the vendor FactoryProject.  The target project subsequently moves
the imported root folders into the Line Boss vendor namespace while Unreal
repairs references.
"""

import unreal


DESTINATION = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content"
PACKAGES = [
    "/Game/Meshes/SM_Cables01",
    "/Game/Meshes/SM_CableSet_01",
    "/Game/Meshes/SM_ElectricalCable_01",
    "/Game/Meshes/SM_Pipe_round_long",
    "/Game/Meshes/SM_Pipe_round_corner1",
    "/Game/Meshes/SM_Pipe_round_tee_transition1",
    "/Game/Meshes/SM_Pipe_round_fixator",
    "/Game/Meshes/SM_Fence_01",
    "/Game/Meshes/SM_FencePart_01",
    "/Game/Meshes/SM_IndustrialPlatform01",
    "/Game/Meshes/SM_PlatformRailing_01",
    "/Game/Meshes/SM_MetalBeam01",
    "/Game/Meshes/SM_Column_02",
    "/Game/Meshes/SM_Lamp01",
    "/Game/Meshes/Crane/SM_ElectricMotor01",
]

options = unreal.MigrationOptions(
    prompt=False,
    ignore_dependencies=False,
    asset_conflict=unreal.AssetMigrationConflict.SKIP,
)
unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
    [unreal.Name(package) for package in PACKAGES], DESTINATION, options)
unreal.log(f"LINE_BOSS_FACTORY_PACK_MIGRATION_PASS requested={len(PACKAGES)} target={DESTINATION}")
