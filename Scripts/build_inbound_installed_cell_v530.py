"""Fresh v530: fully separate docked lorry from protected crane bay."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v529.py").read_text(encoding="utf-8")
source = source.replace("v529", "v530").replace("V529", "V530").replace("V029_", "V030_")
exec(compile(source, str(root / "build_inbound_installed_cell_v529.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def find(suffix):
    return next((a for a in actors.get_all_level_actors()
                 if a.get_actor_label().endswith(suffix)), None)

def place(suffix, location, yaw=None):
    actor = find(suffix)
    if actor is None:
        raise RuntimeError(f"Missing v530 actor: {suffix}")
    actor.set_actor_location(unreal.Vector(*location), False, False)
    if yaw is not None:
        actor.set_actor_rotation(unreal.Rotator(0, 0, yaw), False)
    return actor

# A full additional metre-scale bay separation keeps the tractor nose and
# trailer clear of the protected C-hook envelope.
place("LorryFourCoil_Coherent", (-2200, 0, 0), -90)
place("DockGuidesAndRestraint", (-2350, 0, 35), -90)
place("EntranceDockEnvelope", (-3050, 0, 244), -90)
place("DockControlAndSignals", (-2650, -350, 125), -90)

overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v530")
overview.set_actor_location(unreal.Vector(-750, -7200, 2350), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(-750, 0, 260)), False)
overview.camera_component.set_editor_property("field_of_view", 46.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v530")
hero.set_actor_location(unreal.Vector(1500, -4300, 1850), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(-200, 0, 300)), False)
hero.camera_component.set_editor_property("field_of_view", 54.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v530 separated inbound cell")
unreal.log("LINE_BOSS_INBOUND_SEPARATED_SEQUENCE_V530_BUILD_PASS")
