"""Duplicate v026 to v027 in a dedicated editor process.

Unreal must not load a newly duplicated world while the duplicate's transient
UWorld is still retained by the asset operation.
"""

import unreal


BASE = "/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004CraneRuntimeCandidate_v027"
lib = unreal.EditorAssetLibrary

if lib.does_asset_exist(MAP):
    unreal.log(f"LINE_BOSS_PR004_CRANE_V027_PREP_EXISTS map={MAP}")
else:
    if not lib.duplicate_asset(BASE, MAP):
        raise RuntimeError(f"Could not duplicate {BASE} to {MAP}")
    if not lib.save_asset(MAP, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save duplicated map {MAP}")
    unreal.log(f"LINE_BOSS_PR004_CRANE_V027_PREP_PASS map={MAP}")
