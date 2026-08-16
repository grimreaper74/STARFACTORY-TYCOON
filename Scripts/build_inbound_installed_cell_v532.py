"""Fresh v532: cutaway validation view of the retained v530 spacing."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v531.py").read_text(encoding="utf-8")
source = source.replace("v531", "v532").replace("V531", "V532").replace("V031_", "V032_")
exec(compile(source, str(root / "build_inbound_installed_cell_v531.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# The supplied Pro evidence is a roof-off/cutaway presentation. Remove only
# the near evidence wall and roof in this isolated successor; structural beams
# and columns remain so scale and installed context are still judged.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label() in ("LB_INBOUND_V032_HallFarWall", "LB_INBOUND_V032_HallRoof"):
        actors.destroy_actor(actor)

overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v532")
overview.set_actor_location(unreal.Vector(-750, 6100, 2200), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(-750, 0, 240)), False)
overview.camera_component.set_editor_property("field_of_view", 48.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v532")
hero.set_actor_location(unreal.Vector(1750, 3800, 1550), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(-250, 0, 300)), False)
hero.camera_component.set_editor_property("field_of_view", 56.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v532 cutaway inbound review")
unreal.log("LINE_BOSS_INBOUND_CUTAWAY_V532_BUILD_PASS")
