"""Fresh visual correction of v522; v522 remains rejected evidence."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v522.py").read_text(encoding="utf-8")
source = source.replace("v522", "v523").replace("V522", "V523").replace("V022_", "V023_")
exec(compile(source, str(root / "build_inbound_installed_cell_v522.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_INBOUND_V023_HallRoof":
        actor.set_actor_location(unreal.Vector(0, 0, 1600), False, False)
    elif label.startswith("LB_INBOUND_V023_RoofBeam_"):
        loc = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(loc.x, loc.y, 1480), False, False)
    elif isinstance(actor, unreal.RectLight):
        component = actor.rect_light_component
        component.set_editor_property("intensity", min(float(component.get_editor_property("intensity")) * .16, 125.0))
    elif isinstance(actor, unreal.PostProcessVolume):
        settings = actor.settings
        settings.set_editor_property("auto_exposure_bias", -1.1)
        actor.settings = settings

overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v523")
overview.set_actor_location(unreal.Vector(3100, -3600, 1800), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(0, 0, 235)), False)
overview.camera_component.set_editor_property("field_of_view", 57.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v523")
hero.set_actor_location(unreal.Vector(-500, -2850, 1325), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(80, 0, 360)), False)
hero.camera_component.set_editor_property("field_of_view", 52.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v523 corrected hall review")
unreal.log("LINE_BOSS_INBOUND_HALL_CONTEXT_V523_BUILD_PASS")
