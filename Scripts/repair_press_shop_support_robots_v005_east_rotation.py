"""Correct the east LB-CR01 assembly accidentally pitched below the floor."""
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
labels = ("LB_CR01_EAST_", "LB_CR01_DOCK_EAST_")
fixed = 0
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith(labels):
        actor.set_actor_rotation(unreal.Rotator(0.0, 0.0, 180.0), False)
        fixed += 1
if fixed != 95:
    raise RuntimeError(f"Expected 95 east cleaner/dock actors, fixed {fixed}")
if not levels.save_current_level():
    raise RuntimeError("Could not save corrected Press Shop v005")
unreal.log(f"LINE_BOSS_PRESS_V005_EAST_ROTATION_REPAIR_PASS actors={fixed}")
