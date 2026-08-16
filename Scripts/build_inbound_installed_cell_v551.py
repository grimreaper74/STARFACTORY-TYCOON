"""Corrected signage/control successor: retain useful v550 work, remove dominant stripes."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v550.py").read_text(encoding="utf-8")
source = source.replace("v550", "v551").replace("V550", "V551").replace("V050_", "V051_")
exec(compile(source, str(root / "build_inbound_installed_cell_v550.py"), "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

# The long v550 stripes competed with the machinery and implied verified
# engineering clearances. The Pro sheets mark every such value TBC, so remove
# them and retain only the established route/floor language.
for actor in list(actors.get_all_level_actors()):
    if actor.get_actor_label().startswith("LB_INBOUND_V051_ProcessBoundary_"):
        actors.destroy_actor(actor)

# Bring the three identities into the machinery sightline and make their text
# legible from the fixed review camera without enlarging the boards.
for stem, x, text_size in (
    ("DockIdentity", -3350, 54.0),
    ("CraneIdentity", -450, 50.0),
):
    board = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == f"LB_INBOUND_V051_{stem}Board")
    text = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == f"LB_INBOUND_V051_{stem}Text")
    board.set_actor_location(unreal.Vector(x, -1900, 1140), False, False)
    text.set_actor_location(unreal.Vector(x, -1815, 1140), False, False)
    text.text_render.set_editor_property("world_size", text_size)

pr_board = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V051_PR003IdentitySign")
pr_text = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_INBOUND_V051_PR003SignText")
pr_board.set_actor_location(unreal.Vector(3150, -1900, 1140), False, False)
pr_text.set_actor_location(unreal.Vector(3150, -1815, 1140), False, False)
pr_text.text_render.set_editor_property("world_size", 50.0)

# Restore a useful inspection scale while keeping the full left-to-right process
# readable in one shot.
overview = next(a for a in actors.get_all_level_actors() if a.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v551")
overview.set_actor_location(unreal.Vector(-500, 6900, 2200), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-500, -100, 400)), False)
overview.camera_component.set_editor_property("field_of_view", 51.0)

if not levels.save_current_level():
    raise RuntimeError("Failed saving v551 corrected signage review")
unreal.log("LINE_BOSS_INBOUND_SIGNAGE_CONTROLS_V551_BUILD_PASS")
