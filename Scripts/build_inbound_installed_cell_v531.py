"""Fresh v531: full validation floor and owner-direction cameras."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v530.py").read_text(encoding="utf-8")
source = source.replace("v530", "v531").replace("V530", "V531").replace("V030_", "V031_")
exec(compile(source, str(root / "build_inbound_installed_cell_v530.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

floor = next(a for a in actors.get_all_level_actors()
             if a.get_actor_label().endswith("Floor"))
floor.set_actor_scale3d(unreal.Vector(70, 28, 0.24))
floor.set_actor_location(unreal.Vector(-650, 0, -15), False, False)

# Opposite aisle presents the physical X sequence as lorry -> crane -> saddle
# -> AGV from left to right, matching the owner reference pack.
overview = next(a for a in actors.get_all_level_actors()
                if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v531")
overview.set_actor_location(unreal.Vector(-750, 7200, 2350), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    overview.get_actor_location(), unreal.Vector(-750, 0, 260)), False)
overview.camera_component.set_editor_property("field_of_view", 46.0)

hero = next(a for a in actors.get_all_level_actors()
            if a.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v531")
hero.set_actor_location(unreal.Vector(1500, 4300, 1850), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    hero.get_actor_location(), unreal.Vector(-200, 0, 300)), False)
hero.camera_component.set_editor_property("field_of_view", 54.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v531 owner-direction inbound cell")
unreal.log("LINE_BOSS_INBOUND_OWNER_DIRECTION_V531_BUILD_PASS")
