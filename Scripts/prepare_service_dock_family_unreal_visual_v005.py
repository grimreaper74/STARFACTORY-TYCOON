"""Create a fresh v005 child of the rejected isolated v004 dock visual map."""
import unreal

SOURCE = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v004"
TARGET = "/Game/LineBoss/Developer/Validation/LB_ServiceDockFamilyVisual_v005"
lib = unreal.EditorAssetLibrary
if lib.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite existing visual candidate {TARGET}")
if not lib.duplicate_asset(SOURCE, TARGET):
    raise RuntimeError(f"Could not duplicate {SOURCE} to {TARGET}")
if not lib.save_asset(TARGET, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {TARGET}")
unreal.log("LINE_BOSS_SERVICE_DOCK_VISUAL_V005_PREPARE_PASS")
