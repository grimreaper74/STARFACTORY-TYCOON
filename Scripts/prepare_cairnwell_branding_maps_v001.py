"""Duplicate branding validation maps without loading either destination."""

import unreal

asset_lib = unreal.EditorAssetLibrary
maps = [
    (
        "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation",
        "/Game/LineBoss/Developer/Validation/LB_HMI04_CairnwellBranding_v001",
    ),
    (
        "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation",
        "/Game/LineBoss/Developer/Validation/LB_PR005_CairnwellBranding_v001",
    ),
]
for source, destination in maps:
    if not asset_lib.does_asset_exist(destination):
        if not asset_lib.duplicate_asset(source, destination):
            raise RuntimeError(f"Could not duplicate {source} to {destination}")
    if not asset_lib.save_asset(destination, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {destination}")
unreal.log("LINE_BOSS_CAIRNWELL_BRANDING_MAP_PREP_PASS")
