"""Migrate only potentially useful Factory Environment audio into Line Boss."""

import unreal


DESTINATION = r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content"
PACKAGES = [
    "/Game/Audio/S_AssemblyLine",
    "/Game/Audio/S_Motorized",
    "/Game/Audio/S_Ventilation",
    "/Game/Audio/S_Welding",
    "/Game/Audio/Cue_AssemblyLine",
    "/Game/Audio/Cue_Ventilation",
]

options = unreal.MigrationOptions(
    prompt=False,
    ignore_dependencies=False,
    asset_conflict=unreal.AssetMigrationConflict.SKIP,
)
unreal.AssetToolsHelpers.get_asset_tools().migrate_packages(
    [unreal.Name(package) for package in PACKAGES], DESTINATION, options
)
unreal.log(
    f"LINE_BOSS_FACTORY_AUDIO_MIGRATION_PASS requested={len(PACKAGES)} target={DESTINATION}"
)
