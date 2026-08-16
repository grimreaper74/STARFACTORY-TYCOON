"""Direct-v438 inbound integration with a deliberate west receiving-bay expansion."""
from pathlib import Path
import unreal

root = Path(__file__).parent
source = (root / "build_press_shop_inbound_integration_candidate_v568.py").read_text(encoding="utf-8")
source = source.replace("v568", "v570").replace("V568", "V570")
source = source.replace("-11000.0, -2000.0, 0.0", "-12000.0, -2000.0, 0.0")
source = source.replace("(-15300, 1200, 1350), (-11600,-2000,260)", "(-15600, 1800, 1350), (-12300,-2000,260)")
source = source.replace("(-9800,800,900), (-11200,-2000,260)", "(-10200,900,900), (-11900,-2000,260)")
exec(compile(source, str(root / "build_press_shop_inbound_integration_candidate_v568.py"), "exec"), globals(), globals())

# Enlarge the inherited hall in the candidate only. Preserve the established
# east end and move the west end 50 m outward, matching the owner's direction
# to increase the factory rather than compress realistic station spacing.
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
by_label = {a.get_actor_label(): a for a in actors.get_all_level_actors()}

def require(label):
    actor = by_label.get(label)
    if actor is None:
        raise RuntimeError(f"Missing inherited shell actor {label}")
    return actor

for label in ("LB_PRESS_FinishedFloor", "LB_PRESS_Wall_North", "LB_PRESS_Wall_South"):
    actor = require(label)
    actor.set_actor_location(unreal.Vector(-2500.0, actor.get_actor_location().y, actor.get_actor_location().z), False, False)
    scale = actor.get_actor_scale3d()
    actor.set_actor_scale3d(unreal.Vector(270.0, scale.y, scale.z))
    actor.tags = list(actor.tags) + [unreal.Name("LB.Environment.WestBayExpansion.v570")]

west = require("LB_PRESS_Wall_West")
west.set_actor_location(unreal.Vector(-16000.0, 0.0, 900.0), False, False)
west.tags = list(west.tags) + [unreal.Name("LB.Environment.WestBayExpansion.v570")]

liner = require("LB_INT_FRONT_WestWallLiner")
liner.set_actor_location(unreal.Vector(-15972.0, -3250.0, 1200.0), False, False)
liner.tags = list(liner.tags) + [unreal.Name("LB.Environment.WestBayExpansion.v570")]

if not levels.save_current_level():
    raise RuntimeError("Failed saving v570 expanded shell")
unreal.log("LINE_BOSS_INBOUND_WEST_BAY_EXPANSION_V570_PASS")
