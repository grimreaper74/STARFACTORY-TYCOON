"""Prepare preserved v021 map/mesh packages without loading the new map."""

import unreal


SOURCE_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006"
DEST_MAP = "/Game/LineBoss/Maps/LB_PressShop_BareCoilFrontEndCandidate_v021"
SOURCE_MESH = (
    "/Game/LineBoss/Stations/Press/PR004/Candidate_v006/PackagingRig_v004/"
    "SM_LB_PR004_BareCoilCore_v004"
)
DEST_MESH = (
    "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/"
    "SM_LB_BareMasterCoil_v021"
)

lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(DEST_MAP):
    raise RuntimeError(f"Refusing to overwrite preserved candidate map {DEST_MAP}")
if not lib.duplicate_asset(SOURCE_MAP, DEST_MAP):
    raise RuntimeError("Could not duplicate accepted v006 map")
if not lib.save_asset(DEST_MAP, only_if_is_dirty=False):
    raise RuntimeError("Could not save prepared v021 map package")

if not lib.does_asset_exist(DEST_MESH):
    if not lib.duplicate_asset(SOURCE_MESH, DEST_MESH):
        raise RuntimeError("Could not duplicate accepted bare-coil mesh")
    if not lib.save_asset(DEST_MESH, only_if_is_dirty=False):
        raise RuntimeError("Could not save prepared v021 bare-coil mesh")

unreal.log(
    f"LINE_BOSS_BARE_COIL_FRONT_END_V021_PREPARE_PASS map={DEST_MAP} mesh={DEST_MESH}"
)
unreal.SystemLibrary.quit_editor()
