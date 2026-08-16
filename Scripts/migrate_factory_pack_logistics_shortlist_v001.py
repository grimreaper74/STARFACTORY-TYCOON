"""Migrate only the approved Factory Environment logistics shortlist.

Run against the licensed vendor FactoryProject.  Dependencies are included,
conflicts are skipped, and the canonical project later contains the packages
inside its LineBoss vendor namespace.
"""

import unreal


DESTINATION = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content"
PACKAGES = [
    "/Game/Meshes/SM_ForkLift",
    "/Game/Meshes/SM_Forklift_prop_grate",
    "/Game/Meshes/SM_Forklift_prop_light",
    "/Game/Meshes/SM_Forklift_prop_seat",
    "/Game/Meshes/SM_Forklift_prop_wheel",
    "/Game/Meshes/SM_PalletCart",
    "/Game/Meshes/SM_PalletCart_box",
    "/Game/Meshes/SM_PalletCart_PalletBox_open",
    "/Game/Meshes/SM_PlasticPallet01",
    "/Game/Meshes/SM_AssemblyLineCrate01",
]

options = unreal.MigrationOptions(
    prompt=False,
    ignore_dependencies=False,
    asset_conflict=unreal.AssetMigrationConflict.SKIP,
)
unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
    [unreal.Name(package) for package in PACKAGES], DESTINATION, options)
unreal.log(
    f"LINE_BOSS_FACTORY_LOGISTICS_MIGRATION_PASS requested={len(PACKAGES)} "
    f"target={DESTINATION}"
)

