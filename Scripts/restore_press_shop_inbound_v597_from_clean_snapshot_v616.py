"""One-use semantic restore after UE 5.8 Save Map kept the parent world active.

The v616 package was written before any actor edits.  Load that clean snapshot
and save its world back under the v597 package path, then exit without further
mutation.  A byte-for-byte copy of the touched v597 is retained in Saved first.
"""
import unreal

SNAPSHOT = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
TARGET = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not levels.load_level(SNAPSHOT):
    raise RuntimeError("Clean pre-edit snapshot could not be loaded")
if not unreal.EditorLoadingAndSavingUtils.save_map(editor.get_editor_world(), TARGET):
    raise RuntimeError("v597 semantic restore failed")
unreal.log("LB_INBOUND_V597_SEMANTIC_RESTORE_FROM_CLEAN_SNAPSHOT_PASS")
